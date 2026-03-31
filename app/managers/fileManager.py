from yt_dlp import YoutubeDL
import uuid
import time
import os
import json

import vars
import utils

class File:
    title = ''
    thumbnail = ''
    source = ''
    site = ''
    quality_options: list[str] = []
    filename: str =  ''
    downloaded: bool = False
    quality: str = ''


    def __init__(self, source, filename, title, thumbnail, quality_options):
        self.created_at = time.time()
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.source = source
        self.site = utils.detect_site(source)
        self.filename = filename
        self.thumbnail = thumbnail
        self.quality_options = quality_options

    def filepath(self):
        return os.path.join(vars.USER_DOWNLOAD_DIR, f"{self.id}_{self.filename}")

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
            "filepath": self.filepath(),
            "created_at": self.created_at,
            "downloaded": self.downloaded,
            "quality": self.quality,
            "site": self.site
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
        for l_file in os.listdir(vars.USER_DOWNLOAD_DIR):
            if l_file.endswith(".part") or l_file.endswith(".tmp"): continue

            id = l_file.split("_")[0]
            file = self.get_file(id)
            if not file: continue
            
            file.downloaded = True


    def fetch_and_save(self, url: str) -> File:
        """Fetch video info without downloading."""
    
        opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'proxy': vars.PROXY,
            **({'cookiefile': vars.COOKIE_FILE} if vars.COOKIE_FILE and os.path.exists(vars.COOKIE_FILE) else {}),
            'nocheckcertificate': bool(vars.PROXY),
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
            # print(formats)
            # Build quality options
            quality_set = set()
            for f in formats:
                height = f.get('height')
                if height and f.get("vcodec"): quality_set.add(f"{height}p")
                
            quality_options = sorted(quality_set, key=lambda x: int(x.replace('p','')), reverse=True)
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
  