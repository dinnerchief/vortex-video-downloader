from pathlib import Path

import re
import unicodedata

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


INVALID_CHARS = r'<>:;"/\\|?*. '
INVALID_RE_PATTERN = re.compile(r'[{}]'.format(re.escape(INVALID_CHARS)))
WHITESPACE_RE = re.compile(r'\s+')
def format_filename(text:str, max_len=255, keep_ext=True)->str:

    if not text:
        return "untitled"

    # Normalize unicode and remove control characters
    s = unicodedata.normalize("NFC", text)
    s = ''.join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    # If preserving extension, split off last dot if it looks like an extension
    ext = ""
    if keep_ext:
        p = Path(s)
        if p.suffix and len(p.suffix) <= 10:  # simple heuristic to detect extension
            ext = p.suffix
            s = str(p.with_suffix('')).lstrip('.')

    # Collapse whitespace to single space and trim
    s = WHITESPACE_RE.sub(" ", s).strip()

    # Replace invalid characters with underscore
    s = INVALID_RE_PATTERN.sub("_", s)

    # Remove leading/trailing dots/spaces (Windows forbids filenames that end with . or space)
    s = s.rstrip(". ")

    # If empty after cleanup, fallback
    if not s:
        s = "untitled"

    # Enforce max length
    if ext:
        max_base = max_len - len(ext)
        if len(s) > max_base:
            s = s[:max_base]
        filename = s + ext
    else:
        filename = s[:max_len]

    # Final sanity: Windows reserved names (CON, PRN, AUX, NUL, COM1..COM9, LPT1..LPT9)
    reserved = {"CON","PRN","AUX","NUL"} | {f"COM{i}" for i in range(1,10)} | {f"LPT{i}" for i in range(1,10)}
    if filename.split('.')[0].upper() in reserved:
        filename = "_" + filename

    return filename
