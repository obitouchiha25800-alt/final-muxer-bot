import os
import subprocess
import time
import shutil
import uuid
import re
from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for, session

app = Flask(__name__)
application = app  # <--- SERVER KA BOSS
app.secret_key = "final_default_font_2025"

# --- FOLDERS ---
BASE_DIR = os.getcwd()
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
FONT_FOLDER = os.path.join(BASE_DIR, "fonts")

# --- SMART FFMPEG FINDER ---
FFMPEG_BIN = shutil.which("ffmpeg")
if not FFMPEG_BIN:
    local_ffmpeg = os.path.join(BASE_DIR, "ffmpeg")
    if os.path.exists(local_ffmpeg):
        FFMPEG_BIN = local_ffmpeg
    else:
        FFMPEG_BIN = "ffmpeg"

for f in [DOWNLOAD_FOLDER, UPLOAD_FOLDER, FONT_FOLDER]:
    os.makedirs(f, exist_ok=True)

# --- USER ID HELPER ---
def get_uid():
    if 'uid' not in session:
        session['uid'] = str(uuid.uuid4())[:8]
    return session['uid']

# --- PROGRESS HELPER ---
def calculate_progress(log_content):
    try:
        duration_match = re.search(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", log_content)
        time_matches = re.findall(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", log_content)
        if duration_match and time_matches:
            def to_sec(t):
                p = t.split(':')
                return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
            total = to_sec(duration_match.group(1))
            curr = to_sec(time_matches[-1])
            return min(int((curr / total) * 100), 100) if total > 0 else 0
    except: pass
    return 0

# --- UI CODE ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AD Web Muxer !!</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Poppins', sans-serif; }
        body { background-color: #0d0d10; color: #ffffff; display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding: 20px; }
        .card { background-color: #16161a; width: 100%; max-width: 480px; padding: 35px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); border: 1px solid #25252b; margin-bottom: 30px; }
        .title { text-align: center; font-size: 28px; font-weight: 700; margin-bottom: 30px; background: linear-gradient(to right, #7b61ff, #00d4ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 1px; }
        label { display: block; font-size: 13px; font-weight: 600; color: #b3b3b3; margin-bottom: 8px; margin-top: 15px; }
        input[type="text"], select { width: 100%; padding: 14px 16px; background-color: #212126; border: 1px solid #333; border-radius: 12px; color: #fff; font-size: 14px; outline: none; transition: 0.3s; }
        input[type="text"]:focus, select:focus { border-color: #7b61ff; box-shadow: 0 0 8px rgba(123, 97, 255, 0.3); }
        .file-upload { position: relative; display: flex; align-items: center; justify-content: space-between; background-color: #212126; border: 1px dashed #444; padding: 12px 16px; border-radius: 12px; cursor: pointer; transition: 0.3s; }
        .file-upload:hover { border-color: #7b61ff; }
        .file-upload input { position: absolute; left: 0; top: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
        .file-name-display { font-size: 13px; color: #aaa; white-space: nowrap; overflow: hidden; max-width: 80%; }
        .upload-icon { color: #00d4ff; font-size: 16px; }
        .btn-process { width: 100%; margin-top: 30px; padding: 15px; border: none; border-radius: 12px; font-size: 16px; font-weight: 700; color: white; cursor: pointer; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); transition: 0.2s; box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4); }
        .btn-process:hover { opacity: 0.9; }
        .recent-section { width: 100%; max-width: 480px; }
        .section-header { display: flex; justify-content: space-between; margin-bottom: 15px; }
        .section-title { font-size: 14px; color: #888; font-weight: 600; }
        .refresh-btn { background: #222; border: 1px solid #333; color: #aaa; padding: 5px 12px; border-radius: 20px; font-size: 11px; cursor: pointer; }
        .file-card { background-color: #1a1a20; border: 1px solid #2a2a30; border-radius: 12px; padding: 15px; margin-bottom: 12px; }
        .file-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .fname { font-size: 14px; font-weight: 600; color: #eee; }
        .status-badge { font-size: 10px; font-weight: bold; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }
        .status-done { background: rgba(0, 255, 136, 0.1); color: #00ff88; }
        .status-run { background: rgba(0, 212, 255, 0.1); color: #00d4ff; }
        .status-err { background: rgba(255, 50, 50, 0.1); color: #ff3232; }
        .progress-bar { height: 4px; background: #333; border-radius: 2px; overflow: hidden; margin-top: 8px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #7b61ff); transition: width 0.5s; }
        .action-row { display: flex; gap: 8px; margin-top: 12px; }
        .btn-small { padding: 8px; border-radius: 8px; font-size: 12px; font-weight: 600; text-align: center; text-decoration: none; cursor: pointer; transition: 0.2s; border: none;}
        .btn-dl { flex: 2; background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
        .btn-dl:hover { background: #3b82f6; color: #fff; }
        .btn-copy { flex: 2; background: rgba(123, 97, 255, 0.15); color: #7b61ff; }
        .btn-copy:hover { background: #7b61ff; color: #fff; }
        .btn-del { width: 35px; flex: none; display: flex; align-items: center; justify-content: center; border: 1px solid #333; color: #666; background: transparent; }
        .btn-del:hover { border-color: #ff3232; color: #ff3232; }
        .footer { text-align: center; margin-top: 25px; font-size: 11px; color: #444; }
    </style>
    <script>
        function updateFileName(input, id) {
            document.getElementById(id).innerText = input.files[0] ? input.files[0].name : "Choose File...";
        }
        function copyLink(filename) {
            const link = window.location.origin + "/download/" + filename;
            navigator.clipboard.writeText(link).then(() => alert("✅ Link Copied!\\n" + link)).catch(() => prompt("Copy this:", link));
        }
    </script>
</head>
<body>
    <div class="card">
        <h1 class="title">AD Web Muxer !!</h1>
        <form action="/start" method="POST" enctype="multipart/form-data">
            <label>Video URL (M3U8)</label>
            <input type="text" name="url" placeholder="Paste direct video link here..." required>
            <label>Subtitle File (.ASS)</label>
            <div class="file-upload">
                <span class="file-name-display" id="sub-name">Select .ASS File</span>
                <span class="upload-icon">📂</span>
                <input type="file" name="sub" accept=".ass" required onchange="updateFileName(this, 'sub-name')">
            </div>
            
            <label>Font (Optional)</label>
            {% if saved_fonts %}
            <select name="saved_font" style="margin-bottom: 8px;">
                <option value="">-- Default Font (Helvetica) --</option>
                {% for font in saved_fonts %}
                    <option value="{{ font }}">{{ font }}</option>
                {% endfor %}
            </select>
            {% endif %}
            <div class="file-upload">
                <span class="file-name-display" id="font-name">Upload New Font (.TTF)</span>
                <span class="upload-icon">🔤</span>
                <input type="file" name="font" accept=".ttf,.otf" onchange="updateFileName(this, 'font-name')">
            </div>

            <label>Output Filename</label>
            <input type="text" name="fname" placeholder="e.g. Episode 01" required>
            <button type="submit" class="btn-process">START MUXING 🚀</button>
        </form>
        <div class="footer">Powered by YukiSub</div>
    </div>

    <div class="recent-section">
        <div class="section-header">
            <span class="section-title">Recent Activity</span>
            <button onclick="location.reload()" class="refresh-btn">🔄 Refresh</button>
        </div>
        {% for file in files %}
        <div class="file-card">
            <div class="file-header">
                <span class="fname">{{ file.name }}</span>
                <span class="status-badge {{ 'status-done' if file.status == 'done' else 'status-run' if file.status == 'processing' else 'status-err' }}">{{ file.status }}</span>
            </div>
            {% if file.status == 'processing' %}
                <div class="progress-bar"><div class="progress-fill" style="width: {{ file.percent }}%;"></div></div>
                <div style="text-align: right; font-size: 11px; color: #888;">{{ file.percent }}%</div>
            {% endif %}
            {% if file.status == 'done' %}
            <div class="action-row">
                <a href="/download/{{ file.realname }}" class="btn-small btn-dl">⬇ Download</a>
                <button onclick="copyLink('{{ file.realname }}')" class="btn-small btn-copy">📋 Copy Link</button>
                <a href="/delete/{{ file.realname }}" class="btn-small btn-del">🗑</a>
            </div>
            {% endif %}
            {% if file.status == 'error' %}
             <div class="action-row"><a href="/delete/{{ file.realname }}" class="btn-small btn-del" style="width: 100%">🗑 Remove</a></div>
            {% endif %}
        </div>
        {% else %}
        <div style="text-align: center; color: #555; font-size: 12px; margin-top: 20px;">No files yet. Start muxing above!</div>
        {% endfor %}
    </div>
</body>
</html>
"""

# --- ROUTES ---
@app.route('/')
def home():
    uid = get_uid()
    files_data = []
    saved_fonts_list = []
    if os.path.exists(FONT_FOLDER):
        saved_fonts_list = [f.replace(f"{uid}_", "") for f in sorted(os.listdir(FONT_FOLDER)) if f.startswith(uid)]

    if os.path.exists(DOWNLOAD_FOLDER):
        for f in sorted(os.listdir(DOWNLOAD_FOLDER)):
            if f.startswith(uid) and f.endswith(".mkv"):
                status = "done"
                log_file = os.path.join(DOWNLOAD_FOLDER, f + ".log")
                percent = 0
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as lf:
                            c = lf.read()
                            percent = calculate_progress(c)
                            if "Error" in c or "Invalid data" in c: status = "error"
                            elif "muxing overhead" in c or "LSIZE" in c: status = "done"; percent = 100
                            else: status = "processing"
                    except: status = "processing"
                files_data.append({"name": f.replace(f"{uid}_", "").replace(".mkv", ""), "realname": f, "status": status, "percent": percent})
    
    return render_template_string(HTML_CODE, files=files_data, saved_fonts=saved_fonts_list)

@app.route('/start', methods=['POST'])
def start_mux():
    uid = get_uid()
    url = request.form.get('url')
    fname = request.form.get('fname').strip()
    
    sub_file = request.files.get('sub')
    sub_path = os.path.join(UPLOAD_FOLDER, f"{uid}_sub.ass")
    sub_file.save(sub_path)
    
    final_font_path = None
    font_file = request.files.get('font')
    saved_font_name = request.form.get('saved_font')

    if font_file and font_file.filename:
        final_font_path = os.path.join(FONT_FOLDER, f"{uid}_{font_file.filename}")
        font_file.save(final_font_path)
    elif saved_font_name:
        final_font_path = os.path.join(FONT_FOLDER, f"{uid}_{saved_font_name}")
    
    # --- DEFAULT FONT LOGIC ---
    if not final_font_path:
        default_font = os.path.join(FONT_FOLDER, "default.ttf")
        if os.path.exists(default_font):
            final_font_path = default_font

    font_arg = ['-attach', final_font_path, '-metadata:s:t', 'mimetype=application/x-truetype-font'] if final_font_path else []

    output_path = os.path.join(DOWNLOAD_FOLDER, f"{uid}_{fname}.mkv")
    open(output_path, 'w').close()

    # --- USE SMART FFMPEG PATH ---
    cmd = [FFMPEG_BIN, '-y', '-headers', f'Referer: {url}', '-tls_verify', '0', '-reconnect', '1', '-reconnect_streamed', '1', '-i', url, '-i', sub_path]
    cmd.extend(font_arg)
    cmd.extend(['-map', '0:V', '-map', '0:a', '-map', '1', '-c', 'copy', '-disposition:s:0', 'default', output_path])

    with open(output_path + ".log", "w") as log_file:
        subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)

    time.sleep(1)
    return redirect(url_for('home'))

@app.route('/download/<filename>')
def download(filename):
    clean = filename.split('_', 1)[1] if '_' in filename else filename
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True, download_name=clean)

@app.route('/delete/<filename>')
def delete(filename):
    try:
        os.remove(os.path.join(DOWNLOAD_FOLDER, filename))
        os.remove(os.path.join(DOWNLOAD_FOLDER, filename + ".log"))
    except: pass
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
