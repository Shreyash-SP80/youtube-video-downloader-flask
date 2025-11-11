from flask import Flask, render_template_string, request, send_file, jsonify
import yt_dlp
import os
from pathlib import Path
import shutil

app = Flask(__name__)

# Create downloads folder if it doesn't exist
DOWNLOAD_FOLDER = 'downloads'
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)

# Check if ffmpeg is available
def is_ffmpeg_available():
    return shutil.which('ffmpeg') is not None

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            max-width: 600px;
            width: 100%;
        }
        
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .warning-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            display: none;
        }
        
        .warning-box.show {
            display: block;
        }
        
        .warning-box h3 {
            color: #856404;
            margin-bottom: 8px;
            font-size: 16px;
        }
        
        .warning-box p {
            color: #856404;
            font-size: 13px;
            line-height: 1.5;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 600;
            font-size: 14px;
        }
        
        input[type="text"], select {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 15px;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        select {
            cursor: pointer;
            background-color: white;
        }
        
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .message {
            margin-top: 20px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            display: none;
        }
        
        .message.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .message.info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .loading {
            text-align: center;
            margin-top: 20px;
            display: none;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .quality-note {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📹 YouTube Downloader</h1>
        <p class="subtitle">Download your favorite videos in high quality</p>
        
        <div class="warning-box" id="ffmpegWarning">
            <h3>⚠️ FFmpeg Not Detected</h3>
            <p>High quality formats require FFmpeg. Please install FFmpeg or use "Best Available (Single File)" option.</p>
        </div>
        
        <form id="downloadForm">
            <div class="form-group">
                <label for="url">YouTube Video URL</label>
                <input type="text" id="url" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
            </div>
            
            <div class="form-group">
                <label for="quality">Select Quality</label>
                <select id="quality" name="quality" required>
                    <option value="single_best">Best Available (Single File) - No FFmpeg Required</option>
                    <option value="best">Best Quality (Video + Audio) - Requires FFmpeg</option>
                    <option value="1080p">1080p (Full HD) - Requires FFmpeg</option>
                    <option value="720p">720p (HD) - Requires FFmpeg</option>
                    <option value="480p">480p (SD)</option>
                    <option value="360p">360p (Low)</option>
                    <option value="audio">Audio Only (MP3) - Requires FFmpeg</option>
                </select>
                <div class="quality-note" id="qualityNote"></div>
            </div>
            
            <button type="submit" id="downloadBtn">Download Video</button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px; color: #667eea;">Processing your download...</p>
        </div>
        
        <div class="message" id="message"></div>
    </div>
    
    <script>
        const form = document.getElementById('downloadForm');
        const message = document.getElementById('message');
        const loading = document.getElementById('loading');
        const downloadBtn = document.getElementById('downloadBtn');
        const qualitySelect = document.getElementById('quality');
        const qualityNote = document.getElementById('qualityNote');
        
        // Check FFmpeg availability on page load
        fetch('/check-ffmpeg')
            .then(res => res.json())
            .then(data => {
                if (!data.available) {
                    document.getElementById('ffmpegWarning').classList.add('show');
                }
            });
        
        qualitySelect.addEventListener('change', (e) => {
            const value = e.target.value;
            const requiresFFmpeg = ['best', '1080p', '720p', 'audio'].includes(value);
            
            if (requiresFFmpeg) {
                qualityNote.textContent = '⚠️ This option requires FFmpeg to be installed';
                qualityNote.style.color = '#dc3545';
            } else {
                qualityNote.textContent = '✓ Works without FFmpeg';
                qualityNote.style.color = '#28a745';
            }
        });
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const url = document.getElementById('url').value;
            const quality = document.getElementById('quality').value;
            
            // Reset UI
            message.style.display = 'none';
            loading.style.display = 'block';
            downloadBtn.disabled = true;
            
            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url, quality })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showMessage('success', data.message);
                    
                    // Trigger download
                    window.location.href = `/get-file/${data.filename}`;
                } else {
                    showMessage('error', data.error || 'Download failed');
                }
            } catch (error) {
                showMessage('error', 'An error occurred. Please try again.');
            } finally {
                loading.style.display = 'none';
                downloadBtn.disabled = false;
            }
        });
        
        function showMessage(type, text) {
            message.className = 'message ' + type;
            message.textContent = text;
            message.style.display = 'block';
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/check-ffmpeg')
def check_ffmpeg():
    return jsonify({'available': is_ffmpeg_available()})

@app.route('/download', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url')
        quality = data.get('quality')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Check if FFmpeg is required and available
        requires_ffmpeg = quality in ['best', '1080p', '720p', 'audio']
        if requires_ffmpeg and not is_ffmpeg_available():
            return jsonify({
                'error': 'FFmpeg is not installed. Please install FFmpeg or use "Best Available (Single File)" option.'
            }), 400
        
        # Configure yt-dlp options based on quality
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }
        
        if quality == 'single_best':
            # Download best single file format (no merging required)
            ydl_opts['format'] = 'best[ext=mp4]/best'
        elif quality == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        elif quality == 'best':
            ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == '1080p':
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == '720p':
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            ydl_opts['merge_output_format'] = 'mp4'
        elif quality == '480p':
            ydl_opts['format'] = 'best[height<=480]/best'
        elif quality == '360p':
            ydl_opts['format'] = 'best[height<=360]/best'
        
        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Handle audio conversion filename change
            if quality == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            
            # Get just the filename without path
            filename = os.path.basename(filename)
        
        return jsonify({
            'message': 'Download completed successfully!',
            'filename': filename
        })
        
    except Exception as e:
        error_message = str(e)
        if 'ffmpeg' in error_message.lower():
            error_message = 'FFmpeg is required for this quality. Please install FFmpeg or choose a different quality option.'
        return jsonify({'error': error_message}), 500

@app.route('/get-file/<filename>')
def get_file(filename):
    try:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    print("=" * 50)
    print("YouTube Video Downloader")
    print("=" * 50)
    if is_ffmpeg_available():
        print("✓ FFmpeg detected - All quality options available")
    else:
        print("⚠ FFmpeg not detected - Limited quality options")
        print("  Install FFmpeg for best quality downloads")
    print("=" * 50)
    print("Server starting at http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000);