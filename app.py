import os
import subprocess
import time
import shutil
import uuid
from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "map_fix_2025"

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

# --- UI (Same Premium Look) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AD Web Muxer</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --primary: #7000ff; --accent: #00ccff; --bg: #0a0a0c; --card: #16161a; --text: #e0e0e0; }
        body { background-color: var(--bg); color: var(--text); font-family: 'Poppins', sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        .container { background: rgba(22, 22, 26, 0.8); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); padding: 30px; border-radius: 20px; width: 100%; max-width: 500px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); }
        h1 { font-weight: 600; text-align: center; margin-bottom: 25px; background: linear-gradient(90deg, var(--accent), var(--primary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2rem; }
        .input-group { margin-bottom: 15px; text-align: left; }
        label { font-size: 0.85rem; color: #888; margin-bottom: 5px; display: block; }
        input[type="text"] { width: 100%; padding: 12px; background: #0f0f12; border: 1px solid #333; border-radius: 8px; color: white; font-family: inherit; box-sizing: border-box; transition: 0.3s; }
        input[type="text"]:focus { border-color: var(--accent); outline: none; box-shadow: 0 0 10px rgba(0, 204, 255, 0.2); }
        .file-upload { position: relative; display: flex; align-items: center; justify-content: space-between; background: #0f0f12; border: 1px dashed #444; padding: 10px; border-radius: 8px; cursor: pointer; transition: 0.3s; }
        .file-upload:hover { border-color: var(--primary); }
        .file-upload input { position: absolute; left: 0; top: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
        .file-text { font-size: 0.9rem; color: #aaa; }
        .file-icon { color: var(--accent); font-size: 1.2rem; }
        .btn-submit { width: 100%; padding: 14px; background: linear-gradient(135deg, var(--primary), #a200ff); color: white; border: none; border-radius: 10px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: 0.3s; margin-top: 10px; box-shadow: 0 4px 15px rgba(112, 0, 255, 0.4); }
        .btn-submit:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(112, 0, 255, 0.6); }
        .divider { border-bottom: 1px solid rgba(255,255,255,0.1); margin: 30px 0; }
        .refresh-btn { background: #222; color: #aaa; border: 1px solid #333; padding: 8px 15px; border-radius: 20px; cursor: pointer; font-size: 0.8rem; transition: 0.2s; }
        .refresh-btn:hover { color: white; border-color: white; }
        .file-card { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 15px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 8px; border: 1px solid rgba(255,255,255,0.05); }
        .file-header { display: flex; justify-content: space-between; align-items: center; }
        .file-name { font-weight: 600; font-size: 0.95rem; color: #fff; word-break: break-all; }
        .status { padding: 4px 10px; border-radius: 12px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
        .status.done { background: rgba(0, 255, 136, 0.15); color: #00ff88; }
        .status.processing { background: rgba(255, 187, 0, 0.15); color: #ffbb00; animation: pulse 1.5s infinite; }
        .status.error { background: rgba(255, 50, 50, 0.15); color: #ff3232; }
        .log-box { font-family: monospace; font-size: 0.75rem; color: #ff6b6b; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px; margin-top: 5px; white-space: pre-wrap; word-break: break-word; }
        .actions { display: flex; gap: 10px; margin-top: 5px; }
        .btn-dl { flex: 1; text-align: center; background: rgba(0, 204, 255, 0.1); color: var(--accent); padding: 8px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; font-weight: 600; transition: 0.2s; }
        .btn-dl:hover { background: var(--accent); color: #000; }
        .btn-del { width: 30px; display: flex; align-items: center; justify-content: center; background: transparent; color: #666; border: 1px solid #333; border-radius: 6px; text-decoration: none; font-size: 1rem; transition: 0.2s; }
        .btn-del:hover { border-color: #ff3232; color: #ff3232; }
        @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }
    </style>
    <script>
        function updateFileName(input, id) {
            const name = input.files[0] ? input.files[0].name : "Choose File...";
            document.getElementById(id).innerText = name;
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>AD Web Muxer</h1>
        
        <form action="/start" method="POST" enctype="multipart/form-data">
            <div class="input-group">
                <label>Video URL (M3U8)</label>
                <input type="text" name="url" placeholder="Paste link..." required>
            </div>
            <div class="input-group">
                <label>Subtitle (.ASS)</label>
                <div class="file-upload">
                    <span class="file-text" id="sub-name">Choose .ASS File</span>
                    <span class="file-icon">📂</span>
                    <input type="file" name="sub" accept=".ass" required onchange="updateFileName(this, 'sub-name')">
                </div>
            </div>
            <div class="input-group">
                <label>Custom Font (Optional)</label>
                <div class="file-upload">
                    <span class="file-text" id="font-name">Choose .TTF/.OTF</span>
                    <span class="file-icon">🔤</span>
                    <input type="file" name="font" accept=".ttf,.otf" onchange="updateFileName(this, 'font-name')">
                </div>
            </div>
            <div class="input-group">
                <label>Output Filename</label>
                <input type="text" name="fname" placeholder="Episode 01" required>
            </div>
            <button type="submit" class="btn-submit">⚡ Start Processing</button>
        </form>

        <div class="divider"></div>

        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
            <span style="color:#888; font-size:0.9rem;">Recent Files</span>
            <button onclick="location.reload()" class="refresh-btn">🔄 Refresh</button>
        </div>
        
        <div>
            {% for file in files %}
                <div class="file-card">
                    <div class="file-header">
                        <span class="file-name">{{ file.name }}</span>
                        {% if file.status == 'done' %}
                            <span class="status done">Success</span>
                        {% elif file.status == 'processing' %}
                            <span class="status processing">Running</span>
                        {% else %}
                            <span class="status error">Failed</span>
                        {% endif %}
                    </div>
                    
                    {% if file.status == 'error' %}
                        <div class="log-box">{{ file.log }}</div>
                    {% endif %}

                    {% if file.status != 'processing' %}
                    <div class="actions">
                        {% if file.status == 'done' %}
                            <a href="/download/{{ file.realname }}" class="btn-dl">⬇ Download</a>
                        {% else %}
                             <div style="flex:1;"></div>
                        {% endif %}
                        <a href="/delete/{{ file.realname }}" class="btn-del">🗑</a>
                    </div>
                    {% endif %}
                </div>
            {% else %}
                <div style="text-align:center; color:#444; padding:20px; font-size:0.9rem;">
                    No files yet. Start muxing! 🚀
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    uid = get_uid()
    files_data = []
    
    if os.path.exists(DOWNLOAD_FOLDER):
        for f in sorted(os.listdir(DOWNLOAD_FOLDER)):
            if f.startswith(uid) and f.endswith(".mkv"):
                status = "done"
                log_file = os.path.join(DOWNLOAD_FOLDER, f + ".log")
                err_msg = ""

                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as lf:
                            log_content = lf.read()
                            if "Error" in log_content or "Invalid data" in log_content or "403 Forbidden" in log_content or "Server returned 40" in log_content:
                                status = "error"
                                err_msg = log_content[-300:] 
                            elif "muxing overhead" in log_content or "LSIZE" in log_content: 
                                status = "done"
                            else:
                                status = "processing"
                    except: status = "processing"
                
                display_name = f.replace(f"{uid}_", "").replace(".mkv", "")
                
                files_data.append({
                    "name": display_name,
                    "realname": f,
                    "status": status,
                    "log": err_msg
                })

    return render_template_string(HTML_CODE, files=files_data)

@app.route('/start', methods=['POST'])
def start_mux():
    uid = get_uid()
    
    url = request.form.get('url')
    fname = request.form.get('fname').strip().replace(" ", "_")
    
    sub_file = request.files.get('sub')
    sub_path = os.path.join(UPLOAD_FOLDER, f"{uid}_sub.ass")
    sub_file.save(sub_path)
    
    font_file = request.files.get('font')
    font_arg = []
    if font_file and font_file.filename:
        font_path = os.path.join(FONT_FOLDER, f"{uid}_{font_file.filename}")
        font_file.save(font_path)
        font_arg = ['-attach', font_path, '-metadata:s:t', 'mimetype=application/x-truetype-font']

    output_filename = f"{uid}_{fname}.mkv"
    output_path = os.path.join(DOWNLOAD_FOLDER, output_filename)
    log_path = output_path + ".log"

    open(output_path, 'w').close()

    # --- UPDATED COMMAND WITH STRICT MAPPING ---
    cmd = [
        'ffmpeg', '-y',
        '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '-headers', f'Referer: {url}',
        '-tls_verify', '0',
        '-protocol_whitelist', 'file,http,https,tcp,tls,crypto', 
        '-reconnect', '1', 
        '-reconnect_streamed', '1', 
        '-reconnect_delay_max', '5',
        '-i', url,
        '-i', sub_path
    ]
    
    cmd.extend(font_arg)
    
    # --- HERE IS THE FIX: Explicitly select ONLY Video:0 and Audio:0 ---
    cmd.extend([
        '-map', '0:v:0',      # Select ONLY first video stream
        '-map', '0:a:0',      # Select ONLY first audio stream
        '-map', '1',          # Select Subtitle file (input 1)
        '-c', 'copy',         # Copy without re-encoding
        '-disposition:s:0', 'default', # Make subtitle default
        output_path
    ])

    with open(log_path, "w") as log_file:
        subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)

    time.sleep(1)
    return redirect(url_for('home'))

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete(filename):
    try:
        os.remove(os.path.join(DOWNLOAD_FOLDER, filename))
        os.remove(os.path.join(DOWNLOAD_FOLDER, filename + ".log"))
    except: pass
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
