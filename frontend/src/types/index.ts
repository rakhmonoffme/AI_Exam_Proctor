export interface Session {
  session_id: string;
  user_id: string;
  exam_id: string;
  start_time: string;
  end_time?: string;
  status: 'active' | 'ended';
  total_score: number;
  current_interval_score: number;
}

export interface SessionStats {
  total_sessions: number;
  active_sessions: number;
  high_risk: number;
  flagged: number;
}

export interface Violation {
  type: string;
  description: string;
  score: number;
  timestamp: string;
  severity: 'low' | 'medium' | 'high';
}

export interface GazeData {
  status: 'focused' | 'distracted';
  horizontal_ratio: number;
  vertical_ratio: number;
}

export interface FaceData {
  count: number;
  has_multiple: boolean;
}

export interface AudioData {
  speech_detected: boolean;
  multiple_speakers: boolean;
}

export interface ScreenActivity {
  tab_switches: number;
  copy_paste_events: number;
}

export interface MonitoringUpdate {
  session_id: string;
  frame?: string;
  gaze: GazeData;
  faces: FaceData;
  audio: AudioData;
  screen: ScreenActivity;
  interval_score: number;
  total_score: number;
  violations: Violation[];
  timestamp: string;
  status: 'clear' | 'flagged';
}

export interface FlaggedInterval {
  interval_id: string;
  session_id: string;
  start_time: string;
  end_time: string;
  score: number;
  video_id: string;
}

export interface SessionDetails {
  session: Session;
  monitoring_data: MonitoringUpdate;
  flagged_intervals: FlaggedInterval[];
}
