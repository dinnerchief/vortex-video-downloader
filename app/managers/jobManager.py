from yt_dlp import YoutubeDL
from .fileManager import File

import threading
import uuid
import os

import vars
from utils import *


class Job:
  id: str = str(uuid.uuid4())[:8]
  status: str = vars.STATUS.QUEUED.value
  url: str = None
  progress: int = 0
  speed: str = '0b/s'
  eta: str = '...'
  quality: str = ''
  error: str = ''
  file_id: str = None
  filename: str = ''

  def __init__(self, file_id: str, source: str, filename: str):
    self.file_id = file_id
    self.url = source
    self.filename = filename
  
  def set_error(self, reason="Unknown error"):
    self.status = vars.STATUS.ERROR.value
    self.error = reason
    self.progress = 0

  def download(self, quality):
    if self.status not in (vars.STATUS.QUEUED.value, vars.STATUS.ERROR.value):
        return None # FIX

    def do_download(job: Job):
      """Perform the actual download in a thread."""
      job.status = vars.STATUS.DOWNLOADING.value
      job.progress = 0
      job.speed = ''
      job.eta = ''

      # output_tmpl = os.path.join(USER_DOWNLOAD_DIR, f'{self.file_id}_%(title)s.%(ext)s')
      output_tmpl = os.path.join(vars.USER_DOWNLOAD_DIR, f'{self.id}.tmp')

      def progress_hook(d):
          if d['status'] == 'downloading':
              pct = 0
              total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
              downloaded = d.get('downloaded_bytes', 0)
              if total:
                  pct = int(downloaded / total * 100)
              speed = strip_ansi(d.get('_speed_str', ''))
              eta = strip_ansi(d.get('_eta_str', ''))

              job.progress = pct
              job.speed = speed
              job.eta = eta

          elif d['status'] == 'finished':
              job.progress = 100
              job.speed = ''
              job.eta = 'Finishing...'

      fmt = 'bestvideo+bestaudio/best'
      if quality and quality != 'best':
          h = quality.replace('p', '')
          fmt = f'bestvideo[height<={h}]+bestaudio/best[height<={h}]/bestvideo+bestaudio/best'

      opts = {
          'format': fmt,
          'outtmpl': output_tmpl,
          'progress_hooks': [progress_hook],
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

      try:
          with YoutubeDL(opts) as ydl:
              # info = ydl.extract_info(job.url, download=True)
              # filename = ydl.prepare_filename(info)
              # Find actual file (may have been merged/converted)
              # base = os.path.splitext(filename)[0]
              # final = None
              # for ext in ['.mp4', '.mkv', '.webm', '.m4a', '.mp3']:
              #     candidate = base + ext
              #     if os.path.exists(candidate):
              #         final = candidate
              #         break
              # if not final:
              #     # Search by job_id prefix
              #     for f in os.listdir(USER_DOWNLOAD_DIR):
              #         if f.startswith(job.id):
              #             final = os.path.join(DOWNLOAD_DIR, f)
              #             break
              
              ydl.download([job.url])
              os.rename(
                os.path.join(vars.USER_DOWNLOAD_DIR, f"{self.id}.tmp"),
                os.path.join(vars.USER_DOWNLOAD_DIR, self.filename)
              )

              job.status = vars.STATUS.DONE.value
              job.progress = 100
              job.speed = ''
              job.eta = ''

      except Exception as e:
          job.set_error(str(e))


    t = threading.Thread(target=do_download, args=[self], daemon=True)
    t.start()

    return True

  def cancel():
    pass

  def json(self):
    return {
      "id": self.id,
      "eta": self.eta,
      "url": self.url,
      "error": self.error,
      "speed": self.speed,
      "status": self.status,
      "quality": self.quality,
      "filename": self.filename,
      "progress": self.progress,
    }
    

class JobManager:
  lock = threading.Lock()
  jobs: dict[str, Job] = {}
  _index_job_by_file: dict[str, str] = {}
  
  def create_job(self, file: File):
    job = Job(file.id, file.source, file.filename)
    
    self._index_job_by_file[file.id] = job.id

    with self.lock:
      self.jobs[job.id] = job
    
    return job
  
  def get_job(self, id: str):
    return self.jobs.get(id)
  
  def get_job_by_file(self, file_id: str):
    return self._index_job_by_file.get(file_id)

  def remove_job(self, id: str):
    job = self.get_job(id)
    if job is None:
      return False
    
    job.cancel()
    del self._index_job_by_file[job.file_id]
    del self.jobs[id]

    return True

  def clear(self):
    with self.lock:
      for job in self.jobs:
        job.cancel()
      self.jobs.clear()

  def json(self):
    return [self.jobs[id].json() for id in self.jobs]