import os
import json
import base64
import numpy as np
import cv2
import random
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class HardwareDataSimulator:
    def __init__(self):
        self.vibration_baseline = 0.5
    
    def detect_animals(self, frame):
        """Simple color-based detection (no heavy AI)"""
        try:
            # Convert to HSV
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Define green color range
            lower_green = np.array([40, 40, 40])
            upper_green = np.array([80, 255, 255])
            # Create mask
            mask = cv2.inRange(hsv, lower_green, upper_green)
            # Count green pixels
            green_pixels = np.sum(mask > 0)
            # Calculate confidence (0.0 to 1.0)
            confidence = min(green_pixels / 10000.0, 1.0)
            return round(confidence, 2)
        except Exception as e:
            print(f"Detection error: {e}")
            return 0.0
    
    def generate_simulated_frame(self, has_wildlife=False):
        """Creates a fake camera image"""
        if has_wildlife:
            # Create image with a green box (representing wildlife)
            frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
            cv2.rectangle(frame, (100, 80), (220, 180), (0, 255, 0), 2)
            cv2.putText(frame, "WILDLIFE", (110, 130),
                        0, 0.5, (0, 255, 0), 2)
        else:
            # Create random noise image
            frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        
        # Convert image to base64
        _, buffer = cv2.imencode('.jpg', frame)
        base64_frame = base64.b64encode(buffer).decode('utf-8')
        
        return base64_frame, frame
    
    def generate_data(self):
        """Generate complete sensor data packet"""
        # Randomly decide if there is wildlife (30% chance)
        has_wildlife = random.choice([True, False, False])
        
        # Generate the frame
        base64_frame, raw_frame = self.generate_simulated_frame(has_wildlife)
        
        # Run detection
        animal_confidence = self.detect_animals(raw_frame)
        
        # Generate sensor data
        vibration = round(random.uniform(0.1, 2.0), 2)
        if has_wildlife:
            vibration = round(random.uniform(vibration, vibration + 1.5), 2)
        
        # Return complete data packet
        return {
            "timestamp": datetime.now().isoformat(),
            "gps": {
                "latitude": round(random.uniform(28.5, 28.7), 6),
                "longitude": round(random.uniform(77.1, 77.3), 6),
                "altitude": round(random.uniform(200, 300), 2)
            },
            "vibration": vibration,
            "wildlife_confidence": animal_confidence,
            "has_wildlife": has_wildlife,
            "frame": base64_frame
        }

# Initialize Flask app
simulator = HardwareDataSimulator()

@app.route('/data')
def get_data():
    try:
        data = simulator.generate_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({"status": "VisionPulse Simulator is running", "endpoints": ["/data"]})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
