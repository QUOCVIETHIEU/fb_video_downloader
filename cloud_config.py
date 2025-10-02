# Streamlit Cloud Configuration
# Tệp này giúp tối ưu hóa app cho Streamlit Cloud

import os

# Environment variables for better cloud performance
os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
os.environ.setdefault('STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false')

# YouTube-DL specific optimizations for cloud
os.environ.setdefault('YTDL_OUTPUT_TEMPLATE', '%(title)s.%(ext)s')
os.environ.setdefault('YTDL_IGNORE_ERRORS', 'true')
os.environ.setdefault('YTDL_NO_CHECK_CERTIFICATE', 'true')

# Network timeout settings
os.environ.setdefault('REQUESTS_TIMEOUT', '30')
os.environ.setdefault('URLLIB3_DISABLE_WARNINGS', '1')

print("🔧 Streamlit Cloud configuration loaded successfully!")