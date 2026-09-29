import os
import time
import json
import threading
import urllib.request
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'visionpulse-secret'

# CRITICAL FIX FOR RENDER: Use threading async mode to avoid eventlet/gevent issues
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Get Simulator URL from Environment Variable (set in Render dashboard)
SIMULATOR_URL = os.environ.get('SIMULATOR_URL', 'http://127.0.0.1:8080')
PORT = int(os.environ.get('PORT', 5000))

# --- Risk Calculation Logic ---
def calculate_risk(wildlife_conf, vibration):
    # Weighted risk formula
    risk = (wildlife_conf * 60) + (vibration * 20)
    return min(100, max(0, risk))

# --- Background Data Fetcher ---
def background_fetcher():
    print("Background fetcher started...")
    while True:
        try:
            # Fetch data from the simulator API
            url = f"{SIMULATOR_URL}/data"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())

            # Extract metrics
            wildlife_conf = data.get('wildlife_confidence', 0.0)
            vibration = data.get('vibration', 0.0)
            risk_score = calculate_risk(wildlife_conf, vibration)

            # Determine status and color
            if risk_score < 40:
                status, color = "SAFE", "green"
            elif risk_score < 70:
                status, color = "WARNING", "yellow"
            else:
                status, color = "CRITICAL", "red"

            # Emit data to all connected web clients via WebSockets
            socketio.emit('update_data', {
                'risk_score': round(risk_score, 1),
                'status': status,
                'color': color,
                'wildlife': round(wildlife_conf, 2),
                'vibration': round(vibration, 2),
                'frame': data.get('frame', '')
            })
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            
        time.sleep(2) # Fetch new data every 2 seconds

# --- HTML Templates (Embedded for easy deployment) ---
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>VisionPulse - {{ title }}</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 20px; }
        .card { background: #2d2d2d; padding: 20px; margin: 10px; border-radius: 10px; display: inline-block; min-width: 200px;}
        .status-box { padding: 20px; font-size: 24px; font-weight: bold; border-radius: 10px; margin: 20px 0; }
        img { max-width: 100%; border-radius: 10px; border: 2px solid #555; }
        h1 { color: #00d2ff; }
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
</head>
<body>
    <h1>VisionPulse: {{ title }}</h1>
    <div id="status" class="status-box" style="background: gray;">WAITING FOR DATA...</div>
    
    <div class="card">
        <h3>Risk Score</h3>
        <h2 id="risk">0</h2>
    </div>
    <div class="card">
        <h3>Wildlife Confidence</h3>
        <h2 id="wildlife">0.0</h2>
    </div>
    <div class="card">
        <h3>Vibration</h3>
        <h2 id="vibration">0.0</h2>
    </div>
    <br>
    <img id="camera" src="" alt="Live Feed">

    <script>
        var socket = io();
        socket.on('update_data', function(data) {
            document.getElementById('risk').innerText = data.risk_score;
            document.getElementById('wildlife').innerText = data.wildlife;
            document.getElementById('vibration').innerText = data.vibration;
            
            var statusBox = document.getElementById('status');
            statusBox.innerText = data.status;
            statusBox.style.background = data.color;
            statusBox.style.color = data.color === 'yellow' ? 'black' : 'white';
            
            if(data.frame) {
                document.getElementById('camera').src = "data:image/jpeg;base64," + data.frame;
            }
        });
    </script>
</body>
</html>
"""

# --- Routes ---
@app.route('/')
def index():
    return render_template_string(BASE_HTML, title="Main Dashboard")

@app.route('/driver')
def driver():
    return render_template_string(BASE_HTML, title="Driver HUD")

@app.route('/control')
def control():
    return render_template_string(BASE_HTML, title="Control Room")

# --- Main Execution ---
if __name__ == '__main__':
    # Start the background thread to fetch data from simulator
    thread = threading.Thread(target=background_fetcher, daemon=True)
    thread.start()

    print(f"Starting VisionPulse Main App on port {PORT}")
    print(f"Fetching data from: {SIMULATOR_URL}")
    
    # Run the app
    socketio.run(app, host='0.0.0.0', port=PORT, debug=False)
