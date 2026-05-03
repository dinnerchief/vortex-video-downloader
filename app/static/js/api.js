
const STATUS = {
  QUEUED: "queued",
  DOWNLOADING: "downloading",
  ERROR: "error",
  DONE: "done"
}

/**
 * 
 * @param {string} file_id 
 * @param {string} quality 
 */
async function callFileDownload(file_id, quality) {
  return await fetch(`/api/files/${file_id}/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quality }),
  }).then(res => res.json());
}

async function callFetchFile(url) {
  return await fetch('/api/files', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  }).then(res => res.json());
}

async function callCancel(file_id) {
  return await fetch(`/api/files/${file_id}/cancel`, { method: "POST" })
    .then(res => res.json());
}

async function callDeleteFilesWithMode(mode, force = false) {
  if (!mode || !['all', 'done'].includes(mode)) throw new Error("No selected mode. Availbale: 'all', 'done'")
  return await fetch(`/api/files`, {
    method: "DELETE",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force, mode }),
  })
    .then(res => res.json());
}

async function callDeleteFile(file_id, force = false) {
  return await fetch(`/api/files/${file_id}`, {
    method: "DELETE",
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force }),
  })
    .then(res => res.json());
}

async function callRevealFile(file_id) {
  await fetch(`/api/files/${file_id}/reveal`, { method: "POST" });
}




class APIFile {
  constructor(raw) {
    this.id = raw.id
    this.title = raw.title
    this.source = raw.source
    this.site = raw.site
    this.thumbnail = raw.thumbnail
    this.quality_options = raw.quality_options
    this.filename = raw.filename
    this.filepath = raw.filepath
    this.created_at = raw.created_at
    this.downloaded = raw.downloaded
    this.quality = raw.quality
    
    this.error = raw.error
    this.eta = raw.eta
    this.speed = raw.speed
    this.status = raw.status
    this.progress = raw.progress

    this.description = raw.description || ''
  }

  async cancel() {
    const data = await callCancel(this.id)
    if (data.error) throw new Error(data.error)
    this.status = STATUS.QUEUED
  }

  async download(quality) {
    const data = await callFileDownload(this.id, quality)
    if (data.error) throw new Error(data.error)
    this.status = STATUS.DOWNLOADING
    return data
  }

}
