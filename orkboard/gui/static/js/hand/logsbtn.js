// The bug under the glass (docs/specs/107-what-the-owners-day-said.md §10, decisions §182.12; moved by decisions §190.6, docs/specs/112-the-bars-marks-and-the-play-die.md As built): a quiet icon button with no word at the end of the tabs' row
// (table/tabs.js, after *Stop all*; it stood at the hand's right end before the Play die needed the room) — orkUI's sign `bug` with its icon `search` laid over its lower right (two of orkUI's pictures, nothing drawn here). A press opens a small panel
// under it: *What went wrong? (optional)*, one line, **Save logs** (`saveLogs`, shell/errors.js: the day's logs with the line, then where they were saved). Esc or a press away closes it. The panel is fixed, opens downward from the button's foot and is
// kept inside the window. On a touch phone upright there is no tabs' row: *Settings* saves the logs there (as Stop all is in the **…** menu).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { Icon, Sign } from "../orkui.js";
import { saveLogs } from "../shell/errors.js";

export const LINE_MAX = 300;                          // what went wrong, at most this long

export function LogsButton() {
  const [open, setOpen] = useState(false), [line, setLine] = useState(""), [at, setAt] = useState(null), button = useRef(), panel = useRef(), field = useRef();
  const close = (back = true) => { setOpen(false); setAt(null); if (back) button.current?.focus(); };
  useLayoutEffect(() => {                                                              // the panel lies under the button: its right edge on the button's, its top below the button's foot
    if (!open || !button.current) return;
    const r = button.current.getBoundingClientRect();
    setAt({ right: Math.max(8, Math.min(window.innerWidth - 288, window.innerWidth - r.right)), top: Math.max(8, r.bottom + 8) });
  }, [open]);
  useEffect(() => { if (open && at) field.current?.focus(); }, [open, !!at]);                  // once it is placed (a hidden field takes no focus)
  useEffect(() => {
    if (!open) return undefined;
    const away = (e) => { if (!panel.current?.contains(e.target) && !button.current?.contains(e.target)) close(false); };
    document.addEventListener("pointerdown", away, true);
    return () => document.removeEventListener("pointerdown", away, true);
  }, [open]);
  const save = () => { const said = line.trim(); close(false); setLine(""); saveLogs(said); };
  const key = (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
    else if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); save(); }
  };
  return html`<button ref=${button} type="button" class="ork-btn quiet table-logs" aria-label="Save the logs" title="Save the logs" aria-haspopup="dialog" aria-expanded=${open ? "true" : "false"}
      onClick=${() => (open ? close(false) : setOpen(true))}><span class="table-logs__pic" aria-hidden="true"><${Sign} name="bug" big=${true} /><${Icon} name="search" /></span></button>
    ${open && html`<div ref=${panel} class="ork-menu table-logs__panel" role="dialog" aria-label="Save the logs" style=${at ? `right:${at.right}px;top:${at.top}px` : "visibility:hidden"} onKeyDown=${key}>
      <label class="table-logs__label" for="table-logs-line">What went wrong? (optional)</label>
      <input ref=${field} id="table-logs-line" class="ork-field" type="text" maxlength=${LINE_MAX} value=${line} onInput=${(e) => setLine(e.currentTarget.value)} />
      <button type="button" class="ork-btn primary" onClick=${save}>Save logs</button>
    </div>`}`;
}
