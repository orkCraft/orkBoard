// A place over the pane (docs/specs/98-the-table-and-the-hand.md §3.6, §7, decisions §142): what was a dialog (Settings, Open a project…, New party, Edit the party, Remove party, Pair a phone, a stop's questions,
// the update) lies in the pane, drawn by `Place`: its title is the pane's, its body scrolls, its buttons are pinned at its foot. Nothing dims the window and nothing traps the focus (the hand stays under it).
// **←** or Esc goes back to the map (`closePlace`); a form that is done (Save, Cancel, Done) does the same. `openPlace` opens one from where the pane was left, so a place opened from a place keeps the origin.
import { useLayoutEffect, useRef } from "preact/hooks";
import { html } from "../html.js";
import { closeOver, openOver, over } from "./state.js";
import { litKey } from "../table/card.js";

/** Opens `kind` over the pane keeping where the pane came from (a place opened from a place says the same *← Board*). */
export function openPlace(kind, props = {}, title = "") {
  openOver(kind, props, over.peek()?.from || null, title);
}

/** ← : the map as it was left, the card the place came from lit. */
export function closePlace() {
  const key = closeOver();
  if (key) litKey.value = key;
}

const FOCUSABLE = "button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), a[href]";

/** The body and the foot of a place. `title` names it for a screen reader (the pane's title shows it); `foot`: the buttons; `onClose`: what Esc in a field of the place does (←, by default). */
export function Place({ title, children, foot = null, wide = false, onClose = closePlace }) {
  const box = useRef();
  useLayoutEffect(() => {                                       // the first field, or the first button, has the focus: what is typed goes there
    const el = box.current;
    if (!el || el.contains(document.activeElement)) return;
    (el.querySelector("[autofocus]") || el.querySelector(FOCUSABLE))?.focus({ preventScroll: true });
  }, []);
  const key = (e) => {
    if (e.key !== "Escape" || e.defaultPrevented || e.target?.closest?.("[data-pop]")) return;       // a popover in the place (a seat's list) closes itself on Esc
    e.preventDefault();
    onClose();
  };
  return html`<section class=${`place${wide ? " is-wide" : ""}`} ref=${box} aria-label=${title} data-place onKeyDown=${key}>
    <div class="place__body">${children}</div>
    ${foot && html`<footer class="place__foot">${foot}</footer>`}
  </section>`;
}
