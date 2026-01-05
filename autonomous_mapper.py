#!/usr/bin/env python3
"""
Autonomous House Mapping System
Standalone web application for autonomous indoor mapping using ultrasonic sensors
"""

import time
import math
import threading
import logging
from collections import defaultdict
from flask import Flask, render_template_string, jsonify, request
from lib.movement import CarControl

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app for autonomous mapper
mapper_app = Flask(__name__)

# Global mapper instance
mapper_instance = None

class AutonomousMapper:
    def __init__(self, car_controller):
        self.car = car_controller
        self.is_mapping = False
        self.map_data = defaultdict(dict)  # {x: {y: distance}}
        self.current_position = (0, 0)  # Starting position
        self.current_heading = 0  # Starting direction (degrees)
        self.map_resolution = 10  # cm per grid cell
        self.scan_range = (-90, 90)  # degrees
        self.scan_step = 15  # degrees between scans
        self.mapping_thread = None

        # Navigation parameters
        self.safe_distance = 50  # cm - minimum safe distance
        self.turn_angle = 45  # degrees to turn when avoiding obstacles
        self.move_distance = 30  # cm to move forward each step
        self.speed = 25  # movement speed (0-100)

        logger.info("Autonomous Mapper initialized")

    def start_mapping(self):
        """Start autonomous house mapping"""
        if self.is_mapping:
            logger.warning("Mapping already in progress")
            return False

        self.is_mapping = True
        self.mapping_thread = threading.Thread(target=self._mapping_loop, daemon=True)
        self.mapping_thread.start()
        logger.info("Autonomous house mapping started")
        return True

    def stop_mapping(self):
        """Stop autonomous mapping"""
        self.is_mapping = False
        if self.mapping_thread:
            self.mapping_thread.join(timeout=2.0)
        self.car.stop()
        logger.info("Autonomous mapping stopped")

    def get_map_data(self):
        """Get current map data for visualization"""
        return {
            'grid': dict(self.map_data),
            'current_position': self.current_position,
            'current_heading': self.current_heading,
            'resolution': self.map_resolution,
            'dimensions': self._get_map_dimensions()
        }

    def _get_map_dimensions(self):
        """Calculate map boundaries"""
        if not self.map_data:
            return {'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}

        x_coords = []
        y_coords = []
        for x, y_dict in self.map_data.items():
            x_coords.extend([x] * len(y_dict))
            y_coords.extend(y_dict.keys())

        return {
            'min_x': min(x_coords),
            'max_x': max(x_coords),
            'min_y': min(y_coords),
            'max_y': max(y_coords)
        }

    def _mapping_loop(self):
        """Main autonomous mapping loop"""
        logger.info("Autonomous mapping loop started")

        while self.is_mapping:
            try:
                # Step 1: Scan current surroundings
                scan_data = self._perform_scan()

                # Step 2: Update map with scan data
                self._update_map(scan_data)

                # Step 3: Plan next move based on obstacles
                next_action = self._plan_next_move(scan_data)

                # Step 4: Execute movement
                self._execute_move(next_action)

                # Brief pause between moves
                time.sleep(1.0)

            except Exception as e:
                logger.error(f"Mapping error: {e}")
                self.car.stop()
                time.sleep(2.0)

        logger.info("Autonomous mapping loop ended")

    def _perform_scan(self):
        """Perform ultrasonic scan of surroundings"""
        scan_data = {}

        # Scan from left to right
        for angle in range(self.scan_range[0], self.scan_range[1] + 1, self.scan_step):
            # Move sensor to angle
            self.car.set_camera_pan(90 + angle)
            time.sleep(0.1)  # Wait for servo

            # Take multiple readings for accuracy
            readings = []
            for _ in range(3):
                dist = self.car.get_distance()
                if dist > 0 and dist < 400:  # Valid reading within range
                    readings.append(dist)
                time.sleep(0.02)

            if readings:
                avg_distance = sum(readings) / len(readings)
                scan_data[angle] = avg_distance

        # Return camera to center
        self.car.camera_center()

        return scan_data

    def _update_map(self, scan_data):
        """Update the map with new scan data"""
        current_x, current_y = self.current_position

        for angle, distance in scan_data.items():
            # Convert polar coordinates to cartesian
            # Angle is relative to car's heading
            absolute_angle = math.radians(self.current_heading + angle)

            # Calculate obstacle position relative to car
            obstacle_x = current_x + (distance * math.cos(absolute_angle) / self.map_resolution)
            obstacle_y = current_y + (distance * math.sin(absolute_angle) / self.map_resolution)

            # Convert to grid coordinates
            grid_x = round(obstacle_x)
            grid_y = round(obstacle_y)

            # Update map (store minimum distance to avoid overwriting closer obstacles)
            if grid_x not in self.map_data or grid_y not in self.map_data[grid_x]:
                self.map_data[grid_x][grid_y] = distance
            else:
                self.map_data[grid_x][grid_y] = min(self.map_data[grid_x][grid_y], distance)

        logger.debug(f"Map updated: {len(self.map_data)} grid cells mapped")

    def _plan_next_move(self, scan_data):
        """Plan the next movement based on scan data"""
        # Find the clearest direction to move
        best_angle = 0
        best_score = 0

        # Evaluate each possible direction
        for angle in range(-90, 91, 30):  # Check every 30 degrees
            # Calculate score based on clearance in that direction
            clearance_score = self._calculate_clearance(scan_data, angle)
            if clearance_score > best_score:
                best_score = clearance_score
                best_angle = angle

        # Determine action based on best direction
        if best_score < self.safe_distance:
            # No safe direction found, turn in place
            return {'action': 'turn', 'angle': self.turn_angle}
        else:
            # Move in the best direction
            return {'action': 'move', 'angle': best_angle, 'distance': self.move_distance}

    def _calculate_clearance(self, scan_data, target_angle):
        """Calculate clearance score for a given direction"""
        # Look at readings within ±30° of target angle
        min_clearance = float('inf')

        for scan_angle, distance in scan_data.items():
            angle_diff = abs(scan_angle - target_angle)
            if angle_diff <= 30:  # Within 30° cone
                min_clearance = min(min_clearance, distance)

        return min_clearance if min_clearance != float('inf') else 0

    def _execute_move(self, action):
        """Execute the planned movement"""
        if action['action'] == 'turn':
            # Turn in place
            turn_angle = action['angle']
            logger.info(f"Turning {turn_angle}° to avoid obstacles")
            self.car.turn_right(turn_angle) if turn_angle > 0 else self.car.turn_left(abs(turn_angle))
            self.current_heading = (self.current_heading + turn_angle) % 360
            time.sleep(1.0)  # Wait for turn to complete

        elif action['action'] == 'move':
            # Move forward in specified direction
            move_angle = action['angle']
            move_distance = action['distance']

            # First, turn to face the desired direction if needed
            if abs(move_angle) > 10:  # Only turn if significant angle difference
                logger.info(f"Turning {move_angle}° before moving")
                self.car.turn_right(move_angle) if move_angle > 0 else self.car.turn_left(abs(move_angle))
                self.current_heading = (self.current_heading + move_angle) % 360
                time.sleep(1.0)

            # Move forward
            logger.info(f"Moving forward {move_distance}cm")
            self.car.forward()
            self.car.set_speed(self.speed)

            # Estimate movement time based on distance and speed
            move_time = (move_distance / 50.0) * 2.0  # Rough estimate
            time.sleep(move_time)

            self.car.stop()

            # Update position estimate
            move_angle_rad = math.radians(self.current_heading)
            delta_x = (move_distance * math.cos(move_angle_rad) / self.map_resolution)
            delta_y = (move_distance * math.sin(move_angle_rad) / self.map_resolution)

            self.current_position = (
                self.current_position[0] + delta_x,
                self.current_position[1] + delta_y
            )

        logger.debug(f"Position: {self.current_position}, Heading: {self.current_heading}°")


# Flask routes for autonomous mapper web interface
@mapper_app.route('/')
def mapper_home():
    """Main page for autonomous house mapping"""
    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Autonomous House Mapper</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f0f0f0;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
            }
            .control-section {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .control-section h2 {
                margin-top: 0;
                color: #555;
            }
            button {
                padding: 12px 20px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
                transition: background-color 0.3s;
            }
            .btn-success {
                background-color: #28a745;
                color: white;
            }
            .btn-success:hover {
                background-color: #218838;
            }
            .btn-danger {
                background-color: #dc3545;
                color: white;
            }
            .btn-danger:hover {
                background-color: #c82333;
            }
            .btn-primary {
                background-color: #007bff;
                color: white;
            }
            .btn-primary:hover {
                background-color: #0056b3;
            }
            .status-display {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 15px 0;
                font-family: monospace;
            }
            .map-container {
                text-align: center;
                margin: 20px 0;
            }
            canvas {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 Autonomous House Mapping System</h1>

            <div class="control-section">
                <h2>🚗 Mapping Controls</h2>
                <button id="start-mapping" class="btn-success">Start House Mapping</button>
                <button id="stop-mapping" class="btn-danger">Stop Mapping</button>
                <button id="update-map" class="btn-primary">Update Map Display</button>
            </div>

            <div class="control-section">
                <h2>🗺️ House Map</h2>
                <div class="map-container">
                    <canvas id="house-map-canvas" width="600" height="600"></canvas>
                </div>
            </div>

            <div class="control-section">
                <h2>📊 Mapping Status</h2>
                <div class="status-display" id="status-display">
                    System ready. Click "Start House Mapping" to begin autonomous exploration.
                </div>
            </div>
        </div>

        <script>
            let mappingActive = false;

            // Control buttons
            document.getElementById('start-mapping').addEventListener('click', async () => {
                try {
                    const response = await fetch('/start_mapping', { method: 'POST' });
                    const result = await response.json();
                    if (result.success) {
                        mappingActive = true;
                        updateStatus('Autonomous house mapping started! Car will explore and map your house.');
                        document.getElementById('start-mapping').disabled = true;
                        document.getElementById('stop-mapping').disabled = false;
                    } else {
                        alert('Failed to start mapping: ' + result.error);
                    }
                } catch (error) {
                    alert('Error starting mapping: ' + error.message);
                }
            });

            document.getElementById('stop-mapping').addEventListener('click', async () => {
                try {
                    const response = await fetch('/stop_mapping', { method: 'POST' });
                    const result = await response.json();
                    if (result.success) {
                        mappingActive = false;
                        updateStatus('Mapping stopped. Car has mapped ' + result.cells_mapped + ' areas.');
                        document.getElementById('start-mapping').disabled = false;
                        document.getElementById('stop-mapping').disabled = true;
                    }
                } catch (error) {
                    alert('Error stopping mapping: ' + error.message);
                }
            });

            document.getElementById('update-map').addEventListener('click', updateMapDisplay);

            function updateStatus(message) {
                document.getElementById('status-display').textContent = message;
            }

            function updateMapDisplay() {
                fetch('/get_map')
                    .then(response => response.json())
                    .then(data => {
                        drawHouseMap(data);
                        updateStatus(`Map updated: ${Object.keys(data.grid).length} areas mapped. Car at (${data.current_position[0].toFixed(1)}, ${data.current_position[1].toFixed(1)})`);
                    })
                    .catch(error => {
                        console.error('Error updating map:', error);
                    });
            }

            function drawHouseMap(mapData) {
                const canvas = document.getElementById('house-map-canvas');
                const ctx = canvas.getContext('2d');

                // Clear canvas
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Calculate canvas center
                const centerX = canvas.width / 2;
                const centerY = canvas.height / 2;

                // Scale factor (pixels per grid unit)
                const scale = 20;

                // Draw grid obstacles
                for (const [x, yDict] of Object.entries(mapData.grid)) {
                    for (const [y, distance] of Object.entries(yDict)) {
                        const pixelX = centerX + (parseInt(x) * scale);
                        const pixelY = centerY - (parseInt(y) * scale); // Flip Y axis

                        // Color based on distance (closer = more red)
                        const intensity = Math.max(0, 255 - (distance * 2));
                        ctx.fillStyle = `rgb(${255 - intensity}, ${intensity}, 0)`;

                        // Draw obstacle point
                        ctx.fillRect(pixelX - 2, pixelY - 2, 4, 4);
                    }
                }

                // Draw car position
                const carX = centerX + (mapData.current_position[0] * scale);
                const carY = centerY - (mapData.current_position[1] * scale);

                ctx.fillStyle = '#007bff';
                ctx.beginPath();
                ctx.arc(carX, carY, 8, 0, 2 * Math.PI);
                ctx.fill();

                // Draw car heading indicator
                const headingRad = (mapData.current_heading * Math.PI) / 180;
                const indicatorX = carX + Math.cos(headingRad) * 12;
                const indicatorY = carY - Math.sin(headingRad) * 12;

                ctx.strokeStyle = '#ff0000';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(carX, carY);
                ctx.lineTo(indicatorX, indicatorY);
                ctx.stroke();
            }

            // Auto-update map every 5 seconds when mapping is active
            setInterval(() => {
                if (mappingActive) {
                    updateMapDisplay();
                }
            }, 5000);

            // Initial status
            updateStatus('System ready. Click "Start House Mapping" to begin autonomous exploration and mapping.');
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

@mapper_app.route('/start_mapping', methods=['POST'])
def start_mapping():
    """Start autonomous house mapping"""
    global mapper_instance
    if mapper_instance and mapper_instance.start_mapping():
        return jsonify({'success': True, 'message': 'Mapping started'})
    return jsonify({'success': False, 'error': 'Failed to start mapping'})

@mapper_app.route('/stop_mapping', methods=['POST'])
def stop_mapping():
    """Stop autonomous house mapping"""
    global mapper_instance
    if mapper_instance:
        mapper_instance.stop_mapping()
        map_data = mapper_instance.get_map_data()
        cells_mapped = len(map_data['grid'])
        return jsonify({'success': True, 'cells_mapped': cells_mapped})
    return jsonify({'success': False, 'error': 'No mapper instance'})

@mapper_app.route('/get_map')
def get_map():
    """Get current house map data"""
    global mapper_instance
    if mapper_instance:
        return jsonify(mapper_instance.get_map_data())
    return jsonify({'error': 'No mapper instance'})

# Flask integration functions
def create_autonomous_mapper(car_controller):
    """Create and return an AutonomousMapper instance"""
    return AutonomousMapper(car_controller)

def start_house_mapping(mapper):
    """Start autonomous house mapping"""
    return mapper.start_mapping()

def stop_house_mapping(mapper):
    """Stop autonomous house mapping"""
    mapper.stop_mapping()

def get_house_map(mapper):
    """Get current house map data"""
    return mapper.get_map_data()


if __name__ == '__main__':
    # Run the autonomous mapper web server
    try:
        # Initialize car controller
        car = CarControl()

        # Create autonomous mapper instance (no global needed since it's module-level)
        mapper_instance = AutonomousMapper(car)

        logger.info("Starting Autonomous House Mapping web server on port 5001")
        logger.info("Access the mapper at: http://localhost:5001")

        # Run Flask web server for autonomous mapper
        mapper_app.run(host='0.0.0.0', port=5001, debug=False)

    except Exception as e:
        logger.error(f"Failed to start autonomous mapper: {e}")
        print(f"Error: {e}")
