import streamlit as st
from pathlib import Path
import tempfile, time, os
import shutil
from typing import Optional, Dict, Any

st.set_page_config(
    page_title="FB Video Downloader", 
    page_icon="assets/fb_downloader.png", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===================== CSS (đã thêm fix viền đỏ cho button) =====================
st.markdown("""
<style>
    /* CSS Variables for theme-responsive colors */
    :root {
        --text-color: #333333;
    }
    
    /* Dark theme support */
    @media (prefers-color-scheme: dark) {
        :root {
            --text-color: #ffffff;
        }
    }
    
    /* Streamlit dark theme class override */
    .stApp[data-theme="dark"] {
        --text-color: #ffffff;
    }
    
    .stApp[data-theme="light"] {
        --text-color: #333333;
    }

    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(0deg, #0088F8 0%, #006FCB 100%);
        color: white;
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 10px 10px 10px 10px;
    }

    /* Style nút mặc định */
    .stDownloadButton > button {
        width: 100%;
        background: linear-gradient(0deg, #2B79C2 0%, #006FCB 100%) !important;
        color: white !important;
        border-radius: 20px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        border: 1px solid transparent !important; /* FIX viền */
        outline: none !important;                 /* FIX viền */
        box-shadow: none !important;              /* FIX viền */
        -webkit-appearance: none;                 /* Safari */
        text-align: center;
    }
    .stDownloadButton > button:hover { filter: brightness(1.05); }
    .stDownloadButton > button:focus,
    .stDownloadButton > button:focus-visible,
    .stDownloadButton > button:active {
        outline: none !important;
        box-shadow: none !important;
        border: 1px solid transparent !important;
    }
    .stDownloadButton > button::-moz-focus-inner { border: 0 !important; }

    .preview-wrap {
        height: 500px; 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        border: 1px solid #402031D; 
        border-radius: 10px; 
        overflow: hidden; 
        background-color: #2b2b2b;
    }
    input::placeholder { font-style: italic; color: #999; }
</style>
""", unsafe_allow_html=True)

# ===================== HEADER =====================
st.markdown("""
<div class="main-header">
    <h1>FB Video Downloader</h1>
    <p>Fast and secure Facebook video downloader</p>
</div>
""", unsafe_allow_html=True)

# ===================== STATE =====================
if 'video_info' not in st.session_state:
    st.session_state.video_info = None
if 'formats' not in st.session_state:
    st.session_state.formats = []
if 'download_completed' not in st.session_state:
    st.session_state.download_completed = False
if 'downloaded_file' not in st.session_state:
    st.session_state.downloaded_file = None
if 'current_url' not in st.session_state:
    st.session_state.current_url = ""
# NEW: giữ log giữa các lần rerun
if 'detailed_logs' not in st.session_state:
    st.session_state.detailed_logs = []
# Track temp files để cleanup
if 'temp_files' not in st.session_state:
    st.session_state.temp_files = []

# ===================== IMPORT =====================
try:
    import yt_dlp as ytdlp
except Exception as e:
    st.error("Missing dependency `yt-dlp`. Please install with `pip install -r requirements.txt` and rerun.")
    st.stop()

# ===================== TEMP FILE CLEANUP =====================
def cleanup_temp_files():
    """Clean up temporary files"""
    for temp_file in st.session_state.temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            pass  # Ignore errors
    st.session_state.temp_files.clear()

# Initialize session flag
if 'session_initialized' not in st.session_state:
    st.session_state.session_initialized = True
    # Cleanup any existing temp files from previous sessions
    cleanup_temp_files()

# ===================== DEFAULTS =====================
rate_limit = None
retries = 10
concurrent_frags = 1
proxy = None
no_check_cert = True

# ===================== INPUT URL =====================
st.markdown("### Enter Video URL")
url = st.text_input(
    "ⓕ Facebook video Url:", 
    placeholder="https://www.facebook.com/reel/...", 
    help="Paste your Facebook video or reel URL here and press Enter",
    key="url_input",
)

# ===================== GET INFO =====================
def get_video_info(video_url, max_retries=3):
    """Get video info with retry logic for Facebook parsing errors"""
    for attempt in range(max_retries):
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "listformats": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9"
                }
            }
            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info
        except Exception as e:
            error_msg = str(e)
            if "Cannot parse data" in error_msg and attempt < max_retries - 1:
                st.warning(f"⚠️ Attempt {attempt + 1} failed. Retrying... ({attempt + 2}/{max_retries})")
                time.sleep(2)
                continue
            elif "Cannot parse data" in error_msg:
                st.error("❌ Facebook changed their page structure. Please try again in a few moments or use a different video URL.")
                with st.expander("🔧 Troubleshooting Tips"):
                    st.markdown("""
                    - **Refresh the page** and try again
                    - **Copy the URL again** from Facebook
                    - **Try a different video** to test if the issue is specific
                    - **Wait a few minutes** - Facebook sometimes blocks requests temporarily
                    """)
            else:
                st.error(f"❌ Failed to get video info: {error_msg}")
            return None
    return None

