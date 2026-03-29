/**
 * { Map< file_id , Card > }
 * @type {Map<string, Card>}
 */
const cards = new Map()

const el = (tag = "div", props = {}, ...inner) => {
  const el = document.createElement(tag);
  if (typeof props == "string") el.className = props;
  else Object.assign(el, props)
  el.append(...inner)
  return el
}


function hide(el) {
  el.style.display = "none"
}

function show(el) {
  el.style.display = null
}


class Card {
  /**
   * 
   * @param {APIFile} file 
   */
  constructor(file) {
    this.prevFile = {}
    this.file = file
    this.quality = file.quality

    const card = document.createElement('div');
    this.el = card


    this.elThumbImg = el("img")
    this.elThumbImg.addEventListener("error", function (e) { this.parentElement && (this.parentElement.style.display = "none") })
    this.elThumbImg.src = file.thumbnail
    this.elThumbImg.style = "width:100%;height:100%;object-fit:cover;display:block"

    this.elPlayOverlay = el("div", "play-overlay",
      el("div", "play-overlay-btn", "▶")
    )

    this.elOpenThumb = el("button", "thumb-img-btn")
    this.elOpenThumb.innerHTML = `<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="1" y="1" width="10" height="10" rx="1" stroke="currentColor" stroke-width="1.2"/><circle cx="4" cy="4" r="1.2" fill="currentColor"/><path d="M1 8l3-3 2 2 2-2.5L11 8" stroke="currentColor" stroke-width="1.2" stroke-linejoin="round"/></svg>`
    this.elOpenThumb.title = "View thumbnail"
    this.elOpenThumb.addEventListener("click", e => (e.stopPropagation(), openLightbox(this.file.thumbnail)))

    this.elThumb = el("div", "job-thumb", this.elThumbImg, this.elOpenThumb, this.elPlayOverlay)
    this.elThumb.style = "position:relative;width:100%;height:160px;overflow:hidden;flex-shrink:0;cursor:pointer"
    this.elThumb.addEventListener("click", () => file.downloaded && openPlayer(file.id))

    this.elTitle = el("div", "job-title", esc(file.title || file.source))
    this.elSite = el("span", "job-site")
    this.elSite.innerHTML = siteBadgeHtml(file.site, file.source)
    this.elBadge = el("span", `status-badge badge-${file.downloaded ? "done" : "queued"} job-badge`, file.downloaded ? "done" : "queued")

    this.elSpeed = el("span", "", "0B/s")
    this.elSpeed.style = "color:var(--accent);font-weight:500"
    const elSep = el("span", "", "|")
    elSep.style = "color:var(--border2);padding:0 6px"
    this.elEta = el("span", "", "99:99")
    this.elEta.style = "color:var(--accent2)"
    const elEtaWrap = el("span", "", "ETA ", this.elEta)
    elEtaWrap.style = "color:var(--text2)"

    this.elError = el("span", "", "ERROR")
    this.elError.style = "color:var(--accent3);"

    this.elQuality = el("span", "", "1080p")

    this.elMetaDownloading = el("div", "", this.elSpeed, elSep, elEtaWrap)

    this.elPct = el("span", "job-pct", "0%")
    this.elPct.style = "font-family: DM Mono, monospace; font-size: 10px; color: var(--accent2);"

    const inner = el("div", "job-inner",
      this.elThumb,
      el("div", "job-body",
        el("div", "job-info",
          this.elTitle,
          el("div", "job-meta",
            this.elSite,
            this.elBadge,
            el("span", "job-meta-right", this.elQuality, this.elMetaDownloading, this.elError),
            this.elPct
          )
        )
      )
    )


    this.elPrgsFill = el("div", "progress-bar-fill")
    this.elPrgsWrap = el("div", "job-progress-wrap",
      el("div", "progress-bar-bg",
        this.elPrgsFill
      )
    )

    this.elBtnCopy = el("button", { className: "icon-btn", title: "Copy link", onclick: () => copyToClipboard(file.source) }, "🔗")
    this.elBtnDel = el("button", { className: "icon-btn del", title: "Remove", onclick: () => deleteJob(file.id) }, "✕")

    this.elActStart = el("button", {
      className: "icon-btn start", title: "Start download", onclick: () => {
        file.download(this.quality)
        update()
      }
    }, "▶")
    this.elActRedownload = el("button", {
      className: "icon-btn redownload", title: "File missing — redownload", onclick: () => {
        file.download(this.quality);
        update()
      }
    }, "↺")
    this.elBtnReveal = el("button", { className: "icon-btn reveal", title: "Show in Explorer", onclick: () => revealInExplorer(file.id) }, "📂")
    

    const selectQuality = el("select", {
      className: "quality-select", style: "font-size:10px;padding:4px 6px;height:28px", onchange: e => {
        this.quality = e.target.value
      }
    }, ...file.quality_options.map(v => el("option", { value: v, selected: v == this.quality }, v)))

    this.elSlotQuality = el("snap", "job-quality-slot", selectQuality)


    const footer = el("div", "job-footer",
      this.elPrgsWrap,
      el("div", { className: "job-actions", style: "flex-wrap:wrap;gap:5px" },
        this.elSlotQuality,
        this.elActStart,
        this.elActRedownload,
        this.elBtnReveal,
        this.elBtnCopy,
        this.elBtnDel
      )
    )

    this.el.append(inner, footer)
  }

  /**
   * 
   * @param {APIJob} job 
   */
  render(job) {
    const file = this.file

    let status = 'queued';
    if (file.downloaded) status = 'done';
    if (job) status = job.status;

    this.el.id = 'file-' + file.id;
    this.el.className = `job-card status-${status}`;

    this.elBadge.className = `status-badge badge-${status} job-badge`
    this.elBadge.textContent = status

    this.elPrgsFill.className = `progress-bar-fill ${['done', 'error'].includes(status) ? status : ''}`

    this.elTitle.textContent = esc(file.title || file.source)
    this.elSite.innerHTML = siteBadgeHtml(file.site, file.source)
    this.elTitle.textContent = esc(file.title || file.source)

    if (this.thumbnail != file.thumbnail) {
      this.thumbnail = file.thumbnail
      this.elThumbImg.src = file.thumbnail
    }

    if (job) {
      this.elEta.textContent = job.eta
      this.elSpeed.textContent = job.speed
      this.elEta.textContent = job.eta
      this.elError.textContent = job.error
      this.elPct.textContent = job.progress + "%"
      this.elPrgsFill.style.width = job.progress + "%"
    }

    hide(this.elError)
    hide(this.elMetaDownloading)
    hide(this.elQuality)
    hide(this.elPct)
    hide(this.elPrgsWrap)
    hide(this.elActRedownload)
    hide(this.elBtnReveal)
    hide(this.elActStart)

    switch (status) {
      case "queued":
        show(this.elActStart)
        break;
      case "error":
        show(this.elError)
        show(this.elActRedownload)
        show(this.elPrgsWrap)
        break
      case "done":
        show(this.elQuality)
        show(this.elBtnReveal)
        show(this.elPrgsWrap)
        this.elPrgsFill.style.width = "100%"
        break
      case "downloading":
        show(this.elMetaDownloading)
        show(this.elPct)
        show(this.elPrgsWrap)
        break
    }

  }
}