import os
import subprocess
import time
import re
import shutil
import json
import uuid
import threading
import signal
from datetime import timedelta, datetime
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify, session, render_template_string

app = Flask(__name__)
app.secret_key = "final_rock_solid_2025"

# --- CONFIGURATION ---
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

BASE_UPLOAD = 'uploads'
BASE_DOWNLOAD = 'downloads'
BASE_FONT_ROOT = 'User_Fonts' 
STATUS_FILE = 'status.json'

# Global Dictionary for Active Tasks
TASKS = {}

for folder in [BASE_UPLOAD, BASE_DOWNLOAD, BASE_FONT_ROOT]:
    os.makedirs(folder, exist_ok=True)

# --- AUTO-CLEANER (Background Only - 30 Mins) ---
def clean_old_files():
    while True:
        try:
            now = time.time()
            retention_period = 1800 # 30 Mins
            for folder in [BASE_DOWNLOAD, BASE_UPLOAD]:
                for f in os.listdir(folder):
                    f_path = os.path.join(folder, f)
                    if os.path.isfile(f_path):
                        if now - os.path.getmtime(f_path) > retention_period:
                            try: os.remove(f_path)
                            except: pass
        except: pass
        time.sleep(600)

threading.Thread(target=clean_old_files, daemon=True).start()

# --- HEADERS ---
@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# --- HELPER ---
def get_user_id():
    session.permanent = True 
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())[:8]
    return session['user_id']

def get_user_font_dir():
    uid = get_user_id()
    user_dir = os.path.join(BASE_FONT_ROOT, uid)
    if not os.path.exists(user_dir): os.makedirs(user_dir)
    return user_dir

def get_service_status():
    if not os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, 'w') as f: json.dump({"active": True}, f)
        return True
    try:
        with open(STATUS_FILE, 'r') as f: return json.load(f).get("active", True)
    except: return True

