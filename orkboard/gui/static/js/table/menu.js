// A **…** and the menu it opens (orkUI's `.ork-menu`): the Orkmaster's (the projects, Settings, Files; under 760 px also the AI tools' limits) and a party's (Edit, Remove party). A press opens it, a press away or Esc
// closes it and the focus goes back to the **…**; the arrows move between its items. Nothing is only on a right click (spec 94 §1.1).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";

/** `items`: [[word, run, danger?, icon?]]; `top`: something drawn above the items (the limits' chips at the narrow width); `face`: what the button shows in place of the **…** (the phone's crown, hand/updeck.js), `own`: its class. */
export function Menu({ label, items, top = null, onOpen = null, face = null, own = "" }) {
  const [open, setOpen] = useState(false), box = useRef(), btn = useRef(), list = useRef();
  const close = (back = true) => { setOpen(false); if (back) btn.current?.focus(); };
  useEffect(() => {
    if (!open) return undefined;
    list.current?.querySelector("[role=menuitem]")?.focus();
    const away = (e) => { if (box.current && !box.current.contains(e.target)) setOpen(false); };
    document.addEventListener("pointerdown", away, true);
    return () => document.removeEventListener("pointerdown", away, true);
  }, [open]);
  const keys = (e) => {
    const all = [...list.current.querySelectorAll("[role=menuitem]")], here = all.indexOf(document.activeElement);
    const to = e.key === "ArrowDown" ? (here + 1) % all.length : e.key === "ArrowUp" ? (here <= 0 ? all.length - 1 : here - 1) : e.key === "Home" ? 0 : e.key === "End" ? all.length - 1 : -1;
    if (to >= 0) { e.preventDefault(); all[to].focus(); }
    else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); e.__tableHandled = true; close(); }
    else if (e.key === "Tab") close(false);
  };
  return html`<span class=${cls("table-menu", { "is-open": open })} ref=${box}>
    <button type="button" class=${cls("ork-btn quiet table-menu__btn", own)} ref=${btn} aria-haspopup="menu" aria-expanded=${String(open)} aria-label=${label} title=${label}
      onClick=${() => { if (!open && onOpen) onOpen(); setOpen(!open); }}>${face || html`<${Icon} name="more-horizontal" />`}</button>
    ${open && html`<div class="ork-menu table-menu__list" role="menu" aria-label=${label} ref=${list} onKeyDown=${keys}>
      ${top}
      ${items.map(([word, run, danger, icon]) => html`<button type="button" key=${word} role="menuitem" class=${cls("ork-menu__item table-menu__item", { "is-danger": !!danger })}
        onClick=${() => { close(false); run(); }}>${icon && html`<${Icon} name=${icon} />`}${word}</button>`)}
    </div>`}
  </span>`;
}
