# -*- coding: utf-8 -*-
########################################################################
# Filename    : mock_mdev.py
# Description : Mock version of mDev for testing on systems without I2C hardware
# auther      : AI Assistant
# modification: 2026/01/05
########################################################################
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def numMap(value, fromLow, fromHigh, toLow, toHigh):
    """Map a value from one range to another"""
    try:
        if fromHigh == fromLow:
            return toLow
        return (toHigh - toLow) * (value - fromLow) / (fromHigh - fromLow) + toLow
    except (ZeroDivisionError, TypeError) as e:
        logger.error(f"Error in numMap: {e}")
        return toLow

class mDEV:
    CMD_SERVO1 = 0
    CMD_SERVO2 = 1
    CMD_SERVO3 = 2
    CMD_SERVO4 = 3
    CMD_PWM1 = 4
    CMD_PWM2 = 5
    CMD_DIR1 = 6
    CMD_DIR2 = 7
    CMD_BUZZER = 8
    CMD_IO1 = 9
    CMD_IO2 = 10
    CMD_IO3 = 11
    CMD_SONIC = 12
    SERVO_MAX_PULSE_WIDTH = 2500
    SERVO_MIN_PULSE_WIDTH = 500
    SONIC_MAX_HIGH_BYTE = 50

    def __init__(self, addr=0x18):
        """Initialize the mock Smart Car Shield"""
        self.address = addr
        self.bus = None
        self.mutex = None  # No threading in mock
        self.Is_IO1_State_True = False
        self.Is_IO2_State_True = False
        self.Is_IO3_State_True = False
        self.Is_Buzzer_State_True = False
        self.handle = True

        # Mock register storage
        self.registers = {
            self.CMD_SERVO1: 1500,  # Center position
            self.CMD_SERVO2: 1500,
            self.CMD_SERVO3: 1500,
            self.CMD_SERVO4: 1500,
            self.CMD_PWM1: 0,
            self.CMD_PWM2: 0,
            self.CMD_DIR1: 0,
            self.CMD_DIR2: 0,
            self.CMD_BUZZER: 0,
            self.CMD_IO1: 1,  # LEDs off by default (1 = off)
            self.CMD_IO2: 1,
            self.CMD_IO3: 1,
            self.CMD_SONIC: 100  # Mock distance reading (100 = ~17cm)
        }

        logger.info(f"Mock Smart Car Shield initialized (no hardware)")

    def writeReg(self, cmd, value):
        """Mock register write - just store the value"""
        try:
            value = int(value)
            if not (0 <= value <= 65535):
                logger.warning(f"Value {value} out of range (0-65535), clamping")
                value = max(0, min(65535, value))

            self.registers[cmd] = value
            logger.debug(f"Mock write: register {cmd} = {value}")
            return True
        except Exception as e:
            logger.error(f"Mock write error for register {cmd}: {e}")
            return False

    def readReg(self, cmd):
        """Mock register read - return stored value"""
        try:
            value = self.registers.get(cmd, 0)
            logger.debug(f"Mock read: register {cmd} = {value}")
            return value
        except Exception as e:
            logger.error(f"Mock read error for register {cmd}: {e}")
            return 0

    def setServo(self, index, angle):
        """Set servo position with error handling"""
        try:
            if not isinstance(angle, (int, float)):
                logger.error(f"Invalid angle type: {type(angle)}")
                return False

            angle = max(0, min(180, angle))  # Clamp angle to valid range
            pulse_width = numMap(angle, 0, 180, 500, 2500)

            if index == "1":
                return self.writeReg(self.CMD_SERVO1, pulse_width)
            elif index == "2":
                return self.writeReg(self.CMD_SERVO2, pulse_width)
            elif index == "3":
                return self.writeReg(self.CMD_SERVO3, pulse_width)
            elif index == "4":
                return self.writeReg(self.CMD_SERVO4, pulse_width)
            else:
                logger.error(f"Invalid servo index: {index}")
                return False
        except Exception as e:
            logger.error(f"Error setting servo {index}: {e}")
            return False

    def setBuzzer(self, PWM):
        """Set buzzer PWM with error handling"""
        try:
            if not isinstance(PWM, (int, float)):
                logger.error(f"Invalid PWM type: {type(PWM)}")
                return False

            PWM = max(0, min(65535, int(PWM)))  # Clamp PWM to valid range
            return self.writeReg(self.CMD_BUZZER, PWM)
        except Exception as e:
            logger.error(f"Error setting buzzer: {e}")
            return False

    def getSonic(self):
        """Get mock ultrasonic distance in cm"""
        try:
            # Return a mock distance that varies slightly to simulate real sensor
            import random
            base_distance = 50.0  # Base distance in cm
            variation = random.uniform(-5, 5)  # Random variation
            distance = max(0, base_distance + variation)
            return distance
        except Exception as e:
            logger.error(f"Error getting mock sonic distance: {e}")
            return 0.0

    # Additional methods for compatibility
    def move(self, left_pwm, right_pwm, steering_angle=100):
        """Move the car with specified PWM values and steering angle"""
        try:
            self.setServo('1', steering_angle)
            if left_pwm > 0:
                self.writeReg(self.CMD_DIR2, 1)
                self.writeReg(self.CMD_PWM2, left_pwm)
            else:
                self.writeReg(self.CMD_DIR2, 0)
                self.writeReg(self.CMD_PWM2, abs(left_pwm))
            if right_pwm > 0:
                self.writeReg(self.CMD_DIR1, 1)
                self.writeReg(self.CMD_PWM1, right_pwm)
            else:
                self.writeReg(self.CMD_DIR1, 0)
                self.writeReg(self.CMD_PWM1, abs(right_pwm))
        except Exception as e:
            logger.error(f"Error in mock move function: {e}")

    def setLed(self, R, G, B):
        """Set RGB LED state with error handling"""
        try:
            success = True
            if R:
                success &= self.writeReg(self.CMD_IO1, 0)
            else:
                success &= self.writeReg(self.CMD_IO1, 1)

            if G:
                success &= self.writeReg(self.CMD_IO2, 0)
            else:
                success &= self.writeReg(self.CMD_IO2, 1)

            if B:
                success &= self.writeReg(self.CMD_IO3, 0)
            else:
                success &= self.writeReg(self.CMD_IO3, 1)

            return success
        except Exception as e:
            logger.error(f"Error setting mock LED: {e}")
            return False
