# VisionPulse
VisionPulse is a real-time web application designed to monitor and alert operators about environmental railway threats. Built with a modular, hardware-agnostic architecture, it currently uses a Data Simulator to generate sensor and camera data.
## System Architecture
Data Simulator (Port 8080) -> HTTP/JSON -> Main Dashboard (Port 5000) -> Web Sockets -> UI
## Hardware (Simulated & Real-World Equivalent)
* **Camera:** OpenCV Frame Generator (Real-world: Ruggedized IP67 PoE security camera + Uncooled thermal core)
* **Vibration Sensor:** Random Float Generator (Real-world: MEMS accelerometer)
* **Distance Sensor** Random Float Generator (Real-world: Short-range Radar)
* **GPS Module:** Random Lat/Lon Generator (Real-world: Standard GNSS module)
* **Edge Processor:** Python Script (Real-world: Ruggedized Jetson Orin Nano)
* **Power & Comms:** None (Real-world: Solar + Battery bank, LoRaWAN module)
* **Enclosure:** None (Real-world: Standardized modular IP67 enclosure)
## Detection Logic
python
# 1. Wildlife Detection (HSV color space)
if (green_pixel_count> THRESOLD):
   wildlife_confidence = calculated_confidence()
# 2. Risk Calculation (Weighted Algorithm)
risk_score = (wildlife_confidence*100*0.6)+(vibration_magnitude*50*0.4)
# 3. Alert Categorization
if (risk_score <60): status= "SAFE"
elif (risk_score <80): status= "WARNING"
else: status= "CRITICAL"

send_to_dashboard(status, risk_score)
## Process (Step-by-step)
1. **Data Generation** -Simulator generates random GPS, vibration data, and camera frames.
2. **AI Detection** -OpenCV analyzes the image's HSV color space to detect "wildlife" (green pixels).
3. **Risk Calculation** -A weighted algorithm combines wildlife confidence (60%) and vibration data (40%).
4. **Real-Time Streaming** -Flask-SocketIO pushes the calculated data to web clients via WebSockets.
5. **Visual Alert** -The UI instantly updates its color (Green/Yellow/Red) and displays the hazard type.
6. **Event Logging** -Control room logs the hazard type, timestamp, and risk score.
## Output
* Hardware-agnostic modular design
* Zero-latency WebSocket updates (NO page refresh required).
* Three specialized UI views for different operational needs.
* Dual-threat detection (Wildlife and Landslides).
