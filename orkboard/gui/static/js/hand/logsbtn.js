// The bug's panel (docs/specs/107-what-the-owners-day-said.md §10, decisions §182.12; made the fix's by docs/specs/119-the-hammer-and-the-bug.md §4, decisions §197; **no button of the top row any more**: docs/specs/139-the-die-the-door-and-the-bug.md A.5, decisions §246.6).
// The bug left the tabs' row: its panel opens from **Report a problem…**, an item of the Orkmaster's **…** (table/pane.js) and of the phone's crown menu (hand/upmenu.js), and from the **Report** button of a crash the page shows (crashes.js), with the crash's text in its line:
// `openReport(line)`; `ReportPanel` (mounted once by frame/frame.js) draws it, fixed at the window's top right, over everything. Its content follows `town.repair.state` (the host's snapshot; an old host sends none: idle, cannot):
// - idle: *What went wrong? (optional)*, one line, **Fix it** (only when `repair.can`: it starts Claude Code on this program's own code with the line and the logs, `repair.start`) and **Save logs** (`saveLogs`, shell/errors.js: the day's logs with the line, then where they were saved;
//   the primary when Fix it is not offered, and then a line says why: `repair.why`). Enter presses the primary;
// - working (and updating): the hammer strikes (orkUI's `is-striking`; it stands raised under reduced motion); the panel says where to follow it (the Claude app), since when, and **Stop the fix** (`repair.stop`);
// - ready: orkUI's sign `bug-squashed` under the hammer: the fix is in; the panel says what came in and **Update and restart** (`repair.update`, the restart updates already make: the phone comes back by itself);
// - failed: the bug with a `cross` over it; the panel says the error as it is, **Try again** (a new fix with the line last sent) and **Save logs**.
// `PICTURES` is the one map of pictures by state (docs/specs/119 §4.3, orkUI 0.26.0), drawn at the panel's head. While a fix runs the Orkmaster's line under the pane's title says it (table/notice.js, `fixingLine`). `RepairBody` is the panel's content, which the phone's menu shows too
// (upphone.js; without Save logs: a phone saves nothing on the computer). Esc or a press away closes the panel, the focus goes back to where it was.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { command, town, PRODUCT } from "../link.js";
import { Icon, Sign } from "../orkui.js";
import { pageState, saveLogs } from "../shell/errors.js";

export const LINE_MAX = 300;                          // what went wrong, at most this long

/** The picture by state (docs/specs/119 §4.3, orkUI 0.26.0): a `base` (a sign, `big`) and what lies over its lower right (`[kind, name, cls]`, an icon or a sign): the bug and orkUI's
 *  `hammer`; while Claude works the hammer strikes (orkUI's `is-striking`: raised and lowered, standing raised under reduced motion); when the fix is in, the squashed bug under the hammer laid down. */
export const PICTURES = {
  idle: { base: "bug", over: ["icon", "hammer"] },
  working: { base: "bug", over: ["icon", "hammer", "is-striking"] },
  updating: { base: "bug", over: ["icon", "hammer", "is-striking"] },
  ready: { base: "bug-squashed", over: ["icon", "hammer"] },
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
    ${!r.can && r.why && html`<p class="table-logs__label" data-repair="why">Fix it is not here: ${r.why}.</p>`}
    ${save && html`<button type="button" class=${r.can ? "ork-btn quiet" : "ork-btn primary"} data-repair="save" onClick=${save}>Save logs</button>`}`;
}

/** The panel's state: null while it is shut, else `{line, key}`: the words it opens with (a crash's text, else none) and a number that is new with each opening (a new opening starts the line again). */
export const report = signal(null);
let opened = 0;

/** Opens the bug's panel (from the menus, from a crash's Report): `line` is what its line starts with. */
export function openReport(line = "") { report.value = { line: String(line || "").slice(0, LINE_MAX), key: ++opened }; }
export const closeReport = () => { report.value = null; };

/** What the Orkmaster's line says while a fix runs (docs/specs/139 A.5): *Fixing Orkboard: <its line>*, or "" when none runs. Its line is the one last sent with Fix it (what went wrong), else where it runs. */
export function fixingLine() {
  const r = repairOf();
  if (r.state !== "working" && r.state !== "updating") return "";
  return `Fixing ${PRODUCT}: ${r.state === "updating" ? "updating with the fix" : lastSaid || "Claude is on it in the Claude app"}`;
}

function Picture({ state }) {
  const p = PICTURES[state] || PICTURES.idle;
  return html`<span class="table-logs__pic" aria-hidden="true"><${Sign} name=${p.base} big=${true} />${p.over && (p.over[0] === "icon" ? html`<${Icon} name=${p.over[1]} cls=${p.over[2] || ""} />` : html`<${Sign} name=${p.over[1]} />`)}</span>`;
}

/** The panel, once on the page: nothing while it is shut. */
export function ReportPanel() {
  const at = report.value;
  return at ? html`<${Panel} key=${at.key} first=${at.line} />` : null;
}

function Panel({ first }) {
  const [line, setLine] = useState(first), panel = useRef(), field = useRef(), back = useRef(document.activeElement), r = repairOf(), title = repairTitle(r), mark = r.state === "updating" ? "working" : r.state;
  const close = (focus = true) => { const to = back.current; closeReport(); if (focus && to?.isConnected) to.focus?.(); };
  useEffect(() => { (field.current || panel.current?.querySelector("[data-primary], button"))?.focus(); }, [r.state]);      // a new state puts the focus on its primary
  useLayoutEffect(() => {                                                                                              // listening the moment it is drawn: a press just after it opens is already one away
    const away = (e) => { if (!panel.current?.contains(e.target)) close(false); };
    document.addEventListener("pointerdown", away, true);
    return () => document.removeEventListener("pointerdown", away, true);
  }, []);
  const save = () => { const said = line.trim(); close(false); saveLogs(said); };
  const key = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); } };
  return html`<div ref=${panel} class=${`ork-menu table-logs__panel${mark === "idle" ? "" : ` is-${mark}`}`} role="dialog" aria-label="Report a problem" data-repair-state=${r.state} onKeyDown=${key}>
    <p class="table-logs__head"><${Picture} state=${r.state} /><span>${title}</span></p>
    <${RepairBody} r=${r} line=${line} setLine=${setLine} fieldId="table-logs-line" field=${field} done=${() => close(false)} save=${save} />
  </div>`;
}
