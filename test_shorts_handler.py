#!/usr/bin/env python3
"""
Test script specifically for YouTube Shorts URLs
"""

import yt_dlp as ytdlp
import tempfile
import os
from pathlib import Path

def test_shorts_url_conversion(shorts_url):
    """Test converting shorts URL to regular format"""
    
    print(f"🔄 Testing Shorts URL conversion...")
    print(f"Original: {shorts_url}")
    
    # Convert shorts URL
    if "youtube.com/shorts/" in shorts_url:
        video_id = shorts_url.split("/shorts/")[-1].split("?")[0]
        regular_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"Converted: {regular_url}")
        return regular_url
    
    return shorts_url

def test_shorts_download_strategies(video_url):
    """Test multiple strategies specifically for shorts"""
    
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Temp directory: {temp_dir}")
    
    # Convert URL if needed
    original_url = video_url
    if "/shorts/" in video_url:
        video_url = test_shorts_url_conversion(video_url)
    
    strategies = [
        {
            "name": "Mobile iOS (Shorts Optimized)",
            "options": {
                "quiet": False,
                "nocheckcertificate": True,
                "socket_timeout": 60,
                "retries": 5,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
                },
                "format": "best[height<=720]/best",
                "outtmpl": f"{temp_dir}/%(title)s-mobile.%(ext)s",
                "geo_bypass": True,
                "extractor_args": {
                    "youtube": {
                        "skip": ["dash", "hls"]
                    }
                }
            }
        },
        {
            "name": "Basic Mobile Strategy",
            "options": {
                "quiet": False,
                "nocheckcertificate": True,
                "socket_timeout": 90,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
                },
                "format": "worst[height<=480]/worst",
                "outtmpl": f"{temp_dir}/%(title)s-android.%(ext)s",
                "geo_bypass": True
            }
        },
        {
            "name": "Info Extraction Only",
            "options": {
                "quiet": True,
                "nocheckcertificate": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
                }
            }
        }
    ]
    
    print(f"\n🎯 Testing {len(strategies)} strategies for: {video_url}")
    
    for i, strategy in enumerate(strategies, 1):
        try:
            print(f"\n📋 Strategy {i}: {strategy['name']}")
            
            if strategy["name"] == "Info Extraction Only":
                # Just test info extraction
                with ytdlp.YoutubeDL(strategy["options"]) as ydl:
                    info = ydl.extract_info(video_url, download=False)
                    
                print("✅ Info extraction successful!")
                print(f"   Title: {info.get('title', 'Unknown')}")
                print(f"   Duration: {info.get('duration', 0)} seconds")
                print(f"   View count: {info.get('view_count', 'Unknown')}")
                
                formats = info.get('formats', [])
                video_formats = [f for f in formats if f.get('vcodec') != 'none']
                print(f"   Available formats: {len(formats)} total, {len(video_formats)} video")
                
                continue
            
            # Try download
            with ytdlp.YoutubeDL(strategy["options"]) as ydl:
                ret = ydl.download([video_url])
                
            if ret == 0:
                print("✅ DOWNLOAD SUCCESSFUL!")
                
                # Check files
                files = list(Path(temp_dir).glob("*"))
                success_files = []
                for f in files:
                    if f.suffix in ['.mp4', '.webm', '.mkv'] and f.stat().st_size > 1000:
                        success_files.append(f)
                        print(f"   📄 Downloaded: {f.name} ({f.stat().st_size:,} bytes)")
                
                if success_files:
                    cleanup_temp_files(temp_dir)
                    return True
            else:
                print(f"❌ Download failed with return code: {ret}")
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ FAILED: {error_msg}")
            
            if "403" in error_msg or "Forbidden" in error_msg:
                print("   🚫 403 Forbidden")
            elif "Unsupported URL" in error_msg:
                print("   🔗 URL format issue")
            elif "Failed to extract" in error_msg:
                print("   📊 Extraction failed")
    
    cleanup_temp_files(temp_dir)
    return False

def cleanup_temp_files(temp_dir):
    """Clean up temp files"""
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print(f"🧹 Cleaned up: {temp_dir}")
    except Exception as e:
        print(f"⚠️ Cleanup failed: {e}")

if __name__ == "__main__":
    print("🚀 YouTube Shorts Download Test")
    print("=" * 50)
    
    # Test URLs - both shorts and regular
    test_urls = [
        "https://www.youtube.com/shorts/DaMMkhZLL14",  # Shorts URL
        "https://www.youtube.com/watch?v=DaMMkhZLL14",  # Regular URL  
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Backup
    ]
    
    success_count = 0
    for i, url in enumerate(test_urls, 1):
        print(f"\n🎥 Test {i}/{len(test_urls)}")
        print(f"URL: {url}")
        print("-" * 40)
        
        if test_shorts_download_strategies(url):
            success_count += 1
            print("🎉 SUCCESS! This strategy works!")
            break
        else:
            print("💔 All strategies failed for this URL")
    
    print(f"\n📊 Final Results: {success_count} successful downloads")
    
    if success_count > 0:
        print("✅ YouTube Shorts handling is working!")
        print("📱 Key factors: Mobile User-Agent + URL conversion")
    else:
        print("❌ All URLs failed - YouTube blocking is very strong")
        print("💡 Try Facebook videos or wait and retry later")