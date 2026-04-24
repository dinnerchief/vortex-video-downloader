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
