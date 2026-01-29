#!/usr/bin/env python3
"""
Face Tracking Application
Uses camera to detect and track faces, with visual feedback and direction indicators.
"""

import cv2
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from PIL import Image, ImageTk
import sys
import os

class FaceTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Tracker - Lock On Mode")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # Application state
        self.running = False
        self.cap = None
        self.face_cascade = None
        self.tracking_active = False
        self.face_found = False
        self.last_face_position = None
        self.face_center = None
        
        # Face detection parameters
        self.min_face_size = (50, 50)
        self.max_face_size = (300, 300)
        self.detection_confidence = 1.1
        self.detection_neighbors = 5
        
        # Initialize OpenCV
        self.init_opencv()
        
        # Create UI
        self.create_ui()
        
        # Start camera thread
        self.camera_thread = None
        
    def init_opencv(self):
        """Initialize OpenCV and face detection"""
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Could not open camera")
                self.root.quit()
                return
                
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Load face cascade
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                messagebox.showerror("Error", "Could not load face cascade classifier")
                self.root.quit()
                
        except Exception as e:
            messagebox.showerror("Error", f"OpenCV initialization failed: {e}")
            self.root.quit()
    
    def create_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Top control panel
        control_frame = tk.LabelFrame(main_frame, text="Controls", bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        control_frame.pack(fill='x', pady=(0, 10))
        
        # Control buttons
        self.start_btn = tk.Button(control_frame, text="Start Tracking", 
                                 command=self.toggle_tracking, bg='#27ae60', fg='white', 
                                 font=('Arial', 10, 'bold'), width=15)
        self.start_btn.pack(side='left', padx=5, pady=5)
        
        self.reset_btn = tk.Button(control_frame, text="Reset", 
                                 command=self.reset_tracking, bg='#e74c3c', fg='white', 
                                 font=('Arial', 10, 'bold'), width=10)
        self.reset_btn.pack(side='left', padx=5, pady=5)
        
        # Status indicators
        self.status_frame = tk.Frame(control_frame, bg='#34495e')
        self.status_frame.pack(side='right', padx=5)
        
        self.status_label = tk.Label(self.status_frame, text="Status: Idle", 
                                   bg='#34495e', fg='white', font=('Arial', 10))
        self.status_label.pack(side='left')
        
        self.face_count_label = tk.Label(self.status_frame, text="Faces: 0", 
                                       bg='#34495e', fg='white', font=('Arial', 10))
        self.face_count_label.pack(side='left', padx=(10, 0))
        
        # Video display frame
        video_frame = tk.LabelFrame(main_frame, text="Camera Feed", bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        video_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Video canvas
        self.video_canvas = tk.Canvas(video_frame, bg='black', width=640, height=480)
        self.video_canvas.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Information panel
        info_frame = tk.LabelFrame(main_frame, text="Tracking Information", bg='#34495e', fg='white', font=('Arial', 12, 'bold'))
        info_frame.pack(fill='x', pady=(0, 10))
        
        # Grid layout for info
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)
        
        # Face position info
        tk.Label(info_frame, text="Face Position:", bg='#34495e', fg='white', font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.position_label = tk.Label(info_frame, text="Not Found", bg='#34495e', fg='white', font=('Arial', 10))
        self.position_label.grid(row=1, column=0, sticky='w', padx=5, pady=2)
        
        # Direction info
        tk.Label(info_frame, text="Direction:", bg='#34495e', fg='white', font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky='w', padx=5, pady=2)
        self.direction_label = tk.Label(info_frame, text="Scanning...", bg='#34495e', fg='white', font=('Arial', 10))
        self.direction_label.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        # Progress bar for face detection confidence
        tk.Label(info_frame, text="Lock Status:", bg='#34495e', fg='white', font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.progress_bar = ttk.Progressbar(info_frame, orient='horizontal', length=200, mode='determinate')
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
        
        # Instructions
        instructions = tk.Label(main_frame, text="Instructions: Position your face in the camera view. The app will detect and track your face.", 
                              bg='#2c3e50', fg='white', font=('Arial', 9), wraplength=780)
        instructions.pack(fill='x', pady=(0, 10))
    
    def toggle_tracking(self):
        """Start or stop face tracking"""
        if not self.running:
            self.running = True
            self.tracking_active = True
            self.start_btn.config(text="Stop Tracking", bg='#e74c3c')
            self.status_label.config(text="Status: Active - Scanning for faces...")
            self.face_count_label.config(text="Faces: 0")
            self.direction_label.config(text="Scanning...")
            self.progress_bar['value'] = 0
            
            # Start camera thread
            self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()
        else:
            self.running = False
            self.tracking_active = False
            self.start_btn.config(text="Start Tracking", bg='#27ae60')
            self.status_label.config(text="Status: Idle")
            self.face_count_label.config(text="Faces: 0")
            self.direction_label.config(text="Stopped")
            self.progress_bar['value'] = 0
    
    def reset_tracking(self):
        """Reset tracking state"""
        self.face_found = False
        self.last_face_position = None
        self.face_center = None
        self.progress_bar['value'] = 0
        self.position_label.config(text="Not Found")
        self.direction_label.config(text="Scanning...")
        self.status_label.config(text="Status: Active - Scanning for faces...")
    
    def camera_loop(self):
        """Main camera processing loop"""
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            # Process frame for face detection
            processed_frame = self.process_frame(frame)
            
            # Update UI with processed frame
            self.update_video_display(processed_frame)
            
            # Small delay to prevent overwhelming the system
            time.sleep(0.03)  # ~30 FPS
    
    def process_frame(self, frame):
        """Process a single frame for face detection and tracking"""
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.detection_confidence,
            minNeighbors=self.detection_neighbors,
            minSize=self.min_face_size,
            maxSize=self.max_face_size
        )
        
        # Update face count
        face_count = len(faces)
        self.root.after(0, lambda: self.face_count_label.config(text=f"Faces: {face_count}"))
        
        # Draw detection results
        if face_count > 0:
            # Find the largest face (most prominent)
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            # Calculate face center
            face_center_x = x + w // 2
            face_center_y = y + h // 2
            current_face_center = (face_center_x, face_center_y)
            
            # Update tracking state
            if not self.face_found:
                self.face_found = True
                self.last_face_position = current_face_center
                self.face_center = current_face_center
                self.root.after(0, lambda: self.status_label.config(text="Status: Face Detected - Locking On..."))
            
            # Update face center with smoothing
            if self.face_center:
                # Simple smoothing to reduce jitter
                alpha = 0.3
                self.face_center = (
                    int(self.face_center[0] * (1 - alpha) + current_face_center[0] * alpha),
                    int(self.face_center[1] * (1 - alpha) + current_face_center[1] * alpha)
                )
            
            # Draw face rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw center point
            cv2.circle(frame, self.face_center, 5, (0, 0, 255), -1)
            
            # Draw tracking lines
            frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
            cv2.line(frame, frame_center, self.face_center, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Calculate direction and update UI
            direction = self.calculate_direction(self.face_center, frame_center)
            self.root.after(0, lambda d=direction: self.update_direction_info(d, self.face_center, frame_center))
            
            # Update progress bar (face size indicates distance)
            face_size = w * h
            max_face_size = 640 * 480 * 0.3  # 30% of screen area
            progress = min(100, (face_size / max_face_size) * 100)
            self.root.after(0, lambda p=progress: self.progress_bar.config(value=p))
            
            # Add text overlay
            cv2.putText(frame, f"LOCKED: {direction}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Position: ({self.face_center[0]}, {self.face_center[1]})", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
        else:
            # No faces detected
            if self.face_found:
                self.root.after(0, lambda: self.status_label.config(text="Status: Lost Target - Scanning..."))
                self.face_found = False
                self.last_face_position = None
                self.progress_bar['value'] = 0
                self.root.after(0, lambda: self.direction_label.config(text="Scanning..."))
                self.root.after(0, lambda: self.position_label.config(text="Not Found"))
            
            # Draw scanning indicator
            frame_center = (frame.shape[1] // 2, frame.shape[0] // 2)
            cv2.circle(frame, frame_center, 20, (0, 0, 255), 2)
            cv2.putText(frame, "SCANNING", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return frame
    
    def calculate_direction(self, face_center, frame_center):
        """Calculate the direction of face relative to frame center"""
        fx, fy = face_center
        cx, cy = frame_center
        
        # Calculate relative position
        dx = fx - cx
        dy = fy - cy
        
        # Determine direction
        if abs(dx) < 50 and abs(dy) < 50:
            return "CENTER"
        elif abs(dx) > abs(dy):
            if dx > 0:
                return "RIGHT"
            else:
                return "LEFT"
        else:
            if dy > 0:
                return "DOWN"
            else:
                return "UP"
    
    def update_direction_info(self, direction, face_center, frame_center):
        """Update direction and position information in UI"""
        self.direction_label.config(text=f"Direction: {direction}")
        
        # Calculate distance from center
        distance = ((face_center[0] - frame_center[0])**2 + (face_center[1] - frame_center[1])**2)**0.5
        self.position_label.config(text=f"Position: ({face_center[0]}, {face_center[1]}) - Distance: {int(distance)}px")
    
    def update_video_display(self, frame):
        """Update the video canvas with the processed frame"""
        try:
            # Convert OpenCV BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)
            
            # Convert to Tkinter PhotoImage
            photo = ImageTk.PhotoImage(image=pil_image)
            
            # Update canvas
            self.video_canvas.config(width=frame.shape[1], height=frame.shape[0])
            self.video_canvas.create_image(0, 0, anchor='nw', image=photo)
            self.video_canvas.image = photo  # Keep reference to prevent garbage collection
            
        except Exception as e:
            print(f"Error updating video display: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.cap:
            self.cap.release()
        self.root.quit()

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = FaceTrackerApp(root)
    
    # Handle window close
    root.protocol("WM_DELETE_WINDOW", app.cleanup)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()