# ===================== HELPERS =====================
def ensure_download_dir(path_tmpl: str):
    p = Path(path_tmpl)
    if "%(" in path_tmpl:
        base = Path(path_tmpl.split("%(")[0]).expanduser()
        if base and str(base).strip() and not base.exists():
            base.mkdir(parents=True, exist_ok=True)
    else:
        Path(path_tmpl).parent.mkdir(parents=True, exist_ok=True)

def build_opts(
    outtmpl: str,
    cookies_path: Optional[str],
    fmt: str,
    rate_limit: Optional[str],
    concurrent_fragments: Optional[int],
    retries: int,
    proxy: Optional[str],
    no_check_certificate: bool = False,
    is_audio_only: bool = False
) -> Dict[str, Any]:
    ffmpeg_path = shutil.which("ffmpeg")
    opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "restrictfilenames": False,
        "ignoreerrors": False,
        "noprogress": False,
        "consoletitle": False,
        "nocheckcertificate": no_check_certificate,
        "source_address": None,
        "retries": retries,
        "fragment_retries": retries,
        "continuedl": True,
        "concurrent_fragment_downloads": concurrent_fragments or 1,
        "ratelimit": None,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        },
        "format": fmt,
        "quiet": False,
        "no_warnings": False,
    }
    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path

    if is_audio_only:
        opts["postprocessors"] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        opts["merge_output_format"] = "mp3"
    else:
        if "+" in fmt and ffmpeg_path:
            opts["postprocessors"] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
            opts["merge_output_format"] = "mp4"

    if rate_limit: opts["ratelimit"] = rate_limit
    if cookies_path: opts["cookiefile"] = cookies_path
    if proxy: opts["proxy"] = proxy
    return opts

last_percent = 0
file_out = None

# Dùng logs trong session để không mất khi rerun
error_logs = st.session_state.detailed_logs

def progress_hook(d):
    global last_percent, file_out
    if d.get("status") == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
        downloaded = d.get("downloaded_bytes") or 0
        percent = 0 if total == 0 else int(downloaded * 100 / total)
        if percent != last_percent:
            progress.progress(min(percent, 100), text=f"Downloading... {percent}%")
            last_percent = percent
        spd = d.get("speed")
        eta = d.get("eta")
        status_text = f"{percent}% | {(spd and f'{spd/1024/1024:.2f} MB/s') or '–'} | ETA: {eta or '–'} s"
        log_area.info(status_text)
        error_logs.append(f"PROGRESS: {status_text}")
    elif d.get("status") == "finished":
        file_out = d.get("filename")
        progress.progress(100, text="Processing & finalizing...")
        msg = "Processing & converting video format..."
        log_area.info(msg)
        error_logs.append(f"INFO: {msg}")

# Auto-download khi URL đổi
if url and url.strip() and url.strip() != st.session_state.current_url:
    # Cleanup temp files từ lần trước
    cleanup_temp_files()
    
    st.session_state.download_completed = False
    st.session_state.downloaded_file = None
    st.session_state.current_url = url.strip()
    
    # Nếu muốn mỗi URL là log mới, uncomment dòng dưới:
    st.session_state.detailed_logs.clear()

    with st.spinner("Getting video information..."):
        video_info = get_video_info(url.strip())

    if video_info:
        st.session_state.video_info = video_info
        formats = video_info.get('formats', [])

        unique_formats = {}
        for f in formats:
            if f.get('vcodec') != 'none' and f.get('height'):
                height = f.get('height', 0)
                ext = f.get('ext', 'mp4')
                filesize = f.get('filesize') or 0
                fps = f.get('fps') or 0
                has_audio = f.get('acodec') != 'none'

                key = f"{height}p-{ext.upper()}"
                current_filesize = unique_formats.get(key, {}).get('filesize', 0) or 0

                if key not in unique_formats or filesize > current_filesize:
                    quality_label = f"{height}p - {ext.upper()}"
                    if fps > 0: quality_label += f" ({fps}fps)"
                    if has_audio: quality_label += " 🔊"
                    if filesize > 0:
                        size_mb = filesize / (1024*1024)
                        quality_label += f" (~{size_mb:.1f}MB)"

                    unique_formats[key] = {
                        'format_id': f.get('format_id'),
                        'label': quality_label,
                        'height': height,
                        'ext': ext,
                        'filesize': filesize,
                        'has_audio': has_audio
                    }

        video_formats = list(unique_formats.values())
        video_formats.sort(key=lambda x: (x['has_audio'], x['height'], x['filesize']), reverse=True)
        st.session_state.formats = video_formats

