#!/usr/bin/env python3
# -*- coding: utf-8 -*-
########################################################################
# Filename    : test_tcp.py
# Description : Test TCP connection to the car server
# Author      : Test script
# Modification: 2026/01/04
########################################################################

import socket
import sys
import os

# Add paths to import the command constants
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Server'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Client'))

def test_car_connection():
    """Test connection to the car server like the app does."""
    try:
        from Command import COMMAND as cmd
    except ImportError:
        # Fallback if Command.py not found
        class CMD:
            CMD_ULTRASONIC = ">Ultrasonic"
        cmd = CMD()

    # Use the same IP as the client app
    HOST = '192.168.1.108'
    PORT = 12345

    print(f"Testing connection to car at {HOST}:{PORT}...")

    try:
        # Create socket like the app does
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5)

        # Try to connect
        client.connect((HOST, PORT))
        print("Connected to car server successfully!")

        # Send a test command (ultrasonic to get a response)
        test_cmd = cmd.CMD_ULTRASONIC + ">"
        client.send(test_cmd.encode('utf-8'))
        print(f"Sent test command: {test_cmd}")

        # Try to receive response
        try:
            response = client.recv(1024).decode('utf-8')
            print(f"Received response: {response}")
        except socket.timeout:
            print("No immediate response (normal)")

        # Close connection
        client.close()
        print("Connection closed successfully")

        return True

    except socket.error as e:
        print(f"Connection failed: {e}")
        print("Make sure:")
        print("  - The car server is running")
        print("  - The car's IP address is correct")
        print("  - You're on the same network as the car")
        return False

if __name__ == "__main__":
    success = test_car_connection()
    if success:
        print("\nTCP test PASSED - Car is reachable!")
    else:
        print("\nTCP test FAILED - Cannot connect to car")
    sys.exit(0 if success else 1)
