# FB & YouTube Video Downloader - Streamlit App

> **Use responsibly.** Only download videos you own or have permission to save. Respect copyright, privacy, and platform Terms of Service.

## ✨ Features

- Download videos from Facebook and YouTube
- Multiple quality options (MP4 only for reliability)
- Audio-only downloads
- Advanced anti-detection system for cloud deployment
- Fallback mechanisms for 403 Forbidden errors
- Mobile-friendly interface with GO button
- User-friendly web interface

## 🚀 Quick Start

### Local Installation
1. Install Python 3.9+
2. Create a virtual env and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

### Streamlit Cloud Deployment
1. Push code to GitHub
2. Deploy on [share.streamlit.io](https://share.streamlit.io)
3. The app includes cloud-specific optimizations

## Private videos / login
If a video needs you to be logged-in, export cookies from your browser to a `cookies.txt` file (Netscape format), then pass `--cookies cookies.txt`:
```bash
python fb_downloader.py "<url>" --cookies cookies.txt --no-check-certificate
```
Tips to export cookies:
- Use a browser extension like "Get cookies.txt" for Chrome/Firefox.
- Make sure the cookies are from the same domain as the video page (e.g. `facebook.com`).  
  Keep your cookies private—**they grant access to your account**.

## Custom filename
You can change the filename template using `--template`. Defaults to:
```
downloads/%(title).80s-%(id)s.%(ext)s
```
Examples:
```bash
python fb_downloader.py "https://www.facebook.com/reel/1693153308013202" --template "downloads/%(uploader)s/%(upload_date)s-%(title)s.%(ext)s" --no-check-certificate
```
See more fields: https://github.com/yt-dlp/yt-dlp#output-template

## Common examples
```bash
# Best available quality (default)
python fb_downloader.py "<url>" --no-check-certificate

# Force MP4 if possible
python fb_downloader.py "<url>" --format "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4" --no-check-certificate

# Audio-only (if available)
python fb_downloader.py "<url>" --format "bestaudio/best" --template "downloads/%(title)s.%(ext)s" --no-check-certificate

python fb_downloader.py "https://www.facebook.com/reel/1239868574109827" --format "bestaudio/best" --template "downloads/%(title)s.%(ext)s" --no-check-certificate

# Throttled networks: lower concurrency, rate limit
python fb_downloader.py "<url>" --rate-limit "1M" --concurrent-fragments 1 --no-check-certificate
```

## Notes
- This tool uses `yt-dlp`, which supports Facebook URLs and many sites.
- Some videos may not be downloadable due to site changes or restrictions.
- Do **not** try to bypass DRM or other technical protection measures.
- **SSL Certificate Issues**: If you encounter SSL certificate errors, use the `--no-check-certificate` flag (already included in examples above).
- If downloads fail, try passing cookies, or update `yt-dlp`:
  ```bash
  pip install -U yt-dlp
  ```
