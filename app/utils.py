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