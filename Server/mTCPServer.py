import logging
from socket import *
import threading
from Command import COMMAND as cmd
from mDev import *

# Set up logging
logger = logging.getLogger(__name__)

# Initialize mDEV with error handling
try:
    mdev = mDEV()
except Exception as e:
    logger.error(f"Failed to initialize Smart Car Shield: {e}")
    logger.error("Please check shield connection and power switches")
    raise

class mTCPServer(threading.Thread):
    HOST = ''
    PORT = 12345
    BUFSIZ = 1024
    ADDR = (HOST, PORT)

    def __init__(self):
        super(mTCPServer, self).__init__()
        self.setName("TCP Server")

    def run(self):
        self.startTCPServer()
        self.tcpLink()

    def startTCPServer(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind(self.ADDR)
        self.sock.listen(1)
        print("TCP Server started on port", self.PORT)

    def tcpLink(self):
        while True:
            print("Waiting for connection...")
            try:
                self.tcpClientSock, self.addr = self.sock.accept()
                print("Connected from", self.addr)
            except Exception as e:
                print("Socket error:", e)
                break

            while True:
                try:
                    data = self.tcpClientSock.recv(self.BUFSIZ).decode('utf-8')
                except Exception as e:
                    print("Receive error:", e)
                    self.tcpClientSock.close()
                    break

                if not data:
                    break

                commands = data.split(">")
                for cmd_str in commands:
                    if not cmd_str:
                        continue

                    # Movement commands
                    if cmd.CMD_FORWARD[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_DIR1, 1)
                        mdev.writeReg(mdev.CMD_DIR2, 1)
                        mdev.writeReg(mdev.CMD_PWM1, value*10)
                        mdev.writeReg(mdev.CMD_PWM2, value*10)

                    elif cmd.CMD_BACKWARD[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_DIR1, 0)
                        mdev.writeReg(mdev.CMD_DIR2, 0)
                        mdev.writeReg(mdev.CMD_PWM1, value*10)
                        mdev.writeReg(mdev.CMD_PWM2, value*10)

                    elif cmd.CMD_STOP[1:] in cmd_str:
                        mdev.writeReg(mdev.CMD_PWM1, 0)
                        mdev.writeReg(mdev.CMD_PWM2, 0)

                    # Steering commands
                    elif cmd.CMD_TURN_LEFT[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_SERVO1, numMap(100+value, 0, 180, 500, 2500))

                    elif cmd.CMD_TURN_RIGHT[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_SERVO1, numMap(100-value, 0, 180, 500, 2500))

                    elif cmd.CMD_TURN_CENTER[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_SERVO1, numMap(value, 0, 180, 500, 2500))

                    # Camera commands
                    elif cmd.CMD_CAMERA_LEFT[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_SERVO2, numMap(value, 0, 180, 500, 2500))

                    elif cmd.CMD_CAMERA_RIGHT[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_SERVO2, numMap(180-value, 0, 180, 500, 2500))

                    elif cmd.CMD_CAMERA_UP[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_SERVO3, numMap(value, 0, 180, 500, 2500))

                    elif cmd.CMD_CAMERA_DOWN[1:] in cmd_str:
                        value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                        mdev.writeReg(mdev.CMD_SERVO3, numMap(180-value, 0, 180, 500, 2500))

                    # Buzzer command
                    elif cmd.CMD_BUZZER_ALARM[1:] in cmd_str:
                        try:
                            value = int("0" + "".join(filter(str.isdigit, cmd_str)))
                            mdev.writeReg(mdev.CMD_BUZZER, 2000 if value != 0 else 0)
                        except:
                            # Toggle buzzer
                            if hasattr(mdev, 'Is_Buzzer_State_True') and mdev.Is_Buzzer_State_True:
                                mdev.Is_Buzzer_State_True = False
                                mdev.writeReg(mdev.CMD_BUZZER, 0)
                            else:
                                mdev.Is_Buzzer_State_True = True
                                mdev.writeReg(mdev.CMD_BUZZER, 2000)

                    # LED commands
                    elif cmd.CMD_RGB_R[1:] in cmd_str:
                        if hasattr(mdev, 'Is_IO1_State_True') and mdev.Is_IO1_State_True:
                            mdev.Is_IO1_State_True = False
                            mdev.writeReg(mdev.CMD_IO1, 0)
                        else:
                            mdev.Is_IO1_State_True = True
                            mdev.writeReg(mdev.CMD_IO1, 1)

                    elif cmd.CMD_RGB_G[1:] in cmd_str:
                        if hasattr(mdev, 'Is_IO2_State_True') and mdev.Is_IO2_State_True:
                            mdev.Is_IO2_State_True = False
                            mdev.writeReg(mdev.CMD_IO2, 0)
                        else:
                            mdev.Is_IO2_State_True = True
                            mdev.writeReg(mdev.CMD_IO2, 1)

                    elif cmd.CMD_RGB_B[1:] in cmd_str:
                        if hasattr(mdev, 'Is_IO3_State_True') and mdev.Is_IO3_State_True:
                            mdev.Is_IO3_State_True = False
                            mdev.writeReg(mdev.CMD_IO3, 0)
                        else:
                            mdev.Is_IO3_State_True = True
                            mdev.writeReg(mdev.CMD_IO3, 1)

                    # Ultrasonic command
                    elif cmd.CMD_ULTRASONIC[1:] in cmd_str:
                        distance = mdev.getSonic()
                        self.sendData(str(distance))

    def stopTCPServer(self):
        try:
            if hasattr(self, 'tcpClientSock'):
                self.tcpClientSock.close()
            if hasattr(self, 'sock'):
                self.sock.close()
        except Exception as e:
            print("Stop server error:", e)

    def sendData(self, data):
        try:
            self.tcpClientSock.send(data.encode('utf-8'))
        except Exception as e:
            print("Send error:", e)