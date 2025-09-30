#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import yt_dlp as ytdlp
except Exception as e:
    print("Missing dependency 'yt-dlp'. Install with: pip install -r requirements.txt", file=sys.stderr)
    raise

def build_opts(
    outtmpl: str,
    cookies: Optional[str],
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
        "consoletitle": True,
        "nocheckcertificate": no_check_certificate,
        "source_address": None,
        "retries": retries,
        "fragment_retries": retries,
        "continuedl": True,
        "concurrent_fragment_downloads": concurrent_fragments or 3,
        "ratelimit": None,
        "http_headers": {
            # A realistic UA helps reduce site-side blocks
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        },
        "progress_hooks": [progress_hook],
        "format": fmt,
        "quiet": False,
        "no_warnings": True,
    }
    if rate_limit:
        # yt-dlp expects bytes per second, but accepts strings like "1M"
        opts["ratelimit"] = rate_limit
    if cookies:
        opts["cookiefile"] = cookies
    if proxy:
        opts["proxy"] = proxy
    return opts

def progress_hook(d):
    if d.get("status") == "downloading":
        # Print a compact, single-line progress (yt-dlp already prints rich progress to TTY)
        pass
    elif d.get("status") == "finished":
        filename = d.get("filename")
        print(f"\nDone downloading: {filename}")

def ensure_download_dir(path_tmpl: str):
    # Extract base directory from template; create if needed
    p = Path(path_tmpl)
    if "%(" in path_tmpl:
        # Template contains variables; ensure base dir exists if it looks like one
        base = Path(path_tmpl.split("%(")[0]).expanduser()
        if base and not str(base).strip():
            return
        if base and not base.exists():
            base.mkdir(parents=True, exist_ok=True)
    else:
        Path(path_tmpl).parent.mkdir(parents=True, exist_ok=True)

def download(url: str, opts: Dict[str, Any]) -> int:
    ensure_download_dir(opts.get("outtmpl", "downloads/%(title).80s-%(id)s.%(ext)s"))
    try:
        with ytdlp.YoutubeDL(opts) as ydl:
            return 0 if ydl.download([url]) == 0 else 1
    except ytdlp.utils.DownloadError as e:
        print(f"DownloadError: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 3

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Download a Facebook video (with permission) using yt-dlp."
    )
    parser.add_argument("url", help="Facebook video URL")
    parser.add_argument("--cookies", help="Path to cookies.txt (Netscape format) for private videos")
    parser.add_argument("--template", default="downloads/%(title).80s-%(id)s.%(ext)s",
                        help="Output filename template (yt-dlp format)")
    parser.add_argument("--format", default="bv*+ba/b",
                        help="Desired format (yt-dlp format selector). e.g. 'mp4' or 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4'")
    parser.add_argument("--rate-limit", dest="rate_limit", default=None,
                        help="Max download rate, e.g. '1M' or '500K'")
    parser.add_argument("--concurrent-fragments", type=int, default=3,
                        help="Concurrent fragment downloads (lower if network/storage is slow)")
    parser.add_argument("--retries", type=int, default=10, help="Retry count for network/fragment errors")
    parser.add_argument("--proxy", default=None, help="HTTP proxy URL if needed, e.g. http://127.0.0.1:8888")
    parser.add_argument("--no-check-certificate", action="store_true", 
                        help="Skip SSL certificate verification")

    args = parser.parse_args(argv)
    opts = build_opts(
        outtmpl=args.template,
        cookies=args.cookies,
        fmt=args.format,
        rate_limit=args.rate_limit,
        concurrent_fragments=args.concurrent_fragments,
        retries=args.retries,
        proxy=args.proxy,
        no_check_certificate=args.no_check_certificate
    )
    return download(args.url, opts)

if __name__ == "__main__":
    raise SystemExit(main())
