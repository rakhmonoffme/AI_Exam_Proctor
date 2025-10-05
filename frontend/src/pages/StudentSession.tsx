import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Camera, Mic, Monitor, X } from 'lucide-react';
import { useToast } from '../hooks/useToast';
import { apiService } from '../services/api';

export function StudentSession() {
  const location = useLocation();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [showPermissionModal, setShowPermissionModal] = useState(true);
  const [permissions, setPermissions] = useState({
    camera: false,
    microphone: false,
    screen: false,
  });
  const [sessionStarted, setSessionStarted] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const { sessionId, userId, examId } = location.state || {};

  useEffect(() => {
    if (!sessionId || !userId || !examId) {
      showToast('Invalid session data', 'error');
      navigate('/');
    }
  }, [sessionId, userId, examId, navigate, showToast]);

  useEffect(() => {
    if (sessionStarted) {
      const timer = setInterval(() => {
        setElapsedTime(prev => prev + 1);
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [sessionStarted]);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (sessionStarted) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [sessionStarted]);

  const requestPermissions = async () => {
    if (!permissions.camera || !permissions.microphone || !permissions.screen) {
      showToast('Please enable all required permissions', 'error');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      setShowPermissionModal(false);
      setSessionStarted(true);
      showToast('Session started successfully', 'success');

      document.documentElement.requestFullscreen?.();
    } catch (error) {
      showToast('Failed to access camera and microphone', 'error');
    }
  };

  const handleDeny = () => {
    showToast('Permissions required to start exam', 'error');
    navigate('/');
  };

  const endSession = async () => {
    const confirmed = window.confirm('Are you sure you want to end the exam session?');
    if (!confirmed) return;

    try {
      await apiService.endSession(userId, examId);

      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      if (document.fullscreenElement) {
        document.exitFullscreen();
      }

      showToast('Session ended successfully', 'success');
      navigate('/');
    } catch (error) {
      showToast('Failed to end session', 'error');
    }
  };

  const formatTime = (seconds: number) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (showPermissionModal) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 animate-scale-up">
          <h2 className="text-2xl font-bold text-slate-800 mb-4">Permission Required</h2>
          <p className="text-slate-600 mb-6">This exam requires access to:</p>

          <div className="space-y-4 mb-8">
            <label className="flex items-center gap-3 p-4 bg-slate-50 rounded-xl cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                checked={permissions.camera}
                onChange={(e) => setPermissions(prev => ({ ...prev, camera: e.target.checked }))}
                className="w-5 h-5 text-teal-600 rounded focus:ring-2 focus:ring-teal-500"
              />
              <Camera className="w-5 h-5 text-slate-700" />
              <span className="text-slate-700 font-medium">Camera Access</span>
            </label>

            <label className="flex items-center gap-3 p-4 bg-slate-50 rounded-xl cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                checked={permissions.microphone}
                onChange={(e) => setPermissions(prev => ({ ...prev, microphone: e.target.checked }))}
                className="w-5 h-5 text-teal-600 rounded focus:ring-2 focus:ring-teal-500"
              />
              <Mic className="w-5 h-5 text-slate-700" />
              <span className="text-slate-700 font-medium">Microphone Access</span>
            </label>

            <label className="flex items-center gap-3 p-4 bg-slate-50 rounded-xl cursor-pointer hover:bg-slate-100 transition-colors">
              <input
                type="checkbox"
                checked={permissions.screen}
                onChange={(e) => setPermissions(prev => ({ ...prev, screen: e.target.checked }))}
                className="w-5 h-5 text-teal-600 rounded focus:ring-2 focus:ring-teal-500"
              />
              <Monitor className="w-5 h-5 text-slate-700" />
              <span className="text-slate-700 font-medium">Screen Monitoring</span>
            </label>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleDeny}
              className="flex-1 px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-semibold hover:bg-slate-300 transition-colors"
            >
              Deny
            </button>
            <button
              onClick={requestPermissions}
              className="flex-1 px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all"
            >
              Allow & Continue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-slate-900 border-4 border-green-500">
      <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/50 backdrop-blur-sm px-4 py-2 rounded-lg">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        <span className="text-white text-sm font-medium">Recording</span>
      </div>

      <div className="absolute top-4 right-4">
        <button
          onClick={endSession}
          className="flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white px-6 py-2 rounded-lg font-semibold shadow-lg transition-colors"
        >
          <X className="w-4 h-4" />
          <span>End Session</span>
        </button>
      </div>

      <div className="absolute bottom-4 right-4 bg-black/50 backdrop-blur-sm px-4 py-2 rounded-lg">
        <span className="text-white text-sm font-mono">{formatTime(elapsedTime)}</span>
      </div>

      <div className="absolute bottom-4 left-4">
        <video
          ref={videoRef}
          autoPlay
          muted
          className="w-40 h-40 rounded-2xl border-2 border-white/20 shadow-2xl object-cover"
        />
      </div>

      <div className="flex items-center justify-center h-full p-8">
        <div className="bg-white rounded-2xl shadow-2xl p-12 max-w-4xl w-full">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-slate-800 mb-6">
              Exam Content Area
            </h1>
            <div className="bg-slate-50 rounded-xl p-8 mb-6">
              <p className="text-lg text-slate-600 mb-4">
                This is where your exam content would be displayed.
              </p>
              <p className="text-slate-500">
                The AI proctoring system is actively monitoring your session.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4 text-left bg-slate-50 rounded-xl p-6">
              <div>
                <span className="text-sm text-slate-500">Session ID:</span>
                <p className="font-mono text-sm text-slate-800">{sessionId}</p>
              </div>
              <div>
                <span className="text-sm text-slate-500">Student:</span>
                <p className="font-mono text-sm text-slate-800">{userId}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
