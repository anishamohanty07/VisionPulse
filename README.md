# VisionPulse
VisionPulse is a real-time web application designed to monitor and alert operators about environmental railway threats. Built with a modular, hardware-agnostic architecture, it currently uses a Data Simulator to generate sensor and camera data.
## System Architecture
'''text
Data Simulator (Port 8080) -> HTTP/JSON -> Main Dashboard (Port 5000) -> Web Sockets -> UI
'''
## Hardware (Simulated & Real-World Equivalent)
* **Camera:** OpenCV Frame Generator (Real-world: Ruggedized IP67 PoE security camera + Uncooled thermal core)
* **Vibration Sensor:** Random Float Generator (Real-world: MEMS accelerometer)
* **Distance Sensor** Random Float Generator (Real-world: Short-range Radar)
* **GPS Module:** Random Lat/Lon Generator (Real-world: Standard GNSS module)
* **Edge Processor:** Python Script (Real-world: Ruggedized Jetson Orin Nano)
* **Power & Comms:** None (Real-world: Solar + Battery bank, LoRaWAN module)
* **Enclosure:** None (Real-world: Standardized modular IP67 enclosure)
