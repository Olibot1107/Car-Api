# Face Tracker Application

A real-time face tracking application that uses your camera to detect and track faces with visual feedback and direction indicators.

## Features

- **Real-time Face Detection**: Uses OpenCV's Haar Cascade classifier to detect faces
- **Face Lock-On**: Automatically locks onto the largest/most prominent face in view
- **Direction Tracking**: Shows which direction your face is relative to the screen center
- **Visual Feedback**: Live camera feed with tracking overlays and indicators
- **Smooth Tracking**: Built-in smoothing to reduce jitter and provide stable tracking
- **Distance Estimation**: Progress bar indicates relative distance based on face size

## Requirements

- Python 3.6 or higher
- OpenCV (cv2)
- NumPy
- Pillow (PIL)
- Tkinter (usually included with Python)

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_face_tracker.txt
   ```

2. **Alternative Manual Installation**:
   ```bash
   pip install opencv-python numpy Pillow
   ```

## Usage

### Quick Start

1. **Run the Application**:
   ```bash
   python run_face_tracker.py
   ```
   
   Or directly:
   ```bash
   python face_tracker.py
   ```

2. **Grant Camera Access**: Allow the application to access your camera when prompted.

3. **Position Your Face**: Place your face in the camera view. The application will automatically detect and track it.

### Controls

- **Start Tracking**: Begin face detection and tracking
- **Stop Tracking**: Pause the tracking process
- **Reset**: Clear current tracking state and start fresh

### Understanding the Interface

- **Camera Feed**: Live video with tracking overlays
- **Face Rectangle**: Green box around detected face
- **Center Dot**: Red dot showing tracked face center
- **Tracking Line**: White line from screen center to face
- **Direction Display**: Shows LEFT, RIGHT, UP, DOWN, or CENTER
- **Progress Bar**: Indicates relative distance (larger face = closer)
- **Status Messages**: Real-time updates on tracking state

## How It Works

1. **Scanning Phase**: The application continuously scans for faces when no face is detected
2. **Lock-On Phase**: When a face is found, it locks onto the largest face in view
3. **Tracking Phase**: Smoothly tracks face movement with position smoothing
4. **Lost Target**: If face is lost, returns to scanning phase

## Technical Details

- **Frame Rate**: ~30 FPS for smooth real-time performance
- **Face Detection**: Uses OpenCV's pre-trained Haar Cascade classifier
- **Smoothing**: Alpha blending (0.3) to reduce tracking jitter
- **Direction Calculation**: Based on face center relative to screen center
- **Distance Estimation**: Face size relative to maximum expected size

## Troubleshooting

### Camera Not Found
- Ensure camera is connected and not in use by another application
- Check camera permissions in your operating system
- Try running as administrator if on Windows

### Poor Detection
- Ensure good lighting conditions
- Remove obstructions (glasses, hats may affect detection)
- Face should be reasonably centered in camera view
- Try adjusting detection parameters in the code

### Performance Issues
- Close other applications using the camera
- Reduce camera resolution in code if needed
- Ensure sufficient CPU resources

## Customization

You can modify detection parameters in the `FaceTrackerApp.__init__()` method:

```python
# Face detection parameters
self.min_face_size = (50, 50)      # Minimum face size
self.max_face_size = (300, 300)    # Maximum face size  
self.detection_confidence = 1.1    # Detection sensitivity
self.detection_neighbors = 5       # Detection quality
```

## Files

- `face_tracker.py` - Main application
- `run_face_tracker.py` - Launcher with error handling
- `requirements_face_tracker.txt` - Python dependencies
- `README_Face_Tracker.md` - This documentation

## License

This application is provided as-is for educational and personal use.

## Notes

- This application uses your camera for real-time face detection
- No images or video are saved to disk
- Processing happens locally on your machine