# ===================== RETRY SECTION =====================
if url and url.strip() and not st.session_state.video_info:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("⚠️ Failed to load video information. This might be due to Facebook's anti-bot protection or temporary server issues.")
        col_retry1, col_retry2 = st.columns(2)
        with col_retry1:
            if st.button("🔄 Retry Loading", use_container_width=True):
                st.session_state.current_url = ""
                st.rerun()
        with col_retry2:
            if st.button("🗑️ Clear & Start Over", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith(('video_info', 'formats', 'download_', 'current_url')):
                        del st.session_state[key]
                st.rerun()

# ===================== UI PREVIEW & OPTIONS =====================
if st.session_state.video_info:
    info = st.session_state.video_info

    status_placeholder = st.empty()
    if st.session_state.download_completed:
        status_placeholder.success("✅ Video loaded successfully!")
    else:
        status_placeholder.info("✨ Preparing to processing & converting video format...")

    # placeholders cho tiến trình & log
    log_area = st.empty()
    progress = st.empty()

    col_left, col_right = st.columns([1, 1])

    with col_left:
        if info.get('thumbnail'):
            try:
                preview_url = None
                if info.get('formats'):
                    video_formats = [f for f in info.get('formats', []) if f.get('vcodec') != 'none' and f.get('url')]
                    if video_formats:
                        video_formats.sort(key=lambda x: x.get('height', 0) or 0)
                        preview_url = video_formats[0].get('url')
                if preview_url:
                    st.markdown(f"""
                    <div class="preview-wrap">
                        <video 
                            controls 
                            controlslist="nodownload" 
                            oncontextmenu="return false;" 
                            style="max-width: 100%; max-height: 100%; object-fit: contain;" 
                            poster="{info.get('thumbnail', '')}"
                            preload="metadata"
                        >
                            <source src="{preview_url}" type="video/mp4">
                            <p style="color:#ccc;">Your browser does not support the video tag.</p>
                        </video>
                    </div>
                    <p style="text-align:center; color:#ccc; font-size:0.9em; margin-top:6px;">Video Preview</p>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="preview-wrap">
                        <img src="{info.get('thumbnail','')}" style="max-width:100%; max-height:100%; object-fit:contain;" />
                    </div>
                    <p style="text-align:center; color:#ccc; font-size:0.9em; margin-top:6px;">Video Thumbnail (Preview not available)</p>
                    """, unsafe_allow_html=True)
            except:
                st.info("No thumbnail available")

    # Generate custom filename based on platform and video type
    def generate_custom_filename(url, video_info, is_audio, selected_format=None):
        video_id = video_info.get('id', 'unknown')
        ext = 'mp3' if is_audio else 'mp4'
        
        # Get quality info
        quality_suffix = ""
        if not is_audio and selected_format:
            height = selected_format.get('height', 0)
            if height:
                quality_suffix = f"_{height}p"
        elif is_audio:
            quality_suffix = "_audio"
        
        # Generate filename without path
        filename = ""
        if 'facebook.com' in url:
            if '/reel/' in url:
                filename = f"fb_reel_{video_id}{quality_suffix}.{ext}"
            else:
                filename = f"fb_video_{video_id}{quality_suffix}.{ext}"
        elif 'youtu' in url or 'youtube.com' in url:
            # Detect YouTube Shorts more accurately
            is_short = False
            
            # Method 1: Check URL patterns
            if '/shorts/' in url or 'youtube.com/shorts/' in video_info.get('webpage_url', ''):
                is_short = True
            
            # Method 2: Check duration (shorts are max 60 seconds) 
            duration = video_info.get('duration', 0)
            if not is_short and duration and duration <= 60:
                # Additional check: aspect ratio or other metadata
                formats = video_info.get('formats', [])
                for fmt in formats:
                    height = fmt.get('height', 0)
                    width = fmt.get('width', 0)
                    # Portrait orientation often indicates Shorts
                    if height and width and height > width:
                        is_short = True
                        break
            
            if is_short:
                filename = f"ytb_short_{video_id}{quality_suffix}.{ext}"
            else:
                filename = f"ytb_video_{video_id}{quality_suffix}.{ext}"
        else:
            # Fallback for other platforms
            filename = f"video_{video_id}{quality_suffix}.{ext}"
        
        # Create temp file path và track nó
        temp_file = os.path.join(tempfile.gettempdir(), filename)
        if temp_file not in st.session_state.temp_files:
            st.session_state.temp_files.append(temp_file)
        
        return temp_file

    with col_right:
        download_type = st.selectbox("**Type:**", ["Video + Audio", "Audio Only"], index=0)

        if download_type == "Video + Audio":
            if st.session_state.formats:
                format_labels = [f['label'] for f in st.session_state.formats]
                selected_idx = st.selectbox("**Quality:**", range(len(format_labels)),
                                            format_func=lambda x: format_labels[x], index=0)
                selected_format = st.session_state.formats[selected_idx]
                ffmpeg_path = shutil.which("ffmpeg")
                if selected_format['has_audio']:
                    fmt = selected_format['format_id']
                elif ffmpeg_path:
                    fmt = f"{selected_format['format_id']}+bestaudio/best"
                else:
                    audio_formats = [f for f in st.session_state.formats if f['has_audio']]
                    fmt = audio_formats[0]['format_id'] if audio_formats else "best[height<=720]/best"
            else:
                fmt = "best[height<=1080]+bestaudio/best[height<=1080]/best"
        else:
            selected_format = None  # For audio-only mode
            fmt = "bestaudio[ext=m4a]/bestaudio/best"

        # Generate custom filename with quality info
        outtmpl = generate_custom_filename(url, info, download_type == "Audio Only", selected_format)
        
        # Show filename preview
        filename_preview = outtmpl.split('/')[-1]  # Get just the filename part

        if info.get('description'):
            st.markdown("##### Description:")
            desc = info.get('description', '')
            if len(desc) > 1000:
                st.write(desc[:1000] + "...")
                with st.expander("Read more"):
                    st.write(desc)
            else:
                st.write(desc)

        st.markdown("##### Video Info:")
        # Create compact info list with proper formatting
        filename_preview = outtmpl.split('/')[-1] if '/' in outtmpl else os.path.basename(outtmpl)
        ffmpeg_available = "Available" if shutil.which("ffmpeg") else "Not found"
        
        # Format duration properly
        duration = info.get('duration')  # Get raw duration in seconds
        if duration and isinstance(duration, (int, float)):
            # Convert seconds to mm:ss format
            minutes = int(duration) // 60
            seconds = int(duration) % 60
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = info.get('duration_string', 'N/A')
        
        # Extract clean title from Facebook format
        raw_title = info.get('title', 'N/A')
        if ' | ' in raw_title:
            # Split by | and take the middle part (actual title)
            parts = raw_title.split(' | ')
            if len(parts) >= 2:
                clean_title = parts[1].strip()  # The actual title is usually the second part
            else:
                clean_title = parts[0].strip()
        else:
            clean_title = raw_title
        
        info_items = [
            f"Title: {clean_title}",
            f"Uploader: {info.get('uploader', 'N/A')}",
            f"Duration: {duration_str}"
        ]
        
        if info.get('view_count'):
            info_items.append(f"Views: {info.get('view_count', 0):,}")
            
        info_items.extend([
            f"FFmpeg: {ffmpeg_available}",
            f"Output file: {filename_preview}",
        ])
        
        # Display as compact list with smaller spacing
        st.markdown(
            "<div style='line-height: 1.4; margin: 0.5rem 0;'>" + 
            "<br/>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;• {item}" for item in info_items]) + 
            "</div>", 
            unsafe_allow_html=True
        )

    # ===================== AUTO DOWNLOAD =====================
    if not st.session_state.download_completed:
        # ĐỪNG clear log để expander không mất sau rerun
        temp_cookies = None
        try:
            ensure_download_dir(outtmpl)
            is_audio_only = download_type == "Audio Only"

            ydl_opts = build_opts(
                outtmpl=outtmpl,
                cookies_path=temp_cookies,
                fmt=fmt,
                rate_limit=rate_limit or None,
                concurrent_fragments=int(concurrent_frags),
                retries=int(retries),
                proxy=proxy or None,
                no_check_certificate=bool(no_check_cert),
                is_audio_only=is_audio_only
            )
            ydl_opts["progress_hooks"] = [progress_hook]

            class StreamlitLogger:
                def debug(self, msg): error_logs.append(f"DEBUG: {msg}")
                def info(self, msg): error_logs.append(f"INFO: {msg}")
                def warning(self, msg): error_logs.append(f"WARNING: {msg}")
                def error(self, msg): error_logs.append(f"ERROR: {msg}")

            ydl_opts["logger"] = StreamlitLogger()

            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                ret = ydl.download([url.strip()])

            if ret == 0:
                final_file = None
                if file_out and Path(file_out).exists():
                    final_file = file_out
                else:
                    # Check trong temp files được track
                    final_file = None
                    for temp_file in st.session_state.temp_files:
                        if Path(temp_file).exists():
                            final_file = temp_file
                            break

                if final_file and Path(final_file).exists():
                    st.session_state.download_completed = True
                    st.session_state.downloaded_file = final_file
                    status_placeholder.success("✅ Video downloaded successfully!")
                    # Clear progress bar and processing message
                    progress.empty()
                    log_area.empty()
                else:
                    st.warning("❌ Download completed but file not found.")
            else:
                st.error(f"❌ Download failed with return code: {ret}")
                # Clear progress bar on failure
                progress.empty()
                log_area.empty()

        except ytdlp.utils.DownloadError as e:
            st.error(f"❌ Download Error: {str(e)}")
            # Clear progress bar on error
            progress.empty()
            log_area.empty()
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            # Clear progress bar on error
            progress.empty()
            log_area.empty()

    # ====== LOG EXPANDER: luôn render khi đã load video (vị trí ngay trên nút Download) ======
    with st.expander("📋 Show detailed logs"):
        if st.session_state.detailed_logs:
            st.text("\n".join(st.session_state.detailed_logs[-20:]))
        else:
            st.caption("No logs yet.")

    # ===================== SAVE FILE BUTTON =====================
    if st.session_state.download_completed and st.session_state.downloaded_file:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if Path(st.session_state.downloaded_file).exists():
                with open(st.session_state.downloaded_file, "rb") as f:
                    file_data = f.read()
                    file_name = Path(st.session_state.downloaded_file).name
                    file_size = len(file_data)
                    
                    # Format file size
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.1f} KB"
                    elif file_size < 1024 * 1024 * 1024:
                        size_str = f"{file_size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
                    
                    st.download_button(
                        label=f"📥 Download Video ({size_str})",
                        data=file_data,
                        file_name=file_name,
                        mime="application/octet-stream",
                        key=f"save_file_{time.time()}",
                        use_container_width=True,
                        type="primary"
                    )
            else:
                st.error("Downloaded file not found!")
        

