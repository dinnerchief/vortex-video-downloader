function openLightbox(src) {
  const bg = document.getElementById('lightboxBg');
  const img = document.getElementById('lightboxImg');
  img.src = src;
  bg.classList.add('open');
  requestAnimationFrame(() => requestAnimationFrame(() => bg.classList.add('visible')));
}
function closeLightbox() {
  const bg = document.getElementById('lightboxBg');
  bg.classList.remove('visible');
  setTimeout(() => {
    bg.classList.remove('open');
    document.getElementById('lightboxImg').src = '';
  }, 250);
}
async function saveLightboxImage() {
  const src = document.getElementById('lightboxImg').src;
  if (!src) return;
  try {
    // const res = await fetch(src);
    // const blob = await res.blob();
    // const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = src;
    a.download = '';
    a.click();
    // URL.revokeObjectURL(url);
  } catch(e) {
    console.error(e);
    toast('Failed to save image', 'error');
  }
}
async function copyLightboxImage() {
  const src = document.getElementById('lightboxImg').src;
  if (!src) return;
  try {
    const res = await fetch(src);
    const blob = await res.blob();
    await navigator.clipboard.write([new ClipboardItem({ [blob.type]: blob })]);
    toast('Image copied to clipboard', 'success');
  } catch(e) {
    console.error(e);
    toast('Failed to copy image', 'error');
  }
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeLightbox(); });