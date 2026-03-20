# VORTEX — Video Downloader

A local web-based video downloader powered by yt-dlp. Supports YouTube, Vimeo,
Twitter/X, Instagram, TikTok, PornHub, Twitch, Reddit, and 1000+ more sites.

---

## Requirements

1. **Python 3.8+**
   - Download: https://www.python.org/downloads/
   - ⚠️ During install, check **"Add Python to PATH"**

2. **ffmpeg** (optional but recommended for best quality / video merging)
   - Easy install via winget: `winget install ffmpeg`
   - Or download from: https://ffmpeg.org/download.html
   - Add the `bin` folder to your system PATH

---

## How to Run

Double-click **`start.bat`**

This will:
- Install/update Flask and yt-dlp automatically
- Start the local server on http://localhost:7860
- Open your browser automatically

---

## How to Use

1. Paste any video URL into the input box and press Enter or click ⚡ Fetch
2. Select your desired quality from the dropdown
3. Click **+ Add to Queue**
4. Once the download finishes, click the ⬇ button to save the file
5. Use **Download All** to save all completed videos at once

---

## Files

- `start.bat`   — launcher (double-click this)
- `app.py`      — Flask backend
- `static/`     — frontend web UI
- `downloads/`  — downloaded videos are saved here

---

## Troubleshooting

**"Python not found"** — Reinstall Python and check "Add to PATH"

**Videos download but no audio / low quality** — Install ffmpeg (see above)

**Site not working** — Update yt-dlp: open a terminal and run:
  `python -m pip install -U yt-dlp`

**Port already in use** — Edit `app.py`, change `port=7860` to another port like `7861`
