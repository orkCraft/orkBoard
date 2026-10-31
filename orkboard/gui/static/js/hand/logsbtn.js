// The bug under the glass (docs/specs/107-what-the-owners-day-said.md §10, decisions §182.12; moved by decisions §190.6, docs/specs/112-the-bars-marks-and-the-play-die.md As built; made the fix's by docs/specs/119-the-hammer-and-the-bug.md §4, decisions §197):
// a quiet icon button with no word at the end of the tabs' row (table/tabs.js, after *Stop all*). Its picture and its panel follow `town.repair.state` (the host's snapshot; an old host sends none: idle, cannot):
// - idle: orkUI's sign `bug` with an icon laid over its lower right; the panel is *What went wrong? (optional)*, one line, **Fix it** (only when `repair.can`: it starts Claude Code on this program's own code with the line and the logs,
//   `repair.start`) and **Save logs** (`saveLogs`, shell/errors.js: the day's logs with the line, then where they were saved; the primary when Fix it is not offered). Enter presses the primary;
// - working (and updating): the bug with a sign over it that steps while Claude works; the panel says where to follow it (the Claude app), since when, and **Stop the fix** (`repair.stop`);
// - ready: orkUI's sign `check` in the signal colour (`is-ready`, table.css): main moved; the panel says what came in and **Update and restart** (`repair.update`, the restart updates already make: the phone comes back by itself);
// - failed: the bug with a `cross` over it; the panel says the error as it is, **Try again** (a new fix with the line last sent) and **Save logs**.
// `PICTURES` is the one map of pictures by state (docs/specs/119 §4.3): until orkUI has `hammer` and `bug-squashed` it wears the signs orkUI has; only this map changes then. `RepairBody` is the panel's content, which the phone's menu shows too
// (upphone.js; without Save logs: a phone saves nothing on the computer). Esc or a press away closes the panel. The panel is fixed, opens downward from the button's foot and is kept inside the window.
// On a touch phone upright there is no tabs' row: *Settings* saves the logs there (as Stop all is in the **…** menu), and the paired app's menu has the fix's row.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { command, town, PRODUCT } from "../link.js";
import { Icon, Sign } from "../orkui.js";
import { pageState, saveLogs } from "../shell/errors.js";

export const LINE_MAX = 300;                          // what went wrong, at most this long

/** The picture by state: a `base` (a sign, `big`) and what lies over its lower right (`[kind, name]`, an icon or a sign; none for the check). Docs/specs/119 §4.3, "Until A is copied":
 *  with orkUI's `hammer` it becomes idle `bug` + icon `hammer`, working `bug` + the hammer raised and lowered, ready sign `bug-squashed`, failed `bug` + icon `hammer` aside and `cross`. */
export const PICTURES = {
  idle: { base: "bug", over: ["icon", "search"] },
  working: { base: "bug", over: ["sign", "work"] },
  updating: { base: "bug", over: ["sign", "work"] },
  ready: { base: "check", over: null },
  failed: { base: "bug", over: ["sign", "cross"] },
};

const NONE = { can: false, why: "", state: "idle", started_at: null, landed: [], error: "" };

/** The fix as the snapshot says it; a host that does not know it (`repair` missing) can not. */
export function repairOf() {
  const r = town.value && town.value.repair;
  if (!r || typeof r !== "object") return NONE;
  return { can: !!r.can, why: String(r.why || ""), state: PICTURES[r.state] ? r.state : "idle", started_at: typeof r.started_at === "number" ? r.started_at : null,
    landed: Array.isArray(r.landed) ? r.landed : [], error: String(r.error || "") };
}

/** The button's `title` and `aria-label`, and the phone row's line, by state (docs/specs/119 §1). */
export function repairTitle(r) {
  if (r.state === "working") return `Claude is fixing ${PRODUCT}`;
  if (r.state === "updating") return `Updating ${PRODUCT} with the fix`;
  if (r.state === "ready") return "The fix is in: update and restart";
  if (r.state === "failed") return "The fix did not come in";
  return r.can ? `Save the logs or fix ${PRODUCT}` : "Save the logs";
}

let lastSaid = "";                                     // the line last sent with Fix it: Try again sends it again

/** The commands answer with the fix as the snapshot will say it: shown at once, the next snapshot says the same. */
const adopt = (r) => { if (r && typeof r === "object" && typeof r.state === "string" && town.value) town.value = { ...town.value, repair: { ...(town.value.repair || {}), ...r } }; };
const ask = (name, args = {}) => command(name, args).then(adopt).catch(() => {});          // a refusal is toasted by `command`, in the host's words

