let playerQueue = [];   // job ids of done videos
let playerIndex = 0;
let shuffleOn = false;
let repeatOne = false;
let loopAll = false;
let seekDragging = false;

const vid = () => document.getElementById('mainVideo');

function getDoneJobs() {
  return Object.values(jobs)
    .filter(j => j.status === 'done' && j.filepath)
    .sort((a, b) => (a.created_at || 0) - (b.created_at || 0));
}

function openPlayer(jobId) {
  const done = getDoneJobs();
  if (!done.length) return;
  playerQueue = done.map(j => j.id);
  playerIndex = playerQueue.indexOf(jobId);
  if (playerIndex < 0) playerIndex = 0;

  const overlay = document.getElementById('playerOverlay');
  overlay.classList.add('open');
  requestAnimationFrame(() => requestAnimationFrame(() => overlay.classList.add('visible')));

  loadPlayerTrack(playerIndex);
  renderPlaylist();
}

function closePlayer() {
  const overlay = document.getElementById('playerOverlay');
  overlay.classList.remove('visible');
  vid().pause();
  vid().src = '';
  setTimeout(() => overlay.classList.remove('open'), 250);
}

function loadPlayerTrack(idx) {
  playerIndex = idx;
  const id = playerQueue[idx];
  const j = jobs[id];
  if (!j) return;

  const v = vid();
  v.src = `/api/stream/${id}`;
  v.playbackRate = parseFloat(document.getElementById('speedSelect').value) || 1;
  v.load();
  v.play().catch(() => { });

  document.getElementById('playerTitle').textContent = j.title || 'Unknown';
  document.getElementById('playerSiteBadge').innerHTML = siteBadgeHtml(j.site, j.url);

  // Highlight active in playlist
  document.querySelectorAll('.playlist-item').forEach((el, i) => {
    el.classList.toggle('active', i === idx);
    if (i === idx) el.scrollIntoView({ block: 'nearest' });
  });
}

function renderPlaylist() {
  const container = document.getElementById('playerPlaylist');
  container.innerHTML = playerQueue.map((id, i) => {
    const j = jobs[id];
    if (!j) return '';
    return `<div class="playlist-item${i === playerIndex ? ' active' : ''}" onclick="loadPlayerTrack(${i})">
      ${j.thumbnail ? `<img src="${esc(thumbUrl(j.thumbnail))}" onerror="this.style.display='none'" />` : ''}
      <div class="playlist-item-info">
        <div class="playlist-item-title">${esc(j.title || j.url)}</div>
        <div class="playlist-item-meta">${siteBadgeHtml(j.site, j.url)}</div>
      </div>
    </div>`;
  }).join('');
}

function togglePlay() {
  const v = vid();
  v.paused ? v.play() : v.pause();
}

function playNext() {
  if (shuffleOn) {
    playerIndex = Math.floor(Math.random() * playerQueue.length);
  } else {
    playerIndex = (playerIndex + 1) % playerQueue.length;
  }
  loadPlayerTrack(playerIndex);
  renderPlaylist();
}

function playPrev() {
  const v = vid();
  if (v.currentTime > 3) { v.currentTime = 0; return; }
  playerIndex = (playerIndex - 1 + playerQueue.length) % playerQueue.length;
  loadPlayerTrack(playerIndex);
  renderPlaylist();
}

function toggleShuffle() {
  shuffleOn = !shuffleOn;
  document.getElementById('btnShuffle').classList.toggle('active', shuffleOn);
}

function toggleRepeatOne() {
  repeatOne = !repeatOne;
  loopAll = false;
  document.getElementById('btnRepeatOne').classList.toggle('active', repeatOne);
  document.getElementById('btnLoopAll').classList.remove('active');
  vid().loop = repeatOne;
}

function toggleLoopAll() {
  loopAll = !loopAll;
  repeatOne = false;
  vid().loop = false;
  document.getElementById('btnLoopAll').classList.toggle('active', loopAll);
  document.getElementById('btnRepeatOne').classList.remove('active');
}

function setSpeed(val) { vid().playbackRate = parseFloat(val); }

function setVolume(val) {
  const v = vid();
  v.volume = parseFloat(val);
  v.muted = false;
  document.getElementById('btnMute').textContent = val == 0 ? '🔇' : '🔊';
}

function toggleMute() {
  const v = vid();
  v.muted = !v.muted;
  document.getElementById('btnMute').textContent = v.muted ? '🔇' : '🔊';
  if (!v.muted) document.getElementById('volSlider').value = v.volume;
}

function toggleFullscreen() {
  const el = document.getElementById('mainVideo');
  if (document.fullscreenElement) document.exitFullscreen();
  else el.requestFullscreen?.();
}

function fmtTime(s) {
  if (!isFinite(s)) return '0:00';
  const m = Math.floor(s / 60), sec = Math.floor(s % 60);
  return `${m}:${String(sec).padStart(2, '0')}`;
}

// Wire up video events
document.addEventListener('DOMContentLoaded', () => {
  const v = vid();

  v.addEventListener('timeupdate', () => {
    if (seekDragging) return;
    const pct = v.duration ? (v.currentTime / v.duration) * 1000 : 0;
    document.getElementById('seekBar').value = pct;
    document.getElementById('playerTimeCur').textContent = fmtTime(v.currentTime);
    document.getElementById('playerTimeDur').textContent = fmtTime(v.duration);
  });

  v.addEventListener('play', () => document.getElementById('btnPlayPause').textContent = '⏸');
  v.addEventListener('pause', () => document.getElementById('btnPlayPause').textContent = '▶');

  v.addEventListener('ended', () => {
    if (repeatOne) { v.play(); return; }
    if (playerIndex < playerQueue.length - 1 || loopAll) playNext();
  });

  const seekBar = document.getElementById('seekBar');
  seekBar.addEventListener('mousedown', () => seekDragging = true);
  seekBar.addEventListener('input', () => {
    if (v.duration) v.currentTime = (seekBar.value / 1000) * v.duration;
  });
  seekBar.addEventListener('mouseup', () => seekDragging = false);

  // Keyboard shortcuts
  document.addEventListener('keydown', e => {
    if (!document.getElementById('playerOverlay').classList.contains('open')) return;
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
    if (e.key === 'Escape') closePlayer();
    if (e.key === ' ') { e.preventDefault(); togglePlay(); }
    if (e.key === 'ArrowRight') v.currentTime = Math.min(v.duration, v.currentTime + 10);
    if (e.key === 'ArrowLeft') v.currentTime = Math.max(0, v.currentTime - 10);
    if (e.key === 'ArrowUp') { v.volume = Math.min(1, v.volume + 0.1); document.getElementById('volSlider').value = v.volume; }
    if (e.key === 'ArrowDown') { v.volume = Math.max(0, v.volume - 0.1); document.getElementById('volSlider').value = v.volume; }
    if (e.key === 'n') playNext();
    if (e.key === 'p') playPrev();
  });
});
