# Car API

A Python-based API for controlling a Raspberry Pi-powered smart car with camera streaming, movement control, and remote access capabilities.

## Features

- **Camera Streaming**: MJPEG video feed via Flask web server
- **Movement Control**: Forward/backward movement with speed control
- **Steering**: Servo-controlled steering system
- **Camera Pan/Tilt**: Servo-controlled camera positioning
- **Sensors**: Ultrasonic distance sensor
- **LED Control**: RGB LED indicators
- **Buzzer**: Audio feedback
- **TCP Server**: Remote control via network commands
- **Comprehensive Testing**: Unit tests for all components

## Requirements

- Raspberry Pi (tested on Raspberry Pi 4)
- Compatible car chassis with motors and servos
- Camera module (Raspberry Pi Camera)
- Python 3.7+

### Dependencies

```
flask
picamera2
opencv-python
smbus
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Olibot1107/Car-Api.git
cd Car-Api
```

2. Install dependencies:
```bash
pip3 install flask picamera2 opencv-python smbus
```

## Usage

### Camera Streaming

Start the camera server:
```bash
python3 lib/camera.py
```

Access the video feed at: `http://raspberrypi:5000`

### Car Control

```python
from lib.movement import CarControl

car = CarControl()

# Basic movement
car.forward()
car.set_speed(50)  # 0-100 speed
car.backward()
car.stop()

# Steering
car.turn_left(30)
car.turn_right(30)
car.center_steering()

# Camera control
car.camera_left(10)
car.camera_right(10)
car.camera_up(10)
car.camera_down(10)
car.camera_center()

# Sensors and outputs
distance = car.get_distance()  # Ultrasonic sensor
car.buzzer_on(2000)
car.led_rgb(True, False, True)  # Red and blue LEDs
```

### TCP Server

Start the TCP server for remote control:
```bash
python3 Server/mTCPServer.py
```

The server listens on port 12345 for commands.

## Testing

Run all tests:
```bash
python3 test/run_tests.py
```

Individual tests:
```bash
python3 test/test_camera.py
python3 test/test_movement.py
python3 test/test_tcp.py
```

## Project Structure

```
Car-Api/
├── lib/
│   ├── camera.py       # Flask camera streaming server
│   └── movement.py     # Car control class
├── Server/
│   ├── Command.py      # Command definitions
│   ├── mDev.py         # Hardware interface
│   └── mTCPServer.py   # TCP control server
├── test/
│   ├── README.md       # Test documentation
│   ├── run_tests.py    # Test runner
│   ├── test_camera.py  # Camera tests
│   ├── test_movement.py # Movement tests
│   └── test_tcp.py     # TCP tests
├── Shield Firmware/    # Hardware firmware files
└── README.md           # This file
```

## Hardware Setup

This API is designed to work with Raspberry Pi-based smart car platforms that use I2C communication for motor control and servo positioning.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source. Please check individual files for license information.
