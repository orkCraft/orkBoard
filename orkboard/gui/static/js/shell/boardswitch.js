// Settings' switch for the Board's branch (docs/specs/137 E, decisions §244.1, §244.11): *Keep the Board in the repository*. The host says
// whether to show it and what it reads (gui/board_switch.py `board.switch`). *Turn it on* writes `[board]` (a public repository is refused in
// words); *Not now* leaves *Turn it on* alone. Once on, it says so, and says who holds the Board when it is not this computer; under it, the cloud
// run's settings (docs/specs/137 D, decisions §244.6–8): which secret pays, the schedule, the ceiling of an API key's calls, and the one yes that
// writes the workflow into the project.
import { Fragment } from "preact";
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";

/** The cloud run's settings. Choosing writes nothing: *Write the workflow into this project* is the yes (`board.cloud_write`). */
function CloudRun({ c, done }) {
  const [form, setForm] = useState({ secret: c.secret, schedule: c.schedule, usd: c.usd });
  const [said, setSaid] = useState("");
  const set = (key, value) => setForm((f) => ({ ...f, [key]: value }));
  const pays = c.secrets.find((x) => x.id === form.secret) || c.secrets[0];
  const write = () => command("board.cloud_write", { ...form, usd: Number(form.usd) }).then((r) => { setSaid((r && r.line) || ""); done(); }, (e) => setSaid(String((e && e.message) || e)));
  return html`<div class="shell-field" data-settings="cloud-run" role="group" aria-label=${c.label}>
    <span class="ok-font-label">${c.label}</span>
    <span class="ok-font-status" data-line="cloud-about">${c.line}</span>
    <div class="board-row"><span class="ok-font-label">Who pays</span>
      <select class="ork-field" aria-label="Which secret pays" data-cloud="secret" value=${form.secret} onChange=${(e) => set("secret", e.target.value)}>
        ${c.secrets.map((x) => html`<option key=${x.id} value=${x.id}>${x.label}</option>`)}</select></div>
    <span class="ok-font-status ok-tone-muted" data-line="cloud-secret">${pays.line}</span>
    ${form.secret === "api_key" && html`<div class="board-row"><span class="ok-font-label">Ceiling in dollars</span>
      <input class="ork-field" type="number" min="0.01" step="0.5" aria-label="At most this many dollars a cloud run" data-cloud="usd" value=${form.usd} onInput=${(e) => set("usd", e.target.value)} /></div>
      <span class="ok-font-status ok-tone-muted" data-line="cloud-ceiling">${`At most $${Number(form.usd) || c.usd} a cloud run`}</span>`}
    <div class="board-row"><span class="ok-font-label">Run</span>
      <select class="ork-field" aria-label="How often a cloud run starts by itself" data-cloud="schedule" value=${form.schedule} onChange=${(e) => set("schedule", e.target.value)}>
        ${c.schedules.map((x) => html`<option key=${x.id} value=${x.id}>${x.label}</option>`)}</select></div>
    <span class="ok-font-status ok-tone-muted" data-line="cloud-minute">${c.minute}${form.schedule === "2h" ? ", 12 times a day" : ""}. The minutes are your plan's quota of Actions.</span>
    <span class="ok-font-status" data-line="cloud-write">${c.write_line}</span>
    ${c.workflow === "other" && html`<span class="ok-font-status" data-line="cloud-other">${c.path} is a file of your own: Orkboard does not overwrite it.</span>`}
    ${c.workflow === "ours" && c.current && html`<span class="ok-font-status" data-line="cloud-current">${c.path} is in this project with these settings.</span>`}
    ${said && html`<span class="ok-font-status" data-line="cloud-said" role="status">${said}</span>`}
    <span><button type="button" class="ork-btn primary" data-cloud="write" disabled=${c.workflow === "other"} onClick=${write}>${c.write}</button></span>
  </div>`;
}

export function BoardSwitch() {
  const [s, setS] = useState(null);
  const [said, setSaid] = useState("");
  const read = () => command("board.switch").then(setS, () => {});
  useEffect(() => { read(); }, []);
  if (!s || !s.show) return null;
  const turnOn = () => command("board.turn_on").then((r) => { setSaid((r && r.line) || ""); read(); }, (e) => setSaid(String((e && e.message) || e)));
  const notNow = () => command("board.not_now").then(read, () => {});
  return html`<${Fragment}>
    <div class="shell-field" data-settings="board-switch" role="group" aria-label=${s.label}>
      <span class="ok-font-label">${s.label}</span>
      <span class="ok-font-status" data-line="about">${s.line}</span>
      ${s.on && html`<span class="ok-font-status" data-line="on">${s.status}</span>`}
      ${s.held && html`<span class="ok-font-status" data-line="held">${s.held}</span>`}
      ${s.aside && html`<span class="ok-font-status" data-line="aside">${s.aside}</span>`}
      ${said && html`<span class="ok-font-status" data-line="said" role="status">${said}</span>`}
      ${!s.on && html`<span><button type="button" class="ork-btn primary" data-board="on" onClick=${turnOn}>Turn it on</button>
        ${!s.asked && html`<button type="button" class="ork-btn" data-board="not-now" onClick=${notNow}>Not now</button>`}</span>`}
    </div>
    ${s.on && s.cloud && html`<${CloudRun} c=${s.cloud} done=${read} />`}
  </${Fragment}>`;
}
