async function loadFolder() {
  const res = await fetch('/api/folder');
  const data = await res.json();
  document.getElementById('folderPath').textContent = data.folder;
}

async function openFolderPicker() {
  const btn = document.getElementById('browseBtn');
  btn.disabled = true;
  btn.textContent = 'Picking...';
  try {
    const res = await fetch('/api/folder/pick');
    const data = await res.json();
    if (data.error) { toast('Error: ' + data.error, 'error'); return; }
    if (!data.path) return; // user cancelled
    const res2 = await fetch('/api/folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ folder: data.path }),
    });
    const data2 = await res2.json();
    if (data2.error) { toast('Error: ' + data2.error, 'error'); return; }
    document.getElementById('folderPath').textContent = data2.folder;
    toast('Download folder set', 'success');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Browse';
  }
}


document.addEventListener("DOMContentLoaded", () => loadFolder())