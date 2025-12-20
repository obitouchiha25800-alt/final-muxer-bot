import os
import subprocess
import time
import shutil
import uuid
import re
from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "ultimate_vibe_final_2025"

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
                h, m, s = t.split(':')
                return int(h) * 3600 + int(m) * 60 + float(s)
            
            total_sec = to_sec(total_str)
            current_sec = to_sec(current_str)
            
            if total_sec > 0:
                percent = int((current_sec / total_sec) * 100)
                return min(percent, 100)
    except:
        pass
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
        :root { --primary: #7000ff; --accent: #00ccff; --bg: #0a0a0c; --card: #16161a; --text: #e0e0e0; }
        * { box-sizing: border-box; }
        body { background-color: var(--bg); color: var(--text); font-family: 'Poppins', sans-serif; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; min-height: 100vh; }
        
        .container { background: rgba(22, 22, 26, 0.9); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); padding: 30px; border-radius: 20px; width: 100%; max-width: 500px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); }
        
        h1 { font-weight: 600; text-align: center; margin-bottom: 25px; background: linear-gradient(90deg, var(--accent), var(--primary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2rem; }
        
        @media (max-width: 600px) {
            body { padding: 10px; }
            .container { padding: 20px 15px; border-radius: 16px; }
            h1 { font-size: 1.8rem; margin-bottom: 20px; }
            .btn-submit { padding: 12px; font-size: 0.95rem; }
            .input-group { margin-bottom: 12px; }
        }

        .input-group { margin-bottom: 15px; text-align: left; }
        label { font-size: 0.85rem; color: #888; margin-bottom: 5px; display: block; }
        input[type="text"], select { width: 100%; padding: 12px; background: #0f0f12; border: 1px solid #333; border-radius: 8px; color: white; font-family: inherit; font-size: 0.9rem; transition: 0.3s; }
        input[type="text"]:focus, select:focus { border-color: var(--accent); outline: none; }
        
        .file-upload { position: relative; display: flex; align-items: center; justify-content: space-between; background: #0f0f12; border: 1px dashed #444; padding: 10px; border-radius: 8px; cursor: pointer; transition: 0.3s; }
        .file-upload:hover { border-color: var(--primary); }
        .file-upload input { position: absolute; left: 0; top: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
        .file-text { font-size: 0.85rem; color: #aaa; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 70%; }
        .file-icon { color: var(--accent); font-size: 1.2rem; }

        .btn-submit { width: 100%; padding: 14px; background: linear-gradient(135deg, var(--primary), #a200ff); color: white; border: none; border-radius: 10px; font-weight: 600; font-size: 1rem; cursor: pointer; transition: 0.3s; margin-top: 10px; box-shadow: 0 4px 15px rgba(112, 0, 255, 0.4); }
        .btn-submit:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(112, 0, 255, 0.6); }
        
        .divider { border-bottom: 1px solid rgba(255,255,255,0.1); margin: 25px 0; }
        .refresh-btn { background: #222; color: #aaa; border: 1px solid #333; padding: 6px 12px; border-radius: 20px; cursor: pointer; font-size: 0.75rem; transition: 0.2s; }
        .refresh-btn:hover { color: white; border-color: white; }

        .file-card { background: rgba(255,255,255,0.03); border-radius: 12px; padding: 15px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 8px; border: 1px solid rgba(255,255,255,0.05); }
        .file-header { display: flex; justify-content: space-between; align-items: center; }
        .file-name { font-weight: 600; font-size: 0.9rem; color: #fff; word-break: break-all; }
        
        .status { padding: 4px 10px; border-radius: 12px; font-size: 0.7rem; font-weight: bold; text-transform: uppercase; }
        .status.done { background: rgba(0, 255, 136, 0.15); color: #00ff88; }
        .status.processing { background: rgba(255, 187, 0, 0.15); color: #ffbb00; }
        .status.error { background: rgba(255, 50, 50, 0.15); color: #ff3232; }
        
        .progress-track { width: 100%; height: 6px; background: #222; border-radius: 4px; overflow: hidden; margin-top: 5px; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent), var(--primary)); width: 0%; transition: width 0.5s ease; border-radius: 4px; box-shadow: 0 0 10px var(--accent); }
        .progress-text { font-size: 0.7rem; color: #aaa; text-align: right; margin-top: 2px; }

        .log-box { font-family: monospace; font-size: 0.7rem; color: #aaa; background: rgba(0,0,0,0.5); padding: 8px; border-radius: 6px; margin-top: 5px; white-space: pre-wrap; word-break: break-word; max-height: 100px; overflow-y: auto; }
        
        .actions { display: flex; gap: 8px; margin-top: 5px; }
        .btn-dl { flex: 2; text-align: center; background: rgba(0, 204, 255, 0.1); color: var(--accent); padding: 8px; border-radius: 6px; text-decoration: none; font-size: 0.85rem; font-weight: 600; transition: 0.2s; }
        .btn-dl:hover { background: var(--accent); color: #000; }
        .btn-copy { flex: 1; border: 1px solid #444; background: transparent; color: #ccc; border-radius: 6px; cursor: pointer; transition: 0.2s; font-size: 0.85rem; }
        .btn-copy:hover { border-color: var(--primary); color: var(--primary); }
        .btn-del { width: 32px; display: flex; align-items: center; justify-content: center; background: transparent; color: #666; border: 1px solid #333; border-radius: 6px; text-decoration: none; font-size: 1rem; transition: 0.2s; }
        .btn-del:hover { border-color: #ff3232; color: #ff3232; }
        
        /* Auto Refresh Timer Style */
        #auto-refresh-timer { font-size: 0.75rem; color: var(--accent); margin-left: 10px; display:none; animation: pulse 1s infinite; }
        @keyframes pulse { 0% { opacity: 0.7; } 50% { opacity: 1; } 100% { opacity: 0.7; } }
    </style>
    <script>
        function updateFileName(input, id) {
            const name = input.files[0] ? input.files[0].name : "Choose File...";
            document.getElementById(id).innerText = name;
        }
        function copyLink(filename) {
            const link = window.location.origin + "/download/" + filename;
            navigator.clipboard.writeText(link).then(() => {
                alert("✅ Link Copied!\\n" + link);
            }).catch(err => {
                prompt("Copy this link:", link);
            });
        }
        
        // --- SMART AUTO REFRESH LOGIC ---
        document.addEventListener('DOMContentLoaded', function() {
            const processingItems = document.querySelectorAll('.status.processing');
            // Agar koi file processing mein hai, tabhi refresh karega
            if (processingItems.length > 0) {
                const timerSpan = document.getElementById('auto-refresh-timer');
                if(timerSpan) {
                    timerSpan.style.display = 'inline';
                    let timeLeft = 5; // 5 seconds timer
                    timerSpan.innerText = "⟳ Refresh: " + timeLeft + "s";
                    
                    const interval = setInterval(() => {
                        timeLeft--;
                        timerSpan.innerText = "⟳ Refresh: " + timeLeft + "s";
                        if (timeLeft <= 0) {
                            clearInterval(interval);
                            location.reload();
                        }
                    }, 1000);
                }
            }
        });
    </script>
</head>
<body>
    <div class="container">
        <h1>AD Web Muxer !!</h1>
        
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
                <label>Font (Saved or New)</label>
                {% if saved_fonts %}
                <select name="saved_font" style="margin-bottom: 8px;">
                    <option value="">-- Select Saved Font --</option>
                    {% for font in saved_fonts %}
                        <option value="{{ font }}">{{ font }}</option>
                    {% endfor %}
                </select>
                <div style="text-align:center; font-size:0.75rem; color:#555; margin-bottom:8px;">OR</div>
                {% endif %}
                <div class="file-upload">
                    <span class="file-text" id="font-name">Upload New .TTF/.OTF</span>
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
            <div style="display:flex; align-items:center;">
                <span style="color:#888; font-size:0.85rem;">Recent Files</span>
                <span id="auto-refresh-timer"></span>
            </div>
            <button onclick="location.reload()" class="refresh-btn">🔄 Status</button>
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
                    
                    {% if file.status == 'processing' %}
                        <div class="progress-track">
                            <div class="progress-fill" style="width: {{ file.percent }}%;"></div>
                        </div>
                        <div class="progress-text">{{ file.percent }}% Processed</div>
                    {% endif %}
                    
                    {% if file.status == 'error' or file.status == 'processing' %}
                        <div class="log-box">{{ file.log }}</div>
                    {% endif %}

                    {% if file.status != 'processing' %}
                    <div class="actions">
                        {% if file.status == 'done' %}
                            <a href="/download/{{ file.realname }}" class="btn-dl">⬇ Download</a>
                            <button onclick="copyLink('{{ file.realname }}')" class="btn-copy">📋 Copy</button>
                        {% else %}
                             <div style="flex:1;"></div>
                        {% endif %}
                        <a href="/delete/{{ file.realname }}" class="btn-del">🗑</a>
                    </div>
                    {% endif %}
                </div>
            {% else %}
                <div style="text-align:center; color:#444; padding:20px; font-size:0.85rem;">
                    No files yet. Start muxing! 🚀
                </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

Ab tension free ho ja. **Old file backup hai, New file features ke saath hai.**
Backup plan ready hai, toh darr kis baat ka? Laga de deploy pe! 🚀🔥
