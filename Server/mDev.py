#-*- coding: utf-8 -*-
########################################################################
# Filename    : mDev.py
# Description : This is the Class mDev. Used for Control the Shield.
# auther      : www.freenove.com
# modification: 2020/03/26
# Enhanced error handling: 2026/01/04
########################################################################
import smbus
import time
import threading
from threading import Lock
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def numMap(value,fromLow,fromHigh,toLow,toHigh):
    """Map a value from one range to another"""
    try:
        if fromHigh == fromLow:
            return toLow
        return (toHigh-toLow)*(value-fromLow) / (fromHigh-fromLow) + toLow
    except (ZeroDivisionError, TypeError) as e:
        logger.error(f"Error in numMap: {e}")
        return toLow

class mDEV:
    CMD_SERVO1      =   0
    CMD_SERVO2      =   1
    CMD_SERVO3      =   2
    CMD_SERVO4      =   3
    CMD_PWM1        =   4
    CMD_PWM2        =   5
    CMD_DIR1        =   6
    CMD_DIR2        =   7
    CMD_BUZZER      =   8
    CMD_IO1         =   9
    CMD_IO2         =   10
    CMD_IO3         =   11
    CMD_SONIC       =   12
    SERVO_MAX_PULSE_WIDTH = 2500
    SERVO_MIN_PULSE_WIDTH = 500
    SONIC_MAX_HIGH_BYTE = 50

    def __init__(self,addr=0x18):
        """Initialize the Smart Car Shield with error handling"""
        self.address = addr #default address of mDEV
        self.bus = None
        self.mutex = Lock()
        self.Is_IO1_State_True = False
        self.Is_IO2_State_True = False
        self.Is_IO3_State_True = False
        self.Is_Buzzer_State_True = False
        self.handle = True

        try:
            self.bus = smbus.SMBus(1)
            logger.info(f"Smart Car Shield initialized at I2C address 0x{self.address:02x}")
        except Exception as e:
            logger.error(f"Failed to initialize I2C bus: {e}")
            logger.error("Make sure the Smart Car Shield is properly connected and powered on")
            raise RuntimeError("I2C bus initialization failed") from e
    def i2cRead(self,reg):
        self.bus.read_byte_data(self.address,reg)
        
    def i2cWrite1(self,cmd,value):
        self.bus.write_byte_data(self.address,cmd,value)
        
    def i2cWrite2(self,value):
        self.bus.write_byte(self.address,value)
    
    def writeReg(self,cmd,value):
        """Write a register value to the shield with error handling"""
        if self.bus is None:
            logger.error("I2C bus not initialized")
            return False

        try:
            value = int(value)
            if not (0 <= value <= 65535):
                logger.warning(f"Value {value} out of range (0-65535), clamping")
                value = max(0, min(65535, value))

            with self.mutex:
                # Write the value multiple times for reliability (as per original design)
                for _ in range(3):
                    self.bus.write_i2c_block_data(self.address, cmd, [value>>8, value&0xff])
                    time.sleep(0.001)
            return True
        except ValueError as e:
            logger.error(f"Invalid value for register {cmd}: {value} - {e}")
            return False
        except Exception as e:
            logger.error(f"I2C write error for register {cmd}: {e}")
            return False
        
    def readReg(self,cmd):
        """Read a register value from the shield with error handling"""
        if self.bus is None:
            logger.error("I2C bus not initialized")
            return 0

        try:
            with self.mutex:
                ##################################################################################################
                #Due to the update of SMBus, the communication between Pi and the shield board is not normal.
                #through the following code to improve the success rate of communication.
                #But if there are conditions, the best solution is to update the firmware of the shield board.
                ##################################################################################################
                for i in range(0,10,1):
                    try:
                        self.bus.write_i2c_block_data(self.address,cmd,[0])
                        a = self.bus.read_i2c_block_data(self.address,cmd,1)

                        self.bus.write_byte(self.address,cmd+1)
                        b = self.bus.read_i2c_block_data(self.address,cmd+1,1)

                        self.bus.write_byte(self.address,cmd)
                        c = self.bus.read_byte_data(self.address,cmd)

                        self.bus.write_byte(self.address,cmd+1)
                        d = self.bus.read_byte_data(self.address,cmd+1)

                        if(a[0] == c and c < self.SONIC_MAX_HIGH_BYTE ):
                            return c<<8 | d
                        else:
                            continue
                    except Exception as e:
                        logger.debug(f"I2C read attempt {i+1} failed: {e}")
                        continue

                logger.warning(f"Failed to read register {cmd} after 10 attempts")
                return 0
        except Exception as e:
            logger.error(f"I2C read error for register {cmd}: {e}")
            return 0
    def move(self,left_pwm,right_pwm,steering_angle=90):
        """Move the car with specified PWM values and steering angle"""
        try:
            self.setServo('1',steering_angle)
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
            logger.error(f"Error in move function: {e}")

    def setServo(self,index,angle):
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

    def setLed(self,R,G,B):
        """Set RGB LED state with error handling"""
        try:
            # Validate inputs
            R = bool(R)
            G = bool(G)
            B = bool(B)

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
            logger.error(f"Error setting LED: {e}")
            return False

    def setBuzzer(self,PWM):
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

    def getSonicEchoTime(self):
        """Get ultrasonic echo time"""
        try:
            return self.readReg(self.CMD_SONIC)
        except Exception as e:
            logger.error(f"Error getting sonic echo time: {e}")
            return 0

    def getSonic(self):
        """Get ultrasonic distance in cm"""
        try:
            SonicEchoTime = self.readReg(self.CMD_SONIC)
            distance = SonicEchoTime * 17.0 / 1000.0
            return distance
        except Exception as e:
            logger.error(f"Error getting sonic distance: {e}")
            return 0.0

    def setShieldI2cAddress(self,addr): #addr: 7bit I2C Device Address
        """Set new I2C address for the shield"""
        try:
            if (addr < 0x03) or (addr > 0x77):
                logger.error(f"Invalid I2C address: 0x{addr:02x} (must be 0x03-0x77)")
                return False
            else:
                value = (0xbb << 8) | (addr << 1)
                return self.writeReg(0xaa, value)
        except Exception as e:
            logger.error(f"Error setting I2C address: {e}")
            return False
            
