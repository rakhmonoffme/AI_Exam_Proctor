import cv2
import time
import threading
from datetime import datetime
from pymongo import MongoClient
from gridfs import GridFS
import io
import base64
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# Import detection modules
from backend.detectors.gaze_direction import GazeFocusDetector
from backend.detectors.face_detector import FaceDetector
from backend.detectors.audiodetector import MultiSpeakerDetector
from backend.detectors.screen_monitor import ScreenActivityMonitor
from backend.database.db import ProctoringDatabase

class ProctoringScoreSystem:
    def __init__(self):
        """Initialize Proctoring Score System"""
        
        # Scoring rules
        self.SCORES = {
            'gaze_distracted': 2,      # Looking away (left/right/down)
            'speech_detected': 0,       # Single voice detected
            'multiple_voices': 10,      # Multiple speakers
            'tab_switch': 4,            # Tab switching
            'copy_paste': 5,            # Copy/paste action
            'multiple_faces': 10,        # Multiple people detected
            'no_face': 9               # No face detected
        }
        
        self.FLAG_THRESHOLD = 10
        self.INTERVAL_DURATION = 30 
        
        # Initialize detectors
        self.gaze_detector = GazeFocusDetector()
        self.face_detector = FaceDetector()
        self.audio_detector = MultiSpeakerDetector()
        self.screen_monitor = ScreenActivityMonitor()
        self.db = ProctoringDatabase()
        
        # Overall tracking
        
        self.total_score = 0
        self.all_violations = []
        
        # Interval tracking
        self.interval_start_time = None
        self.session_id = None
        self.interval_score = 0
        self.interval_violations = []
        self.flags = []
        
        self.video_writer = None
        self.temp_video_file = None
        self.is_recording = False
        self.video_fps = 15
    
    def _save_violation_to_db(self, violation):
        """Save violation to database immediately"""
        if self.session_id:
            violation_data = {
                'session_id': str(self.session_id),
                'user_id': self.current_user_id,
                'type': violation['type'],
                'score': violation['score'],
                'timestamp': violation['timestamp'],
                'details': violation.get('details', ''),
                'description': violation.get('description', violation.get('details', '')),
                'severity': self._get_severity(violation['score'])
            }
            self.db.save_violation(violation_data)

    def _get_severity(self, score):
        """Determine severity based on score"""
        if score >= 9:
            return 'high'
        elif score >= 4:
            return 'medium'
        else:
            return 'low'
    
    def _start_new_interval(self):
        """Start a new scoring interval"""
        self.interval_start_time = time.time()
        self.interval_score = 0
        self.interval_violations = []
        
    def _start_video_recording(self, frame_width, frame_height):
        """Start recording video for the interval"""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.temp_video_file = f"temp_interval_{int(time.time())}.mp4"
        self.video_writer = cv2.VideoWriter(
            self.temp_video_file,
            fourcc,
            self.video_fps,
            (frame_width, frame_height)
        )
        self.is_recording = True
        print(f"📹 Started recording: {self.temp_video_file}")

    def _stop_video_recording(self):
        """Stop recording and return video file path"""
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            self.is_recording = False
            print(f"⏹️  Stopped recording")
            # Verify file exists before returning
            if self.temp_video_file and os.path.exists(self.temp_video_file):
                file_size = os.path.getsize(self.temp_video_file)
                print(f"✓ Video file ready: {file_size} bytes")
                return self.temp_video_file
            else:
                print(f"✗ Video file not created: {self.temp_video_file}")
                return None
        
        print(f"✗ No video writer active")
        return None
        
    def _check_and_flag_interval(self, force=False):
        """
        Check if interval should be evaluated and potentially flagged
        
        Args:
            force: Force check regardless of time (for manual triggers)
        """
        if self.interval_start_time is None:
            self._start_new_interval()
            return
        
        # Check if threshold exceeded (immediate flag)
        if self.interval_score >= self.FLAG_THRESHOLD:
            if not self.is_recording:
                print(f"✗ No active recording to flag")
                return False
            video_file = self._stop_video_recording()
            time.sleep(1)
            
            if not video_file or not os.path.exists(video_file):
                print(f"✗ Video file missing: {video_file}")
                self._start_new_interval()
                return False
            print(f"✓ Video file exists: {video_file} ({os.path.getsize(video_file)} bytes)")
            
            # Save video to DB
            flag_data = {
                'interval_start': datetime.fromtimestamp(self.interval_start_time).isoformat(),
                'interval_end': datetime.now().isoformat(),
                'score': self.interval_score,
                'violations': self.interval_violations.copy(),
                'flagged_at': datetime.now().isoformat()
            }
            
            # Save to MongoDB with video - THIS MOVES THE FILE
            if video_file and self.session_id and os.path.exists(video_file):  # ADD os.path.exists check
                flag_data['session_id'] = str(self.session_id)
                flag_data['user_id'] = self.current_user_id 
                self.db.save_flagged_interval(flag_data, video_file)  # This moves the file
                print(f"✓ Video saved via database method")
            elif video_file:
                print(f"✗ Video file not found: {video_file}")
                
            
            self.flags.append(flag_data)
            print(f"\n🚨 IMMEDIATE FLAG! Interval Score: {self.interval_score} (Threshold: {self.FLAG_THRESHOLD})")
            self._start_new_interval()
            return True
        
        return False
    def analyze_gaze(self, frame):
        """
        Analyze gaze direction
        
        Returns:
            dict: Gaze analysis with score
        """
        result = self.gaze_detector.detect_focus(frame)
        
        score = 0
        if result['face_detected'] and not result['focused']:
            score = self.SCORES['gaze_distracted']
            self.total_score += score
            self.interval_score += score
            
            violation = {
                'type': 'gaze_distracted',
                'score': score,
                'timestamp': datetime.now().isoformat(),
                'details': f"Looking {result['where']}" if result['where'] else "focused away",
                
            }
            self.all_violations.append(violation)
            self.interval_violations.append(violation)
            self._save_violation_to_db(violation) 
            
            # Check for immediate flag
            self._check_and_flag_interval()
            
        return {
            'focused': result['focused'],
            'score': score,
            'face_detected': result['face_detected'],
            'interval_score': self.interval_score
        }
    
    def analyze_faces(self, frame):
        """
        Analyze number of faces
        
        Returns:
            dict: Face analysis with score
        """
        result = self.face_detector.detect_faces(frame)
        
        score = 0
        if result['multiple_faces']:
            score = self.SCORES['multiple_faces']
            self.total_score += score
            self.interval_score += score
            violation = {
                'type': 'multiple_faces',
                'score': score,
                'timestamp': datetime.now().isoformat(),
                'details': f"{result['num_faces']} faces detected"
            }
            self.all_violations.append(violation)
            self.interval_violations.append(violation)
            self._save_violation_to_db(violation) 
            
            
        if result['no_face']:
            score = self.SCORES['no_face']
            self.total_score += score
            self.interval_score += score
            violation = {
                'type': 'no_face',
                'score': score,
                'timestamp': datetime.now().isoformat(),
                'details': "No face detected"
            }
            self.all_violations.append(violation)
            self.interval_violations.append(violation)
            self._save_violation_to_db(violation) 
            
            
        # Check for immediate flag
        self._check_and_flag_interval()
        
        return {
            'num_faces': result['num_faces'],
            'multiple_faces': result['multiple_faces'],
            'no_face': result['no_face'],
            'score': score,
            'interval_score': self.interval_score
        }
    
    def analyze_audio(self, duration=5):
        """
        Analyze audio for speech and multiple speakers
        
        Returns:
            dict: Audio analysis with score
        """
        result = self.audio_detector.analyze(duration)
        
        score = 0
        if result['total_speech_frames'] > 0:
            # Speech detected
            speech_score = self.SCORES['speech_detected']
            score += speech_score
            
            violation = {
                'type': 'speech_detected',
                'score': speech_score,
                'timestamp': datetime.now().isoformat(),
                'details': "Single voice detected"
            }
            self.all_violations.append(violation)
            self.interval_violations.append(violation)
            self._save_violation_to_db(violation)
            
            if result['multiple_speakers_detected']:
                # Multiple voices
                multi_score = self.SCORES['multiple_voices']
                score += multi_score
                
                violation = {
                    'type': 'multiple_voices',
                    'score': multi_score,
                    'timestamp': datetime.now().isoformat(),
                    'details': f"Confidence: {result['confidence']:.2%}"
                }
                self.all_violations.append(violation)
                self.interval_violations.append(violation)
                self._save_violation_to_db(violation)
        
        self.total_score += score
        self.interval_score += score
        
        # Check for immediate flag
        if score > 0:
            self._check_and_flag_interval()
        
        return {
            'speech_detected': result['total_speech_frames'] > 0,
            'multiple_speakers': result['multiple_speakers_detected'],
            'score': score,
            'interval_score': self.interval_score
        }
    
    def analyze_screen_activity(self, duration=None):
        """
        Analyze screen activity (tab switches, copy/paste)
        
        Args:
            duration: If provided, starts monitoring. If None, gets current stats.
            
        Returns:
            dict: Screen activity analysis with score
        """
        if duration:
            result = self.screen_monitor.start_monitoring(duration)
        else:
            result = self.screen_monitor.get_current_stats()
        
        score = 0
        
        # Score tab switches
        if result['tab_switches'] > 0:
            tab_score = result['tab_switches'] * self.SCORES['tab_switch']
            score += tab_score
            
            violation = {
                'type': 'tab_switch',
                'score': tab_score,
                'timestamp': datetime.now().isoformat(),
                'details': f"{result['tab_switches']} tab switches"
            }
            self.all_violations.append(violation)
            self.interval_violations.append(violation)
            self._save_violation_to_db(violation)
        
        # Score copy/paste events
        if result['copy_paste_events'] > 0:
            cp_score = result['copy_paste_events'] * self.SCORES['copy_paste']
            score += cp_score
            
            violation = {
                'type': 'copy_paste',
                'score': cp_score,
                'timestamp': datetime.now().isoformat(),
                'details': f"{result['copy_paste_events']} copy/paste events"
            }
            self.all_violations.append(violation)
            self.interval_violations.append(violation)
            self._save_violation_to_db(violation)
        
        self.total_score += score
        self.interval_score += score
        
        # Check for immediate flag
        if score > 0:
            self._check_and_flag_interval()
        
        return {
            'tab_switches': result['tab_switches'],
            'copy_paste_events': result['copy_paste_events'],
            'score': score,
            'interval_score': self.interval_score
        }
    
    def run_continuous_monitoring(self, check_interval=10, user_id='user_001', exam_id='exam_001'):
        """
        Run continuous monitoring for specified duration
        
        Args:
            duration: Total monitoring time in seconds
            check_interval: Seconds between checks
            
        Returns:
            dict: Complete monitoring report
        """
        print(f"Starting continuous monitoring...")
        print(f"Interval duration: {self.INTERVAL_DURATION}s | Flag threshold: {self.FLAG_THRESHOLD}")
        
        # Create session in database
        session_data = {
            'user_id': user_id,
            'exam_id': exam_id,
            'start_time': datetime.now().isoformat()
        }
        self.session_id = self.db.create_session(session_data)
        self.current_user_id = user_id  # ← ADD THIS LINE
        
        # Start first interval
        self._start_new_interval()
        
        # Start screen monitoring in background
        self.screen_monitor.start_monitoring()
        
        audio_running = True
        def audio_monitor_loop():
            while audio_running:
                audio_result = self.analyze_audio(duration=5)
                print(f"[AUDIO] Speech: {audio_result['speech_detected']} | Multiple: {audio_result['multiple_speakers']} | +{audio_result['score']} | Interval: {audio_result['interval_score']}")
                time.sleep(5)  # Check audio every 5 seconds

        audio_thread = threading.Thread(target=audio_monitor_loop, daemon=True)
        audio_thread.start()
        
        # Open webcam
        cap = cv2.VideoCapture(0)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        check_count = 0
        
        try:
            last_check_time = time.time()
            
            while True:
                ret, frame = cap.read()
                
                if ret:
                    # Start recording if not already recording
                    if not self.is_recording:
                        self._start_video_recording(frame_width, frame_height)
                    
                    # Write EVERY frame to video (no delay)
                    if self.video_writer:
                        self.video_writer.write(frame)
                    
                    # Only run detection checks every check_interval seconds
                    current_time = time.time()
                    if current_time - last_check_time >= check_interval:
                        # Check gaze
                        gaze_result = self.analyze_gaze(frame)
                        print(f"[{check_count}] Gaze: {'✓ Focused' if gaze_result['focused'] else '✗ Distracted'} | +{gaze_result['score']} | Interval: {gaze_result['interval_score']}")
                        
                        # Check faces
                        face_result = self.analyze_faces(frame)
                        print(f"[{check_count}] Faces: {face_result['num_faces']} | +{face_result['score']} | Interval: {face_result['interval_score']}")
                        
                        check_count += 1
                        last_check_time = current_time
                
                # Check if 30-second interval completed
                elapsed = time.time() - self.interval_start_time
                if elapsed >= self.INTERVAL_DURATION:
                    if self.interval_score < self.FLAG_THRESHOLD:
                        print(f"\n✓ Interval completed. Score: {self.interval_score} (Clear)\n")
                        # Stop and discard video (not flagged)
                        video_file = self._stop_video_recording()
                        if video_file and os.path.exists(video_file):
                            os.remove(video_file)
                    self._start_new_interval()
                
                # Small delay to prevent CPU overload (but still captures ~30fps)
                time.sleep(0.03)  # ~30 FPS
                
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
        
        finally:
            
            audio_running = False  # Stop audio thread
            time.sleep(1)
            if self.video_writer:
                self.video_writer.release()
            
            cap.release()
            # Stop screen monitoring and get final stats
            screen_result = self.screen_monitor.stop_monitoring()
            final_screen_score = (screen_result['tab_switches'] * self.SCORES['tab_switch'] + 
                            screen_result['copy_paste_events'] * self.SCORES['copy_paste'])
            self.total_score += final_screen_score
            self.interval_score += final_screen_score
            
            # Generate report
            report = self.generate_report()
            if self.session_id:
                self.db.end_session(self.session_id, report)
            # Force final interval check
            self._check_and_flag_interval(force=True)
            return report
        
    
    def run_single_check(self):
        """
        Run a single check across all detectors
        
        Returns:
            dict: Single check results
        """
        print("Running single check...")
        
        if self.interval_start_time is None:
            self._start_new_interval()
        
        # Capture frame
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        results = {}
        
        if ret:
            results['gaze'] = self.analyze_gaze(frame)
            results['faces'] = self.analyze_faces(frame)
        
        # Quick audio check (3 seconds)
        results['audio'] = self.analyze_audio(duration=3)
        
        # Get current screen stats
        screen_stats = self.screen_monitor.get_current_stats()
        results['screen'] = {
            'tab_switches': screen_stats['tab_switches'],
            'copy_paste_events': screen_stats['copy_paste_events'],
            'score': (screen_stats['tab_switches'] * self.SCORES['tab_switch'] + 
                     screen_stats['copy_paste_events'] * self.SCORES['copy_paste'])
        }
        
        results['interval_score'] = self.interval_score
        results['total_score'] = self.total_score
        results['interval_flagged'] = self.interval_score >= self.FLAG_THRESHOLD
        results['num_flags'] = len(self.flags)
        
        return results
    
    def generate_report(self):
        """
        Generate comprehensive monitoring report
        
        Returns:
            dict: Complete report with scores and violations
        """
        report = {
            'total_score': self.total_score,
            'total_violations': len(self.all_violations),
            'violations': self.all_violations,
            'violation_breakdown': self._get_violation_breakdown(),
            'interval_duration': self.INTERVAL_DURATION,
            'flag_threshold': self.FLAG_THRESHOLD,
            'flagged_intervals': self.flags,
            'num_flagged_intervals': len(self.flags),
            'overall_status': 'FLAGGED' if len(self.flags) > 0 else 'CLEAR',
            'timestamp': datetime.now().isoformat()
        }
        
        return report
    
    def _get_violation_breakdown(self):
        """Get breakdown of violations by type"""
        breakdown = {}
        for violation in self.all_violations:
            vtype = violation['type']
            if vtype not in breakdown:
                breakdown[vtype] = {'count': 0, 'total_score': 0}
            breakdown[vtype]['count'] += 1
            breakdown[vtype]['total_score'] += violation['score']
        return breakdown
    
    def reset_score(self):
        """Reset all scores and violations"""
        self.total_score = 0
        self.all_violations = []
        self.interval_score = 0
        self.interval_violations = []
        self.interval_start_time = None
        self.flags = []
        print("Score reset")
    
    def close(self):
        """Close all detectors and release resources"""
        # Stop screen monitoring first (stops background threads)
        if self.screen_monitor.is_monitoring:
            self.screen_monitor.stop_monitoring()
        
        # Release video writer
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        # Close detectors
        self.gaze_detector.close()
        
        # IMPORTANT: Close database LAST after all background operations stopped
        # Wait a moment to ensure any pending database operations complete
        import time
        time.sleep(0.5)
        
        self.db.close()
        print("All detectors closed")


# Example usage
# Example usage
if __name__ == "__main__":
    # Initialize scoring system
    scorer = ProctoringScoreSystem()
    
    try:
        # Continuous monitoring (runs until Ctrl+C)
        report = scorer.run_continuous_monitoring(
            check_interval=10,
            user_id='student_123',
            exam_id='midterm_2024'
        )
                
        # Print report
        print("\n" + "="*60)
        print("PROCTORING REPORT")
        print("="*60)
        print(f"Overall Status: {report['overall_status']}")
        print(f"Flagged Intervals: {report['num_flagged_intervals']}")
        print(f"Total Violations: {report['total_violations']}")
        print("\nViolation Breakdown:")
        for vtype, data in report['violation_breakdown'].items():
            print(f"  {vtype}: {data['count']} occurrences, {data['total_score']} points")
        
        if report['flagged_intervals']:
            print("\n⚠️  FLAGGED INTERVALS:")
            for i, flag in enumerate(report['flagged_intervals'], 1):
                print(f"  #{i} Score: {flag['score']} | {flag['flagged_at']}")
        print("="*60)
        
    finally:
        scorer.close()