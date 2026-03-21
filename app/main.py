import os
import json
import uuid
import threading
import time
from flask import Flask, request, jsonify, send_file, send_from_directory, Response
import yt_dlp
from jobManager import JobManager


# Path to a Netscape-format cookies.txt file (optional)
COOKIE_FILE = ''

# Set your proxy here, e.g. 'http://127.0.0.1:2090' or 'socks5://127.0.0.1:1080'
# Leave as empty string '' to connect directly
PROXY = ''

app = Flask(__name__, static_folder='static', static_url_path="/static")

import re
SITE_MAP = {
    'pornhub': 'PornHub', 'youtube': 'YouTube', 'youtu.be': 'YouTube',
    'vimeo': 'Vimeo', 'twitter': 'Twitter', 'x.com': 'Twitter',
    'instagram': 'Instagram', 'tiktok': 'TikTok', 'twitch': 'Twitch',
    'reddit': 'Reddit', 'xvideos': 'XVideos', 'xhamster': 'xHamster',
    'xnxx': 'XNXX', 'rule34': 'Rule34', 'spankbang': 'SpankBang',
    'eporner': 'EPorner', 'redtube': 'RedTube', 'youporn': 'YouPorn',
    'bilibili': 'Bilibili', 'dailymotion': 'Dailymotion', 'rumble': 'Rumble',
}

def detect_site(url):
    url_lower = (url or '').lower()
    for key, name in SITE_MAP.items():
        if key in url_lower:
            return name
    return 'Other'

def strip_ansi(s):
    s = s or ''
    # Strip proper ANSI escape codes
    s = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', s)
    # Strip mangled codes like D[0;32m or \x0f[1m etc
    s = re.sub(r'.\[[0-9;]+[A-Za-z]', '', s)
    return s.strip()

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# User-configurable download folder
USER_DOWNLOAD_DIR = DOWNLOAD_DIR

# In-memory job store: {job_id: {...}}
jobs = JobManager()

STATE_FILE = os.path.join(os.path.dirname(__file__), 'vortex_state.json')

def save_state():
    state = {
        'proxy': PROXY,
        'download_dir': USER_DOWNLOAD_DIR,
        'cookie_file': COOKIE_FILE,
        'jobs': jobs.json(),
    }
    try:
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f'[vortex] Failed to save state: {e}')

def load_state():
    global PROXY, USER_DOWNLOAD_DIR
    if not os.path.exists(STATE_FILE):
        return
    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        PROXY = state.get('proxy', '')
        COOKIE_FILE = state.get('cookie_file', '')
        d = state.get('download_dir', DOWNLOAD_DIR)
        if os.path.isdir(d):
            USER_DOWNLOAD_DIR = d
        jobs.load(state.get('jobs', []))
        with jobs.lock:
            for job in jobs.jobs:
                # Restore downloading jobs — check if file actually landed on disk
                if job.status == 'downloading':
                    found = None
                    # Search download dir for a file starting with this job id
                    search_dir = state.get('download_dir', DOWNLOAD_DIR)
                    if os.path.isdir(search_dir):
                        for f in os.listdir(search_dir):
                            if f.startswith(job.id):
                                found = os.path.join(search_dir, f)
                                break
                    if found:
                        job.status = 'done'
                        job.filepath = found
                        job.filename = os.path.basename(found)
                        job.progress = 100
                        job.eta = ''
                    else:
                        job.status = 'error'
                        job.error = 'Interrupted (app was restarted)'
                        job.progress = 0
        print(f'[vortex] State restored: {len(jobs)} jobs, proxy={PROXY!r}, dir={USER_DOWNLOAD_DIR}')
    except Exception as e:
        print(f'[vortex] Failed to load state: {e}')

def yt_dlp_opts_for_info(url):
    return {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'skip_download': True,
    }

