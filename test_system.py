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
