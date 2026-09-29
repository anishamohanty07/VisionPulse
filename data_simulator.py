import json
import base64
import numpy as np
import cv2
import random
from datetime import datetime
from flask import Flask, jsonify

class HardwareDataSimulator:
    def __init__(self):
        self.vibration_baseline = 0.5
        print(" Simulator initialized (Simple Mode - No PyTorch needed!)")

    def detect_animals_simple(self, image_frame):
        """
        Simple color-based detection - looks for green/brown colors
        that might indicate wildlife in the frame
        """
        try:
            # Convert to HSV color space
            hsv = cv2.cvtColor(image_frame, cv2.COLOR_BGR2HSV)
            
            # Define range of green colors (for wildlife)
            lower_green = np.array([40, 50, 50])
            upper_green = np.array([70, 255, 255])
            
            # Threshold the HSV image to get green components
            mask = cv2.inRange(hsv, lower_green, upper_green)
            
            # Count how many pixels are green
            green_pixels = cv2.countNonZero(mask)
            total_pixels = image_frame.shape[0] * image_frame.shape[1]
            
            # Calculate confidence based on green pixel percentage
            confidence = min(green_pixels / total_pixels * 10, 1.0)
            
            return round(confidence, 3)
            
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
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            # Create random noise image
            frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        
        # Convert image to text (base64) so we can send it over the internet
        _, buffer = cv2.imencode('.jpg', frame)
        base64_frame = base64.b64encode(buffer).decode('utf-8')
        
        # Return BOTH the base64 text and the raw frame
        return base64_frame, frame 

    def generate_data(self):
        # Randomly decide if there is wildlife (30% chance)
        has_wildlife = random.choice([True, False, False]) 
        
        # Generate the frame
        base64_frame, raw_frame = self.generate_simulated_frame(has_wildlife)
        
        # Run simple detection
        animal_confidence = self.detect_animals_simple(raw_frame) 
        
        # Generate other random sensor data
        vibration_magnitude = round(random.uniform(0.0, 3.0), 2)
        lat = round(random.uniform(28.0, 29.0), 6)
        lon = round(random.uniform(77.0, 78.0), 6)
        alt = round(random.uniform(200, 300), 1)
        
        # Create the final JSON data
        data = {
            "timestamp": datetime.now().isoformat(),
            "camera_frame": base64_frame,
            "wildlife_confidence": animal_confidence,
            "vibration": {
                "magnitude": vibration_magnitude,
                "timestamp": datetime.now().isoformat()
            },
            "gps": {
                "latitude": lat,
                "longitude": lon,
                "altitude": alt
            }
        }
        
        return jsonify(data)

# Flask App Setup
app = Flask(__name__)
simulator = HardwareDataSimulator()

@app.route('/data')
def get_data():
    return simulator.generate_data()

if __name__ == '__main__':
    print(" Starting Data Simulator on http://127.0.0.1:8080")
    print(" Using simple color-based detection (No PyTorch!)")
    app.run(host='127.0.0.1', port=8080, debug=False)