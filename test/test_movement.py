import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Server'))
try:
    from mDev import mdev, numMap
    import time

    # Test steering servo
    mdev.writeReg(mdev.CMD_SERVO1, numMap(90, 0, 180, 500, 2500))
    time.sleep(0.5)
    mdev.writeReg(mdev.CMD_SERVO1, numMap(110, 0, 180, 500, 2500))
    time.sleep(0.5)
    mdev.writeReg(mdev.CMD_SERVO1, numMap(90, 0, 180, 500, 2500))

    # Test motors
    mdev.writeReg(mdev.CMD_DIR1, 1)
    mdev.writeReg(mdev.CMD_DIR2, 1)
    mdev.writeReg(mdev.CMD_PWM1, 100)
    mdev.writeReg(mdev.CMD_PWM2, 100)
    time.sleep(1)
    mdev.writeReg(mdev.CMD_PWM1, 0)
    mdev.writeReg(mdev.CMD_PWM2, 0)
    print("Movement test PASSED")
except Exception as e:
    print(f"Movement test FAILED: {e}")
    sys.exit(1)