# --- HTML UI ---
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>AD Web Muxer!!</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 15px; margin: 0; text-align: center; }
        h1 { font-size: 1.5rem; margin-bottom: 20px; color: #58a6ff; }
        .box { background: #161b22; padding: 15px; border: 1px solid #30363d; border-radius: 12px; margin-bottom: 20px; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; background: #0d1117; color: white; border: 1px solid #30363d; border-radius: 8px; font-size: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 14px; margin-top: 10px; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; border: none; }
        
        .btn-green { background: #238636; color: white; transition: 0.3s; }
        .btn-blue { background: #1f6feb; color: white; transition: 0.3s; font-size: 14px; padding: 6px 12px; } 
        .btn-grey { background: #21262d; color: #c9d1d9; border: 1px solid #30363d; font-size: 14px; padding: 8px 15px; transition: 0.2s; }
        .btn-red { background: #da3633; color: white; transition: 0.3s; padding: 8px 12px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 0.9rem; }
        
        .font-list { text-align: left; margin-top: 15px; max-height: 150px; overflow-y: auto; }
        .font-item { display: flex; justify-content: space-between; align-items: center; background: #21262d; padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #30363d; }
        .font-name { font-size: 0.9rem; color: #e6edf3; }
        .btn-del-font { background: transparent; border: none; color: #da3633; cursor: pointer; font-size: 1.1rem; padding: 0 5px; }
        
        .actions { display: flex; gap: 8px; margin-top: 10px; }
        .btn-dl { background: #238636; color: white; text-decoration: none; padding: 10px; border-radius: 6px; font-weight: bold; font-size: 0.9rem; flex-grow: 2; text-align: center; display: flex; align-items: center; justify-content: center; }
        .btn-copy { background: #1f6feb; color: white; border: none; padding: 10px; border-radius: 6px; font-size: 1.2rem; cursor: pointer; flex-grow: 1; margin-top: 0; }
        .btn-del { background: transparent; border: 1px solid #da3633; color: #da3633; padding: 10px; border-radius: 6px; font-size: 1.2rem; cursor: pointer; flex-grow: 0; margin-top: 0; }
        
        .file-item { background: #21262d; margin-top: 12px; padding: 15px; border-radius: 8px; border: 1px solid #30363d; text-align: left; }
        .file-name { font-weight: bold; word-break: break-all; color: #e6edf3; font-size: 0.95rem; }
        .progress-container { background: #333; height: 6px; border-radius: 3px; overflow: hidden; margin-top: 8px; }
        .progress-bar { height: 100%; background: #238636; width: 0%; transition: width 0.3s; }
        .status-text { font-size: 0.85rem; color: #e3b341; margin-bottom: 5px;}
        .error-msg { color: #ff7b72; background: rgba(255,0,0,0.1); padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px solid #ff7b72; display: none; }
        .cleaner-badge { background: #21262d; color: #8b949e; padding: 5px 10px; border-radius: 20px; font-size: 0.75rem; margin-top: 20px; display: inline-block; border: 1px solid #30363d; }
    </style>
    <script>
        let intervalId;
        function updateProgress() {
            document.querySelectorAll('.processing').forEach(div => {
                let filename = div.getAttribute('data-name');
                fetch('/progress/' + filename + '?t=' + new Date().getTime())
                .then(r => r.json())
                .then(d => {
                    if (d.status.includes("Error") || d.status.includes("Failed")) {
                        div.querySelector('.status-text').innerText = d.status;
                        div.querySelector('.status-text').style.color = "#ff7b72";
                        div.querySelector('.progress-bar').style.backgroundColor = "#ff7b72";
                    } else {
                        div.querySelector('.progress-bar').style.width = d.percent + "%";
                        if(d.percent >= 100) {
                            div.querySelector('.status-text').innerText = "✅ Finalizing...";
                            div.querySelector('.status-text').style.color = "#39d353";
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            div.querySelector('.status-text').innerText = d.status;
                        }
                    }
                }).catch(e => console.log("Waiting..."));
            });
        }
        function copyLink(filename) {
            const link = window.location.origin + "/downloads/" + filename;
            navigator.clipboard.writeText(link).then(() => { alert("✅ Link Copied!"); }).catch(err => { prompt("Copy Link:", link); });
        }
        intervalId = setInterval(updateProgress, 1500);
    </script>
</head>
<body>
    <h1>🚀 AD Web Muxer !!</h1>
    
    <div class="box">
        <form action="/mux" method="POST" enctype="multipart/form-data" onsubmit="document.querySelector('.btn-green').innerText='⏳ Starting...'; document.querySelector('.btn-green').style.opacity='0.7';">
            <input type="text" name="video_url" placeholder="Paste M3U8 Link" required>
            <input type="file" name="subtitle" accept=".ass" required>
            <select name="font">
                <option value="NONE">Default Font</option>
                {% for font in fonts %}
                    <option value="{{ font }}">{{ font }}</option>
                {% endfor %}
            </select>
            <input type="text" name="filename" placeholder="Output Filename (e.g. Episode 1)" required>
            <button type="submit" class="btn-green">Start Muxing</button>
        </form>
        
        <hr style="border-color: #30363d; margin: 15px 0;">
        
        <h3 style="margin: 0 0 10px 0; font-size: 1rem; color: #8b949e;">My Private Fonts</h3>
        <form action="/upload_font" method="POST" enctype="multipart/form-data" style="display:flex; gap:10px; align-items:center;">
            <input type="file" name="font_file" accept=".ttf,.otf" style="flex:1; margin:0;" required>
            <button type="submit" class="btn-grey" style="width:auto; margin:0;">Upload</button>
        </form>
        <div class="font-list">
            {% for font in fonts %}
                <div class="font-item">
                    <span class="font-name">🔤 {{ font }}</span>
                    <a href="/delete_font/{{ font }}" class="btn-del-font" onclick="return confirm('Delete this font?')">🗑️</a>
                </div>
            {% else %}
                <div style="text-align:center; color:#484f58; font-size:0.8rem; margin-top:10px;">No custom fonts uploaded</div>
            {% endfor %}
        </div>
    </div>

    {% if error %}
    <div class="box error-msg" style="display:block;">⚠️ {{ error }}</div>
    {% endif %}

    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <h3 style="margin:0;">📂 Files</h3>
        <button onclick="location.reload()" class="btn-blue" style="width:auto; margin:0;">Refresh</button>
    </div>

    <div>
        {% for file in files %}
            <div class="file-item {% if 'RUNNING_' in file.real_name %}processing{% endif %}" data-name="{{ file.real_name }}">
                <div class="file-name">{{ file.display_name }}</div>
                {% if 'RUNNING_' in file.real_name %}
                    <div style="margin-top:10px;">
                        <div class="status-text">⏳ Initializing...</div>
                        <div class="progress-container"><div class="progress-bar"></div></div>
                        <div style="margin-top: 10px; text-align: right;">
                            <a href="/cancel/{{ file.real_name }}" class="btn-red">❌ Cancel Task</a>
                        </div>
                    </div>
                {% else %}
                    <div class="actions">
                        <a href="/downloads/{{ file.real_name }}" class="btn-dl">⬇️ Download</a>
                        <button onclick="copyLink('{{ file.real_name }}')" class="btn-copy">📋</button>
                        <a href="/delete/{{ file.real_name }}" class="btn-del">🗑️</a>
                    </div>
                {% endif %}
            </div>
        {% else %}
            <p style="color:#8b949e; margin-top: 20px;">No files yet.</p>
        {% endfor %}
    </div>
    
    <div class="cleaner-badge">🧹 Auto-Cleaner Active</div>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def index():
    uid = get_user_id()
    error = request.args.get('error')
    user_font_dir = get_user_font_dir()
    fonts = sorted([f for f in os.listdir(user_font_dir) if f.endswith(('.ttf', '.otf'))])
    
    # --- NO AUTO-DELETE HERE (This was the problem) ---
    all_files = sorted(os.listdir(BASE_DOWNLOAD))
    user_files = []
    
    for f in all_files:
        if f.endswith('.log'): continue
        if f.startswith(uid):
            clean_name = f.replace(f"{uid}_", "").replace("RUNNING_", "")
            user_files.append({'real_name': f, 'display_name': clean_name})
            
    return render_template_string(INDEX_HTML, files=user_files, fonts=fonts, is_active=get_service_status(), error=error)

@app.route('/upload_font', methods=['POST'])
def upload_font():
    file = request.files.get('font_file')
    if file and file.filename:
        file.save(os.path.join(get_user_font_dir(), file.filename))
    return redirect(url_for('index'))

@app.route('/delete_font/<filename>')
def delete_font(filename):
    path = os.path.join(get_user_font_dir(), filename)
    if os.path.exists(path): os.remove(path)
    return redirect(url_for('index'))

@app.route('/progress/<filename>')
def get_progress(filename):
    clean_name = filename.replace("RUNNING_", "")
    log_file = os.path.join(BASE_DOWNLOAD, filename + ".log")
    
    if os.path.exists(os.path.join(BASE_DOWNLOAD, clean_name)):
        return jsonify({"percent": 100, "status": "✅ Done"})
    
    if not os.path.exists(log_file): return jsonify({"percent": 0, "status": "Starting..."})
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
        
        # Check for specific errors
        if "403 Forbidden" in content or "Server returned 403" in content:
             return jsonify({"percent": 0, "status": "❌ Error 403: Link Protected"})
             
        if "Error" in content or "Invalid data" in content:
             return jsonify({"percent": 0, "status": "❌ Error! Check Log"})
        
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
    
    # Simple Cleanup: Only delete OLD COMPLETED files, never active ones
    # We will skip cleanup here to be safe, rely on Background Cleaner
    
    m3u8_link = request.form.get('video_url')
    raw_filename = request.form.get('filename').strip()
    selected_font = request.form.get('font')
    
    sub_file = request.files.get('subtitle')
    if not sub_file: return redirect(url_for('index', error="Subtitle Missing!"))
    if not sub_file.filename.lower().endswith('.ass'):
        return redirect(url_for('index', error="❌ Error: Only .ASS allowed!"))

    final_name = f"{uid}_{raw_filename}"
    if not final_name.endswith('.mkv'): final_name += ".mkv"
    
    sub_path = os.path.join(BASE_UPLOAD, f"sub_{uid}_{int(time.time())}.ass")
    sub_file.save(sub_path)

    temp_name = f"RUNNING_{final_name}"
    temp_path = os.path.join(BASE_DOWNLOAD, temp_name)
    final_path = os.path.join(BASE_DOWNLOAD, final_name)
    log_path = temp_path + ".log"
    
    font_cmd = ""
    if selected_font and selected_font != "NONE":
        f_path = os.path.join(get_user_font_dir(), selected_font)
        if os.path.exists(f_path):
            font_cmd = f' -attach "{f_path}" -metadata:s:t mimetype=application/x-truetype-font'

    try: open(temp_path, 'w').close()
    except: pass

    # BYPASS USER AGENT & REFERER
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    cmd = (
        f'ffmpeg -y -user_agent "{user_agent}" -headers "Referer: {m3u8_link}" -tls_verify 0 '
        f'-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
        f'-i "{m3u8_link}" -i "{sub_path}"{font_cmd} '
        f'-map 0 -map 1 -c copy -disposition:s:0 default '
        f'"{temp_path}" 2> "{log_path}" && mv "{temp_path}" "{final_path}" && rm "{log_path}"'
    )
    
    proc = subprocess.Popen(cmd, shell=True)
    TASKS[temp_name] = proc

    time.sleep(1)
    return redirect(url_for('index'))

@app.route('/cancel/<filename>')
def cancel_task(filename):
    if filename.startswith(get_user_id()):
        if filename in TASKS:
            try:
                TASKS[filename].kill()
                del TASKS[filename]
            except: pass
        
        try:
            path = os.path.join(BASE_DOWNLOAD, filename)
            if os.path.exists(path): os.remove(path)
            log_path = path + ".log"
            if os.path.exists(log_path): os.remove(log_path)
        except: pass
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
