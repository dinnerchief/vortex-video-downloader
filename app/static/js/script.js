
const cards = new CardManager("jobList")


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

async function copyToClipboard(content = "") {
  try {
    await navigator.clipboard.writeText(content);
    toast('Copied!', 'success');
  } catch {
    toast('Failed to copy', 'error');
  }
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

const container = document.getElementById('jobList');
const empty = document.getElementById('queueEmpty');
const count = document.getElementById('queueCount');
const filterBar = document.getElementById('filterBar');

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
      else cards.createCard(file)
    })
  cards.forEach((card, k) => {
    if (!values.has(k)) {
      cards.removeCard(k)
      cards.delete(k)
      return
    }
    card.render()
  })

  count.textContent = cards.size;
  empty.style.display = cards.size ? 'none' : 'block';
  container.style.display = cards.size ? 'grid' : 'none';
  filterBar.style.display = cards.size ? 'flex' : 'none';
}

function startAll() {
  cards.forEach(async card => {
    if (card.file.downloaded) return;
    await card.file.download()
    card.render()
  })
}

const urlInput = document.getElementById('urlInput');
const urlInputsContainer = document.getElementById('urlInputs');

function updateInputs() {
  const inputs = [...urlInputsContainer.childNodes]
    .filter(v => v instanceof HTMLInputElement)
    .map(v => (v.value = v.value.trim(), v))
  const filtered = inputs.filter(v => !v.value && document.activeElement !== v)

  // remove empty fields except one
  filtered
    .slice(1)
    .forEach(v => v.remove())

  // move empty field to end
  const empty = filtered.at(0)
  console.log(filtered, empty);
  if (empty) urlInputsContainer.insertBefore(empty, null)
  
  if (inputs.filter(v => !v.value).length == 0) {
    const clone = urlInput.cloneNode()
    clone.value = ''
    
    clone.addEventListener("input", updateInputs)
    clone.addEventListener("blur", updateInputs)

    urlInputsContainer.append(clone)
  }
}

urlInput.addEventListener("input", updateInputs)
urlInput.addEventListener("blur", updateInputs)

const btn = document.getElementById('fetchBtn');
const icon = document.getElementById('fetchBtnIcon');

async function handleFetch() {
  const inputsNodes = document.getElementById('urlInputs').childNodes
  const inputs = [...inputsNodes].filter(v => v instanceof HTMLInputElement && v.value.trim())
  
  if (inputs.length === 0) { toast('Paste a URL first', 'error'); return; }
  
  inputsNodes.forEach(v => (v.disabled = true))
  btn.disabled = true;
  icon.innerHTML = '<span class="spinner" style="display:inline-block;vertical-align:middle;margin:-2px 4px 0 0"></span>';

  await Promise.all(inputs.map(async input => {
    const url = input.value.trim()
    try {
      const data = await callFetchFile(url)
      if (data.error) throw new Error(data.error || 'Failed to fetch info');
  
      const file = new APIFile(data)

      input.value = '';
  
      toast(`Added: ${file.title.slice(0, 40)}...`, 'success');
    } catch (e) {
      console.error(e)
      toast('Error: ' + e.message, 'error');
    }
  })).finally(async () => {
    inputsNodes.forEach(v => (v.disabled = false))
    btn.disabled = false;
    icon.textContent = '⚡';
    updateInputs()
    await update()
  })
}

const sortByCreatedAtASC = (a, b) => (a.file.created_at || 0) - (b.file.created_at || 0) 
const sortByCreatedAtDESC = (a, b) => (b.file.created_at || 0) - (a.file.created_at || 0) 
const sortByTitleASC = (a, b) => (a.file.title || '').localeCompare(b.file.title || '')
const sortByTitleDESC = (a, b) => (b.file.title || '').localeCompare(a.file.title || '') 
const sortByStatus = (a, b) => {
  const order = { downloading: 0, queued: 1, error: 2, done: 3 };
  return (order[a.file.status] || 9) - (order[b.file.status] || 9);
}

let delayQuery = null
function handleFilterQuery(query) {
  clearTimeout(delayQuery)
  delayQuery = setTimeout(() => {
    cards.applyFilters()
  }, 250)
  if (!query) {
    cards.removeFilter("query")
    return
  }
  cards.setFilter("query", (card) => (card.file.title + card.file.description).search(new RegExp(query, "i")) != -1)
}

function handleFilterStatus(btn, status) {
  document.querySelectorAll('#filterChips .chip').forEach(c => c.classList.remove('active'));
  btn.classList.add('active');

  if (status == 'all') {
    cards.removeFilter("status")
    cards.applyFilters()
    return
  }
  cards.setFilter("status", (card) => card.file.status == status)
  cards.applyFilters()
}

function handleSort(type) {
  switch (type) {
    case "date-asc":
      cards.clearSorts()
      cards.setSort(type, sortByCreatedAtASC)
      break;
    case "date-desc":
      cards.clearSorts()
      cards.setSort(type, sortByCreatedAtDESC)
      break;
    case "title-asc":
      cards.clearSorts()
      cards.setSort(type, sortByTitleASC)
      break;
    case "title-desc":
      cards.clearSorts()
      cards.setSort(type, sortByTitleDESC)
      break;
    case "status":
      cards.clearSorts()
      cards.setSort(type, sortByStatus)
      break;
    default:
      throw new Error(`Unknown sort type '${type}'`)
  }

  cards.reorderFromList(cards.getSortedList())
}


async function clearDone() {
  cards.forEach(card => {
    if (card.file.downloaded) card.hide()
  })
  await callDeleteFilesWithMode("done").catch(e => {
    console.error(e)
    cards.applyFilters()
  })
  await update()
}

async function clearAll() {
  cards.forEach(card => card.hide())
  await callDeleteFilesWithMode("all").catch(e => {
    console.error(e)
    cards.applyFilters()
  })
  await update()
}


document.addEventListener("DOMContentLoaded", async _ => {
  await update()

  const sortType = document.getElementById("sortSelect").value
  handleSort(sortType)

  handleFilterQuery(document.getElementById("filterSearch").value)
  // apply filter immediately
  clearTimeout(delayQuery)
  cards.applyFilters()

  setInterval(async () => {
    if (![...cards.values()].find(c => ['downloading'].includes(c.file.status))) return
    await update()
  }, 1000)
})
