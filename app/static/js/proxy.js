async function loadProxy() {
  const res = await fetch('/api/proxy');
  const data = await res.json();
  if (data.proxy) document.getElementById('proxyInput').value = data.proxy;
}

async function saveProxy() {
  const proxy = document.getElementById('proxyInput').value.trim();
  await fetch('/api/proxy', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ proxy }),
  });
  toast(proxy ? 'Proxy saved: ' + proxy : 'Proxy cleared', 'info');
}

document.addEventListener("DOMContentLoaded", () => loadProxy())