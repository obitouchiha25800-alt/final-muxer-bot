import os
import subprocess
import time
import re
import shutil
import json
import uuid
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = "final_birthday_edition_2025"

# --- CONFIGURATION ---
BASE_UPLOAD = 'uploads'
BASE_DOWNLOAD = 'downloads'
BASE_FONT = 'User_Fonts'
STATUS_FILE = 'status.json'

for folder in [BASE_UPLOAD, BASE_DOWNLOAD, BASE_FONT]:
    os.makedirs(folder, exist_ok=True)

# --- CACHE BUSTER (No Refresh Glitch) ---
@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

# --- SESSION ID ---
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
    # Check 1: File Ban Gayi?
    if os.path.exists(os.path.join(BASE_DOWNLOAD, clean_name)):
        return jsonify({"percent": 100, "status": "✅ Done"})

    # Check 2: Log File
    log_file = os.path.join(BASE_DOWNLOAD, filename + ".log")
    if not os.path.exists(log_file): 
        return jsonify({"percent": 0, "status": "Starting..."})
        
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
    except: 
        return jsonify({"percent": 0})

@app.route('/mux', methods=['POST'])
def mux_video():
    if not get_service_status(): return "⛔ Service is OFF"
    uid = get_user_id()
    
    # Cleanup Old Files
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

    # Pre-allocate dummy file (Fix for instant refresh)
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

# --- BIRTHDAY SURPRISE ROUTE ---
@app.route('/party')
def birthday_countdown():
    return render_template('birthday.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
