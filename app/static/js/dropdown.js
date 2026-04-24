/**
 * @type {{
 *  ul: HTMLUListElement,
 *  dd: HTMLDivElement,
 *  lis: Element[]
 * }}
 */
var ACTIVE_DROPDOWN = null
const DROPDOWN_UL = el("ul", "dropdown-ul invisible")
const DROPDOWN_CONTAINER = document.getElementById("dropdown")
if (DROPDOWN_CONTAINER) DROPDOWN_CONTAINER.append(DROPDOWN_UL)

/**
 * @param {Element} anchor
 * @param {Element} dropdown
 * @param {{
 *   offset: number,
 *   boundary: Window | HTMLElement
 * }} options
 */
function positionDropdown(anchor, dropdown, options = {}) {
  const { offset = 6, boundary = window } = options;

  if (!(anchor instanceof HTMLElement) || !(dropdown instanceof HTMLElement)) return;

  const anchorRect = anchor.getBoundingClientRect();
  const boundaryRect = (boundary === window) ? null : boundary.getBoundingClientRect();
  const viewportWidth = (boundary === window) ? window.innerWidth : boundaryRect.width;
  const viewportHeight = (boundary === window) ? window.innerHeight : boundaryRect.height;

  const ddRect = dropdown.getBoundingClientRect();
  const ddWidth = ddRect.width;
  const ddHeight = ddRect.height;

  let top = anchorRect.top;
  let left = anchorRect.right + offset;

  if (left + ddWidth > viewportWidth) left = anchorRect.left - ddWidth - offset;
  if (top + ddHeight > viewportHeight) top = viewportHeight - ddHeight - offset;

  const scrollX = document.body.scrollLeft;
  const scrollY = document.body.scrollTop;
  dropdown.style.left = (left + scrollX) + 'px';
  dropdown.style.top = (top + scrollY) + 'px';
}


/**
 * @typedef {{
 *  lable: string,
 *  classList: string[],
 *  onclick: (e: PointerEvent) => any
 * }} DropdownItem
 * @param {string} lable 
 * @param {Element} props 
 * @param {DropdownItem[]} list 
 */
function dropdown(lable, props, list) {
  if (!DROPDOWN_CONTAINER) return

  const lis = list.map(v => el("li", { className: ["item", ...(v.classList || [])].join(" "), onclick: v.onclick }, v.lable))
  const dd = el("div", "dropdown",
    props instanceof Element ? (props.textContent = lable, props) : el("div", props, lable)
  )

  dd.addEventListener("click", e => {
    setTimeout(() => {
      if (!ACTIVE_DROPDOWN) {
        DROPDOWN_UL.append(...lis)
        DROPDOWN_UL.classList.remove("invisible")

        positionDropdown(dd, DROPDOWN_UL)

        ACTIVE_DROPDOWN = {
          dd,
          lis
        }
      }
    })
  })

  return dd;
}

function dropdownClose() {
  DROPDOWN_UL.classList.add("invisible")
  DROPDOWN_UL.innerHTML = ''
  ACTIVE_DROPDOWN = null
}

document.addEventListener("click", e => {
  if (ACTIVE_DROPDOWN && !DROPDOWN_UL.contains(e.target))
    dropdownClose()
})
