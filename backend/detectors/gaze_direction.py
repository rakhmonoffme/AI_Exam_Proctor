import cv2
import mediapipe as mp
import numpy as np

class GazeFocusDetector:
    def __init__(self, h_threshold=(0.35, 0.65), v_threshold=(0.35, 0.50)):
       
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Eye landmark indices
        self.LEFT_EYE = [33, 133]
        self.RIGHT_EYE = [362, 263]
        self.LEFT_EYE_TOP = 159
        self.LEFT_EYE_BOTTOM = 145
        self.RIGHT_EYE_TOP = 386
        self.RIGHT_EYE_BOTTOM = 374
        self.LEFT_IRIS = [468, 469, 470, 471, 472]
        self.RIGHT_IRIS = [473, 474, 475, 476, 477]
        
        # Thresholds
        self.h_min, self.h_max = h_threshold
        self.v_min, self.v_max = v_threshold
    
    def detect_focus(self, frame):
        """
        Detect if person is focused or distracted
        
        Args:
            frame: Input image/frame (numpy array, BGR format)
            
        Returns:
            dict: {
                'focused': bool,
                'h_ratio': float,
                'v_ratio': float,
                'face_detected': bool
            }
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return {
                'focused': False,
                'h_ratio': None,
                'v_ratio': None,
                'face_detected': False,
                'where': None
            }
        
        landmarks = results.multi_face_landmarks[0].landmark
        h, w = frame.shape[:2]
        
        # Calculate focus
        focused, h_ratio, v_ratio, where = self._is_looking_straight(landmarks, w, h)
        
        
        return {
            'focused': focused,
            'h_ratio': h_ratio,
            'v_ratio': v_ratio,
            'face_detected': True,
            'where': where
        }
    
    def _is_looking_straight(self, landmarks, w, h):
        """Internal method to calculate gaze direction"""
        
        # Get left eye data
        left_corners = np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in self.LEFT_EYE])
        left_top = np.array([landmarks[self.LEFT_EYE_TOP].x * w, landmarks[self.LEFT_EYE_TOP].y * h])
        left_bottom = np.array([landmarks[self.LEFT_EYE_BOTTOM].x * w, landmarks[self.LEFT_EYE_BOTTOM].y * h])
        left_iris = np.mean([[landmarks[i].x * w, landmarks[i].y * h] for i in self.LEFT_IRIS], axis=0)
        
        # Get right eye data
        right_corners = np.array([[landmarks[i].x * w, landmarks[i].y * h] for i in self.RIGHT_EYE])
        right_top = np.array([landmarks[self.RIGHT_EYE_TOP].x * w, landmarks[self.RIGHT_EYE_TOP].y * h])
        right_bottom = np.array([landmarks[self.RIGHT_EYE_BOTTOM].x * w, landmarks[self.RIGHT_EYE_BOTTOM].y * h])
        right_iris = np.mean([[landmarks[i].x * w, landmarks[i].y * h] for i in self.RIGHT_IRIS], axis=0)
        
        # Calculate horizontal ratios
        left_h_ratio = (left_iris[0] - left_corners[0][0]) / (left_corners[1][0] - left_corners[0][0])
        right_h_ratio = (right_iris[0] - right_corners[0][0]) / (right_corners[1][0] - right_corners[0][0])
        avg_h_ratio = (left_h_ratio + right_h_ratio) / 2
        
        # Calculate vertical ratios
        left_v_ratio = (left_iris[1] - left_top[1]) / (left_bottom[1] - left_top[1])
        right_v_ratio = (right_iris[1] - right_top[1]) / (right_bottom[1] - right_top[1])
        avg_v_ratio = (left_v_ratio + right_v_ratio) / 2
        where = None
        # Check if looking straight
        h_focused = self.h_min < avg_h_ratio < self.h_max
        v_focused = self.v_min < avg_v_ratio < self.v_max
        
        is_focused = h_focused and v_focused
        
        if avg_h_ratio < self.h_min:
            where = "LEFT"
        elif avg_h_ratio > self.h_max:
            where = "RIGHT"
        elif avg_v_ratio > 0.5:
            where = "DOWN"
        elif avg_v_ratio < 0.35:
            where = "UP"
        
        return is_focused, avg_h_ratio, avg_v_ratio, where
    
    def annotate_frame(self, frame, result):
        """
        Draw focus status on frame
        
        Args:
            frame: Input frame
            result: Output from detect_focus()
            
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        if not result['face_detected']:
            cv2.putText(annotated, "NO FACE DETECTED", (20, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
            return annotated
        
        status = "FOCUSED" if result['focused'] else "DISTRACTED: " + (result['where'] if result['where'] else "")
        color = (0, 255, 0) if result['focused'] else (0, 0, 255)
        
        cv2.putText(annotated, status, (20, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.8, color, 4)
        cv2.putText(annotated, f"H: {result['h_ratio']:.2f} | V: {result['v_ratio']:.2f}",
                   (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return annotated
    
    def close(self):
        """Release resources"""
        self.face_mesh.close()


# Standalone function version
def detect_gaze_focus(frame, h_threshold=(0.35, 0.65), v_threshold=(0.35, 0.50)):
    """
    Simple function to detect gaze focus
    
    Args:
        frame: Input frame (BGR)
        h_threshold: Horizontal focus range
        v_threshold: Vertical focus range
        
    Returns:
        dict: Focus detection results
    """
    detector = GazeFocusDetector(h_threshold, v_threshold)
    result = detector.detect_focus(frame)
    detector.close()
    return result


# Example usage
if __name__ == "__main__":
    # Using class
    detector = GazeFocusDetector()
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.flip(frame, 1)
        
        # Detect focus
        result = detector.detect_focus(frame)
        print(f"Focused: {result['focused']}")
        
        # Annotate frame
        annotated = detector.annotate_frame(frame, result)
        
        cv2.imshow('Gaze Focus Detection', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    detector.close()