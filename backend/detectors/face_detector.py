import cv2
from ultralytics import YOLO
import numpy as np

class FaceDetector:
    def __init__(self, model_name='yolov8n.pt', confidence=0.5):
        self.model = YOLO(model_name)
        self.confidence = confidence
    
    def detect_faces(self, frame):
        """
        Detect faces in a frame
        
        Args:
            frame: Input image/frame (numpy array)
            
        Returns:
            dict: {
                'num_faces': int,
                'multiple_faces': bool,
                'boxes': list of bounding boxes [[x1,y1,x2,y2], ...],
                'confidences': list of confidence scores
            }
        """
        results = self.model(frame, classes=[0], conf=self.confidence, verbose=False)
        
        boxes = results[0].boxes.xyxy.cpu().numpy() if len(results[0].boxes) > 0 else []
        confidences = results[0].boxes.conf.cpu().numpy() if len(results[0].boxes) > 0 else []
        
        num_faces = len(boxes)
        
        return {
            'num_faces': num_faces,
            'multiple_faces': num_faces > 1,
            'no_face': num_faces == 0,
            'boxes': boxes,
            'confidences': confidences
        }
    
    def annotate_frame(self, frame, detection_result):
        """
        Draw bounding boxes and status on frame
        
        Args:
            frame: Input frame
            detection_result: Output from detect_faces()
            
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        num_faces = detection_result['num_faces']
        
        # Draw boxes
        for box, conf in zip(detection_result['boxes'], detection_result['confidences']):
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated, f'{conf:.2f}', (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Status text
        cv2.putText(annotated, f"Faces Detected: {num_faces}", (20, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        
        return annotated


# Example usage
if __name__ == "__main__":
    # Initialize detector
    detector = FaceDetector()
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect faces
        result = detector.detect_faces(frame)
        print(f"Faces detected: {result['num_faces']}, Multiple: {result['multiple_faces']}")
        
        # Annotate frame
        annotated = detector.annotate_frame(frame, result)
        
        cv2.imshow('YOLO Face Detection', annotated)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()