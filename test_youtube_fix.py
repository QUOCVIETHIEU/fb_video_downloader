#!/usr/bin/env python3
"""
Test script để kiểm tra các phương pháp bypass YouTube restrictions
"""

import yt_dlp as ytdlp

def test_youtube_methods():
    """Test các phương pháp khác nhau để tải YouTube"""
    
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll - video test phổ biến
    
    methods = [
        {
            "name": "Standard Method",
            "opts": {
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            }
        },
        {
            "name": "Android Client Method", 
            "opts": {
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android"]
                    }
                },
                "http_headers": {
                    "User-Agent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip"
                }
            }
        },
        {
            "name": "iOS Client Method",
            "opts": {
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,
                "extractor_args": {
                    "youtube": {
                        "player_client": ["ios"]
                    }
                },
                "http_headers": {
                    "User-Agent": "com.google.ios.youtube/17.31.4 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)"
                }
            }
        }
    ]
    
    for method in methods:
        print(f"\n🔄 Testing: {method['name']}")
        try:
            with ytdlp.YoutubeDL(method['opts']) as ydl:
                info = ydl.extract_info(test_url, download=False)
                print(f"✅ SUCCESS: {method['name']}")
                print(f"   Title: {info.get('title', 'Unknown')}")
                print(f"   Duration: {info.get('duration', 'Unknown')} seconds")
                return method['name']  # Return first successful method
        except Exception as e:
            print(f"❌ FAILED: {method['name']} - {str(e)[:100]}...")
    
    print("\n❌ All methods failed!")
    return None

if __name__ == "__main__":
    print("🧪 Testing YouTube download methods...")
    successful_method = test_youtube_methods()
    
    if successful_method:
        print(f"\n🎉 Recommended method: {successful_method}")
    else:
        print("\n😞 No methods worked. YouTube restrictions are too strong.")