else:
    # Hướng dẫn sử dụng
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-color);
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            margin: 2rem 0;
            border: 1px solid rgba(200, 200, 200, 0.2);
        ">
        <h3 style="margin: 0 0 0.5rem 0; font-weight: 600; text-align: left; color: inherit;">
            How To Download Videos
        </h3>
        <div style="
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 0.5rem 0;
        ">
            <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 1rem;">
                <span style="
                    background: #28a745;
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 1rem;
                    font-weight: bold;
                ">1</span>
                <span style="font-size: 1.1rem; color: inherit;">Copy Facebook video or reel Url</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 1rem;">
                <span style="
                    background: #007bff;
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 1rem;
                    font-weight: bold;
                ">2</span>
                <span style="font-size: 1.1rem; color: inherit;">Paste Url in the input box above</span>
            </div>
            <div style="display: flex; align-items: center; justify-content: flex-start;">
                <span style="
                    background: #ffc107;
                    color: black;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 1rem;
                    font-weight: bold;
                ">3</span>
                <span style="font-size: 1.1rem; color: inherit;">Press Enter to start automatic download</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

        progress = st.empty()
        log_area = st.empty()

# ===================== FOOTER =====================
st.markdown("""
<div style="
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #f9f9f9;
    border-top: 1px solid #e0e0e0;
    text-align: center;
    padding: 10px 0;
    color: #666;
    font-size: 0.85em;
    z-index: 1000;
    box-shadow: none;
    backdrop-filter: none;
">
    <p style="margin: 0;">Copyright © hieuvoquoc@gmail.com (V1.03)</p>
</div>
""", unsafe_allow_html=True)