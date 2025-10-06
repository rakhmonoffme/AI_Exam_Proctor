import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Activity, TrendingUp, AlertTriangle, RefreshCw, Eye, ChevronRight } from 'lucide-react';
import { apiService } from '../services/api';
import { useToast } from '../hooks/useToast';
import type { Session, SessionStats } from '../types';
import { Spinner } from '../components/Spinner';

export function AdminDashboard() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [stats, setStats] = useState<SessionStats | null>(null);
  const [activeSessions, setActiveSessions] = useState<Session[]>([]);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [sessionFlagCounts, setSessionFlagCounts] = useState<Record<string, number>>({});
  const [showSessionsModal, setShowSessionsModal] = useState(false);
  const [allSessions, setAllSessions] = useState<any[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  const fetchData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);

    try {
      const [statsData, sessionsData] = await Promise.all([
        apiService.getStats(),
        apiService.getActiveSessions(),
      ]);
      setStats(statsData);
      setActiveSessions(sessionsData);
      
      // Fetch flagged interval counts for each session
      const flagCounts: Record<string, number> = {};
      await Promise.all(
        sessionsData.map(async (session) => {
          try {
            const details = await apiService.getSessionDetails(session.session_id);
            flagCounts[session.session_id] = details.flagged_intervals?.length ?? 0;
          } catch (error) {
            flagCounts[session.session_id] = 0;
          }
        })
      );
      setSessionFlagCounts(flagCounts);
      
      if (isRefresh) {
        showToast('Data refreshed', 'success');
      }
    } catch (error) {
      showToast('Failed to fetch dashboard data', 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
  useEffect(() => {
    fetchData();

    const interval = setInterval(() => {
      fetchData(true);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getRiskLevel = (count: number) => {
    if (count >= 4) {
      return {
        label: 'CRITICAL',
        color: 'text-red-600 bg-red-50',
        dotColor: 'bg-red-500'
      };
    } else if (count >= 2) {
      return {
        label: 'HIGH RISK',
        color: 'text-orange-600 bg-orange-50',
        dotColor: 'bg-orange-500'
      };
    } else {
      return {
        label: 'NORMAL',
        color: 'text-green-600 bg-green-50',
        dotColor: 'bg-green-500'
      };
    }
  };

  const viewSessionDetails = (sessionId: string) => {
    navigate(`/admin/session/${sessionId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <Spinner className="w-12 h-12" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-800">Admin Dashboard</h1>
            <p className="text-slate-600 mt-2">Monitor and manage exam sessions in real-time</p>
          </div>
          <button
            onClick={() => fetchData(true)}
            disabled={refreshing}
            className="flex items-center gap-2 px-6 py-3 bg-white border border-slate-200 rounded-xl hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            <span className="font-medium">Refresh</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Total Sessions</p>
                <p className="text-3xl font-bold text-slate-800">{stats?.total_sessions || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <Activity className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Active Sessions</p>
                <p className="text-3xl font-bold text-slate-800">{stats?.active_sessions || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">High Risk</p>
                <p className="text-3xl font-bold text-slate-800">{stats?.high_risk || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-slate-600">Flagged</p>
                <p className="text-3xl font-bold text-slate-800">{stats?.flagged || 0}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-xl font-bold text-slate-800">Active Sessions</h2>
            </div>
            <div className="p-6">
              {activeSessions.length === 0 ? (
                <div className="text-center py-12">
                  <Activity className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">No active sessions</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto">
                  {activeSessions.map((session) => {
                    const flagCount = sessionFlagCounts[session.session_id] ?? 0;
                    const risk = getRiskLevel(flagCount);
                    
                    return (
                      <div
                        key={session.session_id}
                        onClick={() => setSelectedSession(session)}
                        className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                          selectedSession?.session_id === session.session_id
                            ? 'border-teal-500 bg-teal-50'
                            : 'border-slate-200 hover:border-slate-300 bg-white'
                        }`}
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                              <span className="font-semibold text-slate-800">{session.user_id}</span>
                            </div>
                            <p className="text-sm text-slate-600">
                              Exam: <span className="font-mono">{session.exam_id}</span>
                            </p>
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            <div className={`px-3 py-1 rounded-lg text-sm font-semibold ${risk.color}`}>
                              {risk.label}
                            </div>
                            <div className="text-xs text-slate-600">
                              {flagCount} interval{flagCount !== 1 ? 's' : ''}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            viewSessionDetails(session.session_id);
                          }}
                          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm font-medium text-slate-700 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                          <span>View Details</span>
                          <ChevronRight className="w-4 h-4" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-slate-200">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-xl font-bold text-slate-800">Session Details</h2>
            </div>
            <div className="p-6">
              {!selectedSession ? (
                <div className="text-center py-12">
                  <Activity className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500 mb-2 font-medium">Select a Session</p>
                  <p className="text-sm text-slate-400">Click on a session to view real-time monitoring data</p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="bg-slate-50 rounded-xl p-4">
                    <h3 className="font-semibold text-slate-800 mb-3">Session Information</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Session ID:</span>
                        <span className="font-mono text-slate-800">{selectedSession.session_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Student:</span>
                        <span className="font-semibold text-slate-800">{selectedSession.user_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Exam ID:</span>
                        <span className="font-mono text-slate-800">{selectedSession.exam_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Status:</span>
                        <span className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                          <span className="text-green-600 font-semibold">Active</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gradient-to-br from-slate-50 to-white rounded-xl p-4 border border-slate-200">
                    <h3 className="font-semibold text-slate-800 mb-3">Risk Assessment</h3>
                    <div className="flex items-baseline gap-2 mb-2">
                      <span className="text-4xl font-bold text-slate-800">
                        {sessionFlagCounts[selectedSession.session_id] ?? 0}
                      </span>
                      <span className="text-sm text-slate-600">flagged intervals</span>
                    </div>
                    
                    {/* Risk Badge */}
                    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold mb-3 ${
                      getRiskLevel(sessionFlagCounts[selectedSession.session_id] ?? 0).color
                    }`}>
                      <div className={`w-2 h-2 rounded-full ${
                        getRiskLevel(sessionFlagCounts[selectedSession.session_id] ?? 0).dotColor
                      }`} />
                      {getRiskLevel(sessionFlagCounts[selectedSession.session_id] ?? 0).label}
                    </div>
                    
                    <div className="mt-3 h-2 bg-slate-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          (sessionFlagCounts[selectedSession.session_id] ?? 0) === 0
                            ? 'bg-green-500'
                            : (sessionFlagCounts[selectedSession.session_id] ?? 0) <= 3
                            ? 'bg-orange-500'
                            : 'bg-red-500'
                        }`}
                        style={{ 
                          width: `${Math.min(((sessionFlagCounts[selectedSession.session_id] ?? 0) / 5) * 100, 100)}%` 
                        }}
                      />
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      {(sessionFlagCounts[selectedSession.session_id] ?? 0) === 0
                        ? 'No violations detected'
                        : `${sessionFlagCounts[selectedSession.session_id]} interval${(sessionFlagCounts[selectedSession.session_id] ?? 0) === 1 ? '' : 's'} flagged`}
                    </p>
                  </div>

                  <button
                    onClick={() => viewSessionDetails(selectedSession.session_id)}
                    className="w-full py-3 bg-gradient-to-r from-teal-500 to-cyan-600 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transform hover:scale-[1.02] transition-all flex items-center justify-center gap-2"
                  >
                    <Eye className="w-5 h-5" />
                    <span>View Full Monitoring</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
