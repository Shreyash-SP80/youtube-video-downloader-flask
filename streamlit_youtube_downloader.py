import streamlit as st
from pytube import YouTube, request
import tempfile
import os
import subprocess
from io import BytesIO
import shutil
import re
from urllib.error import HTTPError

st.set_page_config(page_title="YouTube Downloader — Dark UI", page_icon="🎬", layout="wide")

# --- Dark theme CSS ---
st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    .stApp { background: #0b0f14; color: #e6eef6; }
    .stButton>button { background-color: #1f6f8b; color: white; }
    .streamlit-expanderHeader { color: #cbd5e1; }
    .stTextInput>div>div>input { background: #111417; color: #e6eef6; }
    .stSelectbox>div>div>div { background: #111417; color: #e6eef6; }
    .stSidebar { background: #0f1720; }
    .download-button { background-color: #059669; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Utilities
def sizeof_fmt(num, suffix='B'):
    if not num:
        return "Unknown"
    for unit in ['','K','M','G','T','P']:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}P{suffix}"

_filename_cleanup_re = re.compile(r"[^0-9a-zA-Z\-_\. ]+")

def safe_filename(name):
    return _filename_cleanup_re.sub('', name).strip()

# Ensure pytube uses a browser-like user-agent (can fix some 400 errors)
request.default_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# session state
if 'yt' not in st.session_state:
    st.session_state.yt = None
if 'progress' not in st.session_state:
    st.session_state.progress = 0
if 'last_filesize' not in st.session_state:
    st.session_state.last_filesize = 0
if 'log' not in st.session_state:
    st.session_state.log = []

# callback for pytube
def on_progress(stream, chunk, bytes_remaining):
    total = stream.filesize or st.session_state.get('last_filesize', 0)
    if total:
        done = total - bytes_remaining
        pct = int(done / total * 100)
        st.session_state.progress = pct

# Sidebar
with st.sidebar:
    st.title("Options")
    st.markdown("A dark-themed YouTube downloader built with Streamlit + pytube")
    st.write("---")
    show_advanced = st.checkbox("Show advanced options", value=True)
    merge_with_ffmpeg = st.checkbox("Enable FFmpeg merge for adaptive streams", value=True)
    extract_mp3 = st.checkbox("Offer MP3 extraction when applicable", value=False)
    st.write("")
    st.caption("Only download content you have rights to. Respect YouTube Terms of Service.")

# Input
st.markdown("# 🎬 YouTube Downloader (Dark)")
col1, col2 = st.columns([8,2])
with col1:
    url = st.text_input("Enter YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")
with col2:
    fetch = st.button("Fetch")

# helper: canonicalize and validate url
_video_id_re = re.compile(r'(?:v=|v/|embed/|youtu\.be/)([A-Za-z0-9_-]{6,})')

def extract_video_id(u: str):
    m = _video_id_re.search(u)
    return m.group(1) if m else None

# Enhanced fetch logic with better error messages and retries
if fetch and url:
    vid = extract_video_id(url)
    if not vid:
        st.error("Invalid YouTube URL — couldn't find a video id. Try a full watch URL: https://www.youtube.com/watch?v=... or a youtu.be short link.")
    else:
        canonical = f"https://www.youtube.com/watch?v={vid}"
        try:
            st.session_state.progress = 0
            # wrap in try/except for HTTP errors
            st.session_state.yt = YouTube(canonical, on_progress_callback=on_progress)
            st.success(f"Fetched: {st.session_state.yt.title}")
            st.session_state.log.append(f"Fetched metadata for: {st.session_state.yt.title}")
        except HTTPError as http_err:
            # show helpful diagnostics
            st.error(f"HTTP error while fetching video: {http_err}")
            st.info("Common fixes: 1) Check the URL, 2) Update pytube (pip install --upgrade pytube), 3) Ensure your server/network can access youtube.com")
            st.session_state.yt = None
        except Exception as e:
            # pytube can throw many exceptions; show short message + hint
            st.error(f"Failed to fetch video: {e}")
            st.info("Try upgrading pytube: pip install --upgrade pytube. If the problem persists, the video might be age-restricted, region-locked, or blocked.")
            st.session_state.yt = None

# Main area
if st.session_state.yt:
    yt = st.session_state.yt
    left, right = st.columns([3,1])

    with left:
        st.subheader(yt.title)
        st.markdown(f"**Channel:** {yt.author}  •  **Duration:** {yt.length}s  •  **Views:** {yt.views}")
        with st.expander("Show description"):
            st.write(yt.description or "(no description)")

        # Build stream lists
        progressive = yt.streams.filter(progressive=True).order_by('resolution').desc()
        video_only = yt.streams.filter(only_video=True).order_by('resolution').desc()
        audio_only = yt.streams.filter(only_audio=True).order_by('abr').desc()

        # Prepare options for dropdown
        dropdown_options = []
        dropdown_map = {}

        # progressive (contains audio)
        for s in progressive:
            label = f"{s.resolution} — progressive — {s.mime_type} — {sizeof_fmt(s.filesize)}"
            dropdown_options.append(label)
            dropdown_map[label] = {'stream': s, 'type': 'progressive'}

        # adaptive video-only
        for s in video_only:
            label = f"{s.resolution} — video-only — {s.mime_type} — {sizeof_fmt(s.filesize)}"
            dropdown_options.append(label)
            dropdown_map[label] = {'stream': s, 'type': 'video-only'}

        # audio-only
        for s in audio_only:
            label = f"Audio: {s.abr} — audio-only — {s.mime_type} — {sizeof_fmt(s.filesize)}"
            dropdown_options.append(label)
            dropdown_map[label] = {'stream': s, 'type': 'audio-only'}

        if not dropdown_options:
            st.warning("No downloadable streams found.")
        else:
            choice = st.selectbox("Select quality / format", dropdown_options)

            # filename override
            filename_override = st.text_input("Optional filename (without extension)", value="")

            # merge option only appears for video-only
            chosen = dropdown_map.get(choice)
            merge_checkbox = False
            if chosen and chosen['type'] == 'video-only' and merge_with_ffmpeg:
                merge_checkbox = st.checkbox("Merge with best audio available (requires ffmpeg)", value=True)

            # Download button
            download = st.button("Start Download")

            # show progress
            if st.session_state.progress:
                st.progress(st.session_state.progress)

            if download:
                try:
                    info = dropdown_map.get(choice)
                    stream = info['stream']
                    st.info("Downloading — this may take a while for large files")

                    # Build filenames
                    base_name = filename_override.strip() or safe_filename(yt.title)

                    tmpdir = tempfile.mkdtemp()

                    # If progressive or audio-only: download single file and offer
                    if info['type'] in ('progressive', 'audio-only'):
                        out_path = stream.download(output_path=tmpdir, filename=base_name)
                        st.session_state.progress = 100

                        # If user wants MP3 and this is audio-only
                        if extract_mp3 and info['type'] == 'audio-only':
                            mp3_path = os.path.join(tmpdir, base_name + '.mp3')
                            try:
                                cmd = ['ffmpeg', '-y', '-i', out_path, '-vn', '-ab', '192k', '-ar', '44100', mp3_path]
                                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                with open(mp3_path, 'rb') as f:
                                    st.download_button(label="Download MP3", data=f, file_name=os.path.basename(mp3_path), mime='audio/mpeg')
                            except Exception:
                                with open(out_path, 'rb') as f:
                                    st.download_button(label="Download (original)", data=f, file_name=os.path.basename(out_path))
                        else:
                            with open(out_path, 'rb') as f:
                                st.download_button(label="Download file", data=f, file_name=os.path.basename(out_path))

                        # cleanup
                        try:
                            for f in os.listdir(tmpdir):
                                os.remove(os.path.join(tmpdir, f))
                            os.rmdir(tmpdir)
                        except Exception:
                            pass

                    elif info['type'] == 'video-only':
                        # download video-only stream
                        video_path = stream.download(output_path=tmpdir, filename=base_name + '.video')
                        st.session_state.log.append(f"Downloaded video-only to {video_path}")

                        if merge_checkbox:
                            # find best audio stream (highest abr)
                            best_audio = None
                            for a in audio_only:
                                if best_audio is None or (a.abr and a.abr > getattr(best_audio, 'abr', 0)):
                                    best_audio = a
                            if best_audio is None:
                                st.warning("No audio stream available to merge — offering video file only.")
                                with open(video_path, 'rb') as f:
                                    st.download_button("Download video", data=f, file_name=os.path.basename(base_name) + '.mp4')
                            else:
                                audio_path = best_audio.download(output_path=tmpdir, filename=base_name + '.audio')
                                # check ffmpeg availability
                                try:
                                    merged_path = os.path.join(tmpdir, base_name + '.mp4')
                                    cmd = [
                                        'ffmpeg', '-y', '-i', video_path, '-i', audio_path,
                                        '-c', 'copy', merged_path
                                    ]
                                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                    with open(merged_path, 'rb') as f:
                                        st.download_button("Download merged MP4", data=f, file_name=os.path.basename(merged_path))
                                except subprocess.CalledProcessError:
                                    st.error("FFmpeg merge failed — ensure ffmpeg is installed on the host.")
                                    # fallback: offer separate files
                                    with open(video_path, 'rb') as vf:
                                        st.download_button("Download video-only", data=vf, file_name=os.path.basename(base_name) + '.mp4')
                                    with open(audio_path, 'rb') as af:
                                        st.download_button("Download audio-only", data=af, file_name=os.path.basename(base_name) + '.mp3')
                                except Exception as e:
                                    st.error(f"Merge error: {e}")
                                finally:
                                    # cleanup
                                    try:
                                        for p in os.listdir(tmpdir):
                                            os.remove(os.path.join(tmpdir, p))
                                        os.rmdir(tmpdir)
                                    except Exception:
                                        pass
                        else:
                            with open(video_path, 'rb') as f:
                                st.download_button("Download video-only", data=f, file_name=os.path.basename(base_name) + '.mp4')
                            # cleanup
                            try:
                                for p in os.listdir(tmpdir):
                                    os.remove(os.path.join(tmpdir, p))
                                os.rmdir(tmpdir)
                            except Exception:
                                pass

                except Exception as e:
                    st.error(f"Download failed: {e}")

    with right:
        if yt.thumbnail_url:
            st.image(yt.thumbnail_url, use_column_width=True)
        st.write("")
        st.write("**Quick actions**")
        if st.button("Open on YouTube"):
            st.experimental_set_query_params(video=yt.watch_url)
        st.write("")
        st.write("**Log**")
        for entry in reversed(st.session_state.log[-10:]):
            st.write(f"• {entry}")

else:
    st.info("Paste a YouTube URL above and click Fetch to start.")

# Footer
st.markdown("---")
st.caption("Note: Use responsibly. This app is for educational/personal use only.")