const startedAt = (s) => (typeof s === "number" ? new Date(s * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "");

/** The panel's content for the fix's state `r` (`repairOf()`): the line `line`/`setLine` (kept by the one that shows it), `fieldId` its input's id, `field` its ref, `done()` after an act that ends the panel, `save` Save logs (the desktop's; none on the phone). */
export function RepairBody({ r, line, setLine, fieldId, field, done = () => {}, save = null }) {
  const fix = () => { const said = line.trim(); lastSaid = said; setLine(""); done(); ask("repair.start", { said, page: pageState() }); };
  const again = () => { done(); ask("repair.start", { said: lastSaid, page: pageState() }); };
  const key = (e) => { if (e.key === "Enter" && !e.isComposing && e.target === field?.current) { e.preventDefault(); if (r.can) fix(); else if (save) save(); } };
  if (r.state === "working") {
    return html`<p class="table-logs__text">Claude is fixing it in the Claude app, session <strong>Fix ${PRODUCT}</strong>.</p>
      ${r.started_at !== null && html`<p class="table-logs__label">Started ${startedAt(r.started_at)}.</p>`}
      <button type="button" class="ork-btn quiet" data-repair="stop" onClick=${() => { done(); ask("repair.stop"); }}>Stop the fix</button>`;
  }
  if (r.state === "ready") {
    const more = r.landed.length - 1;
    return html`<p class="table-logs__text" role="status">The fix is in: ${r.landed[0]?.subject || ""}</p>
      ${more > 0 && html`<p class="table-logs__label">and ${more} more</p>`}
      <button type="button" class="ork-btn primary" data-repair="update" data-primary onClick=${() => ask("repair.update")}>Update and restart</button>
      <p class="table-logs__label">What runs now stops, and the tasks cut off start again by themselves. The phone comes back by itself.</p>`;
  }
  if (r.state === "updating") return html`<p class="table-logs__text" role="status">Updating…</p>`;
  if (r.state === "failed") {
    return html`<pre class="table-logs__error" role="alert">${r.error}</pre>
      <button type="button" class="ork-btn primary" data-repair="again" data-primary onClick=${again}>Try again</button>
      ${save && html`<button type="button" class="ork-btn quiet" onClick=${save}>Save logs</button>`}`;
  }
  return html`<label class="table-logs__label" for=${fieldId}>What went wrong? (optional)</label>
    <input ref=${field} id=${fieldId} class="ork-field" type="text" maxlength=${LINE_MAX} value=${line} onInput=${(e) => setLine(e.currentTarget.value)} onKeyDown=${key} />
    ${r.can && html`<button type="button" class="ork-btn primary" data-repair="fix" onClick=${fix}>Fix it</button>
      <p class="table-logs__label">Starts Claude Code on ${PRODUCT}'s own code with this and the logs; you say go in the Claude app.</p>`}
    ${save && html`<button type="button" class=${r.can ? "ork-btn quiet" : "ork-btn primary"} data-repair="save" onClick=${save}>Save logs</button>`}`;
}

function Picture({ state }) {
  const p = PICTURES[state] || PICTURES.idle;
  return html`<span class="table-logs__pic" aria-hidden="true"><${Sign} name=${p.base} big=${true} />${p.over && (p.over[0] === "icon" ? html`<${Icon} name=${p.over[1]} />` : html`<${Sign} name=${p.over[1]} />`)}</span>`;
}

export function LogsButton() {
  const [open, setOpen] = useState(false), [line, setLine] = useState(""), [at, setAt] = useState(null), button = useRef(), panel = useRef(), field = useRef();
  const r = repairOf(), title = repairTitle(r), mark = r.state === "updating" ? "working" : r.state;
  const close = (back = true) => { setOpen(false); setAt(null); if (back) button.current?.focus(); };
  useLayoutEffect(() => {                                                              // the panel lies under the button: its right edge on the button's, its top below the button's foot
    if (!open || !button.current) return;
    const b = button.current.getBoundingClientRect();
    setAt({ right: Math.max(8, Math.min(window.innerWidth - 288, window.innerWidth - b.right)), top: Math.max(8, b.bottom + 8) });
  }, [open]);
  useEffect(() => { if (open && at) (field.current || panel.current?.querySelector("[data-primary], button"))?.focus(); }, [open, !!at, r.state]);      // once it is placed (a hidden field takes no focus); a new state puts it on its primary
  useEffect(() => {
    if (!open) return undefined;
    const away = (e) => { if (!panel.current?.contains(e.target) && !button.current?.contains(e.target)) close(false); };
    document.addEventListener("pointerdown", away, true);
    return () => document.removeEventListener("pointerdown", away, true);
  }, [open]);
  const save = () => { const said = line.trim(); close(false); setLine(""); saveLogs(said); };
  const key = (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
  };
  return html`<button ref=${button} type="button" class=${`ork-btn quiet table-logs${mark === "idle" ? "" : ` is-${mark}`}`} aria-label=${title} title=${title} aria-haspopup="dialog" aria-expanded=${open ? "true" : "false"} data-repair-state=${r.state}
      onClick=${() => (open ? close(false) : setOpen(true))}><${Picture} state=${r.state} /></button>
    ${open && html`<div ref=${panel} class="ork-menu table-logs__panel" role="dialog" aria-label=${title} style=${at ? `right:${at.right}px;top:${at.top}px` : "visibility:hidden"} onKeyDown=${key}>
      <${RepairBody} r=${r} line=${line} setLine=${setLine} fieldId="table-logs-line" field=${field} done=${() => close(false)} save=${save} />
    </div>`}`;
}
