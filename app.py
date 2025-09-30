import streamlit as st
from pathlib import Path
import tempfile, time, os
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
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(0deg, #0088F8 0%, #006FCB 100%);
        color: white;
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 10px 10px 10px 10px;
    }

    /* Style nút mặc định */
    .stButton > button {
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
    }
    /* Khi hover */
    .stButton > button:hover {
        filter: brightness(1.05);
    }
    /* Khi focus/active: loại bỏ viền đỏ/focus ring mặc định */
    .stButton > button:focus,
    .stButton > button:focus-visible,
    .stButton > button:active {
        outline: none !important;
        box-shadow: none !important;
        border: 1px solid transparent !important;
    }
    /* Firefox */
    .stButton > button::-moz-focus-inner { 
        border: 0 !important; 
    }
    /* (Tuỳ chọn) Nếu muốn vẫn có focus ring xanh nhạt, dùng block dưới và bỏ block trên:
    .stButton > button:focus,
    .stButton > button:focus-visible {
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,.45) !important;
        border: 1px solid transparent !important;
    } */

    /* Thanh video preview khung tối (tuỳ chỉnh nhẹ) */
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

# ===================== IMPORT =====================
try:
    import yt_dlp as ytdlp
except Exception as e:
    st.error("Missing dependency `yt-dlp`. Please install with `pip install -r requirements.txt` and rerun.")
    st.stop()

# ===================== DEFAULTS =====================
rate_limit = None
retries = 10
concurrent_frags = 3
proxy = None
no_check_cert = True

# ===================== INPUT URL =====================
st.markdown("### Enter Video URL")
url = st.text_input(
    "Facebook video URL", 
    placeholder="https://www.facebook.com/reel/...", 
    help="Paste your Facebook video or reel URL here",
    key="url_input"
)

# ===================== GET INFO =====================
def get_video_info(video_url):
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "listformats": True,
        }
        with ytdlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return info
    except Exception as e:
        st.error(f"Failed to get video info: {str(e)}")
        return None

# Auto-preview khi URL đổi
if url and url.strip() and (not st.session_state.video_info or st.session_state.video_info.get('webpage_url') != url.strip()):
    with st.spinner("Getting video information..."):
        video_info = get_video_info(url.strip())
        if video_info:
            st.session_state.video_info = video_info
            formats = video_info.get('formats', [])
            unique_formats = {}
            
            # Ưu tiên format có cả video và audio
            for f in formats:
                if f.get('vcodec') != 'none' and f.get('height'):
                    height = f.get('height', 0)
                    ext = f.get('ext', 'mp4')
                    filesize = f.get('filesize') or 0
                    fps = f.get('fps') or 0
                    has_audio = f.get('acodec') and f.get('acodec') != 'none'
                    
                    key = f"{height}p-{ext.upper()}"
                    current_format = unique_formats.get(key)
                    
                    # Ưu tiên format có audio hoặc filesize lớn hơn
                    should_replace = False
                    if key not in unique_formats:
                        should_replace = True
                    elif has_audio and not current_format.get('has_audio'):
                        should_replace = True
                    elif has_audio == current_format.get('has_audio') and filesize > (current_format.get('filesize') or 0):
                        should_replace = True
                    
                    if should_replace:
                        quality_label = f"{height}p - {ext.upper()}"
                        if has_audio:
                            quality_label += " (with audio)"
                        if fps > 0:
                            quality_label += f" ({fps}fps)"
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
            video_formats.sort(key=lambda x: (x.get('has_audio', False), x['height']), reverse=True)
            st.session_state.formats = video_formats

# ===================== UI PREVIEW & OPTIONS =====================
if st.session_state.video_info:
    info = st.session_state.video_info
    st.success("Video loaded successfully!")
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
    with col_right:
        download_type = st.selectbox("**Type:**", ["Video + Audio", "Audio Only"], index=0)
        if st.session_state.formats and download_type == "Video + Audio":
            format_labels = [f['label'] for f in st.session_state.formats]
            selected_idx = st.selectbox("**Quality:**", range(len(format_labels)),
                                        format_func=lambda x: format_labels[x], index=0)
            selected_format = st.session_state.formats[selected_idx]
            # Sử dụng format đơn giản để tránh merge error, ưu tiên format có sẵn audio
            fmt = f"best[height<={selected_format['height']}]/best"
        elif download_type == "Audio Only":
            st.selectbox("Quality:", ["Best Audio Available"], index=0, disabled=True)
            fmt = "bestaudio/best"
        else:
            st.selectbox("Quality:", ["Best Available"], index=0, disabled=True)
            fmt = "best"
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
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - Title: {info.get('title', 'N/A')}", unsafe_allow_html=True)
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - Uploader: {info.get('uploader', 'N/A')}", unsafe_allow_html=True)
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - Duration: {info.get('duration_string', 'N/A')}", unsafe_allow_html=True)
        if info.get('view_count'):
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - Views: {info.get('view_count', 0):,}", unsafe_allow_html=True)
        st.markdown("---")
        if download_type == "Audio Only":
            outtmpl = "downloads/%(title)s.%(ext)s"
        else:
            outtmpl = "downloads/%(title).80s-%(id)s.%(ext)s"
