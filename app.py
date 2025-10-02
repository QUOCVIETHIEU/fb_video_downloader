# app.py
import streamlit as st
from pathlib import Path
import tempfile, time, os, glob
import shutil
from typing import Optional, Dict, Any

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="FB & YouTube Video Downloader",
    page_icon="assets/fb_downloader.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ===================== CSS =====================
st.markdown("""
<style>
    :root { --text-color: #333333; }
    @media (prefers-color-scheme: dark) { :root { --text-color: #ffffff; } }
    .stApp[data-theme="dark"] { --text-color: #ffffff; }
    .stApp[data-theme="light"] { --text-color: #333333; }

    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(0deg, #0088F8 0%, #006FCB 100%);
        color: white;
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 10px;
    }

    .stDownloadButton > button {
        width: 100%;
        background: linear-gradient(0deg, #2B79C2 0%, #006FCB 100%) !important;
        color: white !important;
        border-radius: 20px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        border: 1px solid transparent !important;
        outline: none !important;
        box-shadow: none !important;
        -webkit-appearance: none;
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
        border: 1px solid #402031;
        border-radius: 10px;
        overflow: hidden;
        background-color: #2b2b2b;
        position: relative;
    }

    .preview-wrap video {
        display: block !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        max-width: 90% !important;
        max-height: 90% !important;
        width: auto !important;
        height: auto !important;
        margin: 0 !important;
        object-fit: contain !important;
    }

    .preview-wrap iframe {
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        border: none !important;
        border-radius: 10px !important;
    }

    .preview-wrap img {
        max-width: 95%;
        max-height: 95%;
        object-fit: contain;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
    }

    input::placeholder { font-style: italic; color: #999; }

    .spinner {
        display: inline-block;
        width: 16px; height: 16px;
        border: 2px solid #f3f3f3;
        border-top: 2px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 8px; vertical-align: middle;
    }
    @keyframes spin { 0% { transform: rotate(0deg);} 100% { transform: rotate(360deg);} }

    .stButton > button[kind="primary"] {
        background: linear-gradient(0deg, #25A0FA 0%, #25A0FA 100%) !important;
        color: white !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover { filter: brightness(1.1) !important; }
</style>
""", unsafe_allow_html=True)

