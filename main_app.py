# main_app.py - WITH THREE DASHBOARDS
import asyncio
import json
import base64
import numpy as np
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit
import aiohttp
import cv2
import os
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class RiskCalculator:
    def __init__(self):
        self.weights = {'wildlife': 0.6, 'landslide': 0.4}
        
    def calculate_risk(self, wildlife_confidence, vibration_magnitude):
        wildlife_score = wildlife_confidence * 100 * self.weights['wildlife']
        landslide_score = min(vibration_magnitude / 2.0, 1.0) * 100 * self.weights['landslide']
        return min(round(wildlife_score + landslide_score, 2), 100)
    
    def get_risk_level(self, score):
        if score < 30:
            return 'SAFE', 'green'
        elif score < 70:
            return 'WARNING', 'yellow'
        else:
            return 'CRITICAL', 'red'

class DetectionSystem:
    def __init__(self):
        self.risk_calculator = RiskCalculator()
        self.hazard_log = []
        
    def decode_frame(self, base64_frame):
        try:
            img_bytes = base64.b64decode(base64_frame)
            nparr = np.frombuffer(img_bytes, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except:
            return None
    
    def detect_wildlife(self, frame):
        if frame is not None:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower_green = np.array([40, 50, 50])
            upper_green = np.array([70, 255, 255])
            mask = cv2.inRange(hsv, lower_green, upper_green)
            if np.sum(mask) > 1000:
                return True, 0.85
        return False, 0.0
    
    def detect_landslide(self, vibration_data):
        magnitude = vibration_data.get('magnitude', 0)
        return magnitude > 2.0, magnitude
    
    def process_data(self, sensor_data):
        frame = self.decode_frame(sensor_data.get('camera_frame', ''))
        wildlife_detected, wildlife_conf = self.detect_wildlife(frame)
        landslide_detected, vibration_mag = self.detect_landslide(
            sensor_data.get('vibration', {})
        )
        
        risk_score = self.risk_calculator.calculate_risk(
            wildlife_conf if wildlife_detected else 0,
            vibration_mag
        )
        risk_level, color = self.risk_calculator.get_risk_level(risk_score)
        
        hazard_types = []
        if wildlife_detected:
            hazard_types.append('WILDLIFE')
        if landslide_detected:
            hazard_types.append('LANDSLIDE')
        
        if risk_score >= 30:
            log_entry = {
                'timestamp': sensor_data.get('timestamp'),
                'risk_score': risk_score,
                'risk_level': risk_level,
                'hazard_types': hazard_types,
                'gps': sensor_data.get('gps'),
                'wildlife_confidence': wildlife_conf,
                'vibration_magnitude': vibration_mag
            }
            self.hazard_log.append(log_entry)
            if len(self.hazard_log) > 100:
                self.hazard_log = self.hazard_log[-100:]
        
        return {
            'wildlife_detected': wildlife_detected,
            'wildlife_confidence': round(wildlife_conf, 3),
            'landslide_detected': landslide_detected,
            'vibration_magnitude': vibration_mag,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_color': color,
            'hazard_types': hazard_types,
            'gps': sensor_data.get('gps'),
            'timestamp': sensor_data.get('timestamp')
        }

detection_system = DetectionSystem()

async def fetch_from_simulator():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://localhost:8080/data') as response:
                return await response.json()
        except Exception as e:
            print(f"Cannot reach simulator: {e}")
            return None

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_status', {'status': 'connected'})

def process_and_emit_data():
    sensor_data = asyncio.run(fetch_from_simulator())
    if sensor_data:
        result = detection_system.process_data(sensor_data)
        socketio.emit('detection_result', result)

# ============================================
# DASHBOARD 1: MAIN DASHBOARD (Full Features)
# ============================================
MAIN_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>Main Dashboard - Hazard Detection</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white; 
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 10px; font-size: 2.5em; }
        .nav-links { text-align: center; margin-bottom: 20px; }
        .nav-links a { 
            color: #4fc3f7; text-decoration: none; margin: 0 15px; 
            padding: 8px 16px; border: 1px solid #4fc3f7; 
            border-radius: 5px; transition: 0.3s;
        }
        .nav-links a:hover { background: #4fc3f7; color: #1a1a2e; }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
            gap: 20px; margin-bottom: 20px;
        }
        .card { 
            background: rgba(255,255,255,0.05); 
            padding: 25px; border-radius: 15px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 { margin-bottom: 15px; color: #4fc3f7; }
        .risk-indicator { 
            font-size: 72px; font-weight: bold; text-align: center; 
            padding: 30px; border-radius: 15px; margin: 15px 0;
        }
        .safe { background: linear-gradient(135deg, #4CAF50, #45a049); }
        .warning { background: linear-gradient(135deg, #FFC107, #FF9800); color: black; }
        .critical { background: linear-gradient(135deg, #f44336, #d32f2f); }
        .hazard-tag { 
            display: inline-block; padding: 8px 20px; margin: 5px; 
            border-radius: 20px; font-weight: bold;
        }
        .wildlife { background: #4CAF50; }
        .landslide { background: #FF9800; }
        .stat-value { font-size: 28px; font-weight: bold; color: #4fc3f7; }
        .stat-label { color: #aaa; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        th { background: rgba(79, 195, 247, 0.2); }
        .connected { color: #4CAF50; }
        .disconnected { color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Main Control Dashboard</h1>
        <div class="nav-links">
            <a href="/">Main Dashboard</a>
            <a href="/driver">Driver HUD</a>
            <a href="/control">Control Room</a>
        </div>
        
        <div style="text-align: center; margin-bottom: 20px;">
            <strong>Status:</strong> 
            <span id="connection-status" class="disconnected">Disconnected</span>
        </div>
        
        <div class="grid">
            <div class="card">
                <h2>Risk Score</h2>
                <div id="risk-display" class="risk-indicator safe">0</div>
                <div style="text-align:center; font-size:24px;" id="risk-level">SAFE</div>
            </div>
            
            <div class="card">
                <h2>Hazard Types</h2>
                <div id="hazard-types" style="min-height:60px; padding:20px 0;">
                    <span style="color: #666;">No hazards detected</span>
                </div>
            </div>
            
            <div class="card">
                <h2>Wildlife Detection</h2>
                <div class="stat-label">Confidence</div>
                <div class="stat-value" id="wildlife-conf">0%</div>
                <div style="margin-top:10px;">
                    Status: <strong id="wildlife-status">No wildlife</strong>
                </div>
            </div>
            
            <div class="card">
                <h2>Landslide/Vibration</h2>
                <div class="stat-label">Magnitude</div>
                <div class="stat-value" id="vibration-mag">0.00</div>
                <div style="margin-top:10px;">
                    Status: <strong id="landslide-status">Normal</strong>
                </div>
            </div>
        </div>
        
        <div class="card" style="margin-bottom:20px;">
            <h2>GPS Location</h2>
            <p>Lat: <span id="gps-lat">--</span>, Lon: <span id="gps-lon">--</span>, Alt: <span id="gps-alt">--</span>m</p>
        </div>
        
        <div class="card">
            <h2>Hazard Log (Last 10)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Risk Score</th>
                        <th>Level</th>
                        <th>Hazards</th>
                        <th>GPS</th>
                    </tr>
                </thead>
                <tbody id="hazard-log"></tbody>
            </table>
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('connect', () => {
            document.getElementById('connection-status').className = 'connected';
            document.getElementById('connection-status').textContent = 'Connected';
        });
        
        socket.on('disconnect', () => {
            document.getElementById('connection-status').className = 'disconnected';
            document.getElementById('connection-status').textContent = 'Disconnected';
        });
        
        socket.on('detection_result', (data) => {
            const riskDisplay = document.getElementById('risk-display');
            riskDisplay.textContent = data.risk_score;
            riskDisplay.className = 'risk-indicator ' + data.risk_level.toLowerCase();
            document.getElementById('risk-level').textContent = data.risk_level;
            
            const hazardDiv = document.getElementById('hazard-types');
            if (data.hazard_types.length > 0) {
                hazardDiv.innerHTML = data.hazard_types.map(h => 
                    `<span class="hazard-tag ${h.toLowerCase()}">${h}</span>`
                ).join('');
            } else {
                hazardDiv.innerHTML = '<span style="color: #666;">No hazards detected</span>';
            }
            
            document.getElementById('wildlife-conf').textContent = 
                (data.wildlife_confidence * 100).toFixed(1) + '%';
            document.getElementById('wildlife-status').textContent = 
                data.wildlife_detected ? 'Wildlife Detected' : 'No wildlife';
            
            document.getElementById('vibration-mag').textContent = data.vibration_magnitude.toFixed(2);
            document.getElementById('landslide-status').textContent = 
                data.landslide_detected ? 'Landslide Risk' : 'Normal';
            
            if (data.gps) {
                document.getElementById('gps-lat').textContent = data.gps.latitude.toFixed(6);
                document.getElementById('gps-lon').textContent = data.gps.longitude.toFixed(6);
                document.getElementById('gps-alt').textContent = data.gps.altitude.toFixed(0);
            }
            
            updateHazardLog();
        });
        
        async function updateHazardLog() {
            try {
                const response = await fetch('/api/hazards');
                const hazards = await response.json();
                const tbody = document.getElementById('hazard-log');
                tbody.innerHTML = hazards.slice(-10).reverse().map(h => `
                    <tr>
                        <td>${new Date(h.timestamp).toLocaleTimeString()}</td>
                        <td>${h.risk_score}</td>
                        <td>${h.risk_level}</td>
                        <td>${h.hazard_types.join(', ') || 'None'}</td>
                        <td>${h.gps?.latitude?.toFixed(4) || '--'}, ${h.gps?.longitude?.toFixed(4) || '--'}</td>
                    </tr>
                `).join('');
            } catch(e) { console.error(e); }
        }
        
        updateHazardLog();
        setInterval(updateHazardLog, 5000);
    </script>
</body>
</html>
'''

# ============================================
# DASHBOARD 2: DRIVER HUD (Simple & Large)
# ============================================
DRIVER_HUD = '''
<!DOCTYPE html>
<html>
<head>
    <title>Driver HUD - Hazard Detection</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: #000;
            color: white; 
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; text-align: center; }
        h1 { font-size: 3em; margin-bottom: 30px; color: #4fc3f7; }
        .nav-links { margin-bottom: 30px; }
        .nav-links a { 
            color: #4fc3f7; text-decoration: none; margin: 0 15px; 
            padding: 10px 20px; border: 1px solid #4fc3f7; 
            border-radius: 5px;
        }
        .risk-display { 
            font-size: 150px; font-weight: bold; 
            padding: 50px; border-radius: 20px; 
            margin: 30px 0;
        }
        .safe { background: #4CAF50; }
        .warning { background: #FFC107; color: black; }
        .critical { background: #f44336; animation: blink 1s infinite; }
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.5; }
        }
        .alert-box { 
            font-size: 48px; padding: 30px; 
            margin: 20px 0; border-radius: 15px;
            min-height: 120px;
        }
        .hazard-warning { 
            background: rgba(255, 0, 0, 0.3); 
            border: 3px solid #f44336;
            color: #fff;
        }
        .all-clear { 
            background: rgba(76, 175, 80, 0.3); 
            border: 3px solid #4CAF50;
        }
        .gps-box { 
            font-size: 24px; margin-top: 30px; 
            padding: 20px; background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        .status { font-size: 24px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>DRIVER HUD</h1>
        <div class="nav-links">
            <a href="/">Main Dashboard</a>
            <a href="/driver">Driver HUD</a>
            <a href="/control">Control Room</a>
        </div>
        
        <div id="risk-display" class="risk-display safe">0</div>
        <div style="font-size: 36px; margin-bottom: 20px;" id="risk-level">SAFE - PROCEED</div>
        
        <div id="alert-box" class="alert-box all-clear">
            ALL CLEAR - NO HAZARDS
        </div>
        
        <div class="status" id="hazard-details"></div>
        
        <div class="gps-box">
             GPS: <span id="gps-lat">--</span>, <span id="gps-lon">--</span> | 
            Altitude: <span id="gps-alt">--</span>m
        </div>
    </div>

    <script>
        const socket = io();
        
        socket.on('detection_result', (data) => {
            const riskDisplay = document.getElementById('risk-display');
            riskDisplay.textContent = data.risk_score;
            riskDisplay.className = 'risk-display ' + data.risk_level.toLowerCase();
            document.getElementById('risk-level').textContent = 
                data.risk_level + (data.risk_level === 'SAFE' ? ' - PROCEED' : ' - CAUTION');
            
            const alertBox = document.getElementById('alert-box');
            const hazardDetails = document.getElementById('hazard-details');
            
            if (data.hazard_types.length > 0) {
                alertBox.className = 'alert-box hazard-warning';
                alertBox.innerHTML = data.hazard_types.join(' + ') + ' DETECTED!';
                hazardDetails.innerHTML = data.hazard_types.map(h => {
                    if (h === 'WILDLIFE') return 'Wildlife: ' + (data.wildlife_confidence * 100).toFixed(0) + '% confidence';
                    if (h === 'LANDSLIDE') return 'Landslide: Vibration ' + data.vibration_magnitude.toFixed(2);
                    return '';
                }).join('<br>');
            } else {
                alertBox.className = 'alert-box all-clear';
                alertBox.innerHTML = 'ALL CLEAR - NO HAZARDS';
                hazardDetails.innerHTML = '';
            }
            
            if (data.gps) {
                document.getElementById('gps-lat').textContent = data.gps.latitude.toFixed(6);
                document.getElementById('gps-lon').textContent = data.gps.longitude.toFixed(6);
                document.getElementById('gps-alt').textContent = data.gps.altitude.toFixed(0);
            }
        });
    </script>
</body>
</html>
'''

# ============================================
# DASHBOARD 3: CONTROL ROOM (Monitoring)
# ============================================
CONTROL_ROOM = '''
<!DOCTYPE html>
<html>
<head>
    <title>Control Room - Hazard Detection</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            color: white; 
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1600px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 10px; font-size: 2.5em; }
        .nav-links { text-align: center; margin-bottom: 20px; }
        .nav-links a { 
            color: #4fc3f7; text-decoration: none; margin: 0 15px; 
            padding: 8px 16px; border: 1px solid #4fc3f7; 
            border-radius: 5px;
        }
        .monitoring-grid { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 20px; margin-bottom: 20px;
        }
        .monitor-card { 
            background: rgba(0,0,0,0.5); 
            padding: 20px; border-radius: 10px;
            border: 2px solid #4fc3f7;
        }
        .monitor-card h2 { 
            color: #4fc3f7; margin-bottom: 15px; 
            border-bottom: 2px solid #4fc3f7; padding-bottom: 10px;
        }
        .metric { 
            display: flex; justify-content: space-between; 
            padding: 10px; margin: 5px 0; 
            background: rgba(255,255,255,0.05);
            border-radius: 5px;
        }
        .metric-label { font-weight: bold; }
        .metric-value { color: #4fc3f7; font-weight: bold; }
        .alert-panel { 
            background: rgba(244, 67, 54, 0.2); 
            border: 2px solid #f44336;
            padding: 20px; border-radius: 10px;
            margin-bottom: 20px;
        }
        .alert-panel h2 { color: #f44336; margin-bottom: 15px; }
        .log-table { 
            width: 100%; border-collapse: collapse; 
            margin-top: 10px;
        }
        .log-table th, .log-table td { 
            padding: 12px; text-align: left; 
            border-bottom: 1px solid rgba(255,255,255,0.1); 
        }
        .log-table th { background: rgba(79, 195, 247, 0.3); }
        .status-indicator { 
            display: inline-block; width: 12px; height: 12px; 
            border-radius: 50%; margin-right: 8px;
        }
        .status-online { background: #4CAF50; }
        .status-offline { background: #f44336; }
        .stats-grid { 
            display: grid; grid-template-columns: repeat(4, 1fr); 
            gap: 15px; margin-bottom: 20px;
        }
        .stat-box { 
            background: rgba(79, 195, 247, 0.2); 
            padding: 20px; border-radius: 10px; 
            text-align: center;
        }
        .stat-number { font-size: 36px; font-weight: bold; color: #4fc3f7; }
        .stat-label { font-size: 14px; color: #aaa; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CONTROL ROOM MONITORING</h1>
        <div class="nav-links">
            <a href="/">Main Dashboard</a>
            <a href="/driver">Driver HUD</a>
            <a href="/control">Control Room</a>
        </div>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-number" id="total-hazards">0</div>
                <div class="stat-label">Total Hazards</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="wildlife-count">0</div>
                <div class="stat-label">Wildlife Detections</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="landslide-count">0</div>
                <div class="stat-label">Landslide Alerts</div>
            </div>
            <div class="stat-box">
                <div class="stat-number" id="current-risk">0</div>
                <div class="stat-label">Current Risk</div>
            </div>
        </div>
        
        <div class="monitoring-grid">
            <div class="monitor-card">
                <h2>System Status</h2>
                <div class="metric">
                    <span class="metric-label"><span class="status-indicator status-online"></span>Simulator</span>
                    <span class="metric-value">Online</span>
                </div>
                <div class="metric">
                    <span class="metric-label"><span class="status-indicator status-online"></span>Detection Engine</span>
                    <span class="metric-value">Active</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Last Update</span>
                    <span class="metric-value" id="last-update">--</span>
                </div>
            </div>
            
            <div class="monitor-card">
                <h2>Current Readings</h2>
                <div class="metric">
                    <span class="metric-label">Risk Score</span>
                    <span class="metric-value" id="current-risk-score">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Risk Level</span>
                    <span class="metric-value" id="current-risk-level">SAFE</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Wildlife Confidence</span>
                    <span class="metric-value" id="current-wildlife">0%</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Vibration Magnitude</span>
                    <span class="metric-value" id="current-vibration">0.00</span>
                </div>
            </div>
        </div>
        
        <div class="alert-panel">
            <h2>Active Alerts</h2>
            <div id="active-alerts">
                <p style="color: #aaa; text-align: center;">No active alerts</p>
            </div>
        </div>
        
        <div class="monitor-card">
            <h2>Complete Hazard Log</h2>
            <table class="log-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Risk Score</th>
                        <th>Level</th>
                        <th>Hazards</th>
                        <th>Wildlife %</th>
                        <th>Vibration</th>
                        <th>GPS Coordinates</th>
                    </tr>
                </thead>
                <tbody id="hazard-log"></tbody>
            </table>
        </div>
    </div>

    <script>
        const socket = io();
        let wildlifeCount = 0;
        let landslideCount = 0;
        
        socket.on('detection_result', (data) => {
            document.getElementById('current-risk').textContent = data.risk_score;
            document.getElementById('current-risk-score').textContent = data.risk_score;
            document.getElementById('current-risk-level').textContent = data.risk_level;
            document.getElementById('current-wildlife').textContent = 
                (data.wildlife_confidence * 100).toFixed(1) + '%';
            document.getElementById('current-vibration').textContent = 
                data.vibration_magnitude.toFixed(2);
            document.getElementById('last-update').textContent = 
                new Date().toLocaleTimeString();
            
            if (data.wildlife_detected) wildlifeCount++;
            if (data.landslide_detected) landslideCount++;
            
            document.getElementById('wildlife-count').textContent = wildlifeCount;
            document.getElementById('landslide-count').textContent = landslideCount;
            
            const alertsDiv = document.getElementById('active-alerts');
            if (data.hazard_types.length > 0) {
                alertsDiv.innerHTML = data.hazard_types.map(h => {
                    return `<div style="padding: 15px; margin: 10px 0; background: rgba(255,255,255,0.1); border-radius: 10px;">
                        <strong>${h} DETECTED</strong><br>
                        <small>Risk: ${data.risk_score} | ${new Date(data.timestamp).toLocaleTimeString()}</small>
                    </div>`;
                }).join('');
            } else {
                alertsDiv.innerHTML = '<p style="color: #aaa; text-align: center;">No active alerts</p>';
            }
            
            updateLog();
        });
        
        async function updateLog() {
            try {
                const response = await fetch('/api/hazards');
                const hazards = await response.json();
                document.getElementById('total-hazards').textContent = hazards.length;
                
                const tbody = document.getElementById('hazard-log');
                tbody.innerHTML = hazards.slice(-20).reverse().map(h => `
                    <tr>
                        <td>${new Date(h.timestamp).toLocaleString()}</td>
                        <td><strong>${h.risk_score}</strong></td>
                        <td>${h.risk_level}</td>
                        <td>${h.hazard_types.join(', ') || 'None'}</td>
                        <td>${(h.wildlife_confidence * 100).toFixed(1)}%</td>
                        <td>${h.vibration_magnitude.toFixed(2)}</td>
                        <td>${h.gps?.latitude?.toFixed(4) || '--'}, ${h.gps?.longitude?.toFixed(4) || '--'}</td>
                    </tr>
                `).join('');
            } catch(e) { console.error(e); }
        }
        
        updateLog();
        setInterval(updateLog, 3000);
    </script>
</body>
</html>
'''

# Routes for all three dashboards
@app.route('/')
def index():
    return render_template_string(MAIN_DASHBOARD)

@app.route('/driver')
def driver_hud():
    return render_template_string(DRIVER_HUD)

@app.route('/control')
def control_room():
    return render_template_string(CONTROL_ROOM)

@app.route('/api/status')
def api_status():
    return jsonify({
        'system_status': 'online',
        'hazard_count': len(detection_system.hazard_log)
    })

@app.route('/api/hazards')
def api_hazards():
    return jsonify(detection_system.hazard_log)

def background_fetch():
    while True:
        process_and_emit_data()
        time.sleep(1)

if __name__ == '__main__':
    print("Starting Main Detection System...")
    print("Three dashboards available:")
    print("   Main Dashboard:    http://127.0.0.1:5000/")
    print("   Driver HUD:        http://127.0.0.1:5000/driver")
    print("   Control Room:      http://127.0.0.1:5000/control")
    
    thread = threading.Thread(target=background_fetch, daemon=True)
    thread.start()
    
    socketio.run(app, host='127.0.0.1', port=5000, debug=False)