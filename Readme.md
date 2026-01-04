# Car API

A Python-based API for controlling a Raspberry Pi-powered smart car with movement control and remote access capabilities.

## Features

- **Movement Control**: Forward/backward movement with speed control
- **Steering**: Servo-controlled steering system
- **Camera Pan**: Servo-controlled camera left/right positioning
- **Sensors**: Ultrasonic distance sensor
- **LED Control**: RGB LED indicators
- **Buzzer**: Audio feedback
- **TCP Server**: Remote control via network commands

## Requirements

- Raspberry Pi (tested on Raspberry Pi 4)
- Compatible car chassis with motors and servos
- Python 3.7+

### Dependencies

```
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
pip3 install smbus
```

## Usage

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

## Demo

Run the movement demo to test forward/backward movement:
```bash
python3 demo_movement.py
```

This will move the car forward for 4 seconds, stop for 2 seconds, then move backward for 4 seconds.

## Project Structure

```
Car-Api/
├── lib/
│   └── movement.py     # Car control class
├── Server/
│   ├── Command.py      # Command definitions
│   ├── mDev.py         # Hardware interface
│   └── mTCPServer.py   # TCP control server
├── Shield Firmware/    # Hardware firmware files
├── demo_movement.py    # Movement demonstration script
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