# ===================== HEADER =====================
st.markdown("""
<div class="main-header">
    <h1>FB & YouTube Video Downloader</h1>
    <p>Fast and secure Facebook & YouTube video downloader</p>
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
if 'detailed_logs' not in st.session_state:
    st.session_state.detailed_logs = []
if 'temp_files' not in st.session_state:
    st.session_state.temp_files = []
if 'last_selected_format_id' not in st.session_state:
    st.session_state.last_selected_format_id = None
if 'last_download_type' not in st.session_state:
    st.session_state.last_download_type = "Video"
if 'session_initialized' not in st.session_state:
    st.session_state.session_initialized = True

# ===================== IMPORT =====================
try:
    import yt_dlp as ytdlp
except Exception:
    st.error("Missing dependency `yt-dlp`. Please install with `pip install -r requirements.txt` and rerun.")
    st.stop()

# ===================== NETWORK / YT TUNING =====================
FORCE_IPV4 = True
YOUTUBE_CLIENTS = ["android", "web"]   # Ưu tiên android để tránh 403
GEO_BYPASS_COUNTRY = "VN"
ADD_REFERER_HEADERS = True

# ===================== HELPERS =====================
def cleanup_temp_files():
    for temp_file in st.session_state.temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass
    st.session_state.temp_files.clear()

def ensure_download_dir(path_tmpl: str):
    p = Path(path_tmpl)
    if "%(" in path_tmpl:
        base = Path(path_tmpl.split("%(")[0]).expanduser()
        if base and str(base).strip() and not base.exists():
            base.mkdir(parents=True, exist_ok=True)
    else:
        Path(path_tmpl).parent.mkdir(parents=True, exist_ok=True)

def get_video_info(video_url, max_retries=3, cookies_path=None, proxy=None):
    for attempt in range(max_retries):
        try:
            http_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
            }
            if ADD_REFERER_HEADERS:
                http_headers.update({
                    "Referer": "https://www.youtube.com/",
                    "Origin": "https://www.youtube.com",
                })

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "listformats": True,
                "http_headers": http_headers,
                "extractor_args": {
                    "youtube": {
                        "player_client": YOUTUBE_CLIENTS,   # ["android","web"]
                        "player_skip": ["configs"],
                    }
                },
                "geo_bypass": True,
                "geo_bypass_country": GEO_BYPASS_COUNTRY,
                "noplaylist": True,
            }
            if FORCE_IPV4:
                ydl_opts["forceipv4"] = True
            if cookies_path:
                ydl_opts["cookiefile"] = cookies_path
            if proxy:
                ydl_opts["proxy"] = proxy

            with ytdlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info
        except Exception as e:
            error_msg = str(e)
            if "Cannot parse data" in error_msg and attempt < max_retries - 1:
                st.warning(f"⚠️ Attempt {attempt + 1} failed. Retrying... ({attempt + 2}/{max_retries})")
                time.sleep(1.2)
                continue
            else:
                st.error(f"❌ Failed to get video info: {error_msg}")
                return None
    return None

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
    http_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if ADD_REFERER_HEADERS:
        http_headers.update({
            "Referer": "https://www.youtube.com/",
            "Origin": "https://www.youtube.com",
        })

    opts: Dict[str, Any] = {
        "outtmpl": outtmpl,
        "restrictfilenames": False,
        "ignoreerrors": False,
        "noprogress": False,
        "consoletitle": False,
        "nocheckcertificate": no_check_certificate,
        "retries": retries,
        "fragment_retries": retries,
        "continuedl": True,
        "concurrent_fragment_downloads": concurrent_fragments or 1,
        "ratelimit": None,
        "http_headers": http_headers,
        "format": fmt,
        "quiet": False,
        "no_warnings": False,

        # YouTube hardening
        "extractor_args": {
            "youtube": {
                "player_client": YOUTUBE_CLIENTS,
            }
        },
        "geo_bypass": True,
        "geo_bypass_country": GEO_BYPASS_COUNTRY,
        "noplaylist": True,

        # dịu throttle
        "sleep_interval_requests": 0.5,
        "max_sleep_interval_requests": 1.5,
    }

    if FORCE_IPV4:
        opts["forceipv4"] = True

    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path

    if is_audio_only:
        if ffmpeg_path:
            opts["postprocessors"] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            opts["merge_output_format"] = "mp3"
            opts["keep_video"] = False
        else:
            opts["format"] = "bestaudio/best"
            st.warning("⚠️ FFmpeg không có sẵn. Sẽ tải audio format gốc thay vì MP3.")
    else:
        if "+" in fmt and ffmpeg_path:
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

# ===================== DEFAULTS =====================
rate_limit = None
retries = 10
concurrent_frags = 1
no_check_cert = True

# ===================== INPUT URL =====================
st.markdown("### Enter Video URL")

# Form input + GO
with st.form("url_form", clear_on_submit=False):
    col_input, col_button = st.columns([15, 1])
    with col_input:
        url_input = st.text_input(
            "Facebook or YouTube video Url:",
            placeholder="https://www.facebook.com/reel/...  hoặc  https://www.youtube.com/watch?v=...",
            help="Paste your Facebook video/reel hoặc YouTube video/shorts URL",
            key="url_input_form",
        )
    with col_button:
        st.markdown("<br>", unsafe_allow_html=True)
        go_submitted = st.form_submit_button("GO", use_container_width=True, type="primary")

# Optional: Cookies & Proxy
with st.expander("🔐 Optional: Cookies & Proxy"):
    cookie_file = st.file_uploader("Upload cookies.txt (Netscape format)", type=["txt"])
    proxy_input = st.text_input("HTTP/HTTPS Proxy (ví dụ: http://user:pass@host:port)", value="")
    use_proxy = bool(proxy_input.strip())

# Lưu cookies tạm (nếu có)
temp_cookies = None
if cookie_file is not None:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
    tmp.write(cookie_file.read())
    tmp.flush(); tmp.close()
    temp_cookies = tmp.name

# Resolve URL
url = ""
if go_submitted and url_input.strip():
    url = url_input.strip()
elif url_input and url_input.strip():
    url = url_input.strip()

# Logs
error_logs = st.session_state.detailed_logs
last_percent = 0
file_out = None

# ===================== GET INFO khi URL đổi =====================
if url and url.strip() and url.strip() != st.session_state.current_url:
    cleanup_temp_files()
    st.session_state.download_completed = False
    st.session_state.downloaded_file = None
    st.session_state.current_url = url.strip()
    st.session_state.detailed_logs.clear()
    with st.spinner("Getting video information..."):
        video_info = get_video_info(
            url.strip(),
            cookies_path=temp_cookies,
            proxy=proxy_input if use_proxy else None
        )
    if video_info:
        st.session_state.video_info = video_info
        formats = video_info.get('formats', [])
        unique_formats = {}
        for f in formats:
            # Chỉ lọc vcodec có video, nhưng KHÔNG giới hạn MP4 (tránh bó hẹp -> 403)
            if f.get('vcodec') != 'none' and (f.get('height') or f.get('quality') is not None):
                height = f.get('height') or 0
                ext = f.get('ext', 'mp4')
                filesize = f.get('filesize') or f.get('filesize_approx') or 0
                fps = f.get('fps') or 0
                has_audio = f.get('acodec') != 'none'
                key = f"{height or 'NA'}p-{ext.upper()}"
                current_filesize = unique_formats.get(key, {}).get('filesize', 0) or 0
                if key not in unique_formats or filesize > current_filesize:
                    quality_label = f"{height}p - {ext.upper()}" if height else f"{ext.upper()}"
                    if fps: quality_label += f" ({fps}fps)"
                    if has_audio: quality_label += " 🔊"
                    if filesize and isinstance(filesize, (int, float)):
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
        video_formats.sort(key=lambda x: (x['has_audio'], x['height'] or 0, x['filesize'] or 0), reverse=True)
        st.session_state.formats = video_formats

# ===================== RETRY SECTION =====================
if url and url.strip() and not st.session_state.video_info:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.warning("⚠️ Failed to load video information. Website có thể đang chặn/throttle, hoặc video private/restricted.")
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
        if st.session_state.get('last_download_type') == "Audio":
            status_placeholder.success("✅ Audio converted and ready to download!")
        else:
            status_placeholder.success("✅ Video loaded successfully!")
    else:
        if st.session_state.get('last_download_type') == "Audio":
            status_placeholder.markdown('<span class="spinner"></span> Preparing to download video and convert to MP3...', unsafe_allow_html=True)
        else:
            status_placeholder.markdown('<span class="spinner"></span> Preparing to processing & converting video format...', unsafe_allow_html=True)

    # placeholders cho tiến trình & log
    log_area = st.empty()
    progress = st.empty()

    # Extract YouTube ID (để embed preview)
    def extract_youtube_id(url, video_info=None):
        import re
        if video_info and video_info.get('id'):
            return video_info.get('id')
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/shorts\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/.*[?&]v=([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            m = re.search(pattern, url)
            if m: return m.group(1)
        return None

    col_left, col_right = st.columns([2, 3])

    with col_left:
        preview_area = st.empty()
        if info.get('thumbnail'):
            try:
                is_youtube = 'youtu' in url or 'youtube.com' in url or 'youtu.be' in url
                if is_youtube:
                    youtube_id = extract_youtube_id(url, info)
                    if youtube_id:
                        is_short = '/shorts/' in url or '/shorts/' in info.get('webpage_url', '')
                        if is_short:
                            preview_area.markdown(f"""
                            <div class="preview-wrap">
                                <iframe 
                                    src="https://www.youtube.com/embed/{youtube_id}?autoplay=0&mute=1&controls=1&showinfo=0&rel=0&modestbranding=1"
                                    style="width: 60%; height: 90%; border: none; border-radius: 10px;"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowfullscreen>
                                </iframe>
                                <div style="position: absolute; bottom: 10px; left: 10px; background: rgba(255, 0, 0, 0.8); color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold;">
                                    YouTube Shorts
                                </div>
                            </div>
                            <p style="text-align:center; color:#ccc; font-size:0.9em; margin-top:6px;">YouTube Shorts Preview</p>
                            """, unsafe_allow_html=True)
                        else:
                            preview_area.markdown(f"""
                            <div class="preview-wrap">
                                <iframe 
                                    src="https://www.youtube.com/embed/{youtube_id}?autoplay=0&mute=1&controls=1&showinfo=0&rel=0&modestbranding=1"
                                    style="width: 90%; height: 90%; border: none; border-radius: 10px;"
                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                    allowfullscreen>
                                </iframe>
                                <div style="position: absolute; bottom: 10px; left: 10px; background: rgba(255, 0, 0, 0.8); color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold;">
                                    YouTube
                                </div>
                            </div>
                            <p style="text-align:center; color:#ccc; font-size:0.9em; margin-top:6px;">YouTube Video Preview</p>
                            """, unsafe_allow_html=True)
                    else:
                        preview_area.markdown(f"""
                        <div class="preview-wrap">
                            <img src="{info.get('thumbnail','')}" />
                            <div style="position: absolute; bottom: 10px; left: 10px; background: rgba(255, 0, 0, 0.8); color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold;">
                                📺 YouTube
                            </div>
                        </div>
                        <p style="text-align:center; color:#ccc; font-size:0.9em; margin-top:6px;">YouTube Thumbnail</p>
                        """, unsafe_allow_html=True)
                else:
                    preview_url = None
                    if info.get('formats'):
                        video_formats_all = [f for f in info.get('formats', []) if f.get('vcodec') != 'none' and f.get('url')]
                        if video_formats_all:
                            video_formats_all.sort(key=lambda x: x.get('height', 0) or 0)
                            preview_url = video_formats_all[0].get('url')

                    if preview_url:
                        preview_area.markdown(f"""
                        <div class="preview-wrap">
                            <video controls controlslist="nodownload" oncontextmenu="return false;"
                                   poster="{info.get('thumbnail', '')}" preload="metadata">
                                <source src="{preview_url}" type="video/mp4">
                                <p style="color:#ccc;">Your browser does not support the video tag.</p>
                            </video>
                            <div style="position: absolute; bottom: 10px; left: 10px; background: rgba(24, 119, 242, 0.8); color: white; padding: 5px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: bold;">
                                Facebook
                            </div>
                        </div>
                        <p style="text-align:center; color:#ccc; font-size:0.9em; margin-top:6px;">Facebook Video Preview</p>
                        """, unsafe_allow_html=True)
                    else:
                        preview_area.markdown(f"""
                        <div class="preview-wrap">
                            <img src="{info.get('thumbnail','')}" />
                        </div>
                        <p style="text-align:center; color:#ccc; font-size:0.9em; margin-top:6px;">Video Thumbnail (Preview not available)</p>
                        """, unsafe_allow_html=True)
            except Exception:
                preview_area.info("No thumbnail available")
        else:
            preview_area.info("No thumbnail available")

    # Generate custom filename
    def generate_custom_filename(url, video_info, is_audio, selected_format=None):
        video_id = video_info.get('id', 'unknown')
        if is_audio:
            ext = ""
            quality_suffix = "_audio"
        else:
            ext = "mp4"
            quality_suffix = ""
            if selected_format:
                height = selected_format.get('height', 0)
                if height:
                    quality_suffix = f"_{height}p"

        if 'facebook.com' in url:
            if '/reel/' in url:
                filename = f"fb_reel_{video_id}{quality_suffix}" + ("" if is_audio else f".{ext}")
            else:
                filename = f"fb_video_{video_id}{quality_suffix}" + ("" if is_audio else f".{ext}")
        elif 'youtu' in url or 'youtube.com' in url or 'youtu.be' in url:
            is_short = False
            if '/shorts/' in url or 'youtube.com/shorts/' in info.get('webpage_url', '') or '/shorts/' in info.get('webpage_url', ''):
                is_short = True
            duration = video_info.get('duration', 0)
            if not is_short and duration and duration <= 60:
                for fmt in video_info.get('formats', []):
                    h = fmt.get('height', 0); w = fmt.get('width', 0)
                    if h and w and h > w:
                        is_short = True; break
            prefix = "ytb_short_" if is_short else "ytb_video_"
            filename = f"{prefix}{video_id}{quality_suffix}" + ("" if is_audio else f".{ext}")
        else:
            filename = f"video_{video_id}{quality_suffix}" + ("" if is_audio else f".{ext}")

        temp_file = os.path.join(tempfile.gettempdir(), filename)
        if temp_file not in st.session_state.temp_files:
            st.session_state.temp_files.append(temp_file)
        return temp_file

    with col_right:
        # TYPE
        new_download_type = st.selectbox("**Type:**", ["Video", "Audio"],
                                         index=(0 if st.session_state.last_download_type=="Video" else 1),
                                         key="download_type_selector")
        if st.session_state.last_download_type != new_download_type:
            st.session_state.download_completed = False
            st.session_state.downloaded_file = None
            st.session_state.last_download_type = new_download_type
            cleanup_temp_files()
            st.rerun()
        download_type = new_download_type

        # QUALITY
        current_selected_format_id = None
        selected_format = None
        if download_type == "Video":
            if st.session_state.formats:
                format_labels = [f['label'] for f in st.session_state.formats]
                new_selected_idx = st.selectbox(
                    "**Quality:**",
                    range(len(format_labels)),
                    format_func=lambda x: format_labels[x],
                    index=0,
                    key="quality_selector"
                )
                selected_format = st.session_state.formats[new_selected_idx]
                current_selected_format_id = selected_format['format_id']

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
            if st.session_state.formats:
                video_with_audio = [f for f in st.session_state.formats if f['has_audio']]
                if video_with_audio:
                    best_video_audio = max(video_with_audio, key=lambda x: x.get('height', 0) or 0)
                    fmt = best_video_audio['format_id']
                    current_selected_format_id = f"audio_from_{best_video_audio['format_id']}"
                else:
                    fmt = "best[height<=720]+bestaudio/bestaudio/best"
                    current_selected_format_id = "audio_from_merged"
            else:
                fmt = "best+bestaudio/bestaudio/best"
                current_selected_format_id = "audio_from_best"

        # TRÁNH DOUBLE PREVIEW
        if st.session_state.last_selected_format_id is None:
            st.session_state.last_selected_format_id = current_selected_format_id
        else:
            if st.session_state.last_selected_format_id != current_selected_format_id:
                st.session_state.download_completed = False
                st.session_state.downloaded_file = None
                st.session_state.last_selected_format_id = current_selected_format_id
                cleanup_temp_files()
                st.rerun()

        # INFO BOX
        outtmpl = generate_custom_filename(url, info, download_type == "Audio", selected_format)
        filename_preview = os.path.basename(outtmpl)
        if download_type == "Audio" and not filename_preview.endswith('.mp3'):
            filename_preview += '.mp3'
        ffmpeg_available = "Available" if shutil.which("ffmpeg") else "Not found"

        duration = info.get('duration')
        if duration and isinstance(duration, (int, float)):
            minutes = int(duration) // 60
            seconds = int(duration) % 60
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = info.get('duration_string', 'N/A')

        raw_title = info.get('title', 'N/A')
        if ' | ' in raw_title:
            parts = raw_title.split(' | ')
            clean_title = parts[1].strip() if len(parts) >= 2 else parts[0].strip()
        else:
            clean_title = raw_title

        st.caption(f"Client(s): {YOUTUBE_CLIENTS} • IPv4: {FORCE_IPV4} • Geo: {GEO_BYPASS_COUNTRY} • Cookies: {bool(temp_cookies)} • Proxy: {use_proxy}")

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
        info_text = "\n".join([f"• {item}" for item in info_items])

        if len(info_text) > 350:
            if 'show_full_info' not in st.session_state: st.session_state.show_full_info = False
            if st.session_state.show_full_info:
                st.markdown("<div style='line-height:1.4; margin:0.5rem 0;'>" + info_text.replace('\n','<br/>') + "</div>", unsafe_allow_html=True)
                if st.button("ℹ️ Rút gọn", key="collapse_info"): st.session_state.show_full_info=False; st.rerun()
            else:
                st.markdown("<div style='line-height:1.4; margin:0.5rem 0;'>" + (info_text[:350]+"...").replace('\n','<br/>') + "</div>", unsafe_allow_html=True)
                if st.button("📖 Xem thêm", key="expand_info"): st.session_state.show_full_info=True; st.rerun()
        else:
            st.markdown("<div style='line-height:1.4; margin:0.5rem 0;'>" + "<br/>".join([f"&nbsp;&nbsp;&nbsp;&nbsp;• {item}" for item in info_items]) + "</div>", unsafe_allow_html=True)

    # ===================== PROGRESS HOOK =====================
    def progress_hook(d):
        try:
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                percent = 0 if total == 0 else int(downloaded * 100 / total)
                global last_percent
                if percent != last_percent:
                    progress.progress(min(percent, 100), text=f"Downloading... {percent}%")
                    last_percent = percent
                spd = d.get("speed"); eta = d.get("eta")
                status_text = f"{percent}% | {(spd and f'{spd/1024/1024:.2f} MB/s') or '–'} | ETA: {eta or '–'} s"
                log_area.info(status_text)
                error_logs.append(f"PROGRESS: {status_text}")
            elif d.get("status") == "finished":
                global file_out
                file_out = d.get("filename")
                progress.progress(100, text="Processing & finalizing...")
                if 'audio' in str(d.get("info_dict", {}).get("ext", "")).lower():
                    msg = "Converting video to MP3 audio format..."
                else:
                    msg = "Processing & converting video format..."
                log_area.warning(msg)
                error_logs.append(f"INFO: {msg}")
        except Exception as e:
            error_logs.append(f"HOOK_ERR: {e}")

    # ===================== AUTO DOWNLOAD =====================
    if not st.session_state.download_completed:
        try:
            ensure_download_dir(outtmpl)
            is_audio_only = (download_type == "Audio")
            ydl_opts = build_opts(
                outtmpl=outtmpl,
                cookies_path=temp_cookies,
                fmt=fmt,
                rate_limit=rate_limit or None,
                concurrent_fragments=int(concurrent_frags),
                retries=int(retries),
                proxy=proxy_input if use_proxy else None,
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
                    for temp_file in st.session_state.temp_files:
                        if Path(temp_file).exists():
                            final_file = temp_file; break
                    if not final_file and is_audio_only:
                        temp_dir = tempfile.gettempdir()
                        mp3_files = glob.glob(os.path.join(temp_dir, "*.mp3"))
                        if mp3_files:
                            mp3_files.sort(key=os.path.getmtime, reverse=True)
                            video_id = info.get('id', '')
                            for mp3_file in mp3_files:
                                if video_id in os.path.basename(mp3_file) or os.path.getmtime(mp3_file) > (time.time() - 300):
                                    final_file = mp3_file
                                    if final_file not in st.session_state.temp_files:
                                        st.session_state.temp_files.append(final_file)
                                    break
                    if not final_file:
                        temp_dir = tempfile.gettempdir()
                        extensions = ['*.mp4', '*.m4a', '*.webm'] if not is_audio_only else ['*.mp3', '*.m4a']
                        for ext in extensions:
                            files = glob.glob(os.path.join(temp_dir, ext))
                            if files:
                                files.sort(key=os.path.getmtime, reverse=True)
                                recent_file = files[0]
                                if os.path.getmtime(recent_file) > (time.time() - 300):
                                    final_file = recent_file
                                    if final_file not in st.session_state.temp_files:
                                        st.session_state.temp_files.append(final_file)
                                    break

                if final_file and Path(final_file).exists():
                    st.session_state.download_completed = True
                    st.session_state.downloaded_file = final_file
                    if is_audio_only:
                        status_placeholder.success("✅ Audio converted and ready to download!")
                    else:
                        status_placeholder.success("✅ Video downloaded successfully!")
                    progress.empty(); log_area.empty()
                else:
                    st.warning("❌ Download completed but file not found.")
                    st.error("Debug info:")
                    st.write(f"file_out: {file_out}")
                    st.write(f"temp_files tracked: {st.session_state.temp_files}")
                    st.write(f"is_audio_only: {is_audio_only}")
                    temp_dir = tempfile.gettempdir()
                    recent_files = []
                    for ext in ['*.mp3', '*.mp4', '*.m4a', '*.webm']:
                        files = glob.glob(os.path.join(temp_dir, ext))
                        for f in files:
                            if os.path.getmtime(f) > (time.time() - 600):
                                recent_files.append(f)
                    st.write(f"Recent temp files: {recent_files}")
            else:
                st.error(f"❌ Download failed with return code: {ret}")
                progress.empty(); log_area.empty()

        except ytdlp.utils.DownloadError as e:
            st.error(f"❌ Download Error: {str(e)}")
            progress.empty(); log_area.empty()
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            progress.empty(); log_area.empty()

    # ====== LOG EXPANDER ======
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
                    if file_size < 1024:
                        size_str = f"{file_size} B"
                    elif file_size < 1024 * 1024:
                        size_str = f"{file_size / 1024:.1f} KB"
                    elif file_size < 1024 * 1024 * 1024:
                        size_str = f"{file_size / (1024 * 1024):.1f} MB"
                    else:
                        size_str = f"{file_size / (1024 * 1024 * 1024):.1f} GB"
                    button_label = f"📥 Download {'Audio' if st.session_state.get('last_download_type')=='Audio' else 'Video'} ({size_str})"
                    st.download_button(
                        label=button_label,
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
    col1, col2, col3 = st.columns([1, 4, 1])
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
        <h3 style="margin: 0 0 0.5rem 0; font-weight: 600; text-align: center; color: inherit;">
            How To Download Videos
        </h3>
        <div style="
            background: rgba(255,255,255,0.1);
            padding: 1.5rem;
            border-radius: 10px;
            margin: 0.5rem 0;
            display: flex;
            justify-content: center;
        ">
            <div style="text-align: left;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="
                        background: #28a745; color: white; width: 30px; height: 30px; border-radius: 50%;
                        display: flex; align-items: center; justify-content: center; margin-right: 1rem; font-weight: bold;
                    ">1</span>
                    <span style="font-size: 1.1rem; color: inherit;">Copy Facebook or YouTube video</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="
                        background: #007bff; color: white; width: 30px; height: 30px; border-radius: 50%;
                        display: flex; align-items: center; justify-content: center; margin-right: 1rem; font-weight: bold;
                    ">2</span>
                    <span style="font-size: 1.1rem; color: inherit;">Paste Url in the input box above</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="
                        background: #FFC107; color: #333; width: 30px; height: 30px; border-radius: 50%;
                        display: flex; align-items: center; justify-content: center; margin-right: 1rem; font-weight: bold;
                    ">3</span>
                    <span style="font-size: 1.1rem; color: inherit;">Press Enter to start download video</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

        progress = st.empty()
        log_area = st.empty()

# ===================== FOOTER =====================
st.markdown("""
<div style="
    position: fixed; bottom: 0; left: 0; right: 0; background: #f9f9f9;
    border-top: 1px solid #e0e0e0; text-align: center; padding: 10px 0;
    color: #666; font-size: 0.85em; z-index: 1000; box-shadow: none; backdrop-filter: none;
">
    <p style="margin: 0;">Copyright © hieuvoquoc@gmail.com (V1.06 - IPv4+AndroidClient+Cookies/Proxy)</p>
</div>
""", unsafe_allow_html=True)