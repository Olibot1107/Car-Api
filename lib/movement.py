from Server.mDev import mDEV, numMap

class CarControl:
    def __init__(self, i2c_addr=0x18):
        self.mdev = mDEV(i2c_addr)
        self.steering_angle = 90
        self.camera_pan = 90
        self.camera_tilt = 90

    # Movement methods
    def forward(self):
        self.mdev.writeReg(self.mdev.CMD_DIR1, 1)
        self.mdev.writeReg(self.mdev.CMD_DIR2, 1)

    def backward(self):
        self.mdev.writeReg(self.mdev.CMD_DIR1, 0)
        self.mdev.writeReg(self.mdev.CMD_DIR2, 0)

    def stop(self):
        self.mdev.writeReg(self.mdev.CMD_PWM1, 0)
        self.mdev.writeReg(self.mdev.CMD_PWM2, 0)

    def set_speed(self, speed):
        pwm = max(0, min(1000, speed * 10))
        self.mdev.writeReg(self.mdev.CMD_PWM1, pwm)
        self.mdev.writeReg(self.mdev.CMD_PWM2, pwm)

    # Steering methods
    def turn_left(self, degrees=30):
        self.steering_angle = max(0, self.steering_angle - degrees)
        self.set_steering(self.steering_angle)

    def turn_right(self, degrees=30):
        self.steering_angle = min(180, self.steering_angle + degrees)
        self.set_steering(self.steering_angle)

    def center_steering(self):
        self.steering_angle = 90
        self.set_steering(90)

    def set_steering(self, angle):
        self.steering_angle = max(0, min(180, angle))
        self.mdev.setServo('1', self.steering_angle)

    def get_steering(self):
        return self.steering_angle

    # Camera servo methods
    def camera_left(self, degrees=10):
        self.camera_pan = max(0, self.camera_pan - degrees)
        self.set_camera_pan(self.camera_pan)

    def camera_right(self, degrees=10):
        self.camera_pan = min(180, self.camera_pan + degrees)
        self.set_camera_pan(self.camera_pan)

    def camera_up(self, degrees=10):
        self.camera_tilt = max(0, self.camera_tilt - degrees)
        self.set_camera_tilt(self.camera_tilt)

    def camera_down(self, degrees=10):
        self.camera_tilt = min(180, self.camera_tilt + degrees)
        self.set_camera_tilt(self.camera_tilt)

    def camera_center(self):
        self.camera_pan = 90
        self.camera_tilt = 90
        self.set_camera_pan(90)
        self.set_camera_tilt(90)

    def set_camera_pan(self, angle):
        self.camera_pan = max(0, min(180, angle))
        self.mdev.setServo('2', self.camera_pan)

    def set_camera_tilt(self, angle):
        self.camera_tilt = max(0, min(180, angle))
        self.mdev.setServo('3', self.camera_tilt)

    def get_camera_pan(self):
        return self.camera_pan

    def get_camera_tilt(self):
        return self.camera_tilt

    # Buzzer methods
    def buzzer_on(self, frequency=2000):
        self.mdev.writeReg(self.mdev.CMD_BUZZER, frequency)

    def buzzer_off(self):
        self.mdev.writeReg(self.mdev.CMD_BUZZER, 0)

    # LED methods
    def led_red_on(self):
        self.mdev.writeReg(self.mdev.CMD_IO1, 0)

    def led_red_off(self):
        self.mdev.writeReg(self.mdev.CMD_IO1, 1)

    def led_green_on(self):
        self.mdev.writeReg(self.mdev.CMD_IO2, 0)

    def led_green_off(self):
        self.mdev.writeReg(self.mdev.CMD_IO2, 1)

    def led_blue_on(self):
        self.mdev.writeReg(self.mdev.CMD_IO3, 0)

    def led_blue_off(self):
        self.mdev.writeReg(self.mdev.CMD_IO3, 1)

    def led_all_off(self):
        self.led_red_off()
        self.led_green_off()
        self.led_blue_off()

    def led_rgb(self, r, g, b):
        if r: self.led_red_on()
        else: self.led_red_off()
        if g: self.led_green_on()
        else: self.led_green_off()
        if b: self.led_blue_on()
        else: self.led_blue_off()

    # Ultrasonic sensor
    def get_distance(self):
        return self.mdev.getSonic()

    # Advanced movement
    def move(self, left_speed, right_speed):
        """Move with different speeds for left/right motors (for turning)"""
        # Left motor
        if left_speed >= 0:
            self.mdev.writeReg(self.mdev.CMD_DIR2, 1)
            self.mdev.writeReg(self.mdev.CMD_PWM2, abs(left_speed))
        else:
            self.mdev.writeReg(self.mdev.CMD_DIR2, 0)
            self.mdev.writeReg(self.mdev.CMD_PWM2, abs(left_speed))

        # Right motor
        if right_speed >= 0:
            self.mdev.writeReg(self.mdev.CMD_DIR1, 1)
            self.mdev.writeReg(self.mdev.CMD_PWM1, abs(right_speed))
        else:
            self.mdev.writeReg(self.mdev.CMD_DIR1, 0)
            self.mdev.writeReg(self.mdev.CMD_PWM1, abs(right_speed))
