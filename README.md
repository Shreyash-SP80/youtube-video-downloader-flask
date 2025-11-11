# 🎬 YouTube Downloader — Flask + yt-dlp

A modern, easy-to-use **YouTube video and audio downloader** built with **Flask** and **yt-dlp**.  
No setup hassle — just run locally and download videos in multiple qualities, with or without FFmpeg.

---

## 🚀 Features

- 🎥 Download YouTube videos in multiple qualities:
  - 1080p / 720p / 480p / 360p
  - Best available (auto-detect)
  - Audio-only (MP3)
- ⚙️ Works even without FFmpeg (basic quality)
- 🧠 Automatically detects if FFmpeg is available
- 🌈 Beautiful modern UI with loading spinner, quality hints, and error messages
- 🗂️ Downloads stored locally in a `downloads/` folder

---

## 📦 Repository name
```
    youtube-downloader-flask-yt-dlp
```

## 📝 Short Description
A Flask web app that uses yt-dlp to download YouTube videos and audio with FFmpeg support and a clean, modern interface.


---

## 🧰 Requirements

- Python 3.8 or newer
- `pip`
- (Optional but recommended) FFmpeg

---

## 🪄 Quick Setup

### 1️⃣ Clone or download this repository

```bash
    git clone https://github.com/<your-username>/youtube-downloader-flask-yt-dlp.git
    cd youtube-downloader-flask-yt-dlp
```

## 2️⃣ Create a virtual environment (recommended)

Before installing dependencies, it’s best to create a Python virtual environment.

```bash
    python -m venv venv
    # Windows PowerShell
    .\venv\Scripts\Activate.ps1
    # or Command Prompt
    venv\Scripts\activate
```

## 3️⃣ Install dependencies
```
    pip install -r requirements.txt
```

## 📄 requirements.txt
```
    Flask>=2.0
    yt-dlp>=2023.0.0
```

## 🧩 Easiest Solution — Manual FFmpeg Installation (No Admin Required!)

Follow these quick steps 👇

### 🪜 Step 1: Download FFmpeg

1. Go to 👉 [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)
2. Click **"ffmpeg-release-essentials.zip"** (around 75 MB)
3. Download and extract the ZIP file

---

### 🪜 Step 2: Place FFmpeg in Your Project

1. After extracting, you’ll see a folder like:
```
    ffmpeg-7.x-essentials_build
```

2. Open that folder → go into the `bin` directory  
3. Copy these three files:
```
    ffmpeg.exe
    ffplay.exe
    ffprobe.exe
```

4. Paste them directly in your **project folder (same folder as `app.py`)**

✅ That’s it — no admin rights, no PATH setup required!

---

> 💡 **Tip:** Once copied, your project folder should look like this:
> ```
> youtube-downloader-flask-yt-dlp/
> ├── app.py
> ├── ffmpeg.exe
> ├── ffplay.exe
> ├── ffprobe.exe
> ├── requirements.txt
> ├── README.md
> └── downloads/
> ```
      
