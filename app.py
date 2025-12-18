import os
import subprocess
import time
import re
import shutil
import json
import uuid
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify, session, render_template_string

app = Flask(__name__)
app.secret_key = "final_birthday_polished_2025"

# --- CONFIGURATION ---
BASE_UPLOAD = 'uploads'
BASE_DOWNLOAD = 'downloads'
BASE_FONT = 'User_Fonts'
STATUS_FILE = 'status.json'

for folder in [BASE_UPLOAD, BASE_DOWNLOAD, BASE_FONT]:
    os.makedirs(folder, exist_ok=True)

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
    return session['user_id']

def get_service_status():
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f: json.dump({"active": True}, f)
        return True
    try:
        with open(STATUS_FILE, 'r') as f: return json.load(f).get("active", True)
    except: return True

# --- POLISHED HTML CODE (FIXED DATE: 19 DEC 2025) ---
BIRTHDAY_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>For You ❤️</title>
    <link href="https://fonts.googleapis.com/css2?family=Pacifico&family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        /* Premium Dark Gradient Background */
        body { 
            background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
            color: white; 
            font-family: 'Poppins', sans-serif; 
            display: flex; flex-direction: column; 
            justify-content: center; align-items: center; 
            min-height: 100vh; margin: 0; text-align: center; 
            overflow-x: hidden; padding: 20px; box-sizing: border-box;
        }
        
        /* Countdown Style */
        h1 { font-family: 'Poppins', sans-serif; font-size: 1.8rem; color: #ff7b72; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; }
        .timer { font-size: 3.5rem; font-weight: 700; color: #4ade80; text-shadow: 0 0 25px rgba(74, 222, 128, 0.6); margin: 15px 0; }
        
        /* Happy Birthday Title (Stylish & Adjusted Size) */
        .message { 
            font-family: 'Pacifico', cursive; 
            font-size: 3rem; display: none; 
            color: #c084fc; /* Soft Purple */
            text-shadow: 0 0 15px rgba(192, 132, 252, 0.6);
            animation: pop 1.2s cubic-bezier(0.34, 1.56, 0.64, 1); 
            line-height: 1.1;
            margin-bottom: 30px;
            margin-top: 20px;
        }
        @keyframes pop { from { transform: scale(0.8) translateY(20px); opacity: 0; } to { transform: scale(1) translateY(0); opacity: 1; } }
        
        /* The Paragraph Container (Glassmorphism Effect) */
        .sub-text { 
            color: #e6edf3; 
            font-size: 1.05rem; 
            line-height: 1.8; 
            width: 100%; max-width: 550px; /* Responsive width */
            background: rgba(30, 35, 45, 0.75); /* Semi-transparent dark */
            padding: 35px 25px; 
            border-radius: 30px; /* Softer corners */
            border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle border */
            box-shadow: 0 20px 40px rgba(0,0,0,0.5); /* Deep shadow */
            backdrop-filter: blur(12px); /* Frosted Glass Effect */
            -webkit-backdrop-filter: blur(12px);
        }
        
        /* Paragraph Spacing */
        .sub-text p { margin-bottom: 20px; }
        .sub-text p:last-of-type { margin-bottom: 30px; }
        
        /* Final Line Highlight */
        .final-line {
            font-weight: 600; color: #ff9f43; font-size: 1.15rem; display: block;
        }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
</head>
<body>
    <h1 id="title">Wait for the magic... ✨</h1>
    <div class="timer" id="countdown">00:00:00</div>
    
    <div class="message" id="hbd">Happy Birthday<br>Bestie! 🎂</div>
    
    <div class="sub-text" id="sign" style="display:none;">
        <p>Happy Birthday to the person who knows all my secrets and still chooses to be seen in public with me! 😜</p>
        <p>On your special day, I just want to say thank you for being the most amazing human in my life. You are not just a friend; you are family. Life is simply better with you in it. May this year bring you as much happiness as you bring to everyone around you.</p>
        <span class="final-line">Keep shining, star! 🌟</span>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const isTest = urlParams.get('test');
        
        let targetTime;
        
        if (isTest) {
            // Test Mode: 3 Seconds baad
            targetTime = new Date().getTime() + 3000;
        } else {
            // REAL MODE: Aaj Raat 12 Baje (Dec 19, 2025 00:00:00)
            targetTime = new Date("December 19, 2025 00:00:00").getTime();
        }

        function updateTimer() {
            const now = new Date().getTime();
            const diff = targetTime - now;

            if (diff <= 0) {
                document.getElementById('countdown').style.display = 'none';
                document.getElementById('title').style.display = 'none';
                document.getElementById('hbd').style.display = 'block';
                document.getElementById('sign').style.display = 'block';
                launchConfetti();
                clearInterval(interval);
                return;
            }

            const h = Math.floor((diff / (1000 * 60 * 60)) % 24);
            const m = Math.floor((diff / (1000 * 60)) % 60);
            const s = Math.floor((diff / 1000) % 60);
            document.getElementById('countdown').innerText = (h<10?"0"+h:h) + ":" + (m<10?"0"+m:m) + ":" + (s<10?"0"+s:s);
        }
        
        function launchConfetti() {
            var duration = 15 * 1000;
            var end = Date.now() + duration;
            (function frame() {
                confetti({ particleCount: 5, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#a864fd', '#29cdff', '#78ff44', '#ff718d', '#fdff6a'] });
                confetti({ particleCount: 5, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#a864fd', '#29cdff', '#78ff44', '#ff718d', '#fdff6a'] });
                if (Date.now() < end) requestAnimationFrame(frame);
            }());
        }
        const interval = setInterval(updateTimer, 1000);
        updateTimer();
    </script>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    uid = get_user_id()
    user_font_dir = os.path.join(BASE_FONT, uid)
    os.makedirs(user_font_dir, exist_ok=True)
    fonts = [f for f in os.listdir(user_font_dir) if f.endswith(('.ttf', '.otf'))]
    all_files = sorted(os.listdir(BASE_DOWNLOAD))
    user_files = []
    for f in all_files:
        if f.endswith('.log'): continue
        if f.startswith(uid) or (f.startswith("RUNNING_") and uid in f):
            clean_name = f.replace(f"{uid}_", "").replace("RUNNING_", "")
            user_files.append({'real_name': f, 'display_name': clean_name})
    return render_template('index.html', files=user_files, fonts=fonts, is_active=get_service_status())

@app.route('/upload_font', methods=['POST'])
def upload_font():
    uid = get_user_id()
    user_font_dir = os.path.join(BASE_FONT, uid)
    file = request.files.get('font_file')
    if file and file.filename:
        file.save(os.path.join(user_font_dir, file.filename))
    return redirect(url_for('index'))

@app.route('/progress/<filename>')
def get_progress(filename):
    clean_name = filename.replace("RUNNING_", "")
    if os.path.exists(os.path.join(BASE_DOWNLOAD, clean_name)):
        return jsonify({"percent": 100, "status": "✅ Done"})
    log_file = os.path.join(BASE_DOWNLOAD, filename + ".log")
    if not os.path.exists(log_file): return jsonify({"percent": 0, "status": "Starting..."})
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
        duration_match = re.search(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", content)
        time_matches = re.findall(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", content)
        if duration_match and time_matches:
            def to_sec(t):
                h, m, s = t.split(':')
                return int(h)*3600 + int(m)*60 + float(s)
            total = to_sec(duration_match.group(1))
            current = to_sec(time_matches[-1])
            percent = int((current / total) * 100) if total > 0 else 0
            if percent > 98: percent = 100
            return jsonify({"percent": percent, "status": f"Processing {percent}%"})
        return jsonify({"percent": 5, "status": "Initializing..."})
    except: return jsonify({"percent": 0})

@app.route('/mux', methods=['POST'])
def mux_video():
    if not get_service_status(): return "⛔ Service is OFF"
    uid = get_user_id()
    for f in os.listdir(BASE_DOWNLOAD):
        if f.startswith(uid):
            try: os.remove(os.path.join(BASE_DOWNLOAD, f))
            except: pass
    m3u8_link = request.form.get('video_url')
    raw_filename = request.form.get('filename').replace(" ", "_")
    selected_font = request.form.get('font')
    final_name = f"{uid}_{raw_filename}"
    if not final_name.endswith('.mkv'): final_name += ".mkv"
    sub_file = request.files.get('subtitle')
    if not sub_file: return "Subtitle Required!"
    sub_path = os.path.join(BASE_UPLOAD, f"sub_{uid}_{int(time.time())}.ass")
    sub_file.save(sub_path)
    temp_name = f"RUNNING_{final_name}"
    temp_path = os.path.join(BASE_DOWNLOAD, temp_name)
    final_path = os.path.join(BASE_DOWNLOAD, final_name)
    log_path = temp_path + ".log"
    font_cmd = ""
    if selected_font and selected_font != "NONE":
        f_path = os.path.join(BASE_FONT, uid, selected_font)
        if os.path.exists(f_path):
            font_cmd = f' -attach "{f_path}" -metadata:s:t mimetype=application/x-truetype-font'
    try:
        with open(temp_path, 'w') as f: pass
    except: pass
    cmd = f'ffmpeg -y -i "{m3u8_link}" -i "{sub_path}"{font_cmd} -c copy "{temp_path}" 2> "{log_path}" && mv "{temp_path}" "{final_path}" && rm "{log_path}"'
    subprocess.Popen(cmd, shell=True)
    time.sleep(1)
    return redirect(url_for('index'))

@app.route('/downloads/<filename>')
def download_file(filename):
    if os.path.exists(os.path.join(BASE_DOWNLOAD, filename)):
        clean_name = filename.split('_', 1)[1] if '_' in filename else filename
        return send_from_directory(BASE_DOWNLOAD, filename, as_attachment=True, download_name=clean_name)
    return "⛔ File Not Found", 404

@app.route('/delete/<filename>')
def delete_file(filename):
    if filename.startswith(get_user_id()):
        path = os.path.join(BASE_DOWNLOAD, filename)
        if os.path.exists(path): os.remove(path)
        log_p = path + ".log"
        if os.path.exists(log_p): os.remove(log_p)
    return redirect(url_for('index'))

@app.route('/party')
def birthday_countdown():
    return render_template_string(BIRTHDAY_HTML)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
