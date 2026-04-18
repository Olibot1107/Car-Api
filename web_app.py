from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import logging
import cv2
import time
import threading
from lib.movement import CarControl

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
car = None
proximity_thread = None
proximity_running = False

# Autonomous mapping system
mapper = None


class CameraStream:
    """Background camera reader that always keeps the latest frame.

    This avoids building a backlog of old frames when the browser connection
    is slow or unstable. The stream endpoint can then encode the newest frame
    on demand with a bandwidth-friendly size and quality.
    """

    def __init__(self, index=0):
        self.index = index
        self.camera = None
        self.lock = threading.Lock()
        self.latest_frame = None
        self.latest_frame_id = 0
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return

        self.camera = cv2.VideoCapture(self.index)
        if not self.camera.isOpened():
            raise RuntimeError("Could not open camera")

        # Keep the source capture modest; the stream endpoint can downscale further.
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        # Keep the capture buffer small so slow clients do not see a backlog.
        self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.running = True
        self.thread = threading.Thread(target=self._reader_loop, daemon=True)
        self.thread.start()

    def _reader_loop(self):
        try:
            while self.running:
                success, frame = self.camera.read()
                if not success:
                    time.sleep(0.05)
                    continue

                with self.lock:
                    self.latest_frame = frame
                    self.latest_frame_id += 1
        finally:
            if self.camera is not None:
                self.camera.release()
                self.camera = None

    def get_latest_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return None, self.latest_frame_id
            return self.latest_frame.copy(), self.latest_frame_id

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)


camera_stream = None


def find_working_camera_index(preferred_index=None, max_index=10):
    """Return the first camera index that can actually produce frames."""
    candidates = []
    if preferred_index is not None:
        candidates.append(preferred_index)
    candidates.extend(i for i in range(max_index + 1) if i not in candidates)

    for index in candidates:
        cap = cv2.VideoCapture(index)
        if not cap.isOpened():
            cap.release()
            continue

        try:
            ok, _ = cap.read()
            if ok:
                return index
        finally:
            cap.release()

    return None


def init_camera_stream():
    global camera_stream
    if camera_stream is not None and camera_stream.running:
        return camera_stream

    camera_stream = None

    camera_index = find_working_camera_index()
    if camera_index is None:
        raise RuntimeError("No usable camera was found")

    stream = CameraStream(camera_index)
    try:
        stream.start()
    except Exception:
        stream.stop()
        raise

    camera_stream = stream
    logger.info("Camera stream initialized successfully on camera index %s", camera_index)
    return camera_stream

def init_car():
    global car
    try:
        car = CarControl()
        logger.info("Car control initialized successfully")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize car hardware: {e}")
        logger.warning("Running in simulation mode - hardware controls will be disabled")
        car = None
        return False

def generate_camera_feed(target_width=320, target_height=240, quality=55, fps=12):
    """Generator function for camera feed."""
    stream = init_camera_stream()
    interval = 1.0 / max(1, fps)
    last_frame_id = -1
    start_time = time.time()

    while True:
        frame, frame_id = stream.get_latest_frame()
        if frame is None:
            if time.time() - start_time > 5:
                raise RuntimeError("Camera did not provide frames in time")
            time.sleep(0.05)
            continue

        # Skip duplicate frames when the camera thread has not produced a new one.
        if frame_id == last_frame_id:
            time.sleep(interval)
            continue

        last_frame_id = frame_id

        # Resize before JPEG encoding to keep the stream lighter on slow links.
        if target_width > 0 and target_height > 0:
            frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)

        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), max(20, min(95, quality))]
        ret, buffer = cv2.imencode('.jpg', frame, encode_params)
        if not ret:
            continue

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

        time.sleep(interval)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/control/<action>', methods=['POST'])
def control(action):
    if not car:
        return jsonify({'success': False, 'error': 'Car not initialized'})

    try:
        data = request.get_json() or {}
        speed = data.get('speed', 50)
        angle = data.get('angle', 10)

        success = False

        if action == 'forward':
            success = car.forward() and car.set_speed(speed)
        elif action == 'backward':
            success = car.backward() and car.set_speed(speed)
        elif action == 'stop':
            success = car.stop()
        elif action == 'turn_left':
            success = car.turn_left(angle)
        elif action == 'turn_right':
            success = car.turn_right(angle)
        elif action == 'center_steering':
            success = car.center_steering()
        elif action == 'buzzer_on':
            frequency = data.get('frequency', 2000)
            success = car.buzzer_on(frequency)
        elif action == 'buzzer_off':
            success = car.buzzer_off()
        elif action == 'led_red':
            success = car.led_red_on() if data.get('state', True) else car.led_red_off()
        elif action == 'led_green':
            success = car.led_green_on() if data.get('state', True) else car.led_green_off()
        elif action == 'led_blue':
            success = car.led_blue_on() if data.get('state', True) else car.led_blue_off()

        return jsonify({'success': success})

    except Exception as e:
        logger.error(f"Control error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/emergency_stop', methods=['POST'])
def emergency_stop():
    """Emergency stop - stops car and shuts down the app"""
    if not car:
        return jsonify({'success': False, 'error': 'Car not initialized'})

    try:
        # Stop the car
        success = car.stop()
        logger.warning("Emergency stop activated - car stopped")

        # Shut down the Flask app
        import os
        logger.warning("Shutting down application...")
        os._exit(0)  # Force exit

        return jsonify({'success': success, 'message': 'Emergency stop activated'})

    except Exception as e:
        logger.error(f"Emergency stop error: {e}")
        return jsonify({'success': False, 'error': str(e)})





@app.route('/camera_feed')
def camera_feed():
    width = request.args.get('width', default=320, type=int)
    height = request.args.get('height', default=240, type=int)
    quality = request.args.get('quality', default=55, type=int)
    fps = request.args.get('fps', default=12, type=int)

    try:
        init_camera_stream()
    except Exception as e:
        logger.error(f"Could not start camera feed: {e}")
        return jsonify({'success': False, 'error': 'Could not open camera'}), 503

    return Response(generate_camera_feed(width, height, quality, fps),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    return jsonify({
        'car_initialized': car is not None,
        'steering_angle': car.get_steering() if car else 0,
        'speed': car.get_speed() if car and hasattr(car, 'get_speed') else 0,
        'led_red': car.led_red_state if car and hasattr(car, 'led_red_state') else False,
        'led_green': car.led_green_state if car and hasattr(car, 'led_green_state') else False,
        'led_blue': car.led_blue_state if car and hasattr(car, 'led_blue_state') else False,
        'buzzer_active': car.buzzer_state if car and hasattr(car, 'buzzer_state') else False
    })



if __name__ == '__main__':
    init_car()
    try:
        init_camera_stream()
    except Exception as e:
        logger.warning(f"Camera stream could not be initialized: {e}")
    logger.info("Starting web server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
