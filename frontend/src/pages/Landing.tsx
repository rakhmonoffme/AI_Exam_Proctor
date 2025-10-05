import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Shield } from 'lucide-react';
import { useToast } from '../hooks/useToast';
import { apiService } from '../services/api';

export function Landing() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [studentName, setStudentName] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [loading, setLoading] = useState(false);

  const handleStartExam = async () => {
    if (!studentName.trim()) {
      showToast('Please enter your name', 'error');
      return;
    }

    setLoading(true);
    try {
      const examId = sessionId.trim() || `exam_${Date.now()}`;
      const session = await apiService.createSession(studentName, examId);
      navigate('/student/session', {
        state: {
          sessionId: session.session_id,
          userId: studentName,
          examId: examId
        }
      });
    } catch (error) {
      showToast('Failed to start exam session', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAdminAccess = () => {
    navigate('/admin/dashboard');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100">
      <div className="max-w-7xl mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-teal-600 via-cyan-600 to-blue-600 bg-clip-text text-transparent">
              AI Proctoring System
            </span>
          </h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Advanced real-time exam monitoring with AI-powered behavioral analysis,
            eye tracking, and comprehensive academic integrity protection.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-2xl mb-6 shadow-lg">
              <User className="w-8 h-8 text-white" />
            </div>

            <h2 className="text-2xl font-bold text-slate-800 mb-6">Student Portal</h2>

            <div className="space-y-4 mb-8">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Student Name
                </label>
                <input
                  type="text"
                  value={studentName}
                  onChange={(e) => setStudentName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500 focus:ring-opacity-50 transition-all outline-none"
                  onKeyDown={(e) => e.key === 'Enter' && handleStartExam()}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Session ID (Optional)
                </label>
                <input
                  type="text"
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  placeholder="Leave blank for auto-generated"
                  className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:border-teal-500 focus:ring-2 focus:ring-teal-500 focus:ring-opacity-50 transition-all outline-none"
                  onKeyDown={(e) => e.key === 'Enter' && handleStartExam()}
                />
              </div>
            </div>

            <button
              onClick={handleStartExam}
              disabled={loading}
              className="w-full py-4 bg-gradient-to-r from-teal-500 to-cyan-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Starting...</span>
                </>
              ) : (
                <>
                  <span>Start Exam Session</span>
                  <span>→</span>
                </>
              )}
            </button>
          </div>

          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8 hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
            <div className="flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl mb-6 shadow-lg">
              <Shield className="w-8 h-8 text-white" />
            </div>

            <h2 className="text-2xl font-bold text-slate-800 mb-6">Admin Dashboard</h2>

            <div className="mb-8">
              <p className="text-slate-600 leading-relaxed">
                Monitor active exam sessions, review AI-powered violation detection,
                analyze student behavior patterns, and access comprehensive session analytics
                in real-time.
              </p>
            </div>

            <div className="space-y-3 mb-8 bg-slate-50 rounded-xl p-4">
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <div className="w-2 h-2 bg-teal-500 rounded-full" />
                <span>Real-time session monitoring</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <div className="w-2 h-2 bg-teal-500 rounded-full" />
                <span>AI-powered violation detection</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <div className="w-2 h-2 bg-teal-500 rounded-full" />
                <span>Comprehensive analytics dashboard</span>
              </div>
            </div>

            <button
              onClick={handleAdminAccess}
              className="w-full py-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all duration-200 flex items-center justify-center gap-2"
            >
              <span>Access Admin Dashboard</span>
              <span>→</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