mdev = mDEV()   
def loop(): 
    mdev.readReg(mdev.CMD_SONIC)
    while True:
        SonicEchoTime = mdev.readReg(mdev.CMD_SONIC)
        distance = SonicEchoTime * 17.0 / 1000.0
        print("EchoTime: %d, Sonic: %.2f cm"%(SonicEchoTime,distance))
        time.sleep(0.001)
    
if __name__ == '__main__':
    import sys
    print("mDev.py is starting ... ")
    #setup()
    try:
        if len(sys.argv)<2:
            print("Parameter error: Please assign the device")
            exit() 
        print(sys.argv[0],sys.argv[1])
        if sys.argv[1] == "servo":      
            cnt = 3 
            while (cnt != 0):       
                cnt = cnt - 1
                for i in range(50,140,1):   
                    mdev.writeReg(mdev.CMD_SERVO1,numMap(i,0,180,500,2500))
                    time.sleep(0.005)
                for i in range(140,50,-1):  
                    mdev.writeReg(mdev.CMD_SERVO1,numMap(i,0,180,500,2500))
                    time.sleep(0.005)
            mdev.writeReg(mdev.CMD_SERVO1,numMap(90,0,180,500,2500))
        if sys.argv[1] == "buzzer":
            mdev.writeReg(mdev.CMD_BUZZER,2000)
            time.sleep(3)
            mdev.writeReg(mdev.CMD_BUZZER,0)
        if sys.argv[1] == "RGBLED":
            for i in range(0,3):
                mdev.writeReg(mdev.CMD_IO1,0)
                mdev.writeReg(mdev.CMD_IO2,1)
                mdev.writeReg(mdev.CMD_IO3,1)
                time.sleep(1)
                mdev.writeReg(mdev.CMD_IO1,1)
                mdev.writeReg(mdev.CMD_IO2,0)
                mdev.writeReg(mdev.CMD_IO3,1)
                time.sleep(1)
                mdev.writeReg(mdev.CMD_IO1,1)
                mdev.writeReg(mdev.CMD_IO2,1)
                mdev.writeReg(mdev.CMD_IO3,0)
                time.sleep(1)
            mdev.writeReg(mdev.CMD_IO1,1)
            mdev.writeReg(mdev.CMD_IO2,1)
            mdev.writeReg(mdev.CMD_IO3,1)
        if sys.argv[1] == "ultrasonic" or sys.argv[1] == "s":
            while True:
                print("Sonic: ",mdev.getSonic())
                time.sleep(0.1)
        if sys.argv[1] == "motor":
                mdev.writeReg(mdev.CMD_DIR1,0)
                mdev.writeReg(mdev.CMD_DIR2,0)
                for i in range(0,1000,10):  
                    mdev.writeReg(mdev.CMD_PWM1,i)
                    mdev.writeReg(mdev.CMD_PWM2,i)
                    time.sleep(0.005)
                time.sleep(1)
                for i in range(1000,0,-10): 
                    mdev.writeReg(mdev.CMD_PWM1,i)
                    mdev.writeReg(mdev.CMD_PWM2,i)
                    time.sleep(0.005)
                mdev.writeReg(mdev.CMD_DIR1,1)
                mdev.writeReg(mdev.CMD_DIR2,1)
                for i in range(0,1000,10):  
                    mdev.writeReg(mdev.CMD_PWM1,i)
                    mdev.writeReg(mdev.CMD_PWM2,i)
                    time.sleep(0.005)
                time.sleep(1)
                for i in range(1000,0,-10): 
                    mdev.writeReg(mdev.CMD_PWM1,i)
                    mdev.writeReg(mdev.CMD_PWM2,i)
                    time.sleep(0.005)
    except KeyboardInterrupt:
        pass
