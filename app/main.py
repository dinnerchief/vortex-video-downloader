import os
import json
from flask import Flask, request, jsonify, send_file, send_from_directory, Response
from managers import FileManager, File

import vars

app = Flask(__name__, static_folder='static', static_url_path="/static")


# In-memory job store: {job_id: {...}}
files = FileManager()


def save_state():
    state = {
        'proxy': vars.PROXY,
        'download_dir': vars.USER_DOWNLOAD_DIR,
        'cookie_file': vars.COOKIE_FILE,
        'files': files.json()
    }
    try:
        with open(vars.STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f'[vortex] Failed to save state: {e}')

def load_state():
    if not os.path.exists(vars.STATE_FILE):
        return
    try:
        with open(vars.STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        vars.PROXY = state.get('proxy', '')
        vars.COOKIE_FILE = state.get('cookie_file', '')
        d = state.get('download_dir', vars.DOWNLOAD_DIR)
        if os.path.isdir(d):
            vars.USER_DOWNLOAD_DIR = d

        for file in state.get('files', []):
            f = File(
                file.get('source'),
                file.get('filename'),
                file.get('title'),
                file.get('thumbnail'),
                file.get('quality_options')
            )

            f.created_at = file.get('created_at')
            f.downloaded = file.get('downloaded')
            f.id = file.get('id')

            files.files[f.id] = f

        print(f'[vortex] State restored: {len(files)} files, proxy={vars.PROXY!r}, dir={vars.USER_DOWNLOAD_DIR}')
    except Exception as e:
        print(f'[vortex] Failed to load state: {e}')


# ──────────────────────────── Routes ────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/files', methods=['POST'])
def api_fetch():
    data = request.json or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    try:
        file = files.fetch_and_save(url)
        save_state()
        return jsonify(file.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/files', methods=['DELETE'])
def api_delete_files():
    modes = ('done', 'all')

    data = request.json or {}
    mode = data.get('mode', 'done')
    mode = 'done' if mode not in modes else mode
    force = data.get('force', False)

    file_ids = [file_id for file_id in files.files]

    counter = 0
    match mode:
        case "all":
            for file_id in file_ids:
                file = files.get_file(file_id)
                files.remove_file(file, force)
                counter += 1
        case "done":
            for file_id in file_ids:
                file = files.get_file(file_id)
                if file.downloaded:
                    files.remove_file(file, force)
                    counter += 1

    save_state()
    return jsonify({'removed': counter})

@app.route('/api/files/<file_id>', methods=['DELETE'])
def api_delete_file(file_id):
    data = request.json or {}
    force = data.get('force', False)

    file = files.get_file(file_id)
    if file is None:
        return jsonify({'error': 'File not found'}), 404

    files.remove_file(file, force)

    save_state()
    return jsonify({'ok': True})

@app.route('/api/files/<file_id>/reveal', methods=['POST'])
def api_reveal(file_id):
    """Open the file's folder in Windows Explorer with the file selected."""
    file = files.get_file(file_id)
    if not file or not file.downloaded:
        return jsonify({'error': 'No file'}), 404
    fp = file.filepath()
    try:
        import subprocess
        subprocess.Popen(['explorer', '/select,', fp])
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<file_id>/file')
def api_file_stream(file_id):
    file = files.get_file(file_id)
    if not file or file.downloaded:
        return jsonify({'error': 'Not ready'}), 404
    
    fp = file.filepath()
    if not fp or not os.path.exists(fp):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(fp, as_attachment=True, download_name=os.path.basename(fp))

@app.route('/api/files/<file_id>/download', methods=['POST'])
def api_download(file_id):
    data = request.json or {}
    quality = data.get('quality', 'best')

    file = files.get_file(file_id)
    if file is None:
        return jsonify({'error': 'File not found'}), 404

    if file.status == vars.STATUS.DOWNLOADING:
        return jsonify({'error': 'Has an active job for this file'}), 403

    if file.downloaded:
        files.remove_file(file)

    files.download(file, quality)

    save_state()
    return jsonify({'ok': True})

@app.route('/api/files/<file_id>/cancel', methods=['POST'])
def api_cancel_job(file_id: str):
    file = files.get_file(file_id)
    if not file:
        return jsonify({'error': 'File not found'}), 404

    file.cancel()

    save_state()
    return jsonify({ 'ok': True })

@app.route('/api/update')
def api_update():
    files.sync_local_files()


    save_state()
    return jsonify({
        "files": files.json()
    })

@app.route('/api/folder', methods=['GET', 'POST'])
def api_folder():
    if request.method == 'POST':
        folder = (request.json or {}).get('folder', '').strip()
        if folder:
            try:
                os.makedirs(folder, exist_ok=True)
                vars.USER_DOWNLOAD_DIR = folder
                print(f'[vortex] Download folder set to: {folder}')
                save_state()
                return jsonify({'folder': vars.USER_DOWNLOAD_DIR, 'ok': True})
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        else:
            vars.USER_DOWNLOAD_DIR = vars.DOWNLOAD_DIR
            return jsonify({'folder': vars.USER_DOWNLOAD_DIR, 'ok': True})
    return jsonify({'folder': vars.USER_DOWNLOAD_DIR})

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
    if request.method == 'POST':
        path = (request.json or {}).get('path', '').strip()
        if path and not os.path.exists(path):
            return jsonify({'error': f'File not found: {path}'}), 400
        vars.COOKIE_FILE = path
        save_state()
        print(f'[vortex] Cookie file set to: {vars.COOKIE_FILE!r}')
        return jsonify({'path': vars.COOKIE_FILE})
    return jsonify({'path': vars.COOKIE_FILE})

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
    # global vars.PROXY
    if request.method == 'POST':
        vars.PROXY = (request.json or {}).get('proxy', '').strip()
        print(f'[vortex] Proxy set to: {vars.PROXY!r}')
        save_state()
        return jsonify({'proxy': vars.PROXY})
    return jsonify({'proxy': vars.PROXY})

# @app.route('/api/check_files', methods=['POST'])
# def api_check_files():
#     """Return list of done job ids whose files are missing from disk."""
#     missing = []
#     for job in jobs.values():
#         if job.get('status') == 'done':
#             fp = job.get('filepath', '')
#             if not fp or not os.path.exists(fp):
#                 missing.append(job['id'])
#     return jsonify({'missing': missing})

@app.route('/api/thumb')
def api_thumb():
    url = request.args.get('url', '').strip()
    if not url:
        return '', 400
    
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
            content_type = resp.headers.get('Content-Type', 'image/jpeg')

        from flask import Response
        return Response(data, content_type=content_type)
    
    except Exception as e:
        return str(e), 502

# @app.route('/api/quality/<job_id>', methods=['POST'])
# def api_quality(job_id):
#     job = get_job(job_id)
#     if not job:
#         return jsonify({'error': 'Not found'}), 404
#     if job.get('status') not in ('queued', 'error'):
#         return jsonify({'error': 'Can only change quality when queued'}), 400
#     quality = (request.json or {}).get('quality', 'best')
#     update_job(job_id, quality=quality)
#     save_state()
#     return jsonify({'ok': True})


if __name__ == '__main__':
    load_state()
    app.run(debug=False, host='0.0.0.0', port=7860, threaded=True)