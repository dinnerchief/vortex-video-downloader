/**
 * @type {Map<string, APIJob>}
 */
let jobs = new Map();         // job_id → job obj

/**
 * { Record< file_id , job_id > }
 * @type {Record<string, string>}
 */
let _index_file_job = {}

/**
 * @type {Map<string, APIFile>}
 */
let files = new Map();


function esc(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function thumbUrl(url) {
  if (!url) return '';
  // Proxy ytimg and youtube thumbnails through backend to bypass CORS/referrer block
  if (url.includes('ytimg.com') || url.includes('yt3.gg') || url.includes('i.ytimg')) {
    return '/api/thumb?url=' + encodeURIComponent(url);
  }
  return url;
}

// ──────────────────── Site colors ────────────────────
const SITE_COLORS = {
  'YouTube': { bg: 'rgba(255,0,0,.15)', color: '#ff4444' },
  'PornHub': { bg: 'rgba(255,149,0,.15)', color: '#ff9500' },
  'Vimeo': { bg: 'rgba(26,183,234,.15)', color: '#1ab7ea' },
  'Twitter': { bg: 'rgba(29,161,242,.15)', color: '#1da1f2' },
  'Instagram': { bg: 'rgba(225,48,108,.15)', color: '#e1306c' },
  'TikTok': { bg: 'rgba(254,44,85,.15)', color: '#fe2c55' },
  'Twitch': { bg: 'rgba(145,71,255,.15)', color: '#9147ff' },
  'Reddit': { bg: 'rgba(255,69,0,.15)', color: '#ff4500' },
  'XVideos': { bg: 'rgba(255,0,0,.15)', color: '#ff2020' },
  'xHamster': { bg: 'rgba(255,102,0,.15)', color: '#ff6600' },
  'XNXX': { bg: 'rgba(255,50,50,.15)', color: '#ff3232' },
  'SpankBang': { bg: 'rgba(255,80,0,.15)', color: '#ff5000' },
  'Bilibili': { bg: 'rgba(0,161,214,.15)', color: '#00a1d6' },
  'Dailymotion': { bg: 'rgba(0,120,220,.15)', color: '#0078dc' },
  'Rumble': { bg: 'rgba(133,195,0,.15)', color: '#85c300' },
};

const SITE_URL_MAP = {
  'pornhub': 'PornHub', 'youtube': 'YouTube', 'youtu.be': 'YouTube',
  'vimeo': 'Vimeo', 'twitter': 'Twitter', 'x.com': 'Twitter',
  'instagram': 'Instagram', 'tiktok': 'TikTok', 'twitch': 'Twitch',
  'reddit': 'Reddit', 'xvideos': 'XVideos', 'xhamster': 'xHamster',
  'xnxx': 'XNXX', 'rule34': 'Rule34', 'spankbang': 'SpankBang',
  'eporner': 'EPorner', 'redtube': 'RedTube', 'youporn': 'YouPorn',
  'bilibili': 'Bilibili', 'dailymotion': 'Dailymotion', 'rumble': 'Rumble',
};

function detectSiteFromUrl(url) {
  const u = (url || '').toLowerCase();
  for (const [key, name] of Object.entries(SITE_URL_MAP)) {
    if (u.includes(key)) return name;
  }
  return null;
}

function siteBadgeHtml(site, url) {
  const resolved = site || detectSiteFromUrl(url);
  if (!resolved) return '';
  const s = SITE_COLORS[resolved] || { bg: 'rgba(100,100,100,.2)', color: 'var(--text3)' };
  return `<span class="site-badge" style="background:${s.bg};color:${s.color}">${esc(resolved)}</span>`;
}

function toast(msg, type = 'info') {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${esc(msg)}</span>`;
  document.getElementById('toastContainer').appendChild(el);
  let t = setTimeout(() => el.remove(), 3000);
  el.addEventListener('click', e => {
    clearTimeout(t)
    el.remove()
  })
  el.addEventListener('mouseenter', e => {
    clearTimeout(t)
  })
  el.addEventListener('mouseleave', e => {
    t = setTimeout(() => el.remove(), 1000);
  })
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

/**
 * 
 * @param {APIFile} file 
 */
function createCard(file) {
  const container = document.getElementById("jobList")
  const card = new Card(file)
  cards.set(file.id, card)
  container.append(card.el)
}

/**
 * 
 * @param {string} id 
 */
function removeCard(id) {
  const card = cards.get(id)
  card.el.remove()
  cards.delete(id)
}


const container = document.getElementById('jobList');
const empty = document.getElementById('queueEmpty');
const count = document.getElementById('queueCount');

async function update() {
  const data = await fetch("/api/update")
    .then(res => res.json())
  
  if (data.error) return toast("Unable to update file list")

  const values = new Set()
  Object.values(data.files)
    .forEach(v => {
      const file = new APIFile(v)
      values.add(file.id)
      const card = cards.get(file.id)
      if (card) card.file = file
      else createCard(file)
    })
  cards.forEach((card, k) => {
    if (!values.has(k)) removeCard(k)
  })

  _index_file_job = {}
  jobs.clear()
  Object.values(data.jobs)
    .forEach(v => {
      const job = new APIJob(v)
      jobs.set(job.id, job)
      _index_file_job[job.file_id] = job.id
    })

  cards.forEach(v => {
    const job = jobs.get(_index_file_job[v.file.id])
    // if (job && job.status == 'downloading')
    v.render(job)
  })

  count.textContent = cards.size;
  empty.style.display = cards.size ? 'none' : 'block';
  container.style.display = cards.size ? 'grid' : 'none';
}

async function handleStartJob(file_id) {
  const card = cards.get(file_id)
  await card.file.download(card.quality)

  await update()
}

async function handleFetch() {
  const url = document.getElementById('urlInput').value.trim();
  if (!url) { toast('Paste a URL first', 'error'); return; }

  const btn = document.getElementById('fetchBtn');
  const icon = document.getElementById('fetchBtnIcon');
  btn.disabled = true;
  icon.innerHTML = '<span class="spinner" style="display:inline-block;vertical-align:middle;margin:-2px 4px 0 0"></span>';

  try {
    const data = await callFetchFile(url)
    if (data.error) throw new Error(data.error || 'Failed to fetch info');

    const file = new APIFile(data)
    createCard(file)

    toast(`Added: ${file.title.slice(0, 40)}...`, 'success');

    document.getElementById('urlInput').value = '';
    await update()
  } catch (e) {
    console.error(e)
    toast('Error: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    icon.textContent = '⚡';
  }
}

update()

setInterval(async () => {
  if ([...jobs.values()].find(v => v.status == 'downloading')) await update()
}, 1000)