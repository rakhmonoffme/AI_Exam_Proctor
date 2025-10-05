import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Eye, User, Mic, Monitor, AlertCircle, CheckCircle,
  TrendingUp, ArrowLeft, Video, Clock
} from 'lucide-react';
import { apiService } from '../services/api';
import { useToast } from '../hooks/useToast';
import type { SessionDetails, MonitoringUpdate, Violation } from '../types';
import { Spinner } from '../components/Spinner';

export function SessionMonitoring() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [sessionDetails, setSessionDetails] = useState<SessionDetails | null>(null);
  const [monitoringData, setMonitoringData] = useState<MonitoringUpdate | null>(null);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      showToast('Invalid session ID', 'error');
      navigate('/admin/dashboard');
      return;
    }

    const fetchSessionDetails = async () => {
      try {
        const data = await apiService.getSessionDetails(sessionId);
        setSessionDetails(data);
        setMonitoringData(data.monitoring_data);
      } catch (error) {
        showToast('Failed to fetch session details', 'error');
      } finally {
        setLoading(false);
      }
    };

    fetchSessionDetails();

    const socket = apiService.connectSocket();

    socket.on('connect', () => {
      setConnected(true);
      apiService.joinSession(sessionId);
    });

    socket.on('disconnect', () => {
      setConnected(false);
    });

    const handleMonitoringUpdate = (data: MonitoringUpdate) => {
      if (data.session_id === sessionId) {
        setMonitoringData(data);
        setSessionDetails(prev => prev ? {
          ...prev,
          session: {
            ...prev.session,
            total_score: data.total_score,
            current_interval_score: data.interval_score,
          }
        } : null);
      }
    };

    apiService.onMonitoringUpdate(handleMonitoringUpdate);

    return () => {
      apiService.offMonitoringUpdate(handleMonitoringUpdate);
    };
  }, [sessionId, navigate, showToast]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getStatusColor = (status: string) => {
    return status === 'clear' ? 'bg-green-500' : 'bg-red-500';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Spinner className="w-12 h-12" />
      </div>
    );
  }

  if (!sessionDetails) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <p className="text-xl text-slate-700">Session not found</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center gap-4 mb-6">
          <button
            onClick={() => navigate('/admin/dashboard')}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Back to Dashboard</span>
          </button>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-slate-800">Session Monitoring</h1>
            <p className="text-sm text-slate-600">Real-time analytics and violation detection</p>
          </div>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${connected ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
            <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-sm font-medium">{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>

        <div className="grid lg:grid-cols-[60%_40%] gap-6">
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="relative bg-black aspect-video flex items-center justify-center">
                {monitoringData?.frame ? (
                  <img src={monitoringData.frame} alt="Live feed" className="w-full h-full object-contain" />
                ) : (
                  <div className="text-white text-center">
                    <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg">No video feed available</p>
                  </div>
                )}
                <div className="absolute top-4 left-4 bg-black/70 backdrop-blur-sm px-4 py-2 rounded-lg">
                  <p className="text-white font-semibold">{sessionDetails.session.user_id}</p>
                  <p className="text-white/70 text-sm font-mono">{sessionId}</p>
                </div>
                <div className="absolute bottom-4 left-4 bg-black/70 backdrop-blur-sm px-4 py-2 rounded-lg">
                  <p className="text-white text-sm">{monitoringData?.timestamp || 'N/A'}</p>
                </div>
                <div className="absolute top-4 right-4 flex items-center gap-2 bg-red-500 px-3 py-2 rounded-lg">
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                  <span className="text-white text-sm font-medium">LIVE</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-gradient-to-br from-white to-slate-50 rounded-xl shadow-sm border border-slate-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-slate-800">Score Dashboard</h3>
                <div className={`w-3 h-3 rounded-full ${getStatusColor(monitoringData?.status || 'clear')}`} />
              </div>
              <div className="flex items-baseline gap-3 mb-2">
                <span className="text-5xl font-bold text-slate-800">{sessionDetails.session.total_score}</span>
                <span className="text-xl text-slate-600">/ 100</span>
              </div>
              <div className="flex items-center gap-3 text-sm mb-4">
                <div className="flex items-center gap-1">
                  <span className="text-slate-600">Interval:</span>
                  <span className="font-semibold text-slate-800">{sessionDetails.session.current_interval_score}</span>
                </div>
                <div className="w-1 h-1 bg-slate-400 rounded-full" />
                <div className={`flex items-center gap-1 font-semibold ${monitoringData?.status === 'clear' ? 'text-green-600' : 'text-red-600'}`}>
                  {monitoringData?.status === 'clear' ? (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      <span>CLEAR</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="w-4 h-4" />
                      <span>FLAGGED</span>
                    </>
                  )}
                </div>
              </div>
              <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    sessionDetails.session.total_score < 10
                      ? 'bg-green-500'
                      : sessionDetails.session.total_score <= 20
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                  style={{ width: `${Math.min(sessionDetails.session.total_score, 100)}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Eye className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-600">Gaze Detection</p>
                    <p className={`text-sm font-bold ${monitoringData?.gaze.status === 'focused' ? 'text-green-600' : 'text-orange-600'}`}>
                      {monitoringData?.gaze.status || 'N/A'}
                    </p>
                  </div>
                </div>
                <div className="text-xs text-slate-600 space-y-1">
                  <div className="flex justify-between">
                    <span>H-Ratio:</span>
                    <span className="font-mono">{monitoringData?.gaze.horizontal_ratio.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>V-Ratio:</span>
                    <span className="font-mono">{monitoringData?.gaze.vertical_ratio.toFixed(2) || '0.00'}</span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                    <User className="w-5 h-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-600">Face Detection</p>
                    <p className={`text-sm font-bold ${monitoringData?.faces.has_multiple ? 'text-red-600' : 'text-green-600'}`}>
                      {monitoringData?.faces.count || 0} Face(s)
                    </p>
                  </div>
                </div>
                {monitoringData?.faces.has_multiple && (
                  <div className="flex items-center gap-1 text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                    <AlertCircle className="w-3 h-3" />
                    <span>Multiple faces detected</span>
                  </div>
                )}
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <Mic className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-600">Audio Analysis</p>
                    <p className="text-sm font-bold text-slate-800">
                      {monitoringData?.audio.speech_detected ? 'Speech' : 'Silent'}
                    </p>
                  </div>
                </div>
                {monitoringData?.audio.multiple_speakers && (
                  <div className="flex items-center gap-1 text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                    <AlertCircle className="w-3 h-3" />
                    <span>Multiple speakers</span>
                  </div>
                )}
              </div>

              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Monitor className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-xs text-slate-600">Screen Activity</p>
                    <p className="text-sm font-bold text-slate-800">Monitored</p>
                  </div>
                </div>
                <div className="text-xs text-slate-600 space-y-1">
                  <div className="flex justify-between">
                    <span>Tab Switches:</span>
                    <span className="font-bold text-slate-800">{monitoringData?.screen.tab_switches || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Copy/Paste:</span>
                    <span className="font-bold text-slate-800">{monitoringData?.screen.copy_paste_events || 0}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200">
              <div className="p-4 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-slate-700" />
                  <h3 className="text-lg font-bold text-slate-800">Violations Timeline</h3>
                </div>
              </div>
              <div className="p-4 max-h-[300px] overflow-y-auto">
                {!monitoringData?.violations || monitoringData.violations.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                    <p className="text-sm text-slate-600">No violations detected</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {monitoringData.violations.map((violation, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border ${getSeverityColor(violation.severity)}`}
                      >
                        <div className="flex items-start justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            <span className="font-semibold text-sm">{violation.type}</span>
                          </div>
                          <span className="text-xs font-bold">+{violation.score}</span>
                        </div>
                        <p className="text-xs mb-1">{violation.description}</p>
                        <div className="flex items-center gap-1 text-xs opacity-75">
                          <Clock className="w-3 h-3" />
                          <span>{violation.timestamp}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-slate-200">
              <div className="p-4 border-b border-slate-200">
                <h3 className="text-lg font-bold text-slate-800">Flagged Intervals</h3>
              </div>
              <div className="p-4 max-h-[250px] overflow-y-auto">
                {!sessionDetails.flagged_intervals || sessionDetails.flagged_intervals.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
                    <p className="text-sm text-slate-600">No flagged intervals</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {sessionDetails.flagged_intervals.map((interval) => (
                      <div key={interval.interval_id} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-semibold text-red-700">
                            {interval.start_time} - {interval.end_time}
                          </span>
                          <span className="text-xs font-bold text-red-600 bg-red-100 px-2 py-1 rounded">
                            Score: {interval.score}
                          </span>
                        </div>
                        <button
                          onClick={() => window.open(apiService.getVideoUrl(interval.video_id), '_blank')}
                          className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-white border border-red-200 rounded-lg text-sm font-medium text-red-700 hover:bg-red-50 transition-colors"
                        >
                          <Video className="w-4 h-4" />
                          <span>View Video</span>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
