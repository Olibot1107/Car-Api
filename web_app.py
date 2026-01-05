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

def generate_camera_feed():
    """Generator function for camera feed"""
    camera = cv2.VideoCapture(0)  # Use default camera
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not camera.isOpened():
        logger.error("Could not open camera")
        return

    try:
        while True:
            success, frame = camera.read()
            if not success:
                break

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            time.sleep(0.02)  # Control frame rate - faster (50 FPS)
    finally:
        camera.release()



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
        elif action == 'camera_left':
            success = car.camera_left(angle)
        elif action == 'camera_right':
            success = car.camera_right(angle)
        elif action == 'camera_up':
            success = car.camera_up(angle)
        elif action == 'camera_down':
            success = car.camera_down(angle)
        elif action == 'camera_center':
            success = car.camera_center()
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





@app.route('/camera_feed')
def camera_feed():
    return Response(generate_camera_feed(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/sensor/distance')
def get_distance():
    if not car:
        return jsonify({'distance': 0, 'success': False})

    try:
        distance = car.get_distance()
        return jsonify({'distance': distance, 'success': True})
    except Exception as e:
        logger.error(f"Distance sensor error: {e}")
        return jsonify({'distance': 0, 'success': False, 'error': str(e)})

@app.route('/status')
def status():
    return jsonify({
        'car_initialized': car is not None,
        'steering_angle': car.get_steering() if car else 0,
        'camera_pan': car.get_camera_pan() if car else 0,
        'camera_tilt': car.get_camera_tilt() if car else 0,
        'speed': car.get_speed() if car and hasattr(car, 'get_speed') else 0,
        'distance': car.get_distance() if car else 0,
        'led_red': car.led_red_state if car and hasattr(car, 'led_red_state') else False,
        'led_green': car.led_green_state if car and hasattr(car, 'led_green_state') else False,
        'led_blue': car.led_blue_state if car and hasattr(car, 'led_blue_state') else False,
        'buzzer_active': car.buzzer_state if car and hasattr(car, 'buzzer_state') else False
    })



if __name__ == '__main__':
    init_car()
    logger.info("Starting web server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
