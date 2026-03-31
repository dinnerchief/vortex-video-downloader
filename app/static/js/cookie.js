async function loadCookies() {
  const res = await fetch('/api/cookies');
  const data = await res.json();
  document.getElementById('cookiePath').textContent = data.path || 'No cookie file set';
  document.getElementById('cookieDisplay').style.borderColor = data.path ? 'rgba(232,255,71,.3)' : '';
}

async function pickCookieFile() {
  const btn = document.getElementById('cookieBtn');
  btn.disabled = true; btn.textContent = 'Picking...';
  try {
    const res = await fetch('/api/cookies/pick');
    const data = await res.json();
    if (data.error) { toast('Error: ' + data.error, 'error'); return; }
    if (!data.path) return;
    const res2 = await fetch('/api/cookies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: data.path }),
    });
    const data2 = await res2.json();
    if (data2.error) { toast(data2.error, 'error'); return; }
    document.getElementById('cookiePath').textContent = data2.path;
    document.getElementById('cookieDisplay').style.borderColor = 'rgba(232,255,71,.3)';
    toast('Cookie file set', 'success');
  } finally {
    btn.disabled = false; btn.textContent = 'Browse';
  }
}

async function clearCookieFile() {
  await fetch('/api/cookies', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: '' }),
  });
  document.getElementById('cookiePath').textContent = 'No cookie file set';
  document.getElementById('cookieDisplay').style.borderColor = '';
  toast('Cookie file cleared', 'info');
}

document.addEventListener("DOMContentLoaded", () => loadCookies())