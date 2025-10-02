#!/usr/bin/env python3
"""
Test script cho Streamlit Cloud - Kiểm tra khả năng tải video YouTube
"""

import yt_dlp as ytdlp
import random
import time
import sys

def test_youtube_extraction(url):
    """Test multiple strategies for YouTube video extraction"""
    
    print(f"🔄 Testing URL: {url}")
    
    # Strategy 1: Standard approach with enhanced headers
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    strategies = [
        {
            "name": "Enhanced Headers Strategy",
            "opts": {
                "quiet": True,
                "nocheckcertificate": True,
                "extractor_retries": 3,
                "socket_timeout": 30,
                "http_headers": {
                    "User-Agent": random.choice(user_agents),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-us,en;q=0.5",
                    "Accept-Encoding": "gzip,deflate",
                    "Connection": "keep-alive",
                    "Cache-Control": "max-age=0",
                    "Upgrade-Insecure-Requests": "1"
                },
                "geo_bypass": True,
                "geo_bypass_country": "US"
            }
        },
        {
            "name": "Generic Extractor Strategy", 
            "opts": {
                "quiet": True,
                "force_generic_extractor": True,
                "nocheckcertificate": True,
                "http_headers": {
                    "User-Agent": "curl/7.68.0"
                }
            }
        },
        {
            "name": "Minimal Headers Strategy",
            "opts": {
                "quiet": True,
                "nocheckcertificate": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
                }
            }
        }
    ]
    
    for i, strategy in enumerate(strategies, 1):
        try:
            print(f"📋 Strategy {i}: {strategy['name']}")
            
            with ytdlp.YoutubeDL(strategy["opts"]) as ydl:
                info = ydl.extract_info(url, download=False)
                
            print("✅ SUCCESS!")
            print(f"   Title: {info.get('title', 'Unknown')}")
            print(f"   Duration: {info.get('duration', 0)} seconds")
            print(f"   View Count: {info.get('view_count', 'Unknown')}")
            print(f"   Uploader: {info.get('uploader', 'Unknown')}")
            
            # Count available formats
            formats = info.get('formats', [])
            video_formats = [f for f in formats if f.get('vcodec') != 'none']
            audio_formats = [f for f in formats if f.get('acodec') != 'none']
            
            print(f"   Available formats: {len(formats)} total ({len(video_formats)} video, {len(audio_formats)} audio)")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ FAILED: {error_msg}")
            
            # Check for specific error types
            if "403" in error_msg or "Forbidden" in error_msg:
                print("   → 403 Forbidden detected")
            elif "404" in error_msg or "Not Found" in error_msg:
                print("   → Video not found or removed")
            elif "Private" in error_msg or "private" in error_msg:
                print("   → Video is private")
            elif "region" in error_msg.lower():
                print("   → Geographic restriction detected")
            
            # Add delay between strategies
            if i < len(strategies):
                print("   ⏳ Waiting before next strategy...")
                time.sleep(2)
    
    print("❌ All strategies failed!")
    return False

if __name__ == "__main__":
    # Test URLs
    test_urls = [
        "https://www.youtube.com/watch?v=DaMMkhZLL14",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - always available
    ]
    
    print("🚀 YouTube Extraction Test for Streamlit Cloud")
    print("=" * 50)
    
    success_count = 0
    for url in test_urls:
        if test_youtube_extraction(url):
            success_count += 1
        print("-" * 50)
    
    print(f"📊 Result: {success_count}/{len(test_urls)} URLs successful")
    
    if success_count == 0:
        print("⚠️  All tests failed - YouTube may be blocking cloud servers")
        print("💡 Recommendations:")
        print("   1. Try Facebook videos instead (usually more reliable)")
        print("   2. Use different YouTube URLs") 
        print("   3. Consider using a proxy service")
        sys.exit(1)
    else:
        print("✅ At least some URLs work - system is functional!")
        sys.exit(0)