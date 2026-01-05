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
scanner_thread = None
scanner_running = False
scan_data = {}  # Store scan points: {angle: distance}
current_scan_angle = 0
scan_step = 15  # degrees between scan points (more points!)
scan_range = (-90, 90)  # scan from -90 to +90 degrees
last_movement_time = 0  # Track when car last moved
movement_detected = False

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

            time.sleep(0.1)  # Control frame rate
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
            movement_detected = True
        elif action == 'backward':
            success = car.backward() and car.set_speed(speed)
            movement_detected = True
        elif action == 'stop':
            success = car.stop()
        elif action == 'turn_left':
            success = car.turn_left(angle)
            movement_detected = True
        elif action == 'turn_right':
            success = car.turn_right(angle)
            movement_detected = True
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
        'camera_pan': car.get_camera_pan() if car else 0
    })

def start_scanner():
    """Start the ultrasonic scanner thread"""
    global scanner_thread, scanner_running
    if scanner_running:
        logger.warning("Scanner already running")
        return

    scanner_running = True
    scanner_thread = threading.Thread(target=scanner_loop, daemon=True)
    scanner_thread.start()
    logger.info("Ultrasonic scanner started")

def stop_scanner():
    """Stop the scanner thread"""
    global scanner_running
    scanner_running = False
    if scanner_thread:
        scanner_thread.join(timeout=1.0)
    logger.info("Ultrasonic scanner stopped")

def scanner_loop():
    """Main scanning loop - movement-aware high-speed scanning"""
    logger.info("Movement-aware scanner started")
    data_history = {}  # Store multiple readings for averaging
    last_steering_angle = 0
    movement_scan_count = 0

    while scanner_running:
        try:
            if car:  # Only scan if car is available
                current_steering = car.get_steering()
                steering_changed = abs(current_steering - last_steering_angle) > 5  # 5° threshold

                # Detect movement/turning
                is_moving = steering_changed or movement_detected
                last_steering_angle = current_steering

                if is_moving:
                    # Movement detected - ULTRA-HIGH RESOLUTION scanning for 900+ points
                    logger.debug("Movement detected - ULTRA-HIGH RESOLUTION scanning mode")
                    movement_scan_count += 1

                    # Ultra-fine scanning for massive data collection
                    ultra_step = 0.25  # 0.25° steps = 4 points per degree
                    ultra_range = (-135, 135)  # Even wider range: 270° total

                    for angle in range(int(ultra_range[0] * 4), int(ultra_range[1] * 4) + 1):
                        real_angle = angle / 4.0  # Convert back to degrees
                        if not scanner_running:
                            break

                        # Move camera/sensor to this precise angle
                        car.set_camera_pan(90 + real_angle)
                        time.sleep(0.01)  # Ultra-fast servo movement (10ms)

                        # Take single high-speed reading for maximum data rate
                        dist = car.get_distance()
                        if dist > 0:
                            # Direct data storage for maximum speed (no averaging during ultra-scan)
                            scan_data[real_angle] = dist

                            # Only debug log every 10th point to avoid spam
                            if int(real_angle * 4) % 40 == 0:  # Every 10°
                                logger.debug(f"Ultra-scan {real_angle:.1f}°: {dist:.1f}cm")

                    logger.info(f"Ultra-scan complete: {len(scan_data)} data points collected")

                    time.sleep(0.1)  # Very fast cycle during movement (100ms)

                else:
                    # Normal scanning when stationary
                    # Scan with normal parameters
                    for angle in range(scan_range[0], scan_range[1] + 1, scan_step):
                        if not scanner_running:
                            break

                        # Move camera/sensor to this angle
                        car.set_camera_pan(90 + angle)
                        time.sleep(0.08)  # Normal servo movement (80ms)

                        # Take multiple readings for better data quality
                        readings = []
                        for _ in range(2):  # Take 2 readings per angle
                            dist = car.get_distance()
                            if dist > 0:
                                readings.append(dist)
                            time.sleep(0.02)

                        # Calculate average for cleaner data
                        if readings:
                            avg_distance = sum(readings) / len(readings)
                            # Simple moving average with history
                            if angle not in data_history:
                                data_history[angle] = []
                            data_history[angle].append(avg_distance)
                            # Keep only last 3 readings for smoothing
                            if len(data_history[angle]) > 3:
                                data_history[angle].pop(0)

                            # Final smoothed value
                            scan_data[angle] = sum(data_history[angle]) / len(data_history[angle])

                            logger.debug(f"Stationary scan {angle}°: {scan_data[angle]:.1f}cm (avg of {len(readings)} readings)")

                    # Return camera to center after scan
                    car.camera_center()
                    logger.debug(f"Stationary scan cycle complete. {len(scan_data)} active points")

                    time.sleep(0.5)  # Slower cycle when stationary (500ms)

                # Reset movement detection
                global movement_detected
                movement_detected = False

        except Exception as e:
            logger.error(f"Scanner error: {e}")
            time.sleep(0.2)

@app.route('/scan_data')
def get_scan_data():
    """Get current scan data for mapping"""
    return jsonify({
        'scan_points': scan_data,
        'scan_step': scan_step,
        'scan_range': scan_range,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    if init_car():
        start_scanner()  # Start ultrasonic scanner if car initialized
    logger.info("Starting web server on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
