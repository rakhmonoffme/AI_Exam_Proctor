from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import cv2
import threading
import base64
import json
from datetime import datetime
import time

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.score import ProctoringScoreSystem
from database.db import ProctoringDatabase

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60, ping_interval=25)

# Store active sessions
active_sessions = {}
db = ProctoringDatabase()

class SessionMonitor:
    def __init__(self, user_id, exam_id):
        self.user_id = user_id
        self.exam_id = exam_id
        self.scorer = ProctoringScoreSystem()
        self.is_running = False
        self.session_id = None
        
    def start(self):
        """Start monitoring session (web-based, frames come from client)"""
        self.is_running = True
        self.scorer.current_user_id = self.user_id
        session_data = {
            'user_id': self.user_id,
            'exam_id': self.exam_id,
            'start_time': datetime.now().isoformat()
        }
        self.session_id = self.scorer.db.create_session(session_data)
        self.scorer.session_id = self.session_id
        self.scorer._start_new_interval()
        self.scorer.screen_monitor.start_monitoring()
        
    def stop(self):
        """Stop monitoring"""
        self.is_running = False
        
        # Generate final report
        report = self.scorer.generate_report()
        if self.session_id:
            self.scorer.db.end_session(self.session_id, report)
        
        self.scorer.close()
        return report

# ============= REST API ENDPOINTS =============
@app.route('/')
def index():
    return "AI Proctoring Backend is running."

