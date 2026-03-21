import threading
import uuid
import time


class Job:
  id: str = str(uuid.uuid4())[:8]
  status: str = 'queued'
  thumbnail: str = None
  title: str = None
  url: str = None
  progress: int = 0
  speed: str = '0b/s'
  eta: str = '...'
  quality_options: list[str] = []
  created_at:float = time.time()
  filename: str =  ''
  filepath: str = ''
  quality: str = ''
  error: str = ''

  def __init__(self, title, url, quality, quality_options, thumbnail):
    self.title = title
    self.url = url
    self.quality = quality
    self.quality_options = quality_options
    self.thumbnail = thumbnail
  
  def download(self, quality):

    pass

  def cancel():
    pass

  def json(self):
    return {
      "id": self.id,
      "status": self.status,
      "thumbnail": self.thumbnail,
      "title": self.title,
      "url": self.url,
      "progress": self.progress,
      "speed": self.speed,
      "eta": self.eta,
      "quality_options": self.quality_options,
      "created_at": self.created_at,
      "filename": self.filename,
      "filepath": self.filepath,
      "quality": self.quality,
      "error": self.error,
    }
    

class JobManager:
  lock = threading.Lock()
  jobs: dict[str, Job] = {}
  
  def create_job(self, title, url, quality, quality_options, thumbnail) -> Job:
    job = Job(title, url, quality, quality_options, thumbnail)
    
    with self.lock:
      self.jobs[job.id] = job
    
    return job
  
  def get_job(self, id: str):
    return self.jobs.get(id)

  def clear(self):
    with self.lock:
      for job in self.jobs:
        job.cancel()
      self.jobs.clear()

  def load(self, json):
    self.clear()

    with self.lock:
      for x in json:
        job = Job(
          x.get("title"),
          x.get("url"),
          x.get("quality"),
          x.get("quality_options"),
          x.get("thumbnail")
        )

        job.id = x.get("id")
        job.status = x.get("status")
        job.progress = x.get("progress")
        job.speed = x.get("speed")
        job.eta = x.get("eta")
        job.created_at = x.get("created_at")
        job.filename = x.get("filename")
        job.filepath = x.get("filepath")
        job.error = x.get("error")

        self.jobs.append(job)

  def json(self):
    return [self.jobs[id].json() for id in self.jobs]