else:
    fmt = "best"
    outtmpl = "downloads/%(title).80s-%(id)s.%(ext)s"

# ===================== PROGRESS ZONE =====================
st.markdown("---")
if st.session_state.video_info:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        download_clicked = st.button("Download Video", type="primary", use_container_width=True)
    log_area = st.empty()
    progress = st.progress(0, text="Ready to download...")
    done_placeholder = st.empty()
else:
    st.info("Enter a Facebook video URL above to get started")
    download_clicked = False
    log_area = st.empty()
    progress = st.empty()
    done_placeholder = st.empty()

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
    no_check_certificate: bool = False
) -> Dict[str, Any]:
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
        "concurrent_fragment_downloads": concurrent_fragments or 3,
        "ratelimit": None,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        },
        "format": fmt,
        "quiet": False,
        "no_warnings": False,
        "ffmpeg_location": "/opt/homebrew/bin/ffmpeg",  # Chỉ định đường dẫn ffmpeg
    }
    if rate_limit:
        opts["ratelimit"] = rate_limit
    if cookies_path:
        opts["cookiefile"] = cookies_path
    if proxy:
        opts["proxy"] = proxy
    return opts

last_percent = 0
file_out = None
error_logs = []

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
        status_text = f"{percent}% | { (spd and f'{spd/1024/1024:.2f} MB/s') or '–' } | ETA: {eta or '–'} s"
        log_area.info(status_text)
    elif d.get("status") == "finished":
        file_out = d.get("filename")
        progress.progress(100, text="Merging & finalizing...")
        log_area.info(f"Saved: {file_out}")

# ===================== DOWNLOAD =====================
if download_clicked:
    error_logs.clear()
    temp_cookies = None
    try:
        log_area.info("Starting download...")
        ensure_download_dir(outtmpl)
        ydl_opts = build_opts(
            outtmpl=outtmpl,
            cookies_path=temp_cookies,
            fmt=fmt,
            rate_limit=rate_limit or None,
            concurrent_fragments=int(concurrent_frags),
            retries=int(retries),
            proxy=proxy or None,
            no_check_certificate=bool(no_check_cert)
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
            if file_out and Path(file_out).exists():
                done_placeholder.success("Download completed successfully!")
                with open(file_out, "rb") as f:
                    st.download_button("Save File", data=f, file_name=Path(file_out).name)
            else:
                downloads_dir = Path("downloads")
                if downloads_dir.exists():
                    recent_files = sorted(downloads_dir.rglob("*"), key=os.path.getctime, reverse=True)
                    video_files = [f for f in recent_files if f.is_file() and f.suffix in ['.mp4', '.m4a', '.webm', '.mp3']]
                    if video_files:
                        file_out = str(video_files[0])
                        done_placeholder.success("Download completed!")
                        with open(file_out, "rb") as f:
                            st.download_button("Save File", data=f, file_name=Path(file_out).name)
                    else:
                        st.warning("Download seems successful but file not found.")
                else:
                    st.error("Download failed - no downloads directory found")
        else:
            st.error(f"Download failed with return code: {ret}")

        if error_logs:
            with st.expander("📋 Show detailed logs"):
                st.text("\n".join(error_logs[-20:]))

    except ytdlp.utils.DownloadError as e:
        st.error(f"Download Error: {str(e)}")
        if error_logs:
            with st.expander("Show detailed logs"):
                st.text("\n".join(error_logs[-20:]))
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        if error_logs:
            with st.expander("Show detailed logs"):
                st.text("\n".join(error_logs[-20:]))

# ===================== FOOTER =====================
st.markdown("---")
st.markdown("""
<div style="
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #f9f9f9; /* hoặc #fff */
    border-top: 1px solid #e0e0e0;
    text-align: center;
    padding: 10px 0;
    color: #666;
    font-size: 0.85em;
    z-index: 1000;
    box-shadow: none;
    backdrop-filter: none;
">
    <p style="margin: 0;">Copyright VO QUOC HIEU (hieuvoquoc@gmail.com)</p>
</div>
""", unsafe_allow_html=True)