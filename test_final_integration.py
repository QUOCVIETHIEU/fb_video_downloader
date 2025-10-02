#!/usr/bin/env python3
"""
Final integration test for the complete 403 bypass system
Tests both info extraction and download with mobile user-agents
"""

import yt_dlp as ytdlp
import tempfile
import os
from pathlib import Path
import time

def test_complete_workflow(video_url):
    """Test complete workflow: info extraction + download"""
    
    print(f"🎯 Testing complete workflow for: {video_url}")
    
    # Step 1: Test info extraction
    print("\n📋 Step 1: Testing info extraction...")
    
    try:
        info_opts = {
            "quiet": True,
            "nocheckcertificate": True,
            "extractor_retries": 3,
            "socket_timeout": 30,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            },
            "geo_bypass": True
        }
        
        with ytdlp.YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
        print("✅ Info extraction successful!")
        print(f"   Title: {info.get('title', 'Unknown')}")
        print(f"   Duration: {info.get('duration', 0)} seconds")
        print(f"   Uploader: {info.get('uploader', 'Unknown')}")
        
        # Get available formats
        formats = info.get('formats', [])
        video_formats = [f for f in formats if f.get('vcodec') != 'none' and f.get('height')]
        print(f"   Available video formats: {len(video_formats)}")
        
    except Exception as e:
        print(f"❌ Info extraction failed: {e}")
        return False
    
    # Step 2: Test download with mobile user-agent
    print("\n📱 Step 2: Testing download with mobile user-agent...")
    
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Temp directory: {temp_dir}")
    
    try:
        download_opts = {
            "quiet": False,
            "nocheckcertificate": True,
            "socket_timeout": 90,
            "retries": 8,
            "sleep_interval": 4,
            "fragment_retries": 10,
            "extractor_retries": 5,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            },
            "format": "worst[height<=360]/worst",  # Low quality for faster test
            "outtmpl": f"{temp_dir}/%(title)s.%(ext)s",
            "geo_bypass": True,
            "concurrent_fragment_downloads": 1,
            "skip_unavailable_fragments": True,
            "abort_on_unavailable_fragment": False
        }
        
        with ytdlp.YoutubeDL(download_opts) as ydl:
            ret = ydl.download([video_url])
        
        if ret == 0:
            print("✅ Download successful!")
            
            # Check downloaded files
            download_files = list(Path(temp_dir).glob("*"))
            if download_files:
                for f in download_files:
                    if f.suffix in ['.mp4', '.webm', '.mkv'] and f.stat().st_size > 1000:
                        print(f"   📄 Downloaded: {f.name} ({f.stat().st_size:,} bytes)")
                        
                        # Cleanup
                        try:
                            import shutil
                            shutil.rmtree(temp_dir)
                        except:
                            pass
                        
                        return True
                
            print("⚠️ Download completed but no valid video file found")
        else:
            print(f"❌ Download failed with return code: {ret}")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Download failed: {error_msg}")
        
        if "403" in error_msg or "Forbidden" in error_msg:
            print("   🚫 Still getting 403 Forbidden")
        elif "404" in error_msg:
            print("   🔍 Video not found")
        
    # Cleanup
    try:
        import shutil
        shutil.rmtree(temp_dir)
    except:
        pass
    
    return False

def main():
    print("🚀 Complete 403 Bypass System Test")
    print("=" * 50)
    
    test_urls = [
        "https://www.youtube.com/watch?v=DaMMkhZLL14",  # Original problematic URL
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Backup test
    ]
    
    success_count = 0
    for i, url in enumerate(test_urls, 1):
        print(f"\n🎥 Test {i}/{len(test_urls)}")
        print("-" * 30)
        
        if test_complete_workflow(url):
            success_count += 1
            print("🎉 SUCCESS! This URL works with the new system!")
        else:
            print("💔 FAILED! This URL still doesn't work")
        
        # Wait between tests
        if i < len(test_urls):
            print("\n⏳ Waiting 5 seconds before next test...")
            time.sleep(5)
    
    print(f"\n📊 Final Results: {success_count}/{len(test_urls)} URLs successful")
    
    if success_count > 0:
        print("\n🎉 SUCCESS! The mobile user-agent strategy works!")
        print("✅ Your Streamlit Cloud deployment should now work better")
        print("📱 Key success factors:")
        print("   - Mobile User-Agent (iOS Safari)")
        print("   - Smart retry mechanisms") 
        print("   - Fragment handling")
        print("   - Proper timeout settings")
    else:
        print("\n😞 All tests failed. YouTube may be:")
        print("   - Blocking all cloud IPs completely")
        print("   - Using advanced bot detection")
        print("   - Temporarily having issues")
        print("\n💡 Alternatives:")
        print("   - Try Facebook videos instead")
        print("   - Use a different cloud provider")
        print("   - Wait and retry later")

if __name__ == "__main__":
    main()