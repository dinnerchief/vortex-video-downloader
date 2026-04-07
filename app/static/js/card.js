
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
    this.quality = file.quality || file.quality_options[0]

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

    this.elQuality = el("span", "", "best")

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
    this.elBtnDel = el("button", { className: "icon-btn del", title: "Remove", onclick: () => {
      this.hide();
      callDeleteFile(file.id).catch((e) => {
        console.error(e)
        this.show()
      }).then(_=> update())
    }}, "✕")

    this.elActStart = el("button", {
      className: "icon-btn start", title: "Start download", onclick: () => this.startDownload()
    }, "▶")
    this.elActRedownload = el("button", {
      className: "icon-btn redownload", title: "File missing — redownload", onclick: () => this.startDownload()
    }, "↺")
    this.elBtnReveal = el("button", { className: "icon-btn reveal", title: "Show in Explorer", onclick: () => callRevealFile(file.id) }, "📂")


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

  static elementId(fileId) {
    return `file-${fileId}`
  }

  async startDownload() {
    this.file.status = 'downloading'
    this.render()
    return await this.file.download(this.quality)
  }

  hide() {
    this.el.style.display = "none"
  }

  show() {
    this.el.style.display = null
  }

  render() {
    const file = this.file
    const status = file.status;

    this.el.id = Card.elementId(file.id)
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
    
    if (['done', 'error', 'downloading'].includes(status)) {
      this.elEta.textContent = file.eta
      this.elSpeed.textContent = file.speed
      this.elEta.textContent = file.eta
      this.elError.textContent = file.error
      this.elPct.textContent = file.progress + "%"
      this.elPrgsFill.style.width = file.progress + "%"
    }

    hide(this.elError)
    hide(this.elMetaDownloading)
    hide(this.elQuality)
    hide(this.elPct)
    hide(this.elPrgsWrap)
    hide(this.elActRedownload)
    hide(this.elBtnReveal)
    hide(this.elActStart)
    hide(this.elPlayOverlay)
    hide(this.elSlotQuality)

    switch (status) {
      case "queued":
        show(this.elActStart)
        show(this.elSlotQuality)
        break;
      case "error":
        show(this.elError)
        show(this.elActRedownload)
        show(this.elPrgsWrap)
        show(this.elSlotQuality)
        break
      case "done":
        show(this.elPlayOverlay)
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


class CardManager extends Map {
  constructor(containerId) {
    super()
    this.container = document.getElementById(containerId)

    this._filters = new Map()
    this._sorts = new Map()
  }

  // --- Card list manage --- //

  getCardElement(fileId) {
    return document.getElementById(Card.elementId(fileId))
  }

  /**
   * @param {APIFile} file 
   * @returns {Card}
   */
  createCard(file) {
    const card = new Card(file)
    this.set(file.id, card)
    if (!this.getCardElement(file.id)) {
      this.container.append(card.el)
      
      const isFiltered = this._filters.size ? [...this._filters.values()].every(fn => fn(card)) : false
      if (isFiltered) card.hide()
    
      this.reorderFromList(this.getSortedList())
    }
    return card
  }

  /**
   * @param {string} id 
   */
  removeCard(id) {
    const card = this.get(id)
    card.el.remove()
    return this.delete(id)
  }


  // --- Sorts --- //
  /**
   * @returns {Card[]}
   */
  getSortedList() {
    let list = [...this.values()]
    this._sorts.forEach(fn => (list = list.sort(fn)))
    return list
  }

  setSort(key, fn) {
    this._sorts.set(key, fn)
  }

  clearSorts() {
    this._sorts.clear()
  }

  /**
   * Reorder DOM to match list (move each card to correct index position)
   * @param {Card[]} list list of cards 
   */
  reorderFromList(list) {
    list = list.filter(c => this.has(c.file.id))
    
    list.forEach((card, idx) => {
      const current = this.container.children[idx];      
      if (current !== card.el) this.container.insertBefore(card.el, current || null);
    });
  }

  // --- Filters --- //
  applyFilters() {
    if (!this._filters.size) this.forEach(card => card.show())
    const fns = [...this._filters.values()]
    this.forEach(card => fns.every(fn => fn(card)) ? card.show() : card.hide())
  }

  setFilter(key, fn) {
    this._filters.set(key, fn)
  }

  removeFilter(key) {
    this._filters.delete(key)
  }
  
  clearFilters() {
    this._filters.clear()
  }

}