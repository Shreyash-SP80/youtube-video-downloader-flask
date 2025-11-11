# YouTube Downloader — Flask + yt-dlp

A lightweight Flask web application that lets you download YouTube videos and audio using `yt-dlp`.  
Includes a modern single-page UI, multiple quality options, and optional FFmpeg support for merging video+audio and exporting MP3 audio.

> NOTE: This tool downloads content from YouTube for personal use. Respect YouTube's Terms of Service and copyright law. Do not download content you do not have the right to download.

---

## Features

- Paste a YouTube URL and download:
  - Best available single-file MP4 (no FFmpeg required)
  - Best quality (video + audio merged) — requires FFmpeg
  - Specific resolutions (1080p, 720p, 480p, 360p)
  - Audio-only MP3 conversion — requires FFmpeg
- Frontend shows FFmpeg availability and disables/annotates options accordingly
- Simple `/download` API that returns filename and triggers browser download
- Downloads are stored in a `downloads/` folder

---

## Repository name
`youtube-downloader-flask-yt-dlp`

---

## Quick Start (local)

### Requirements
- Python 3.8+
- `ffmpeg` (optional — required for merging and mp3 conversion)
- `pip`

### Install dependencies
Create a virtual environment (recommended):

```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
