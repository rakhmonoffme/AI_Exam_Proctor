export interface Session {
  session_id: string;
  user_id: string;
  exam_id: string;
  total_score: number;
  current_interval_score?: number;
  is_running?: boolean;
}

export interface SessionStats {
  total_sessions: number;
  active_sessions: number;
  high_risk: number;
  flagged: number;
}

export interface Violation {
  type: string;
  score: number;
  timestamp: string;
  details: string;
  description?: string;  
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
  user_id: string;
  frame?: string;
  gaze: {
    status: string;
    horizontal_ratio: number;
    vertical_ratio: number;
  };
  faces: {
    count: number;
    has_multiple: boolean;
  };
  audio: {
    speech_detected: boolean;
    multiple_speakers: boolean;
  };
  screen: {
    tab_switches: number;
    copy_paste_events: number;
  };
  interval_score: number;
  total_score: number;
  violations: Violation[];
  status?: string;  // Make optional
  timestamp: string;
}

export interface FlaggedInterval {
  interval_id: string;
  session_id: string;
  start_time: string;
  end_time: string;
  score: number;
  video_id: string;
  video_path: string;
  violations: Violation[];
}

export interface SessionDetails {
  session: Session;
  monitoring_data: MonitoringUpdate;
  flagged_intervals: FlaggedInterval[];
  all_violations: Violation[];
}