def fetch_info(url):
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
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info is None:
            raise ValueError("Could not extract info")
        
        # Handle playlists
        if info.get('_type') == 'playlist':
            entries = info.get('entries', [])
            return {
                'type': 'playlist',
                'title': info.get('title', 'Playlist'),
                'thumbnail': info.get('thumbnail', ''),
                'count': len(entries),
                'entries': [
                    {
                        'url': e.get('url') or e.get('webpage_url', ''),
                        'title': e.get('title', 'Unknown'),
                        'thumbnail': e.get('thumbnail', ''),
                        'duration': e.get('duration', 0),
                        'uploader': e.get('uploader', ''),
                    } for e in entries if e
                ]
            }
        
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

        return {
            'type': 'video',
            'title': info.get('title', 'Unknown Title'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'uploader': info.get('uploader', ''),
            'view_count': info.get('view_count', 0),
            'description': (info.get('description') or '')[:300],
            'quality_options': quality_options,
            'webpage_url': info.get('webpage_url', url),
            'extractor': info.get('extractor_key', ''),
        }

def do_download(job_id, url, quality):
    """Perform the actual download in a thread."""
    update_job(job_id, status='downloading', progress=0, speed='', eta='')

    output_tmpl = os.path.join(USER_DOWNLOAD_DIR, f'{job_id}_%(title)s.%(ext)s')

    def progress_hook(d):
        if d['status'] == 'downloading':
            pct = 0
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                pct = int(downloaded / total * 100)
            speed = strip_ansi(d.get('_speed_str', ''))
            eta = strip_ansi(d.get('_eta_str', ''))
            update_job(job_id, progress=pct, speed=speed, eta=eta)
        elif d['status'] == 'finished':
            update_job(job_id, progress=100, speed='', eta='Finishing...')

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
        'proxy': PROXY,
        **({'cookiefile': COOKIE_FILE} if COOKIE_FILE and os.path.exists(COOKIE_FILE) else {}),
        'nocheckcertificate': bool(PROXY),

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
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # Find actual file (may have been merged/converted)
            base = os.path.splitext(filename)[0]
            final = None
            for ext in ['.mp4', '.mkv', '.webm', '.m4a', '.mp3']:
                candidate = base + ext
                if os.path.exists(candidate):
                    final = candidate
                    break
            if not final:
                # Search by job_id prefix
                for f in os.listdir(USER_DOWNLOAD_DIR):
                    if f.startswith(job_id):
                        final = os.path.join(DOWNLOAD_DIR, f)
                        break
            
            save_state()
            update_job(job_id,
                status='done',
                progress=100,
                filename=os.path.basename(final) if final else '',
                filepath=final or '',
                speed='', eta='')
    except Exception as e:
        update_job(job_id, status='error', error=str(e), progress=0)
        save_state()

# ──────────────────────────── Routes ────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/info', methods=['POST'])
def api_info():
    data = request.json or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        info = fetch_info(url)
        return jsonify(info)
    except Exception as e:
        return jsonify({'error': str(e)}), 400



@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.json or {}
    url = (data.get('url') or '').strip()
    quality = data.get('quality', 'best')
    quality_options = data.get('quality_options', ['best'])
    title = data.get('title', 'Unknown')
    thumbnail = data.get('thumbnail', '')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    job = jobs.create_job(title, url, quality, quality_options, thumbnail)
    save_state()

    return jsonify({'job_id': job.id})

@app.route('/api/folder', methods=['GET', 'POST'])
def api_folder():
    global USER_DOWNLOAD_DIR
    if request.method == 'POST':
        folder = (request.json or {}).get('folder', '').strip()
        if folder:
            try:
                os.makedirs(folder, exist_ok=True)
                USER_DOWNLOAD_DIR = folder
                print(f'[vortex] Download folder set to: {folder}')
                save_state()
                return jsonify({'folder': USER_DOWNLOAD_DIR, 'ok': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        else:
            USER_DOWNLOAD_DIR = DOWNLOAD_DIR
            return jsonify({'folder': USER_DOWNLOAD_DIR, 'ok': True})
    return jsonify({'folder': USER_DOWNLOAD_DIR})

@app.route('/api/folder/pick', methods=['GET'])
def api_folder_pick():
    """Open a native OS folder picker dialog and return the chosen path."""
    try:
        if os.name == 'nt':
            import subprocess, sys
            # Use PowerShell's FolderBrowserDialog
            ps_script = (
                "Add-Type -AssemblyName System.Windows.Forms;"
                "$d = New-Object System.Windows.Forms.FolderBrowserDialog;"
                "$d.Description = 'Select download folder';"
                "$d.RootFolder = 'MyComputer';"
                "$d.ShowNewFolderButton = $true;"
                "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.SelectedPath }"
            )
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_script],
                capture_output=True, text=True, timeout=60
            )
            chosen = result.stdout.strip()
        else:
            # Linux/Mac fallback using zenity or osascript
            import subprocess
            try:
                result = subprocess.run(
                    ['zenity', '--file-selection', '--directory'],
                    capture_output=True, text=True, timeout=60
                )
                chosen = result.stdout.strip()
            except FileNotFoundError:
                chosen = ''

        if chosen and os.path.isdir(chosen):
            return jsonify({'path': chosen})
        else:
            return jsonify({'path': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cookies', methods=['GET', 'POST'])
def api_cookies():
    global COOKIE_FILE
    if request.method == 'POST':
        path = (request.json or {}).get('path', '').strip()
        if path and not os.path.exists(path):
            return jsonify({'error': f'File not found: {path}'}), 400
        COOKIE_FILE = path
        save_state()
        print(f'[vortex] Cookie file set to: {COOKIE_FILE!r}')
        return jsonify({'path': COOKIE_FILE})
    return jsonify({'path': COOKIE_FILE})

@app.route('/api/cookies/pick', methods=['GET'])
def api_cookies_pick():
    try:
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$d = New-Object System.Windows.Forms.OpenFileDialog;"
            "$d.Title = 'Select cookies.txt file';"
            "$d.Filter = 'Cookie files (*.txt)|*.txt|All files (*.*)|*.*';"
            "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.FileName }"
        )
        import subprocess
        result = subprocess.run(['powershell', '-NoProfile', '-Command', ps_script],
            capture_output=True, text=True, timeout=60)
        chosen = result.stdout.strip()
        if chosen and os.path.exists(chosen):
            return jsonify({'path': chosen})
        return jsonify({'path': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy', methods=['GET', 'POST'])
def api_proxy():
    global PROXY
    if request.method == 'POST':
        PROXY = (request.json or {}).get('proxy', '').strip()
        print(f'[vortex] Proxy set to: {PROXY!r}')
        save_state()
        return jsonify({'proxy': PROXY})
    return jsonify({'proxy': PROXY})

@app.route('/api/check_files', methods=['POST'])
def api_check_files():
    """Return list of done job ids whose files are missing from disk."""
    missing = []
    for job in jobs.values():
        if job.get('status') == 'done':
            fp = job.get('filepath', '')
            if not fp or not os.path.exists(fp):
                missing.append(job['id'])
    return jsonify({'missing': missing})

@app.route('/api/thumb')
def api_thumb():
    url = request.args.get('url', '').strip()
    if not url:
        return '', 400
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
        from flask import Response
        return Response(data, content_type=content_type)
    except Exception as e:
        return str(e), 502



@app.route('/api/start/<job_id>', methods=['POST'])
def api_start(job_id):
    job = jobs.get_job(job_id)
    if not job:
        return jsonify({'error': 'Not found'}), 404
    if job.get('status') not in ('queued', 'error'):
        return jsonify({'error': 'Already running or done'}), 400
    t = threading.Thread(target=do_download, args=(job_id, job['url'], job['quality']), daemon=True)
    t.start()
    return jsonify({'ok': True})

@app.route('/api/status/<job_id>')
def api_status(job_id):
    job = jobs.get_job(job_id)
    if not job:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(job)

@app.route('/api/jobs')
def api_jobs():
    return jsonify(jobs.json())

@app.route('/api/file/<job_id>')
def api_file(job_id):
    job = jobs.get_job(job_id)
    if not job or job.get('status') != 'done':
        return jsonify({'error': 'Not ready'}), 404
    fp = job.get('filepath', '')
    if not fp or not os.path.exists(fp):
        return jsonify({'error': 'File not found'}), 404
    return send_file(fp, as_attachment=True, download_name=os.path.basename(fp))

@app.route('/api/delete/<job_id>', methods=['DELETE'])
def api_delete(job_id):
    with jobs_lock:
        job = jobs.pop(job_id, None)
    if job:
        pass  # file is kept on disk
    save_state()
    return jsonify({'ok': True})

@app.route('/api/clear', methods=['POST'])
def api_clear():
    data = request.json or {}
    mode = data.get('mode', 'done')  # 'done' or 'all'
    with jobs_lock:
        to_remove = [jid for jid, j in jobs.items() if mode == 'all' or j['status'] in ('done', 'error')]
        for jid in to_remove:
            del jobs[jid]
    save_state()
    return jsonify({'removed': len(to_remove)})

@app.route('/api/stream/<job_id>')
def api_stream(job_id):
    job = get_job(job_id)
    if not job or not job.get('filepath'):
        return jsonify({'error': 'No file'}), 404
    fp = job['filepath']
    if not os.path.exists(fp):
        return jsonify({'error': 'File not found'}), 404
    return send_file(fp, conditional=True)

@app.route('/api/redownload/<job_id>', methods=['POST'])
def api_redownload(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Not found'}), 404
    # Reset job so it can be restarted — use current USER_DOWNLOAD_DIR
    update_job(job_id,
        status='queued',
        progress=0,
        speed='',
        eta='',
        filename='',
        filepath='',
        error='',
    )
    save_state()
    return jsonify({'ok': True})


@app.route('/api/quality/<job_id>', methods=['POST'])
def api_quality(job_id):
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Not found'}), 404
    if job.get('status') not in ('queued', 'error'):
        return jsonify({'error': 'Can only change quality when queued'}), 400
    quality = (request.json or {}).get('quality', 'best')
    update_job(job_id, quality=quality)
    save_state()
    return jsonify({'ok': True})

@app.route('/api/reveal/<job_id>', methods=['POST'])
def api_reveal(job_id):
    """Open the file's folder in Windows Explorer with the file selected."""
    job = get_job(job_id)
    if not job or not job.get('filepath'):
        return jsonify({'error': 'No file'}), 404
    fp = job['filepath']
    if not os.path.exists(fp):
        return jsonify({'error': 'File not found'}), 404
    try:
        import suapirocess
        suapirocess.Popen(['explorer', '/select,', fp])
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    load_state()
    app.run(debug=False, host='0.0.0.0', port=7860, threaded=True)