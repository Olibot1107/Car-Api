import logging
from Server.mDev import mDEV, numMap

# Set up logging
logger = logging.getLogger(__name__)

class CarControl:
    def __init__(self, i2c_addr=0x18):
        """Initialize car control with error handling"""
        try:
            self.mdev = mDEV(i2c_addr)
            self.steering_angle = 90
            self.camera_pan = 90
            logger.info("Car control initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize car control: {e}")
            raise

    # Movement methods
    def forward(self):
        """Move car forward"""
        try:
            if not self.mdev.writeReg(self.mdev.CMD_DIR1, 1):
                logger.error("Failed to set forward direction for right motor")
                return False
            if not self.mdev.writeReg(self.mdev.CMD_DIR2, 1):
                logger.error("Failed to set forward direction for left motor")
                return False
            return True
        except Exception as e:
            logger.error(f"Error moving forward: {e}")
            return False

    def backward(self):
        """Move car backward"""
        try:
            if not self.mdev.writeReg(self.mdev.CMD_DIR1, 0):
                logger.error("Failed to set backward direction for right motor")
                return False
            if not self.mdev.writeReg(self.mdev.CMD_DIR2, 0):
                logger.error("Failed to set backward direction for left motor")
                return False
            return True
        except Exception as e:
            logger.error(f"Error moving backward: {e}")
            return False

    def stop(self):
        """Stop the car"""
        try:
            if not self.mdev.writeReg(self.mdev.CMD_PWM1, 0):
                logger.error("Failed to stop right motor")
                return False
            if not self.mdev.writeReg(self.mdev.CMD_PWM2, 0):
                logger.error("Failed to stop left motor")
                return False
            return True
        except Exception as e:
            logger.error(f"Error stopping car: {e}")
            return False

    def set_speed(self, speed):
        """Set car speed (0-100)"""
        try:
            if not isinstance(speed, (int, float)):
                logger.error(f"Invalid speed type: {type(speed)}")
                return False

            speed = max(0, min(100, speed))  # Clamp speed to 0-100
            pwm = int(speed * 10)  # Convert to PWM value

            if not self.mdev.writeReg(self.mdev.CMD_PWM1, pwm):
                logger.error("Failed to set speed for right motor")
                return False
            if not self.mdev.writeReg(self.mdev.CMD_PWM2, pwm):
                logger.error("Failed to set speed for left motor")
                return False
            return True
        except Exception as e:
            logger.error(f"Error setting speed: {e}")
            return False

    # Steering methods
    def turn_left(self, degrees=30):
        """Turn steering left by specified degrees"""
        try:
            if not isinstance(degrees, (int, float)):
                logger.error(f"Invalid degrees type: {type(degrees)}")
                return False
            self.steering_angle = max(0, self.steering_angle - degrees)
            return self.set_steering(self.steering_angle)
        except Exception as e:
            logger.error(f"Error turning left: {e}")
            return False

    def turn_right(self, degrees=30):
        """Turn steering right by specified degrees"""
        try:
            if not isinstance(degrees, (int, float)):
                logger.error(f"Invalid degrees type: {type(degrees)}")
                return False
            self.steering_angle = min(180, self.steering_angle + degrees)
            return self.set_steering(self.steering_angle)
        except Exception as e:
            logger.error(f"Error turning right: {e}")
            return False

    def center_steering(self):
        """Center the steering"""
        try:
            self.steering_angle = 90
            return self.set_steering(90)
        except Exception as e:
            logger.error(f"Error centering steering: {e}")
            return False

    def set_steering(self, angle):
        """Set steering to specific angle (0-180)"""
        try:
            if not isinstance(angle, (int, float)):
                logger.error(f"Invalid angle type: {type(angle)}")
                return False

            self.steering_angle = max(0, min(180, angle))
            return self.mdev.setServo('1', self.steering_angle)
        except Exception as e:
            logger.error(f"Error setting steering angle: {e}")
            return False

    def get_steering(self):
        """Get current steering angle"""
        return self.steering_angle

    # Camera servo methods (for pan/tilt control)
    def camera_left(self, degrees=10):
        """Pan camera left by specified degrees"""
        try:
            if not isinstance(degrees, (int, float)):
                logger.error(f"Invalid degrees type: {type(degrees)}")
                return False
            self.camera_pan = max(0, self.camera_pan - degrees)
            return self.set_camera_pan(self.camera_pan)
        except Exception as e:
            logger.error(f"Error panning camera left: {e}")
            return False

    def camera_right(self, degrees=10):
        """Pan camera right by specified degrees"""
        try:
            if not isinstance(degrees, (int, float)):
                logger.error(f"Invalid degrees type: {type(degrees)}")
                return False
            self.camera_pan = min(180, self.camera_pan + degrees)
            return self.set_camera_pan(self.camera_pan)
        except Exception as e:
            logger.error(f"Error panning camera right: {e}")
            return False

    def camera_center(self):
        """Center the camera (pan only)"""
        try:
            self.camera_pan = 90
            return self.set_camera_pan(90)
        except Exception as e:
            logger.error(f"Error centering camera: {e}")
            return False

    def set_camera_pan(self, angle):
        """Set camera pan to specific angle (0-180)"""
        try:
            if not isinstance(angle, (int, float)):
                logger.error(f"Invalid angle type: {type(angle)}")
                return False

            self.camera_pan = max(0, min(180, angle))
            return self.mdev.setServo('2', self.camera_pan)
        except Exception as e:
            logger.error(f"Error setting camera pan: {e}")
            return False

    def get_camera_pan(self):
        """Get current camera pan angle"""
        return self.camera_pan

    # Buzzer methods
    def buzzer_on(self, frequency=2000):
        """Turn buzzer on with specified frequency"""
        try:
            if not isinstance(frequency, (int, float)):
                logger.error(f"Invalid frequency type: {type(frequency)}")
                return False

            frequency = max(0, min(65535, int(frequency)))  # Clamp frequency to valid range
            return self.mdev.setBuzzer(frequency)
        except Exception as e:
            logger.error(f"Error turning buzzer on: {e}")
            return False

    def buzzer_off(self):
        """Turn buzzer off"""
        try:
            return self.mdev.setBuzzer(0)
        except Exception as e:
            logger.error(f"Error turning buzzer off: {e}")
            return False

    # LED methods
    def led_red_on(self):
        """Turn red LED on"""
        try:
            return self.mdev.writeReg(self.mdev.CMD_IO1, 0)
        except Exception as e:
            logger.error(f"Error turning red LED on: {e}")
            return False

    def led_red_off(self):
        """Turn red LED off"""
        try:
            return self.mdev.writeReg(self.mdev.CMD_IO1, 1)
        except Exception as e:
            logger.error(f"Error turning red LED off: {e}")
            return False

    def led_green_on(self):
        """Turn green LED on"""
        try:
            return self.mdev.writeReg(self.mdev.CMD_IO2, 0)
        except Exception as e:
            logger.error(f"Error turning green LED on: {e}")
            return False

    def led_green_off(self):
        """Turn green LED off"""
        try:
            return self.mdev.writeReg(self.mdev.CMD_IO2, 1)
        except Exception as e:
            logger.error(f"Error turning green LED off: {e}")
            return False

    def led_blue_on(self):
        """Turn blue LED on"""
        try:
            return self.mdev.writeReg(self.mdev.CMD_IO3, 0)
        except Exception as e:
            logger.error(f"Error turning blue LED on: {e}")
            return False

    def led_blue_off(self):
        """Turn blue LED off"""
        try:
            return self.mdev.writeReg(self.mdev.CMD_IO3, 1)
        except Exception as e:
            logger.error(f"Error turning blue LED off: {e}")
            return False

    def led_all_off(self):
        """Turn all LEDs off"""
        try:
            success = self.led_red_off()
            success &= self.led_green_off()
            success &= self.led_blue_off()
            return success
        except Exception as e:
            logger.error(f"Error turning all LEDs off: {e}")
            return False

    def led_rgb(self, r, g, b):
        """Set RGB LED colors (True/False for each color)"""
        try:
            success = True
            if r:
                success &= self.led_red_on()
            else:
                success &= self.led_red_off()
            if g:
                success &= self.led_green_on()
            else:
                success &= self.led_green_off()
            if b:
                success &= self.led_blue_on()
            else:
                success &= self.led_blue_off()
            return success
        except Exception as e:
            logger.error(f"Error setting RGB LED: {e}")
            return False

    # Ultrasonic sensor
    def get_distance(self):
        """Get distance from ultrasonic sensor in cm"""
        try:
            distance = self.mdev.getSonic()
            if distance < 0:
                logger.warning(f"Invalid distance reading: {distance}")
                return 0.0
            return distance
        except Exception as e:
            logger.error(f"Error getting distance: {e}")
            return 0.0

    # Advanced movement
    def move(self, left_speed, right_speed):
        """Move with different speeds for left/right motors (for turning)"""
        try:
            if not isinstance(left_speed, (int, float)) or not isinstance(right_speed, (int, float)):
                logger.error(f"Invalid speed types: left={type(left_speed)}, right={type(right_speed)}")
                return False

            # Clamp speeds to valid PWM range
            left_speed = max(-1000, min(1000, left_speed))
            right_speed = max(-1000, min(1000, right_speed))

            success = True

            # Left motor
            if left_speed >= 0:
                success &= self.mdev.writeReg(self.mdev.CMD_DIR2, 1)
                success &= self.mdev.writeReg(self.mdev.CMD_PWM2, abs(left_speed))
            else:
                success &= self.mdev.writeReg(self.mdev.CMD_DIR2, 0)
                success &= self.mdev.writeReg(self.mdev.CMD_PWM2, abs(left_speed))

            # Right motor
            if right_speed >= 0:
                success &= self.mdev.writeReg(self.mdev.CMD_DIR1, 1)
                success &= self.mdev.writeReg(self.mdev.CMD_PWM1, abs(right_speed))
            else:
                success &= self.mdev.writeReg(self.mdev.CMD_DIR1, 0)
                success &= self.mdev.writeReg(self.mdev.CMD_PWM1, abs(right_speed))

            return success
        except Exception as e:
            logger.error(f"Error in advanced movement: {e}")
            return False
