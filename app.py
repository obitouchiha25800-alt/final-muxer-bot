import os
import subprocess
import time
import shutil
import uuid
from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for, jsonify, session

app = Flask(__name__)
app.secret_key = "debug_mode_2025"

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

# --- HTML UI ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <title>AD Web Muxer (Debug)</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #121212; color: #fff; font-family: sans-serif; padding: 20px; text-align: center; }
        input, select, button { width: 100%; padding: 12px; margin: 10px 0; border-radius: 5px; border: 1px solid #333; background: #1e1e1e; color: white; }
        button { background: #007bff; border: none; font-weight: bold; cursor: pointer; }
        button:hover { background: #0056b3; }
        .file-box { background: #1e1e1e; padding: 15px; margin-top: 10px; border-radius: 8px; text-align: left; }
        a { color: #4CAF50; text-decoration: none; font-weight: bold; font-size: 18px; }
        .error-box { background: #330000; color: #ff9999; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; margin-top: 5px; white-space: pre-wrap; }
        h3 { border-bottom: 1px solid #333; padding-bottom: 10px; }
    </style>
</head>
<body>
    <h2>⚡ AD Web Muxer (Debug Mode)</h2>
    
    <form action="/start" method="POST" enctype="multipart/form-data">
        <input type="text" name="url" placeholder="Paste M3U8 Link Here" required>
        <input type="file" name="sub" accept=".ass" required>
        <input type="file" name="font" accept=".ttf,.otf" placeholder="Upload Font (Optional)">
        <input type="text" name="fname" placeholder="Output Filename (e.g. Episode 01)" required>
        <button type="submit">🚀 Start Processing</button>
    </form>

    <h3>📂 Your Files</h3>
    <button onclick="location.reload()" style="background:#333; width:auto; padding:5px 15px;">Refresh List</button>
    
    <div id="file-list">
        {% for file in files %}
            <div class="file-box">
                <div style="font-size:18px;">📄 {{ file.name }}</div>
                {% if file.status == 'done' %}
                    <a href="/download/{{ file.realname }}">⬇️ Download Now</a>
                {% elif file.status == 'processing' %}
                    <span style="color:orange;">⏳ Processing... (Click Refresh)</span>
                {% else %}
                    <span style="color:red;">❌ FAILED</span>
                    <div class="error-box">LOG: {{ file.log }}</div>
                {% endif %}
                <br>
                <a href="/delete/{{ file.realname }}" style="color:#aaa; font-size:12px; float:right;">🗑️ Delete</a>
            </div>
        {% else %}
            <p style="color:#777;">No files found.</p>
        {% endfor %}
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
                            # Check for common failure keywords
                            if "Error" in log_content or "Invalid data" in log_content or "403 Forbidden" in log_content or "Server returned 40" in log_content:
                                status = "error"
                                # GRAB THE LAST 300 CHARACTERS OF LOG TO SHOW USER
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

    # --- FIXED COMMAND LIST WITH PROTOCOL WHITELIST ---
    cmd = [
        'ffmpeg', '-y',
        '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '-headers', f'Referer: {url}',
        '-tls_verify', '0',
        '-protocol_whitelist', 'file,http,https,tcp,tls,crypto',  # ADDED THIS!
        '-reconnect', '1', 
        '-reconnect_streamed', '1', 
        '-reconnect_delay_max', '5',
        '-i', url,
        '-i', sub_path
    ]
    
    cmd.extend(font_arg)
    
    cmd.extend([
        '-map', '0', 
        '-map', '1', 
        '-c', 'copy', 
        '-disposition:s:0', 'default',
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
