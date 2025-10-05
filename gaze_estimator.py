import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Eye landmark indices for iris and eye corners
LEFT_EYE = [33, 133, 160, 159, 158, 157, 173]
RIGHT_EYE = [362, 263, 387, 386, 385, 384, 398]
LEFT_IRIS = [468, 469, 470, 471, 472]
RIGHT_IRIS = [473, 474, 475, 476, 477]
LEFT_EYE_TOP = 159
LEFT_EYE_BOTTOM = 145
RIGHT_EYE_TOP = 386
RIGHT_EYE_BOTTOM = 374

def get_gaze_direction(eye_points, iris_points):
    """Calculate gaze direction based on iris position relative to eye corners"""
    left_corner = eye_points[0]
    right_corner = eye_points[1]
    iris_center = np.mean(iris_points, axis=0)
    
    eye_width = np.linalg.norm(right_corner - left_corner) #  calculate eye width
    eye_center = (left_corner + right_corner) / 2 # calculate eye center
    offset_ratio = (iris_center[0] - eye_center[0]) / eye_width # horizontal offset ratio
    
    """Detect if gaze is looking down based on vertical eye offset ratio"""
    
    # Get left eye points
    left_top = np.array([landmarks[LEFT_EYE_TOP].x * w, landmarks[LEFT_EYE_TOP].y * h])
    left_bottom = np.array([landmarks[LEFT_EYE_BOTTOM].x * w, landmarks[LEFT_EYE_BOTTOM].y * h])
    left_iris_center = np.mean([[landmarks[i].x * w, landmarks[i].y * h] for i in LEFT_IRIS], axis=0)
    
    # Get right eye points
    right_top = np.array([landmarks[RIGHT_EYE_TOP].x * w, landmarks[RIGHT_EYE_TOP].y * h])
    right_bottom = np.array([landmarks[RIGHT_EYE_BOTTOM].x * w, landmarks[RIGHT_EYE_BOTTOM].y * h])
    right_iris_center = np.mean([[landmarks[i].x * w, landmarks[i].y * h] for i in RIGHT_IRIS], axis=0)
    
    # Calculate vertical offset ratio for each eye
    left_eye_height = left_bottom[1] - left_top[1]
    left_offset = (left_iris_center[1] - left_top[1]) / left_eye_height
    
    right_eye_height = right_bottom[1] - right_top[1]
    right_offset = (right_iris_center[1] - right_top[1]) / right_eye_height
    
    # Average both eyes
    avg_vertical_ratio = (left_offset + right_offset) / 2
    
    # Determine gaze direction
    # if avg_vertical_ratio > 0.45:
    #     return "LOOKING DOWN", avg_vertical_ratio
    # elif avg_vertical_ratio < 0.40:
    #     return "LOOKING UP", avg_vertical_ratio
    # else:
    #     return "LOOKING STRAIGHT", avg_vertical_ratio
    
    # if offset_ratio < -0.08:
    #     return "LEFT"
    # elif offset_ratio > 0.08:
    #     return "RIGHT"
    # return "CENTER"
    
    HOR = (iris_center.x - eye_left.x) / (eye_right.x - eye_left.x)

# Vertical Offset Ratio (VOR)
    VOR = (iris_center.y - eye_top.y) / (eye_bottom.y - eye_top.y)

    print("HOR:", HOR, "VOR:", VOR)

# Start webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)
    
    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        h, w = frame.shape[:2]
        
        # Extract left eye and iris points
        left_eye_pts = np.array([[landmarks[i].x * w, landmarks[i].y * h] 
                                  for i in [33, 133]])
        left_iris_pts = np.array([[landmarks[i].x * w, landmarks[i].y * h] 
                                   for i in LEFT_IRIS])
        
        # Extract right eye and iris points
        right_eye_pts = np.array([[landmarks[i].x * w, landmarks[i].y * h] 
                                   for i in [362, 263]])
        right_iris_pts = np.array([[landmarks[i].x * w, landmarks[i].y * h] 
                                    for i in RIGHT_IRIS])
        
        # Get gaze direction
        left_gaze = get_gaze_direction(left_eye_pts, left_iris_pts)
        right_gaze = get_gaze_direction(right_eye_pts, right_iris_pts)
        
        # Use consensus from both eyes
        gaze = left_gaze if left_gaze == right_gaze else "CENTER"
        
        # Display result
        cv2.putText(frame, f"Gaze: {gaze}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        
        # Draw iris points
        for point in left_iris_pts:
            cv2.circle(frame, tuple(point.astype(int)), 2, (0, 255, 255), -1)
        for point in right_iris_pts:
            cv2.circle(frame, tuple(point.astype(int)), 2, (0, 255, 255), -1)
    
    cv2.imshow('Eye Gaze Detection', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()