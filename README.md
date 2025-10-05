# 🎓 AI Proctoring System

Advanced real-time exam monitoring system with AI-powered behavioral analysis, eye tracking, audio monitoring, and comprehensive academic integrity protection.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v3.0.0-green.svg)
![MongoDB](https://img.shields.io/badge/mongodb-v7.0-green.svg)


---

## 📋 Table of Contents

- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## ✨ Features

### 🎯 Core Detection Features

- **Advanced Eye Tracking** - Real-time gaze detection using MediaPipe FaceMesh
  - Detects looking left/right/down
  - Iris position tracking
  - Blink detection (counted as focused)

- **Face Detection** - YOLO-based person detection
  - Detects multiple faces in frame
  - Real-time face counting

- **Audio Monitoring** - Voice activity detection
  - Single vs multiple speaker detection
  - Frequency-based speaker differentiation

- **Screen Activity Monitoring**
  - Tab switching detection (Alt+Tab, Cmd+Tab)
  - Copy/paste event tracking
  - Clipboard monitoring

### 📊 Scoring & Analytics

- **Interval-based Scoring** (30-second intervals)
  - Gaze distracted: +2 points
  - Speech detected: +3 points
  - Multiple voices: +10 points
  - Tab switch: +4 points per occurrence
  - Copy/paste: +5 points per occurrence
  - Multiple faces: +10 points

- **Automatic Flagging** - Intervals with score ≥ 10 are flagged immediately
- **Video Recording** - Only flagged intervals are saved to disk
- **Real-time Updates** - WebSocket-based live monitoring

### 💾 Data Management

- **MongoDB Integration** - Persistent storage of sessions and violations
- **Video Storage** - Organized by user in `flagged_videos/` folder
- **Session Tracking** - Complete audit trail of all monitoring sessions

---

## 🏗️ System Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  Student Side   │         │   Admin Side    │
│                 │         │                 │
│  - Webcam       │         │  - Dashboard    │
│  - Microphone   │◄───────►│  - Live View    │
│  - Screen       │         │  - Analytics    │
└─────────────────┘         └─────────────────┘
         │                           │
         │    WebSocket (Socket.IO)  │
         └───────────┬───────────────┘
                     │
            ┌────────▼────────┐
            │  Flask Backend  │
            │    (app.py)     │
            └────────┬────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐  ┌────▼────┐  ┌───▼────┐
   │ Gaze   │  │  Face   │  │ Audio  │
   │Detector│  │Detector │  │Detector│
   └────────┘  └─────────┘  └────────┘
        │            │            │
        └────────────┼────────────┘
                     │
            ┌────────▼────────┐
            │   score.py      │
            │  (Scoring)      │
            └────────┬────────┘
                     │
            ┌────────▼────────┐
            │   database.py   │
            │   (MongoDB)     │
            └─────────────────┘
```

---

## 🔧 Prerequisites

### Required Software

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **MongoDB 4.4+** - [Download](https://www.mongodb.com/try/download/community)
- **Webcam** - For video monitoring
- **Microphone** - For audio monitoring

### Operating System Support

- ✅ macOS
- ✅ Linux (Ubuntu/Debian)
- ✅ Windows 10/11

---

## 🚀 Installation

### Option 1: Automated Setup (Recommended)

```bash
# Clone the repository (or download files)
cd AI_Exam_Proctor

# Make setup script executable
chmod +x setup.sh

# Run automated setup
./setup.sh
#  Start the application
./run.sh
```

The script will:
- Create virtual environment
- Install all dependencies
- Download YOLO models
- Set up MongoDB
- Create configuration files
- Test the system
- Generate run scripts

### Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p logs flagged_videos temp

# Start MongoDB (macOS)
brew services start mongodb-community

# Start MongoDB (Linux)
sudo systemctl start mongodb
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file (or modify existing):

```bash
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
DB_NAME=proctoring_db

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Scoring Configuration
INTERVAL_DURATION=30  # seconds
FLAG_THRESHOLD=10     # score threshold for flagging

# Video Configuration
VIDEO_FPS=10
```

### MongoDB Atlas (Cloud Option)

If using MongoDB Atlas instead of local MongoDB:

1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create cluster and get connection string
3. Update `.env`:
   ```bash
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```

---

## 📖 Usage

### Starting the Backend Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run the server
python app.py

# Or use the run script
./run.sh
```

Server will start at: `http://localhost:5000`

### Testing the System

```bash
# Run system tests
python test_system.py
```

This will verify:
- All libraries are installed correctly
- MongoDB connection is working
- System is ready to run

### Starting a Monitoring Session

#### Via API:

```bash
curl -X POST http://localhost:5000/api/session/create \
  -H "Content-Type: application/json" \
  -d '{"user_id": "student_123", "exam_id": "midterm_2024"}'
```

#### Via Frontend:
1. Open student portal
2. Enter user ID and exam ID
3. Grant camera/microphone/screen permissions
4. Click "Start Exam Session"

### Ending a Session

```bash
curl -X POST http://localhost:5000/api/session/end \
  -H "Content-Type: application/json" \
  -d '{"user_id": "student_123", "exam_id": "midterm_2024"}'
```

---

## 📡 API Documentation

### REST Endpoints

#### Create Session
```http
POST /api/session/create
Content-Type: application/json

{
  "user_id": "string",
  "exam_id": "string" (optional)
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "ObjectId",
  "user_id": "student_123",
  "exam_id": "midterm_2024"
}
```

#### End Session
```http
POST /api/session/end
Content-Type: application/json

{
  "user_id": "string",
  "exam_id": "string"
}
```

#### Get Active Sessions
```http
GET /api/sessions/active
```

**Response:**
```json
{
  "sessions": [
    {
      "user_id": "student_123",
      "exam_id": "midterm_2024",
      "session_id": "ObjectId",
      "interval_score": 5,
      "total_score": 15,
      "is_running": true
    }
  ],
  "count": 1
}
```

#### Get Session Statistics
```http
GET /api/sessions/stats
```

**Response:**
```json
{
  "total_sessions": 10,
  "active_sessions": 2,
  "flagged_intervals": 5,
  "high_risk": 2
}
```

#### Get Session Details
```http
GET /api/session/{session_id}/details
```

#### Get All Flagged Intervals
```http
GET /api/flagged/all
```

#### Get Video
```http
GET /api/video/{video_id}
GET /api/video/file/{filepath}
```

### WebSocket Events

#### Connect
```javascript
const socket = io('http://localhost:5000');
```

#### Join Session
```javascript
socket.emit('join_session', { session_id: 'ObjectId' });
```

#### Receive Real-time Updates
```javascript
socket.on('monitoring_update', (data) => {
  // data contains:
  // - frame (base64 encoded)
  // - gaze (focused/distracted)
  // - faces (number detected)
  // - interval_score
  // - violations
  // - timestamp
});
```

---

## 📁 Project Structure

```
ai-proctoring-system/
├── app.py                 # Flask backend server
├── score.py               # Scoring and monitoring logic
├── database.py            # MongoDB operations
├── gaze_direction.py      # Gaze detection class
├── face_detector.py       # Face detection class
├── audiodetector.py       # Audio monitoring class
├── screenmonitor.py       # Screen activity monitoring
├── logger.py              # Logging configuration
│
├── flagged_videos/        # Stored videos (organized by user)
│   ├── user_123/
│   │   ├── flagged_2024-10-05T14-30-00_score12.mp4
│   │   └── flagged_2024-10-05T15-45-30_score15.mp4
│   └── user_456/
│
├── logs/                  # Application logs
│   ├── app.log
│   └── app_errors.log
│
├── temp/                  # Temporary files
│
├── venv/                  # Virtual environment
├── requirements.txt       # Python dependencies
├── .env                   # Environment configuration
├── setup.sh              # Automated setup script
├── run.sh                # Run script
├── test_system.py        # System tests
└── README.md             # This file
```

---

## 🐛 Troubleshooting

### MongoDB Connection Error

**Error:** `Connection refused on localhost:27017`

**Solution:**
```bash
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongodb

# Verify it's running
pgrep mongod
```

### Camera Not Detected

**Error:** `Cannot open camera`

**Solution:**
1. Check camera permissions in System Preferences/Settings
2. Close other apps using the camera
3. Try different camera index:
   ```python
   cap = cv2.VideoCapture(1)  # Try 0, 1, 2, etc.
   ```

### Audio Device Error

**Error:** `sounddevice error`

**Solution:**
```bash
# List available audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Install PortAudio (if needed)
# macOS
brew install portaudio

# Linux
sudo apt-get install portaudio19-dev
```

### YOLO Model Download Fails

**Solution:**
```bash
# Manually download
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### Module Not Found Errors

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### High CPU Usage

**Solution:**
- Reduce FPS in video recording (change `VIDEO_FPS` in .env)
- Increase check interval (default is 10 seconds)
- Use smaller YOLO model or disable face detection temporarily

---

## 📊 Performance Optimization

### Recommended Settings

**For Low-End Systems:**
```python
# In score.py
check_interval = 15  # Check every 15 seconds instead of 10
VIDEO_FPS = 5        # Reduce video FPS
```

**For High-End Systems:**
```python
check_interval = 5   # More frequent checks
VIDEO_FPS = 30       # Higher quality video
```

---

## 🔐 Security Considerations

1. **Always use HTTPS in production**
2. **Implement authentication** (JWT, OAuth)
3. **Sanitize user inputs**
4. **Enable MongoDB authentication**
5. **Use environment variables** for sensitive data
6. **Regular security updates**

---

## 📝 Scoring Rules Summary

| Activity | Score | Description |
|----------|-------|-------------|
| Gaze Distracted | +2 | Looking left/right/down |
| No face detected | +9 | No face detected |
| Multiple Voices | +10 | Multiple speakers detected |
| Tab Switch | +4 | Per tab switch event |
| Copy/Paste | +5 | Per copy/paste event |
| Multiple Faces | +10 | More than one face detected |

**Flag Threshold:** Score ≥ 10 triggers immediate flag

**Interval Duration:** 30 seconds (configurable)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Support

For issues and questions: shohrakhmonov@gmail.com
- Create an issue in the repository
- Check troubleshooting section above
- Review API documentation

---
