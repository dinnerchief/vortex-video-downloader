import os
import enum
class STATUS(enum.Enum):
  ERROR = 'error'
  QUEUED = 'queued'
  DOWNLOADING = 'downloading'
  DONE = 'done'


# Path to a Netscape-format cookies.txt file (optional)
COOKIE_FILE = ''

# Set your proxy here, e.g. 'http://127.0.0.1:2090' or 'socks5://127.0.0.1:1080'
# Leave as empty string '' to connect directly
PROXY = ''

STATE_FILE = os.path.join(os.path.dirname(__file__), 'vortex_state.json')

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

THUMBNAIL_DIR = os.path.join(os.path.dirname(__file__), '.thumbnails')
os.makedirs(THUMBNAIL_DIR, exist_ok=True)


# User-configurable download folder
USER_DOWNLOAD_DIR = DOWNLOAD_DIR

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"