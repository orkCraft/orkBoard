// The small pieces the seats' lists share (docs/specs/91-the-owners-list.md §7): a popover under its trigger and the chip of what a role needs.
import { useEffect, useRef } from "preact/hooks";
import { html } from "../html.js";

/** A popover under its trigger: it takes the focus, Esc closes it (and only it: the dialog stays) and the focus goes back to the trigger, a press outside closes it, the arrows move between its buttons. */
export function Pop({ label, onClose, children, cls: extra = "", boxRef = null }) {
  const own = useRef(), box = boxRef || own;
  useEffect(() => {
    const trigger = document.activeElement;
    box.current?.querySelector("button:not([disabled])")?.focus();
    const away = (e) => { if (!box.current?.parentElement?.contains(e.target)) onClose(); };
    document.addEventListener("pointerdown", away, true);
    return () => { document.removeEventListener("pointerdown", away, true); if (trigger?.isConnected) trigger.focus?.(); };
  }, []);
  const key = (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); onClose(); return; }
    const step = { ArrowDown: 1, ArrowUp: -1 }[e.key];
    if (!step) return;
    const items = [...box.current.querySelectorAll("button:not([disabled])")], at = items.indexOf(document.activeElement);
    e.preventDefault();
    items[(at + step + items.length) % items.length]?.focus();
  };
  return html`<div class=${`shell-pop${extra ? ` ${extra}` : ""}`} role="group" aria-label=${label} data-pop ref=${box} onKeyDown=${key}>${children}</div>`;
}

/** *needs pictures* · *needs sound*: a chip on a role that needs its AI tool to make something. */
export const NeedsChip = ({ role }) => (role?.needs || []).length ? html`<span class="ork-chip shell-seat__needs" data-needs=${role.needs.join(" ")}>needs ${role.needs.join(" and ")}</span>` : null;

