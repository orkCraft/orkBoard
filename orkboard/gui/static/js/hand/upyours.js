// The phone's *Yours* (decisions §298.9; the mockup docs/mockups/table-grammar/ ?face=phone&s=yours): in the header, after the lamp's chain, a 44 px button whose face is orkUI's backpack (`aria-label="Yours"`, `aria-haspopup="menu"`). Pressed, a small menu opens under it
// with what the person has: **Inventory** (the backpack: *your tools, agents and skills*), **History** (the book: *what was decided, what came of it*) and **Settings** when the header gave Settings way for room (the row's `data-fit`, uptop.js `useRoom`). Each opens what it opens today. Esc, a press outside or a pick closes it, the focus back on the button; the arrows walk the items.
// The table of cards only (cards/on.js): uptop.js draws it there and the round button's fan (upround.js) no longer holds the backpack and the book. Layout only (cards/phone.css); every colour, face and corner is orkUI's.
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { openInventory, openOver } from "../frame/state.js";
import { openHistory } from "../table/history.js";
import { Pic } from "./upround.js";

export const YOURS = "Yours";

const ITEMS = (settings) => [
  { key: "inventory", word: "Inventory", line: "your tools, agents and skills", pic: ["pack", "pack-shut", 32, 32], go: () => openInventory() },
  { key: "history", word: "History", line: "what was decided, what came of it", pic: ["book", "book-shut", 47, 40], go: () => openHistory() },
  ...(settings ? [{ key: "settings", word: "Settings", line: "", pic: null, go: () => openOver("settings", {}, { title: "", key: "" }, "Settings") }] : []),
];

/** The Yours button and, while it is pressed, its menu. */
export function Yours() {
  const wrap = useRef(), btn = useRef(), [open, setOpen] = useState(false), [settings, setSettings] = useState(false);
  const close = (back = true) => { setOpen(false); if (back) btn.current?.focus(); };
  const press = () => {
    if (open) { close(); return; }
    setSettings(wrap.current?.closest(".up-top")?.dataset.fit !== "all");                      // Settings gave way in the row: the menu keeps it
    setOpen(true);
  };
  useLayoutEffect(() => {                                                                  // listening as soon as it is drawn: a press that follows at once is not missed
    if (!open) return undefined;
    wrap.current?.querySelector("[role=menuitem]")?.focus();
    const keys = (e) => {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); return; }
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      const all = [...(wrap.current?.querySelectorAll("[role=menuitem]") || [])], at = all.indexOf(document.activeElement);
      if (at < 0) return;
      e.preventDefault();
      all[(at + (e.key === "ArrowDown" ? 1 : all.length - 1)) % all.length].focus();
    };
    const away = (e) => { if (!wrap.current?.contains(e.target)) close(false); };
    document.addEventListener("keydown", keys, true);
    document.addEventListener("pointerdown", away, true);
    return () => { document.removeEventListener("keydown", keys, true); document.removeEventListener("pointerdown", away, true); };
  }, [open]);
  return html`<span class=${cls("up-yours", { "is-open": open })} ref=${wrap}>
    <button ref=${btn} type="button" class="up-yours__btn" aria-label=${YOURS} title="Yours: Inventory, History" aria-haspopup="menu" aria-expanded=${open ? "true" : "false"} aria-controls=${open ? "up-yours-menu" : undefined} onClick=${press}>
      <${Pic} thing="pack" name="pack-shut" w=${32} h=${32} /></button>
    ${open && html`<div class="up-yours__menu" id="up-yours-menu" role="menu" aria-label=${YOURS}>${ITEMS(settings).map((o) => html`
      <button key=${o.key} type="button" role="menuitem" class="up-yours__item" data-place=${o.key} onClick=${() => { close(); o.go(); }}>
        ${o.pic ? html`<${Pic} thing=${o.pic[0]} name=${o.pic[1]} w=${o.pic[2]} h=${o.pic[3]} />` : html`<span class="up-yours__none" aria-hidden="true"><${Icon} name="sliders" /></span>`}
        <span class="up-yours__words"><b class="up-yours__word">${o.word}</b>${o.line && html`<span class="up-yours__line">${o.line}</span>`}</span></button>`)}</div>`}
  </span>`;
}
