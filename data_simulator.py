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
        
        # These are the ID numbers for animals in the AI's brain
        self.animal_ids = [16, 17, 18, 19, 20, 21, 22, 23, 24, 25] 

    def detect_animals(self, image_frame):
        """
        Looks at the raw image and returns how confident it is that an animal is there.
        """
        try:
            # Convert the image to a format the AI understands
            transform = T.Compose([T.ToTensor()])
            img_tensor = transform(image_frame).unsqueeze(0)
            
            # Ask the AI to look
            with torch.no_grad():
                predictions = self.model(img_tensor)
            
            # Check if it found an animal
            for i, score in enumerate(predictions[0]['scores']):
                label = predictions[0]['labels'][i].item()
                if label in self.animal_ids and score > 0.5:
                    # Found an animal! Return the confidence score (0.0 to 1.0)
                    return float(score)
                    
            return 0.0 # No animal found
            
        except Exception as e:
            print(f"AI Error: {e}")
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
        
        # Return BOTH the base64 text (for the web) and the raw frame (for the AI)
        return base64_frame, frame 

    def generate_data(self):
        # Randomly decide if there is wildlife (30% chance)
        has_wildlife = random.choice([True, False, False]) 
        
        # Generate the frame
        base64_frame, raw_frame = self.generate_simulated_frame(has_wildlife)
        
        # RUN THE AI DETECTOR HERE on the raw frame
        animal_confidence = self.detect_animals(raw_frame) 
        
        # Generate other random sensor data
        vibration_magnitude = round(random.uniform(0.0, 3.0), 2)
        lat = round(random.uniform(28.0, 29.0), 6)
        lon = round(random.uniform(77.0, 78.0), 6)
        alt = round(random.uniform(200, 300), 1)
        
        # Create the final JSON data
        data = {
            "timestamp": datetime.now().isoformat(),
            "camera_frame": base64_frame,
            "wildlife_confidence": animal_confidence, # The AI result!
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

# ==========================================
# Flask App Setup
# ==========================================
app = Flask(__name__)
simulator = HardwareDataSimulator()

@app.route('/data')
def get_data():
    return simulator.generate_data()

if __name__ == '__main__':
    print("Starting Data Simulator on http://127.0.0.1:8080")
    app.run(host='127.0.0.1', port=8080, debug=False)