@app.route('/api/session/<session_id>/frame', methods=['POST'])
def receive_frame(session_id):
    """Receive frame from client browser"""
    data = request.json
    frame_base64 = data.get('frame')
    screen_activity = data.get('screen_activity', {})
    
    if not frame_base64:
        return jsonify({'error': 'Missing frame data'}), 400
    
    # Find active session
    monitor = None
    for key, mon in active_sessions.items():
        if str(mon.session_id) == session_id:
            monitor = mon
            break
    
    if not monitor:
        return jsonify({'error': 'Session not found'}), 200
    if not monitor.is_running:
        return jsonify({'success': True, 'message': 'Session ending'}), 201
    
    try:
        import numpy as np
        # Decode base64 frame
        frame_data = base64.b64decode(frame_base64.split(',')[1] if ',' in frame_base64 else frame_base64)
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid frame data'}), 400
        
        # Run AI analysis
        gaze_result = monitor.scorer.analyze_gaze(frame)
        face_result = monitor.scorer.analyze_faces(frame)
        
        # Update screen activity scores
        if screen_activity:
            monitor.scorer.screen_monitor.tab_switches = screen_activity.get('tabSwitches', 0)
            monitor.scorer.screen_monitor.copy_paste_events = screen_activity.get('copyPasteEvents', 0)
        
        # Write frame to video if recording
        if monitor.scorer.video_writer:
            monitor.scorer.video_writer.write(frame)
        elif not monitor.scorer.is_recording:
            h, w = frame.shape[:2]
            monitor.scorer._start_video_recording(w, h)
        
        # Encode frame for streaming
        _, buffer = cv2.imencode('.jpg', frame)
        frame_encoded = base64.b64encode(buffer).decode('utf-8')
        
        # Emit real-time update
        socketio.emit('monitoring_update', {
            'session_id': session_id,
            'user_id': monitor.user_id,
            'frame': f'data:image/jpeg;base64,{frame_encoded}',
            'gaze': {
                'status': 'focused' if gaze_result.get('focused') else 'distracted',
                'horizontal_ratio': 0.5,
                'vertical_ratio': 0.5
            },
            'faces': {
                'count': face_result.get('num_faces', 0),
                'has_multiple': face_result.get('multiple_faces', False)
            },
            'audio': {
                'speech_detected': False,
                'multiple_speakers': False
            },
            'screen': {
                'tab_switches': screen_activity.get('tabSwitches', 0),
                'copy_paste_events': screen_activity.get('copyPasteEvents', 0)
            },
            'interval_score': monitor.scorer.interval_score,
            'total_score': monitor.scorer.total_score,
            'violations': monitor.scorer.interval_violations,
            'status': 'flagged' if monitor.scorer.interval_score >= monitor.scorer.FLAG_THRESHOLD else 'clear',
            'timestamp': datetime.now().isoformat()
        }, room=session_id)
        
        # Check interval completion
        elapsed = time.time() - monitor.scorer.interval_start_time
        if elapsed >= monitor.scorer.INTERVAL_DURATION:
            if monitor.scorer.interval_score < monitor.scorer.FLAG_THRESHOLD:
                video_file = monitor.scorer._stop_video_recording()
                if video_file and os.path.exists(video_file):
                    os.remove(video_file)
            monitor.scorer._start_new_interval()
        
        return jsonify({
            'success': True,
            'interval_score': monitor.scorer.interval_score,
            'total_score': monitor.scorer.total_score
        })
        
    except Exception as e:
        print(f"Error processing frame: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/session/create', methods=['POST'])
def create_session():
    """Create a new monitoring session"""
    data = request.json
    user_id = data.get('user_id')
    exam_id = data.get('exam_id', 'default_exam')
    
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    # Create session monitor
    monitor = SessionMonitor(user_id, exam_id)
    monitor.start()
    
    # Store in active sessions
    session_key = f"{user_id}_{exam_id}"
    active_sessions[session_key] = monitor
    
    return jsonify({
        'success': True,
        'session_id': str(monitor.session_id),
        'user_id': user_id,
        'exam_id': exam_id,
        'message': 'Session started successfully'
    })

@app.route('/api/session/end', methods=['POST'])
def end_session():
    """End a monitoring session"""
    data = request.json
    user_id = data.get('user_id')
    exam_id = data.get('exam_id', 'default_exam')
    
    session_key = f"{user_id}_{exam_id}"
    
    if session_key not in active_sessions:
        return jsonify({'error': 'Session not found'}), 404
    
    monitor = active_sessions[session_key]
    
    try:
        report = monitor.stop()
        del active_sessions[session_key]
        
        # Convert ObjectId to string in report
        if '_id' in report:
            report['_id'] = str(report['_id'])
        if 'session_id' in report:
            report['session_id'] = str(report['session_id'])
        
        # Convert ObjectId in flagged intervals
        if 'flagged_intervals' in report:
            for interval in report['flagged_intervals']:
                if '_id' in interval:
                    interval['_id'] = str(interval['_id'])
                if 'session_id' in interval:
                    interval['session_id'] = str(interval['session_id'])
                if 'video_id' in interval:
                    interval['video_id'] = str(interval['video_id'])
        
        return jsonify({
            'success': True,
            'message': 'Session ended successfully'
        })
    except Exception as e:
        print(f"Error ending session: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/sessions/active', methods=['GET'])
def get_active_sessions():
    """Get all active sessions"""
    sessions = []
    for key, monitor in active_sessions.items():
        sessions.append({
            'user_id': monitor.user_id,
            'exam_id': monitor.exam_id,
            'session_id': str(monitor.session_id),
            'interval_score': monitor.scorer.interval_score,
            'total_score': monitor.scorer.total_score,
            'is_running': monitor.is_running
        })
    
    return jsonify(sessions)

@app.route('/api/sessions/stats', methods=['GET'])
def get_session_stats():
    """Get overall statistics"""
    all_sessions = list(db.sessions.find())
    flagged_intervals = list(db.flagged_intervals.find())
    
    stats = {
        'total_sessions': len(all_sessions),
        'active_sessions': len(active_sessions),
        'flagged_intervals': len(flagged_intervals),
        'high_risk': len([f for f in flagged_intervals if f.get('score', 0) > 20])
    }
    
    return jsonify(stats)
@app.route('/api/session/<session_id>/details', methods=['GET'])
def get_session_details(session_id):
    """Get details of a specific session with ALL violations and flagged intervals"""
    from bson.objectid import ObjectId
    
    try:
        session = db.sessions.find_one({'_id': ObjectId(session_id)})
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get ALL violations for this session (from violations collection)
        all_violations = db.get_session_violations(session_id)
        
        # Get flagged intervals with video paths
        flagged = db.get_session_flagged_intervals(session_id)
        
        # Convert ObjectId to string
        session['_id'] = str(session['_id'])
        
        # Format flagged intervals for frontend
        formatted_flagged = []
        for flag in flagged:
            formatted_flagged.append({
                'interval_id': str(flag['_id']),
                'start_time': flag.get('interval_start', ''),
                'end_time': flag.get('interval_end', ''),
                'score': flag.get('score', 0),
                'video_path': flag.get('video_path', ''),  # File path instead of GridFS ID
                'violations': flag.get('violations', [])
            })
        
        return jsonify({
            'session': session,
            'all_violations': all_violations,  # NEW: All violations from entire session
            'flagged_intervals': formatted_flagged,
            'monitoring_data': {
                'total_score': session.get('total_score', 0),
                'interval_score': session.get('current_interval_score', 0)
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/flagged/all', methods=['GET'])
def get_all_flagged():
    """Get all flagged intervals"""
    flagged = db.get_all_flagged_intervals(limit=100)
    
    # Convert ObjectId to string
    for flag in flagged:
        flag['_id'] = str(flag['_id'])
        if 'video_id' in flag:
            flag['video_id'] = str(flag['video_id'])
    
    return jsonify({'flagged_intervals': flagged, 'count': len(flagged)})

@app.route('/api/video/<video_id>', methods=['GET'])
def get_video(video_id):
    """Stream video by ID"""
    from bson.objectid import ObjectId
    
    try:
        video_data = db.get_video(ObjectId(video_id))
        if video_data:
            return Response(video_data, mimetype='video/mp4')
        return jsonify({'error': 'Video not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/video/path', methods=['POST'])
def get_video_by_path():
    """Get video from file system by path"""
    data = request.json
    video_path = data.get('video_path')
    
    print(f"=== VIDEO REQUEST ===")
    print(f"Requested path: {video_path}")
    
    if not video_path:
        return jsonify({'error': 'video_path is required'}), 400
    
    try:
        # Security: Ensure path is within flagged_videos directory
        abs_path = os.path.abspath(video_path)
        base_dir = os.path.abspath('flagged_videos')
        
        print(f"Absolute path: {abs_path}")
        print(f"Base directory: {base_dir}")
        print(f"File exists: {os.path.exists(abs_path)}")
        
        if not abs_path.startswith(base_dir):
            return jsonify({'error': 'Invalid video path - security check failed'}), 403
        
        if os.path.exists(abs_path):
            print(f"✓ Serving video from: {abs_path}")
            return send_file(abs_path, mimetype='video/mp4')
        else:
            print(f"✗ File not found at: {abs_path}")
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"✗ Error: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/video/file/<path:filepath>', methods=['GET'])
def get_video_file(filepath):
    """Get video from file system"""
    try:
        if os.path.exists(filepath):
            return send_file(filepath, mimetype='video/mp4')
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= WEBSOCKET EVENTS =============

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('join_session')
def handle_join_session(data):
    """Join a session room for real-time updates"""
    session_id = data.get('session_id')
    join_room(session_id)
    emit('joined_session', {'session_id': session_id})
    print(f"Client joined session: {session_id}")

@socketio.on('leave_session')
def handle_leave_session(data):
    """Leave a session room"""
    session_id = data.get('session_id')
    leave_room(session_id)
    emit('left_session', {'session_id': session_id})
    print(f"Client left session: {session_id}")


# ============= HEALTH CHECK =============

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


if __name__ == '__main__':
    print("="*60)
    print("🚀 AI Proctoring Backend Server Starting...")
    print("="*60)
    print(f"📡 Server: http://localhost:8000")
    print(f"🔌 WebSocket: ws://localhost:8000")
    print(f"💾 Database: MongoDB")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=8000, debug=True, allow_unsafe_werkzeug=True)