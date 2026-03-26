
/**
 * 
 * @param {string} file_id 
 * @param {string} quality 
 * @returns APIJob
 */
async function callFileDownload(file_id, quality) {
  const data = await fetch(`/api/files/${file_id}/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quality }),
  }).then(res => res.json());
  return new APIJob(data)
}

async function callFetchFile(url) {
  return await fetch('/api/files', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  }).then(res => res.json());
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
  }

  async download(quality) {
    const data = await callFileDownload(this.id, quality)
    if (data.error) throw new Error(data.error)
    return data
  }
}

class APIJob {
  constructor(raw) {
    this.id = raw.id
    this.eta = raw.eta
    this.url = raw.url
    this.error = raw.error
    this.speed = raw.speed
    this.status = raw.status
    this.file_id = raw.file_id
    this.quality = raw.quality
    this.filename = raw.filename
    this.progress = raw.progress
  }
}
