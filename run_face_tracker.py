#!/usr/bin/env python3
"""
Face Tracker Launcher
Simple script to run the face tracking application with error handling.
"""

import sys
import os
import subprocess

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import cv2
        import numpy
        import PIL
        import tkinter
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install requirements with: pip install -r requirements_face_tracker.txt")
        return False

def main():
    """Main launcher function"""
    print("Face Tracker Application")
    print("=" * 30)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("Dependencies OK ✓")
    print("Starting Face Tracker...")
    print("Press Ctrl+C to exit")
    
    try:
        # Import and run the main application
        from face_tracker import main as app_main
        app_main()
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()