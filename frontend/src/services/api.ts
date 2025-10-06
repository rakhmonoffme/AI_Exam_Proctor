import { io, Socket } from 'socket.io-client';
import type { Session, SessionStats, SessionDetails, FlaggedInterval, MonitoringUpdate } from '../types';

const API_BASE_URL = 'http://localhost:8000';

class APIService {
  private socket: Socket | null = null;

  async createSession(userId: string, examId: string): Promise<Session> {
    const response = await fetch(`${API_BASE_URL}/api/session/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId, exam_id: examId }),
    });

    if (!response.ok) {
      throw new Error('Failed to create session');
    }

    return response.json();
  }

  async endSession(sessionId: string, userId: string, examId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/session/end`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId, exam_id: examId }),
    });

    if (!response.ok) {
      throw new Error('Failed to end session');
    }
  }

  async sendFrame(sessionId: string, frameData: string, screenActivity?: {
    tabSwitches: number;
    copyPasteEvents: number;
    windowBlurred: boolean;
  }): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/frame`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        frame: frameData,
        screen_activity: screenActivity,
      }),
    });

    if (!response.ok) {
      console.error('Failed to send frame');
    }
  }

  async getActiveSessions(): Promise<Session[]> {
    const response = await fetch(`${API_BASE_URL}/api/sessions/active`);

    if (!response.ok) {
      throw new Error('Failed to fetch active sessions');
    }

    return response.json(); // Backend now returns array directly
  }

  async getStats(): Promise<SessionStats> {
    const response = await fetch(`${API_BASE_URL}/api/sessions/stats`);

    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }

    return response.json();
  }

  async getSessionDetails(sessionId: string): Promise<SessionDetails> {
    const response = await fetch(`${API_BASE_URL}/api/session/${sessionId}/details`);

    if (!response.ok) {
      throw new Error('Failed to fetch session details');
    }

    return response.json();
  }

  async getFlaggedIntervals(): Promise<FlaggedInterval[]> {
    const response = await fetch(`${API_BASE_URL}/api/flagged/all`);

    if (!response.ok) {
      throw new Error('Failed to fetch flagged intervals');
    }

    return response.json();
  }

  // This method is deprecated - use getVideoByPath instead
getVideoUrl(videoPath: string): string {
  console.warn('getVideoUrl is deprecated, use getVideoByPath instead');
  return `${API_BASE_URL}/api/video/path`;
}
  async getVideoByPath(videoPath: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/api/video/path`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ video_path: videoPath }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch video');
    }

    // Return blob URL for video playback
    const blob = await response.blob();
    return URL.createObjectURL(blob);
  }

  connectSocket(): Socket {
    if (!this.socket) {
      this.socket = io(API_BASE_URL, {
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
      });

      this.socket.on('connect', () => {
        console.log('Socket connected');
      });

      this.socket.on('disconnect', () => {
        console.log('Socket disconnected');
      });

      this.socket.on('connect_error', (error) => {
        console.error('Socket connection error:', error);
      });
    }

    return this.socket;
  }

  joinSession(sessionId: string): void {
    if (this.socket) {
      this.socket.emit('join_session', { session_id: sessionId });
    }
  }

  onMonitoringUpdate(callback: (data: MonitoringUpdate) => void): void {
    if (this.socket) {
      this.socket.on('monitoring_update', callback);
    }
  }

  offMonitoringUpdate(callback: (data: MonitoringUpdate) => void): void {
    if (this.socket) {
      this.socket.off('monitoring_update', callback);
    }
  }

  disconnectSocket(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export const apiService = new APIService();
