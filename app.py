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
    /* Khi hover */
    .stDownloadButton > button:hover {
        filter: brightness(1.05);
    }
    /* Khi focus/active: loại bỏ viền đỏ/focus ring mặc định */
    .stDownloadButton > button:focus,
    .stDownloadButton > button:focus-visible,
    .stDownloadButton > button:active {
        outline: none !important;
        box-shadow: none !important;
        border: 1px solid transparent !important;
    }
    /* Firefox */
    .stDownloadButton > button::-moz-focus-inner { 
        border: 0 !important; 
    }
    /* (Tuỳ chọn) Nếu muốn vẫn có focus ring xanh nhạt, dùng block dưới và bỏ block trên:
    .stDownloadButton > button:focus,
    .stDownloadButton > button:focus-visible {
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
            
    /* Placeholder text nghiêng */               
    input::placeholder {
        font-style: italic;
        color: #999;
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
if 'download_completed' not in st.session_state:
    st.session_state.download_completed = False
if 'downloaded_file' not in st.session_state:
    st.session_state.downloaded_file = None
if 'current_url' not in st.session_state:
    st.session_state.current_url = ""

# ===================== IMPORT =====================
try:
    import yt_dlp as ytdlp
except Exception as e:
    st.error("Missing dependency `yt-dlp`. Please install with `pip install -r requirements.txt` and rerun.")
    st.stop()

# ===================== DEFAULTS =====================
rate_limit = None
retries = 10
concurrent_frags = 1
proxy = None
no_check_cert = True

# ===================== INPUT URL =====================
st.markdown("### Enter Video URL")
url = st.text_input(
    "Facebook video URL", 
    placeholder="https://www.facebook.com/reel/...", 
    help="Paste your Facebook video or reel URL here and press Enter",
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
    
    # Auto-detect ffmpeg
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
    
    # Add ffmpeg location if available
    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path
    
    # Audio-only specific settings
    if is_audio_only:
        opts["postprocessors"] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
        opts["merge_output_format"] = "mp3"
    else:
        # Video + Audio settings
        if "+" in fmt and ffmpeg_path:  # Only add postprocessors if merging and ffmpeg available
            opts["postprocessors"] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
            opts["merge_output_format"] = "mp4"
    
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
        progress.progress(100, text="Processing & finalizing...")
        log_area.info(f"Processing: {Path(file_out).name}")

# Auto-download khi URL đổi
if url and url.strip() and url.strip() != st.session_state.current_url:
    # Reset download state
    st.session_state.download_completed = False
    st.session_state.downloaded_file = None
    st.session_state.current_url = url.strip()
    
    with st.spinner("Getting video information..."):
        video_info = get_video_info(url.strip())
        
    if video_info:
            st.session_state.video_info = video_info
            formats = video_info.get('formats', [])
            
            # Lọc và sắp xếp formats với audio info
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
                        if fps > 0:
                            quality_label += f" ({fps}fps)"
                        if has_audio:
                            quality_label += " 🔊"
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
            
            # Sắp xếp: audio first, then quality, then filesize
            video_formats = list(unique_formats.values())
            video_formats.sort(key=lambda x: (x['has_audio'], x['height'], x['filesize']), reverse=True)
            st.session_state.formats = video_formats

# ===================== UI PREVIEW & OPTIONS =====================
if st.session_state.video_info:
    info = st.session_state.video_info
    
    # Hiển thị trạng thái tại đây
    status_placeholder = st.empty()
    if st.session_state.download_completed:
        status_placeholder.success("Download completed successfully!")
    else:
        status_placeholder.success("Video loaded successfully!")
    
    # Progress area (đặt sau status để xuất hiện bên dưới)
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
    
    with col_right:
        # Download type selection
        download_type = st.selectbox("**Type:**", ["Video + Audio", "Audio Only"], index=0)
        
        # Quality selection - only show for Video + Audio
        if download_type == "Video + Audio":
            if st.session_state.formats:
                format_labels = [f['label'] for f in st.session_state.formats]
                selected_idx = st.selectbox("**Quality:**", range(len(format_labels)),
                                            format_func=lambda x: format_labels[x], index=0)
                selected_format = st.session_state.formats[selected_idx]
                
                # Auto-select best strategy for video + audio
                ffmpeg_path = shutil.which("ffmpeg")
                if selected_format['has_audio']:
                    fmt = selected_format['format_id']
                elif ffmpeg_path:
                    fmt = f"{selected_format['format_id']}+bestaudio/best"
                else:
                    # Fallback to best format with audio
                    audio_formats = [f for f in st.session_state.formats if f['has_audio']]
                    if audio_formats:
                        fmt = audio_formats[0]['format_id']
                    else:
                        fmt = "best[height<=720]/best"
            else:
                fmt = "best[height<=1080]+bestaudio/best[height<=1080]/best"
        else:
            # Audio Only mode - no quality selection needed
            fmt = "bestaudio[ext=m4a]/bestaudio/best"
        
        # Description
        if info.get('description'):
            st.markdown("##### Description:")
            desc = info.get('description', '')
            if len(desc) > 1000:
                st.write(desc[:1000] + "...")
                with st.expander("Read more"):
                    st.write(desc)
            else:
                st.write(desc)
        
        # Video Info
        st.markdown("##### Video Info:")
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - Title: {info.get('title', 'N/A')}", unsafe_allow_html=True)
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - Uploader: {info.get('uploader', 'N/A')}", unsafe_allow_html=True)
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - Duration: {info.get('duration_string', 'N/A')}", unsafe_allow_html=True)
        if info.get('view_count'):
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - Views: {info.get('view_count', 0):,}", unsafe_allow_html=True)
        
        # FFmpeg status
        ffmpeg_available = "✅ Available" if shutil.which("ffmpeg") else "❌ Not found"
        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; - FFmpeg: {ffmpeg_available}", unsafe_allow_html=True)
        
        
        # Set output template based on download type
        if download_type == "Audio Only":
            outtmpl = "downloads/%(title).100s-%(id)s.%(ext)s"
        else:
            outtmpl = "downloads/%(title).80s-%(id)s.%(ext)s"
    
    # ===================== AUTO DOWNLOAD =====================
    if not st.session_state.download_completed:
        error_logs.clear()
        temp_cookies = None
        
        try:
            log_area.info("Starting download...")
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
                # Tìm file đã download
                final_file = None
                
                if file_out and Path(file_out).exists():
                    final_file = file_out
                else:
                    downloads_dir = Path("downloads")
                    if downloads_dir.exists():
                        recent_files = sorted(downloads_dir.rglob("*"), key=os.path.getctime, reverse=True)
                        if is_audio_only:
                            audio_files = [f for f in recent_files if f.is_file() and f.suffix in ['.mp3', '.m4a', '.aac']]
                            target_files = audio_files
                        else:
                            video_files = [f for f in recent_files if f.is_file() and f.suffix in ['.mp4', '.webm', '.mkv']]
                            target_files = video_files
                        
                        if target_files:
                            final_file = str(target_files[0])
                
                if final_file and Path(final_file).exists():
                    st.session_state.download_completed = True
                    st.session_state.downloaded_file = final_file
                    # Cập nhật status và xóa log thay vì tạo thông báo mới
                    status_placeholder.success("Download completed successfully!")
                    log_area.empty()  # Xóa thông báo "Starting download..."
                else:
                    st.warning("Download completed but file not found.")
                    log_area.empty()  # Xóa thông báo "Starting download..." kể cả khi lỗi
            else:
                st.error(f"Download failed with return code: {ret}")
                log_area.empty()  # Xóa thông báo "Starting download..." khi lỗi

            if error_logs:
                with st.expander("📋 Show detailed logs"):
                    st.text("\n".join(error_logs[-20:]))

        except ytdlp.utils.DownloadError as e:
            st.error(f"Download Error: {str(e)}")
            log_area.empty()  # Xóa thông báo "Starting download..." khi lỗi
            if error_logs:
                with st.expander("Show detailed logs"):
                    st.text("\n".join(error_logs[-20:]))
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            log_area.empty()  # Xóa thông báo "Starting download..." khi lỗi
            if error_logs:
                with st.expander("Show detailed logs"):
                    st.text("\n".join(error_logs[-20:]))

    # ===================== SAVE FILE BUTTON =====================
    if st.session_state.download_completed and st.session_state.downloaded_file:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if Path(st.session_state.downloaded_file).exists():
                with open(st.session_state.downloaded_file, "rb") as f:
                    file_data = f.read()
                    file_name = Path(st.session_state.downloaded_file).name
                    
                    st.download_button(
                        label="Save Video",
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
    # Hướng dẫn sử dụng với thiết kế đẹp - chiều rộng 2/3
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            color: #333;
            padding: 1.5rem;
            border-radius: 15px;
            text-align: center;
            margin: 2rem 0;
            border: 1px solid rgba(200, 200, 200, 0.2);
        ">
        <h3 style="margin: 0 0 0.5rem 0; font-weight: 600; text-align: left;">
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
                <span style="font-size: 1.1rem;">
                    Copy Facebook video or reel Url
                </span>
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
                <span style="font-size: 1.1rem;">
                    Paste Url in the input box above
                </span>
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
                <span style="font-size: 1.1rem;">
                    Press Enter to start automatic download
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
        
        # Tạo empty placeholders cho trường hợp chưa có video
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
    <p style="margin: 0;">Copyright © hieuvoquoc@gmail.com (V1.02)</p>
</div>
""", unsafe_allow_html=True)