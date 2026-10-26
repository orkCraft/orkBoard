// A party's menu (docs/specs/90-what-the-first-look-said.md §5, decisions §105.5): on a party's row in the left column (partylist.js) and on its column at the Orkmaster's level
// (project.js), opened by a right click on the row or by its **…** (shown on hover and on focus): *About this party*, *Edit the party*, *Remove party…* (General has no *Remove party…*).
// *Remove party…* opens spec 80's question as Edit the party's foot does (shell/partyremove.js, unchanged). Keyboard: Enter or Space on **…** opens it, ↑ ↓ (Home, End) move, Esc closes
// and gives the focus back to **…**, Tab leaves. orkUI's tokens only (column.css `.arena-pmenu*`); the menu has no heading.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { aboutAt, showGoal } from "../shell/store.js";
import { openDialog } from "../shell/modals.js";
import { GENERAL } from "../shell/partyremove.js";

/** The menu's items for a party: [word, what it does]. General is the system's, never removed. */
export const itemsOf = (slug, ops = false) => [
  ...(ops ? [] : [["About this party", () => { aboutAt.value = ""; showGoal(slug, { via: "map" }); }],        // the Team party (`ops`) holds Operations, not goals: it has nothing to be about or edited, only to be removed (spec 92 §3)
    ["Edit the party", () => openDialog("goal", { slug })]]),
  ...(slug === GENERAL ? [] : [["Remove party…", () => openDialog("remove-party", { slug })]]),
];

/** A party's row (or column head) with its menu: `children` is the row's own button; the **…** and the menu come beside it. `at` is a class for the wrapper. */
export function PartyMenu({ slug, name, at = "", ops = false, children }) {
  const [pos, setPos] = useState(null), box = useRef(), btn = useRef(), list = useRef();
  const open = !!pos, close = (back) => { setPos(null); if (back) btn.current?.focus(); };
  useEffect(() => {
    if (!open) return undefined;
    list.current?.querySelector("[role=menuitem]")?.focus();
    const away = (e) => { if (box.current && !box.current.contains(e.target)) close(false); };
    window.addEventListener("mousedown", away);
    return () => window.removeEventListener("mousedown", away);
  }, [open]);
  useLayoutEffect(() => {                                   // kept inside the window, whichever way it was opened
    const el = list.current;
    if (!el || !pos) return;
    const w = el.offsetWidth, h = el.offsetHeight;
    el.style.left = `${Math.max(4, Math.min(pos.x, window.innerWidth - w - 4))}px`;
    el.style.top = `${Math.max(4, Math.min(pos.y, window.innerHeight - h - 4))}px`;
  }, [pos]);
  const byButton = () => {
    if (open) { close(true); return; }
    const r = btn.current.getBoundingClientRect();
    setPos({ x: r.left, y: r.bottom + 2 });
  };
  const byRightClick = (e) => { e.preventDefault(); setPos({ x: e.clientX, y: e.clientY }); };
  const keys = (e) => {
    const all = [...list.current.querySelectorAll("[role=menuitem]")], here = all.indexOf(document.activeElement);
    const to = e.key === "ArrowDown" ? (here + 1) % all.length : e.key === "ArrowUp" ? (here <= 0 ? all.length - 1 : here - 1) : e.key === "Home" ? 0 : e.key === "End" ? all.length - 1 : -1;
    if (to >= 0) { e.preventDefault(); e.stopPropagation(); all[to].focus(); }
    else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(true); }
    else if (e.key === "Tab") close(false);
  };
  const pick = (fn) => () => { close(false); fn(); };
  return html`<div class=${cls("arena-pmenu", at, { "is-open": open })} data-party=${slug} ref=${box} onContextMenu=${byRightClick}>
    ${children}
    <button type="button" class="arena-pmenu__btn" ref=${btn} aria-haspopup="menu" aria-expanded=${open} aria-label=${`More about ${name}`} title=${`More about ${name}`} onClick=${byButton}>…</button>
    ${open && html`<div class="arena-pmenu__list" role="menu" aria-label=${name} ref=${list} onKeyDown=${keys}>
      ${itemsOf(slug, ops).map(([word, fn]) => html`<button type="button" key=${word} role="menuitem" class=${cls("arena-pmenu__item", { "is-danger": word.startsWith("Remove") })} onClick=${pick(fn)}>${word}</button>`)}
    </div>`}
  </div>`;
}
