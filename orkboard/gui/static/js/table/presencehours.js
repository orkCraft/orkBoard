// The person's hours at the lamp's chain (docs/specs/168 H2, decisions §283.31: *the hours belong to the lamp's chain, a long pull*): the chain held down for `LONG` ms (or pressed with Shift, for the keyboard) opens a small
// panel with **When I am at the computer**, the Board's `hours` as Settings has them (shell/hoursfield.js, `ideas.board_set {hours}`), and *Done*. A short press stays *Here* / *Away* (presence.js). Esc and *Done* shut it; a press away shuts it.
// The field is loaded when first asked for (it lies in the shell's modules, which the table does not load before). The desktop's chain only (`half`): the phone and the narrow page keep their chain as it was.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";

export const LONG = 600;                                                   // ms held down for a long pull
export const HOURS_TITLE = "Hold to set your hours";

/** The press of a chain: `{props, held}`; `props` go on the chain's button (pointer events that count the time held), `held()` says, once, whether the click that follows was the end of a long pull. */
export function useLongPull(on, open) {
  const timer = useRef(0), long = useRef(false);
  const stop = () => { clearTimeout(timer.current); timer.current = 0; };
  useEffect(() => stop, []);
  if (!on) return { props: {}, held: () => false };
  return {
    props: {
      onPointerDown: (e) => { if (e.button) return; long.current = false; stop(); timer.current = setTimeout(() => { long.current = true; timer.current = 0; open(); }, LONG); },
      onPointerUp: stop, onPointerLeave: stop, onPointerCancel: stop,
    },
    held: (e) => { if (long.current) { long.current = false; return true; } if (e?.shiftKey) { open(); return true; } return false; },
  };
}

/** The panel under the chain `anchor` (an element): the hours' field and *Done*. */
export function HoursPanel({ anchor, close }) {
  const [Field, setField] = useState(null), box = useRef(null);
  useEffect(() => { let live = true; import("../shell/hoursfield.js").then((m) => { if (live) setField(() => m.HoursField); }); return () => { live = false; }; }, []);
  useEffect(() => {
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); close(); } };
    const away = (e) => { if (!box.current?.contains(e.target) && !anchor?.contains(e.target)) close(); };
    addEventListener("keydown", esc);
    document.addEventListener("pointerdown", away, true);
    box.current?.focus({ preventScroll: true });
    return () => { removeEventListener("keydown", esc); document.removeEventListener("pointerdown", away, true); anchor?.focus?.({ preventScroll: true }); };
  }, []);
  const r = anchor?.getBoundingClientRect(), style = r ? `top:${Math.round(r.bottom + 4)}px;right:${Math.max(8, Math.round(innerWidth - r.right))}px` : undefined;
  return html`<div ref=${box} class="presence-hours ork-frame" role="dialog" tabindex="-1" aria-label="When I am at the computer" data-presence-hours style=${style}>
    ${Field ? html`<${Field} />` : html`<p class="ok-font-status ok-tone-muted">Looking at your hours…</p>`}
    <button type="button" class="ork-btn" data-act="done" onClick=${close}>Done</button>
  </div>`;
}
