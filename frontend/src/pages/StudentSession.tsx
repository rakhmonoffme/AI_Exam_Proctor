import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Camera, Mic, Monitor, X, ExternalLink } from 'lucide-react';
import { useToast } from '../hooks/useToast';
import { apiService } from '../services/api';

export function StudentSession() {
  const location = useLocation();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [showPermissionModal, setShowPermissionModal] = useState(true);
  const [showExamUrlModal, setShowExamUrlModal] = useState(false);
  const [examUrl, setExamUrl] = useState('');
  const [permissions, setPermissions] = useState({
    camera: false,
    microphone: false,
    screen: false,
  });
  const [sessionStarted, setSessionStarted] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [screenActivity, setScreenActivity] = useState({
    tabSwitches: 0,
    copyPasteEvents: 0,
    windowBlurred: false,
  });
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isEndingRef = useRef(false);

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
    const handleVisibilityChange = () => {
      if (document.hidden && sessionStarted) {
        setScreenActivity(prev => ({
          ...prev,
          tabSwitches: prev.tabSwitches + 1,
          windowBlurred: true,
        }));
      } else {
        setScreenActivity(prev => ({
          ...prev,
          windowBlurred: false,
        }));
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [sessionStarted]);

  useEffect(() => {
    const handleCopy = () => {
      setScreenActivity(prev => ({
        ...prev,
        copyPasteEvents: prev.copyPasteEvents + 1,
      }));
    };

    const handlePaste = () => {
      setScreenActivity(prev => ({
        ...prev,
        copyPasteEvents: prev.copyPasteEvents + 1,
      }));
    };

    document.addEventListener('copy', handleCopy);
    document.addEventListener('paste', handlePaste);

    return () => {
      document.removeEventListener('copy', handleCopy);
      document.removeEventListener('paste', handlePaste);
    };
  }, []);

  useEffect(() => {
    if (!sessionStarted || !videoRef.current || !streamRef.current) return;

    if (!canvasRef.current) {
      canvasRef.current = document.createElement('canvas');
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    const captureInterval = setInterval(async () => {
      if (isEndingRef.current) return;
      if (videoRef.current && videoRef.current.readyState === 4) {
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;

        ctx?.drawImage(videoRef.current, 0, 0);

        const frameData = canvas.toDataURL('image/jpeg', 0.7);

        try {
          await apiService.sendFrame(sessionId, frameData, screenActivity);
        } catch (error) {
          console.error('Failed to send frame:', error);
        }
      }
    }, 2000);

    return () => clearInterval(captureInterval);
  }, [sessionStarted, sessionId, screenActivity]);

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
      console.log('Requesting camera and microphone access...');
      
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });

      console.log('Media stream obtained successfully');
      streamRef.current = stream;

      setShowPermissionModal(false);
      setShowExamUrlModal(true);

    } catch (error) {
      showToast('Failed to access camera and microphone', 'error');
      console.error('Media access error:', error);
    }
  };

  const startExam = () => {
    if (!examUrl.trim()) {
      showToast('Please enter exam URL', 'error');
      return;
    }

    // Add protocol if missing
    let validUrl = examUrl.trim();
    if (!validUrl.startsWith('http://') && !validUrl.startsWith('https://')) {
      validUrl = 'https://' + validUrl;
    }

    // Open exam in new window (fullscreen)
    const examWindow = window.open(validUrl, 'examWindow', 'width=1400,height=900');
    
    if (!examWindow) {
      showToast('Please allow popups for this site', 'error');
      return;
    }

    // Request fullscreen for exam window
    setTimeout(() => {
      examWindow.document.documentElement.requestFullscreen?.();
    }, 500);


    setExamUrl(validUrl);
    setShowExamUrlModal(false);
    setSessionStarted(true);
    
    // Attach stream to video AFTER state changes
    setTimeout(() => {
      if (videoRef.current && streamRef.current) {
        videoRef.current.srcObject = streamRef.current;
        videoRef.current.play()
          .then(() => {
            console.log('✓ Camera feed playing');
          })
          .catch(err => console.error('✗ Video play error:', err));
      }
    }, 100);
    
    showToast('Click "Enable Floating Camera" button', 'info');
  };

  const enablePictureInPicture = async () => {
    if (!videoRef.current) {
      showToast('Camera not ready', 'error');
      return;
    }

    if (!('pictureInPictureEnabled' in document)) {
      showToast('Picture-in-Picture not supported in your browser', 'error');
      return;
    }

    try {
      await videoRef.current.requestPictureInPicture();
      console.log('✓ Picture-in-Picture enabled');
      showToast('Camera now floating over exam window', 'success');
    } catch (err) {
      console.error('PIP error:', err);
      showToast('Failed to enable floating camera', 'error');
    }
  };

  const handleDeny = () => {
    showToast('Permissions required to start exam', 'error');
    navigate('/');
  };

  const endSession = async () => {
    const confirmed = window.confirm('Are you sure you want to end the exam session?');
    if (!confirmed) return;
    isEndingRef.current = true;
    try {
      // Close all camera feeds
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }

      // Exit PIP if active
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture();
      }

      await new Promise(resolve => setTimeout(resolve, 500));

      // Call backend to end session
      await apiService.endSession(sessionId, userId, examId);

      showToast('Session ended successfully', 'success');
      navigate('/');
    } catch (error) {
      console.error('End session error:', error);
      showToast('Session ended (with errors)', 'info');
      navigate('/'); // Navigate anyway
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
        <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8">
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

  if (showExamUrlModal) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8">
          <h2 className="text-2xl font-bold text-slate-800 mb-4">Enter Exam URL</h2>
          <p className="text-slate-600 mb-4">Your exam will open in a new window</p>
          <p className="text-sm text-slate-500 mb-6">Keep this proctoring window visible during your exam</p>

          <div className="mb-6">
            <input
              type="url"
              value={examUrl}
              onChange={(e) => setExamUrl(e.target.value)}
              placeholder="https://forms.google.com/..."
              className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500 focus:ring-opacity-50 transition-all outline-none"
              onKeyDown={(e) => e.key === 'Enter' && startExam()}
            />
          </div>

          <button
            onClick={startExam}
            className="w-full px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
          >
            <ExternalLink className="w-5 h-5" />
            <span>Open Exam & Start Proctoring</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900" style={{ border: '4px solid #10b981' }}>
      {/* End Session Button - Top Right */}
      <div className="absolute top-6 right-6 z-50">
        <button
          onClick={endSession}
          className="flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-xl font-semibold shadow-xl transition-colors"
        >
          <X className="w-5 h-5" />
          <span>End Session</span>
        </button>
      </div>

      {/* Main Content - Center */}
      <div className="flex items-center justify-center h-full p-8">
        <div className="text-center max-w-2xl">
          <div className="mb-8">
            <div className="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6 animate-pulse">
              <Camera className="w-12 h-12 text-green-400" />
            </div>
            <h1 className="text-4xl font-bold text-white mb-4">Proctoring Active</h1>
            <p className="text-slate-300 text-xl mb-2">Your exam is open in another window</p>
            <p className="text-slate-400">Camera feed is floating over your exam</p>
          </div>

          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 mb-6">
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="text-left">
                <p className="text-slate-400 text-sm mb-1">Session ID</p>
                <p className="text-white font-mono text-sm break-all">{sessionId}</p>
              </div>
              <div className="text-left">
                <p className="text-slate-400 text-sm mb-1">Student</p>
                <p className="text-white font-semibold">{userId}</p>
              </div>
            </div>
            
            <div className="flex items-center justify-center gap-3 text-green-400 bg-green-500/10 rounded-lg py-3 mb-4">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="font-semibold">Recording Active</span>
              <span className="font-mono ml-2">{formatTime(elapsedTime)}</span>
            </div>

            <button
              onClick={enablePictureInPicture}
              className="w-full px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
            >
              <Camera className="w-5 h-5" />
              <span>Enable Floating Camera</span>
            </button>
            <p className="text-slate-400 text-xs mt-2">Click if camera isn't floating</p>
          </div>

          <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4">
            <p className="text-amber-300 text-sm">
              AI monitoring is tracking your behavior. Any violations will be flagged.
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Left - Camera Feed */}
      <div className="absolute bottom-6 left-6 z-50">
        <div className="bg-black/90 backdrop-blur-md rounded-2xl p-4 shadow-2xl border-2 border-green-500/30">
          <div className="relative">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-64 h-48 rounded-xl object-cover bg-slate-900"
            />
            <div className="absolute top-2 left-2 bg-red-500 px-3 py-1 rounded-lg flex items-center gap-2 shadow-lg">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
              <span className="text-white text-xs font-bold">LIVE</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}