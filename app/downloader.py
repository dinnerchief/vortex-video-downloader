from yt_dlp import YoutubeDL
from vars import STATUS

import utils
import json
import sys

def main(source, opts):
  opts = json.loads(opts)

  print(json.dumps({
    "status": STATUS.DOWNLOADING.name,
    "progress": 0,
    "speed": "",
    "eta": ""
  }))

  def progress_hook(d):
    if d['status'] == 'downloading':
      pct = 0
      total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
      downloaded = d.get('downloaded_bytes', 0)
      if total:
        pct = int(downloaded / total * 100)
      speed = utils.strip_ansi(d.get('_speed_str', ''))
      eta = utils.strip_ansi(d.get('_eta_str', ''))

      print(json.dumps({
        "status": STATUS.DOWNLOADING.name,
        "progress": pct,
        "speed": speed,
        "eta": eta
      }))

    elif d['status'] == 'finished':
      print(json.dumps({
        "status": STATUS.DOWNLOADING.name,
        "progress": 100,
        "speed": "",
        "eta": "Finishing..."
      }))

  opts = {
    **opts,
    'progress_hooks': [progress_hook],
  }

  try:
    with YoutubeDL(opts) as ydl:
      ydl.download([source])
      print(json.dumps({
        "status": STATUS.DONE.name,
        "progress": 100,
        "speed": "",
        "eta": ""
      }))

  except Exception as e:
    print(json.dumps({
      "status": STATUS.ERROR.name,
      "error": str(e)
    }))

if __name__ == "__main__":
  if len(sys.argv) < 3:
    print(f"usage: {sys.argv[0]} <url> <json_yt_dlp_options>")
    exit(1)
  main(sys.argv[1], sys.argv[2])