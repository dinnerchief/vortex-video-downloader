# VORTEX — Video Downloader

A local web-based video downloader powered by yt-dlp. Supports YouTube, Vimeo,
Twitter/X, Instagram, TikTok, PornHub, Twitch, Reddit, and 1000+ more sites.

---

## Requirements

1. **Python 3.8+**

   Windows:
   - Download: https://www.python.org/downloads/
   - ⚠️ During install, check **"Add Python to PATH"**

   Linux (RHEL/CentOS/Fedora):
   - `dnf in -y python3 python3-pip`

   Linux (Debian/Ubuntu):
   - `apt install python3 python3-pip`

2. **ffmpeg** (optional but recommended for best quality / video merging)

   Windows:
   - Easy install via winget: `winget install ffmpeg`
   - Or download from: https://ffmpeg.org/download.html
   - Add the `bin` folder to your system PATH

   Linux (RHEL/CentOS/Fedora):
   - `dnf in -y ffmpeg-free`

   Linux (Debian/Ubuntu):
   - `apt install -y ffmpeg`

---

## How to Run

For Windows, just double-click **`start.bat`**

For Linux, make sure that the file is executable `chmod +x ./start`, then run `./start`

This will:
- Install/update Flask and yt-dlp automatically
- Start the local server on http://localhost:7860
- Open your browser automatically

---

## How to Use

1. Paste any video URL into the input box and press Enter or click ⚡ Fetch
2. Select your desired quality from the dropdown
3. Click the ▶ button to download the video
4. Use **Download All** to save all completed videos at once

---

## Files

- `start.bat`   — launcher (double-click this)
- `start`       — launcher (bash-script for linux)
- `app.py`      — Flask backend
- `static/`     — frontend web UI
- `downloads/`  — downloaded videos are saved here

---

## Troubleshooting

**"Python not found"** — Reinstall Python and check "Add to PATH"

**Videos download but no audio / low quality** — Install ffmpeg (see above)

**Site not working** — Update yt-dlp: open a terminal and run:
  `python3 -m pip install -U yt-dlp`

**Port already in use** — Edit `app.py`, change `port=7860` to another port like `7861`
