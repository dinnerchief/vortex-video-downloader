from yt_dlp import YoutubeDL

from subprocess import Popen, PIPE
from pathlib import Path

import threading
import asyncio 
import uuid
import json
import time
import os

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
  status: vars.STATUS = vars.STATUS.QUEUED

  progress: int = 0
  speed: str = ''
  eta: str = ''
  error: str = ''

  process: asyncio.subprocess.Process | None = None


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
    return os.path.join(vars.USER_DOWNLOAD_DIR, f"{self.id}_{self.title}.mp4")

  def remove_locally(self):
    fp = self.filepath()
    if os.path.exists(fp):
      os.remove(fp)
    self.downloaded = False
    return True

  def set_error(self, reason="Unknown error"):
    self.status = vars.STATUS.ERROR
    self.error = reason
    self.progress = 0

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
      "site": self.site,
      "status": self.status.value,
      "eta": self.eta,
      "speed": self.speed,
      "progress": self.progress,
      "error": self.error
    }

class FileManager:
  files: dict[str, File] = {}

  def __init__(self):
    self.loop = asyncio.new_event_loop()
    def _run(loop):
      asyncio.set_event_loop(loop)
      loop.run_forever()
    self.thread = threading.Thread(target=_run, args=(self.loop,), daemon=True)
    self.thread.start()

  def get_file(self, id: str):
    return self.files.get(id)
  
  def remove_file(self, file: File, include_local = False):
    self.cancel(file)

    if include_local:
      file.remove_locally()

    del self.files[file.id]
    return True

  def sync_local_files(self):
    # Reset downloaded status
    for id in self.files:
      file = self.get_file(id)
      file.downloaded = False
      if file.status == vars.STATUS.DONE:
        file.status = vars.STATUS.QUEUED

    # Refresh downloaded status
    for l_file in os.listdir(vars.USER_DOWNLOAD_DIR):
      if l_file.endswith(".part") or l_file.endswith(".tmp") or l_file.endswith(".ytdl"): continue

      id = l_file.split("_")[0]
      file = self.get_file(id)
      if not file: continue
      
      file.downloaded = True
      if file.status == vars.STATUS.QUEUED:
        file.status = vars.STATUS.DONE

  def download(self, file: File, quality: str):
    fmt = 'bestvideo+bestaudio/best'
    if quality and quality != 'best':
      h = quality.replace('p', '')
      fmt = f'bestvideo[height<={h}]+bestaudio/best[height<={h}]/bestvideo+bestaudio/best'

    opts = {
      'format': fmt,
      'outtmpl': file.filepath(),
      'quiet': True,
      'no_warnings': True,
      'proxy': vars.PROXY,
      **({'cookiefile': vars.COOKIE_FILE} if vars.COOKIE_FILE and os.path.exists(vars.COOKIE_FILE) else {}),
      'nocheckcertificate': bool(vars.PROXY),
      'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
      },
      'socket_timeout': 60,
      'retries': 5,
      'merge_output_format': 'mp4',
      'keepvideo': False,
      'postprocessors': [{
        'key': 'FFmpegVideoConvertor',
        'preferedformat': 'mp4',
      }],
    }

    async def download_process():
      downloader_file = str(Path(__file__).resolve().parents[1] / "downloader.py")
      try:
        proc = await asyncio.create_subprocess_exec(
          "python3", "-u", downloader_file, file.source, json.dumps(opts),
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.STDOUT,
        )
      except Exception as e:
        file.status = vars.STATUS.ERROR
        file.error = f"Failed to start subprocess: {e}"
        return

      file.process = proc

      try:
        assert proc.stdout is not None
        while True:
          line = await proc.stdout.readline()
          if not line:  # EOF
            break
          try:
            text = line.decode(errors="replace").strip()
          except Exception:
            text = line.decode("utf-8", "replace").strip()

          idx = text.find("{")
          if idx == -1:
            print(f"[file-{file.id}] non-json stdout: {text}")
            continue

          json_str = text[idx:]
          try:
            data = json.loads(json_str)
          except json.JSONDecodeError:
            print(f"[file-{file.id}] invalid json: {json_str}")
            continue

          file.status = vars.STATUS[data.get("status", vars.STATUS.DOWNLOADING.name)]
          file.error = data.get("error", "") or ""
          file.progress = data.get("progress", 0)
          file.eta = data.get("eta", "")
          file.speed = data.get("speed", "")

          if file.status != vars.STATUS.ERROR:
            print(f"[file-{file.id}] Process: status={file.status} speed={file.speed} progress={file.progress} eta={file.eta}")
          else:
            print(f"[file-{file.id}] Process: status={file.status} error={file.error} progress={file.progress}")

          if file.status in (vars.STATUS.ERROR, vars.STATUS.DONE):
            break

        rc = await proc.wait()
        if file.status not in (vars.STATUS.ERROR, vars.STATUS.DONE):
          # если процесс завершился без явного DONE/ERROR
          file.status = vars.STATUS.ERROR
          file.error = f"Subprocess exited with code {rc}"
        else:
          print(f"[file-{file.id}] Downloading proccess successfull done. RC={rc}")

      finally:
        if file.process is proc:
            file.process = None

    print(f'[file-{file.id}] Starting process: source="{file.source}" opts={json.dumps(opts)}')
    asyncio.run_coroutine_threadsafe(download_process(), self.loop)

    file.status = vars.STATUS.DOWNLOADING
    file.quality = quality

    return True


  def cancel(self, file: File):
    if file.process:
      file.process.terminate()
      file.process = None
      file.status = vars.STATUS.QUEUED
      file.progress = 0
      file.eta = ''
      file.speed = ''

    return True

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
      #   'type': 'video',
      #   'title': info.get('title', 'Unknown Title'),
      #   'thumbnail': info.get('thumbnail', ''),
      #   'duration': info.get('duration', 0),
      #   'uploader': info.get('uploader', ''),
      #   'view_count': info.get('view_count', 0),
      #   'description': (info.get('description') or '')[:300],
      #   'quality_options': quality_options,
      #   'webpage_url': info.get('webpage_url', url),
      #   'extractor': info.get('extractor_key', ''),
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
  