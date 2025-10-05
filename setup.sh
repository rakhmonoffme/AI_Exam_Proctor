#!/bin/bash

# AI Proctoring System - Automated Setup Script
# This script will set up the entire project environment

echo "=================================================="
echo "🚀 AI Proctoring System - Automated Setup"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
echo "📋 Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} Python found: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Create project directory structure
echo ""
echo "📁 Step 2: Creating project directory structure..."
mkdir -p logs
mkdir -p flagged_videos
mkdir -p temp
echo -e "${GREEN}✓${NC} Directories created"

# Create virtual environment
echo ""
echo "🐍 Step 3: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3.10 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}!${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Step 4: Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"



# Upgrade pip
echo ""
echo "📦 Step 5: Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo -e "${GREEN}✓${NC} Pip upgraded"


# Download YOLO model
echo ""
echo "🤖 Step 7: Downloading YOLO model..."
python3 -c "from ultralytics import YOLO; YOLO('yolov8n.pt')" > /dev/null 2>&1
echo -e "${GREEN}✓${NC} YOLO model downloaded"

# Check MongoDB
echo ""
echo "💾 Step 8: Checking MongoDB installation..."
if command -v mongod &> /dev/null; then
    echo -e "${GREEN}✓${NC} MongoDB is installed"
    
    # Check if MongoDB is running
    if pgrep -x "mongod" > /dev/null; then
        echo -e "${GREEN}✓${NC} MongoDB is running"
    else
        echo -e "${YELLOW}!${NC} MongoDB is not running"
        echo "Starting MongoDB..."
        
        # Try to start MongoDB (macOS)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start mongodb-community 2>/dev/null || mongod --fork --logpath /usr/local/var/log/mongodb/mongo.log 2>/dev/null
        # Linux
        else
            sudo systemctl start mongodb 2>/dev/null || sudo service mongodb start 2>/dev/null
        fi
        
        sleep 2
        if pgrep -x "mongod" > /dev/null; then
            echo -e "${GREEN}✓${NC} MongoDB started successfully"
        else
            echo -e "${YELLOW}!${NC} Could not start MongoDB automatically"
        fi
    fi
else
    echo -e "${YELLOW}!${NC} MongoDB is not installed"
    echo ""
    echo "Please install MongoDB:"
    echo "  macOS: brew install mongodb-community"
    echo "  Ubuntu: sudo apt-get install mongodb"
    echo "  Or use MongoDB Atlas (cloud): https://www.mongodb.com/cloud/atlas"
fi

# Create .env file
echo ""
echo "⚙️  Step 9: Creating configuration file..."
if [ ! -f ".env" ]; then
cat > .env << EOF
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
DB_NAME=proctoring_db

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Scoring Configuration
INTERVAL_DURATION=30
FLAG_THRESHOLD=10

# Video Configuration
VIDEO_FPS=10
EOF
    echo -e "${GREEN}✓${NC} Configuration file created (.env)"
else
    echo -e "${YELLOW}!${NC} Configuration file already exists"
fi

# Create requirements.txt
echo ""
echo "📝 Step 10: Creating requirements.txt..."
cat > requirements.txt << EOF
# Computer Vision
ultralytics>=8.2.0
opencv-python>=4.8.0
mediapipe>=0.10.14
numpy>=1.24.0,<2.0
 

# Audio Processing
sounddevice==0.4.6

# System Monitoring
pyperclip
pynput

# Database
pymongo


# Web Framework
flask
flask_socketio
flask_cors
python-socketio

# Utilities
python-dotenv==1.0.0

pybind11>=2.12

EOF
echo -e "${GREEN}✓${NC} requirements.txt created"
# Install Python dependencies
echo ""
echo "📥 Step 6: Installing Python dependencies from requirements.txt..."
echo "This may take a few minutes..."

# Install all dependencies from requirements.txt
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} All Python dependencies installed successfully!"


# Create run script
echo ""
echo "🏃 Step 11: Creating run script..."
cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python backend/app.py
EOF
chmod +x run.sh
echo -e "${GREEN}✓${NC} Run script created (run.sh)"

# Create test script
echo ""
echo "🧪 Step 12: Creating test script..."
cat > test_system.py << 'EOF'
#!/usr/bin/env python3
import sys

def test_imports():
    """Test if all required libraries can be imported"""
    print("Testing imports...")
    
    try:
        import cv2
        print("✓ OpenCV")
    except ImportError as e:
        print(f"✗ OpenCV: {e}")
        return False
    
    try:
        import mediapipe
        print("✓ MediaPipe")
    except ImportError as e:
        print(f"✗ MediaPipe: {e}")
        return False
    
    try:
        from ultralytics import YOLO
        print("✓ YOLO")
    except ImportError as e:
        print(f"✗ YOLO: {e}")
        return False
    
    try:
        import pymongo
        print("✓ PyMongo")
    except ImportError as e:
        print(f"✗ PyMongo: {e}")
        return False
    
    try:
        from flask import Flask
        print("✓ Flask")
    except ImportError as e:
        print(f"✗ Flask: {e}")
        return False
    
    print("\n✓ All imports successful!")
    return True

def test_mongodb():
    """Test MongoDB connection"""
    print("\nTesting MongoDB connection...")
    try:
        from pymongo import MongoClient
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✓ MongoDB connection successful")
        client.close()
        return True
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False

if __name__ == "__main__":
    print("="*50)
    print("AI Proctoring System - System Test")
    print("="*50)
    print()
    
    imports_ok = test_imports()
    mongodb_ok = test_mongodb()
    
    print()
    print("="*50)
    if imports_ok and mongodb_ok:
        print("✓ All tests passed! System is ready.")
        sys.exit(0)
    else:
        print("✗ Some tests failed. Please check the errors above.")
        sys.exit(1)
EOF
chmod +x test_system.py
echo -e "${GREEN}✓${NC} Test script created (test_system.py)"

echo ""
echo "2. Testing the system:"
python test_system.py


# Print summary
echo ""
echo "=================================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "📋 Next Steps:"

echo ""
echo "1. Start the backend server:"
echo "   python app.py"
echo "   or"
echo "   ./run.sh"
echo ""
echo "2. Access the API at:"
echo "   http://localhost:5000"
echo ""
echo "📚 Read README.md for detailed documentation"
echo ""
echo "=================================================="