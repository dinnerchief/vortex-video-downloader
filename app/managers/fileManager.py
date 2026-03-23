from yt_dlp import YoutubeDL
import uuid
import time
import os

from vars import *

class File:
    id = str(uuid.uuid4())[:8]
    title = ''
    thumbnail = ''
    source = ''
    quality_options: list[str] = []
    created_at:float = time.time()
    filename: str =  ''
    downloaded: bool = False


    def __init__(self, source, filename, title, thumbnail, quality_options):
        self.title = title
        self.source = source
        self.filename = f"{self.id}_{filename}"
        self.thumbnail = thumbnail
        self.quality_options = quality_options

    def filepath(self):
        return os.path.join(USER_DOWNLOAD_DIR, self.filename)

    def remove_locally(self):
        fp = self.filepath()
        if os.path.exists(fp):
            os.remove(fp)
        self.downloaded = False
        return True

    def json(self):
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "thumbnail": self.thumbnail,
            "quality_options": self.quality_options,
            "filename": self.filename,
            "created_at": self.created_at
        }

class FileManager:
    files: dict[str, File] = {}

    def get_file(self, id: str):
        return self.files.get(id)
    
    def remove_file(self, id: str, include_local = False):
        if include_local:
            file = self.get_file(id)
            file.remove_locally()

        del self.files[id]
        return True

    def sync_local_files(self):
        # Reset downloaded status
        for id in self.files:
            self.files[id].downloaded = False

        # Refresh downloaded status
        for l_file in os.listdir(USER_DOWNLOAD_DIR):
            id = l_file.split("_")[0]
            self.files[id].downloaded = True


    def fetch_and_save(self, url: str) -> File:
        """Fetch video info without downloading."""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'proxy': PROXY,
            **({'cookiefile': COOKIE_FILE} if COOKIE_FILE and os.path.exists(COOKIE_FILE) else {}),
            'nocheckcertificate': bool(PROXY),
            'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            },
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                raise ValueError("Could not extract info")
            
            filename = ydl.prepare_filename(info)

            formats = info.get('formats', [])
            # Build quality options
            quality_map = {}
            for f in formats:
                height = f.get('height')
                if height and f.get('vcodec') != 'none':
                    label = f"{height}p"
                    if label not in quality_map:
                        quality_map[label] = f.get('format_id')
            
            quality_options = sorted(quality_map.keys(), key=lambda x: int(x.replace('p','')), reverse=True)
            if not quality_options:
                quality_options = ['best']

            # data = {
            #     'type': 'video',
            #     'title': info.get('title', 'Unknown Title'),
            #     'thumbnail': info.get('thumbnail', ''),
            #     'duration': info.get('duration', 0),
            #     'uploader': info.get('uploader', ''),
            #     'view_count': info.get('view_count', 0),
            #     'description': (info.get('description') or '')[:300],
            #     'quality_options': quality_options,
            #     'webpage_url': info.get('webpage_url', url),
            #     'extractor': info.get('extractor_key', ''),
            # }

            file = File(
                url, 
                filename,
                info.get('title', 'Unknown Title'), 
                info.get('thumbnail', ''),
                quality_options
            )
            self.files[file.id] = file
            return file
    
    def json(self):
        return [self.files[id].json() for id in self.files]
  