import sys
try:
    from picamera2 import Picamera2
    import cv2
    import time

    camera = Picamera2()
    camera.configure(camera.create_video_configuration(main={"size": (640, 480)}))
    camera.start()
    time.sleep(1)
    frame = camera.capture_array()
    cv2.imwrite('test.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    camera.stop()
    print("Camera test PASSED")
except Exception as e:
    print(f"Camera test FAILED: {e}")
    sys.exit(1)
