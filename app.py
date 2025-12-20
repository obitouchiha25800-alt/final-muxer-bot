import os
import subprocess
import time
import shutil
import uuid
import re
from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "final_dark_theme_2025"

# --- FOLDERS ---
BASE_DIR = os.getcwd()
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, "downloads")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
FONT_FOLDER = os.path.join(BASE_DIR, "fonts")

for f in [DOWNLOAD_FOLDER, UPLOAD_FOLDER, FONT_FOLDER]:
    os.makedirs(f, exist_ok=True)

# --- CHECK FFMPEG ---
if not shutil.which("ffmpeg"):
    print("⚠️ CRITICAL: FFmpeg is NOT installed on this server!")

# --- USER ID HELPER ---
def get_uid():
    if 'uid' not in session:
        session['uid'] = str(uuid.uuid4())[:8]
    return session['uid']

# --- PROGRESS CALCULATION HELPER ---
def calculate_progress(log_content):
    try:
        duration_match = re.search(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})", log_content)
        time_matches = re.findall(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", log_content)
        
        if duration_match and time_matches:
            total_str = duration_match.group(1)
            current_str = time_matches[-1]
            
            def to_sec(t):
                parts = t.split(':')
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            
            total_sec = to_sec(total_str)
            current_sec = to_sec(current_str)
            
            if total_sec > 0:
                percent = int((current_sec / total_sec) * 100)
                return min(percent, 100)
    except:
        pass
    return 0

# --- UI CODE (Dark Theme + Correct Label) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AD Web Muxer !!</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        /* --- RESET & FONTS --- */
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Poppins', sans-serif; }

        /* --- DARK BACKGROUND --- */
        body {
            background-color: #0d0d10; /* Pitch dark background */
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }

        /* --- MAIN CARD --- */
        .card {
            background-color: #16161a;
            width: 100%;
            max-width: 480px;
            padding: 35px;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            border: 1px solid #25252b;
            margin-bottom: 30px;
        }

        /* --- TITLE --- */
        .title {
            text-align: center;
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 30px;
            background: linear-gradient(to right, #7b61ff, #00d4ff); 
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1px;
        }

        /* --- INPUTS --- */
        label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: #b3b3b3;
            margin-bottom: 8px;
            margin-top: 15px;
        }

        input[type="text"], select {
            width: 100%;
            padding: 14px 16px;
            background-color: #212126;
            border: 1px solid #333;
            border-radius: 12px;
            color: #fff;
            font-size: 14px;
            outline: none;
            transition: 0.3s;
        }

        input[type="text"]:focus, select:focus {
            border-color: #7b61ff;
            box-shadow: 0 0 8px rgba(123, 97, 255, 0.3);
        }

        /* --- FILE UPLOAD BOX --- */
        .file-upload {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            background-color: #212126;
            border: 1px dashed #444;
            padding: 12px 16px;
            border-radius: 12px;
            cursor: pointer;
            transition: 0.3s;
        }
        .file-upload:hover { border-color: #7b61ff; }
        .file-upload input { position: absolute; left: 0; top: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
        .file-name-display { font-size: 13px; color: #aaa; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 80%; }
        .upload-icon { color: #00d4ff; font-size: 16px; }

        /* --- BUTTON --- */
        .btn-process {
            width: 100%;
            margin-top: 30px;
            padding: 15px;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 700;
            color: white;
            cursor: pointer;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            transition: transform 0.2s, opacity 0.2s;
            box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4);
        }
        .btn-process:hover { opacity: 0.9; }
        .btn-process:active { transform: scale(0.98); }

        /* --- RECENT FILES SECTION --- */
        .recent-section { width: 100%; max-width: 480px; }
        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        .section-title { font-size: 14px; color: #888; font-weight: 600; }
        .refresh-btn { background: #222; border: 1px solid #333; color: #aaa; padding: 5px 12px; border-radius: 20px; font-size: 11px; cursor: pointer; transition: 0.2s; }
        .refresh-btn:hover { color: #fff; border-color: #fff; }

        .file-card {
            background-color: #1a1a20;
            border: 1px solid #2a2a30;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
        }
        
        .file-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .fname { font-size: 14px; font-weight: 600; color: #eee; }
        
        .status-badge { font-size: 10px; font-weight: bold; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }
        .status-done { background: rgba(0, 255, 136, 0.1); color: #00ff88; }
        .status-run { background: rgba(0, 212, 255, 0.1); color: #00d4ff; }
        .status-err { background: rgba(255, 50, 50, 0.1); color: #ff3232; }

        .progress-bar { height: 4px; background: #333; border-radius: 2px; overflow: hidden; margin-top: 8px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #00d4ff, #7b61ff); transition: width 0.5s; }
        
        .action-row { display: flex; gap: 10px; margin-top: 12px; }
        .btn-small { flex: 1; padding: 8px; border-radius: 8px; font-size: 12px; font-weight: 600; text-align: center; text-decoration: none; cursor: pointer; transition: 0.2s; }
        
        .btn-dl { background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid transparent; }
        .btn-dl:hover { background: #3b82f6; color: #fff; }
        
        .btn-del { width: 35px; flex: none; display: flex; align-items: center; justify-content: center; border: 1px solid #333; color: #666; }
        .btn-del:hover { border-color: #ff3232; color: #ff3232; }

        /* --- FOOTER --- */
        .footer { text-align: center; margin-top: 25px; font-size: 11px; color: #444; font-weight: 500; letter-spacing: 0.5px; opacity: 0.7; }
    </style>
    
    <script>
        function updateFileName(input, id) {
            const name = input.files[0] ? input.files[0].name : "Choose File...";
            document.getElementById(id).innerText = name;
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

            <label>Font (Saved or New)</label>
            {% if saved_fonts %}
            <select name="saved_font" style="margin-bottom: 8px;">
                <option value="">-- Use Saved Font --</option>
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
                {% if file.status == 'done' %}
                    <span class="status-badge status-done">Success</span>
                {% elif file.status == 'processing' %}
                    <span class="status-badge status-run">Processing</span>
                {% else %}
                    <span class="status-badge status-err">Failed</span>
                {% endif %}
            </div>

            {% if file.status == 'processing' %}
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ file.percent }}%;"></div>
                </div>
                <div style="text-align: right; font-size: 11px; color: #888; margin-top: 4px;">{{ file.percent }}%</div>
            {% endif %}

            {% if file.status == 'done' %}
            <div class="action-row">
                <a href="/download/{{ file.realname }}" class="btn-small btn-dl">⬇ Download File</a>
                <a href="/delete/{{ file.realname }}" class="btn-small btn-del">🗑</a>
            </div>
            {% endif %}
            
            {% if file.status == 'error' %}
            <div style="font-size: 10px; color: #ff5555; margin-top: 5px; font-family: monospace;">Check Logs</div>
             <div class="action-row">
                <a href="/delete/{{ file.realname }}" class="btn-small btn-del" style="width: 100%">🗑 Remove</a>
            </div>
            {% endif %}
        </div>
        {% else %}
        <div style="text-align: center; color: #555; font-size: 12px; margin-top: 20px;">
            No files yet. Start muxing above!
        </div>
        {% endfor %}
    </div>

</body>
</html>
"""

# --- FLASK ROUTES ---
@app.route('/')
def home():
    uid = get_uid()
    files_data = []
    
    saved_fonts_list = []
    if os.path.exists(FONT_FOLDER):
        raw_fonts = sorted([f for f in os.listdir(FONT_FOLDER) if f.startswith(uid)])
        saved_fonts_list = [f.replace(f"{uid}_", "") for f in raw_fonts]

    if os.path.exists(DOWNLOAD_FOLDER):
        for f in sorted(os.listdir(DOWNLOAD_FOLDER)):
            if f.startswith(uid) and f.endswith(".mkv"):
                status = "done"
                log_file = os.path.join(DOWNLOAD_FOLDER, f + ".log")
                percent = 0

                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as lf:
                            content = lf.read()
                            percent = calculate_progress(content)
                            if "Error" in content or "Invalid data" in content:
                                status = "error"
                            elif "muxing overhead" in content or "LSIZE" in content: 
                                status = "done"
                                percent = 100
                            else:
                                status = "processing"
                    except: status = "processing"
                
                display_name = f.replace(f"{uid}_", "").replace(".mkv", "")
                
                files_data.append({
                    "name": display_name,
                    "realname": f,
                    "status": status,
                    "percent": percent
                })

    return render_template_string(HTML_CODE, files=files_data, saved_fonts=saved_fonts_list)

@app.route('/start', methods=['POST'])
def start_mux():
    uid = get_uid()
    url = request.form.get('url')
    fname = request.form.get('fname').strip()
    
    sub_file = request.files.get('sub')
    sub_path = os.path.join(UPLOAD_FOLDER, f"{uid}_sub.ass")
    sub_file.save(sub_path)
    
    font_arg = []
    final_font_path = None
    font_file = request.files.get('font')
    saved_font_name = request.form.get('saved_font')

    if font_file and font_file.filename:
        final_font_path = os.path.join(FONT_FOLDER, f"{uid}_{font_file.filename}")
        font_file.save(final_font_path)
    elif saved_font_name:
        final_font_path = os.path.join(FONT_FOLDER, f"{uid}_{saved_font_name}")
    
    if final_font_path and os.path.exists(final_font_path):
        font_arg = ['-attach', final_font_path, '-metadata:s:t', 'mimetype=application/x-truetype-font']

    output_filename = f"{uid}_{fname}.mkv"
    output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
    log_path = output_path + ".log"
    open(output_path, 'w').close()

    cmd = [
        'ffmpeg', '-y',
        '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '-headers', f'Referer: {url}',
        '-tls_verify', '0', '-reconnect', '1', '-reconnect_streamed', '1',
        '-i', url, '-i', sub_path
    ]
    cmd.extend(font_arg)
    cmd.extend(['-map', '0:V', '-map', '0:a', '-map', '1', '-c', 'copy', '-disposition:s:0', 'default', output_path])

    with open(log_path, "w") as log_file:
        subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)

    time.sleep(1)
    return redirect(url_for('home'))

@app.route('/download/<filename>')
def download(filename):
    clean_name = filename.split('_', 1)[1] if '_' in filename else filename
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True, download_name=clean_name)

@app.route('/delete/<filename>')
def delete(filename):
    try:
        os.remove(os.path.join(DOWNLOAD_FOLDER, filename))
        os.remove(os.path.join(DOWNLOAD_FOLDER, filename + ".log"))
    except: pass
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    
