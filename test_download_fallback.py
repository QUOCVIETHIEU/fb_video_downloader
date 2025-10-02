#!/usr/bin/env python3
"""
Test script for YouTube download fallback strategies
Specifically tests the download phase, not just info extraction
"""

import yt_dlp as ytdlp
import random
import time
import tempfile
import os
from pathlib import Path

def test_download_strategies(video_url):
    """Test multiple download strategies for 403 bypass"""
    
    print(f"🎯 Testing download strategies for: {video_url}")
    
    # Create temp directory for downloads
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Temp directory: {temp_dir}")
    
    strategies = [
        {
            "name": "Enhanced Headers Strategy",
            "options": {
                "quiet": False,
                "nocheckcertificate": True,
                "socket_timeout": 60,
                "retries": 10,
                "fragment_retries": 10,
                "extractor_retries": 5,
                "sleep_interval": 3,
                "max_sleep_interval": 15,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Origin": "https://www.youtube.com",
                    "Referer": "https://www.youtube.com/"
                },
                "format": "worst[height<=360]/worst",  # Low quality for faster test
                "outtmpl": f"{temp_dir}/%(title)s-enhanced.%(ext)s",
                "geo_bypass": True,
                "geo_bypass_country": "US",
                "youtube_include_dash_manifest": False,
                "concurrent_fragment_downloads": 1,
                "skip_unavailable_fragments": True,
                "abort_on_unavailable_fragment": False
            }
        },
        {
            "name": "Throttled Download Strategy",
            "options": {
                "quiet": False,
                "nocheckcertificate": True,
                "socket_timeout": 120,
                "retries": 15,
                "fragment_retries": 15,
                "sleep_interval": 5,
                "max_sleep_interval": 20,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
                },
                "format": "worst[height<=240]/worst",
                "outtmpl": f"{temp_dir}/%(title)s-throttled.%(ext)s",
                "ratelimit": "200K",  # Very slow to avoid detection
                "concurrent_fragment_downloads": 1,
                "geo_bypass": True
            }
        },
        {
            "name": "Mobile User-Agent Strategy", 
            "options": {
                "quiet": False,
                "nocheckcertificate": True,
                "socket_timeout": 90,
                "retries": 8,
                "sleep_interval": 4,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
                },
                "format": "worst[height<=240]/worst",
                "outtmpl": f"{temp_dir}/%(title)s-mobile.%(ext)s",
                "geo_bypass": True,
                "concurrent_fragment_downloads": 1
            }
        }
    ]
    
    for i, strategy in enumerate(strategies, 1):
        try:
            print(f"\n📋 Strategy {i}: {strategy['name']}")
            print("   ⏳ Starting download...")
            
            # Add delay between strategies
            if i > 1:
                delay = random.uniform(2, 5)
                print(f"   🕐 Waiting {delay:.1f}s before attempt...")
                time.sleep(delay)
            
            with ytdlp.YoutubeDL(strategy["options"]) as ydl:
                ret = ydl.download([video_url])
                
            if ret == 0:
                print("   ✅ DOWNLOAD SUCCESSFUL!")
                
                # Check if file was created
                download_files = list(Path(temp_dir).glob("*"))
                if download_files:
                    for f in download_files:
                        print(f"   📄 Downloaded: {f.name} ({f.stat().st_size} bytes)")
                    
                    # Cleanup and return success
                    cleanup_temp_files(temp_dir)
                    return True
                else:
                    print("   ⚠️ Download reported success but no file found")
            else:
                print(f"   ❌ Download failed with return code: {ret}")
                
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ FAILED: {error_msg}")
            
            # Analyze error type
            if "403" in error_msg or "Forbidden" in error_msg:
                print("   🚫 403 Forbidden - YouTube blocking download")
            elif "404" in error_msg:
                print("   🔍 Video not found or removed")
            elif "throttl" in error_msg.lower():
                print("   🐌 Download throttling detected")
            elif "timeout" in error_msg.lower():
                print("   ⏰ Timeout - network issue or blocking")
            elif "unavailable" in error_msg.lower():
                print("   📵 Video unavailable in region")
    
    # Cleanup
    cleanup_temp_files(temp_dir)
    print("\n❌ All download strategies failed!")
    return False

def cleanup_temp_files(temp_dir):
    """Clean up temporary files"""
    try:
        import shutil
        shutil.rmtree(temp_dir)
        print(f"🧹 Cleaned up temp directory: {temp_dir}")
    except Exception as e:
        print(f"⚠️ Cleanup failed: {e}")

if __name__ == "__main__":
    # Test URLs
    test_urls = [
        "https://www.youtube.com/watch?v=DaMMkhZLL14",  # Your problematic URL
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll backup
    ]
    
    print("🚀 YouTube Download Fallback Test")
    print("=" * 60)
    
    success_count = 0
    for i, url in enumerate(test_urls, 1):
        print(f"\n🎥 Test {i}/{len(test_urls)}: Testing download...")
        if test_download_strategies(url):
            success_count += 1
            print("✅ This URL works with fallback system!")
            break  # Stop on first success
        else:
            print("❌ This URL failed all strategies")
        
        if i < len(test_urls):
            print("\n" + "-" * 60)
    
    print(f"\n📊 Final Result: {success_count}/{len(test_urls)} URLs successful")
    
    if success_count == 0:
        print("\n💡 Recommendations:")
        print("   1. YouTube is heavily blocking cloud downloads")
        print("   2. Try Facebook videos instead")  
        print("   3. Consider using a VPN/proxy service")
        print("   4. Wait and retry later (blocking may be temporary)")
    else:
        print("\n✅ Fallback system is working!")
        print("   The enhanced strategies can bypass some YouTube blocks")