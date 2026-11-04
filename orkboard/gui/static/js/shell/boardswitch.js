// Settings' switch for the Board's branch (docs/specs/137 E, decisions §244.1, §244.11): *Keep the Board in the repository*. The host says
// whether to show it and what it reads (gui/board_switch.py `board.switch`). *Turn it on* writes `[board]` (a public repository is refused in
// words); *Not now* leaves *Turn it on* alone. Once on, it says so, and says who holds the Board when it is not this computer.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";

export function BoardSwitch() {
  const [s, setS] = useState(null);
  const [said, setSaid] = useState("");
  const read = () => command("board.switch").then(setS, () => {});
  useEffect(() => { read(); }, []);
  if (!s || !s.show) return null;
  const turnOn = () => command("board.turn_on").then((r) => { setSaid((r && r.line) || ""); read(); }, (e) => setSaid(String((e && e.message) || e)));
  const notNow = () => command("board.not_now").then(read, () => {});
  return html`<div class="shell-field" data-settings="board-switch" role="group" aria-label=${s.label}>
    <span class="ok-font-label">${s.label}</span>
    <span class="ok-font-status" data-line="about">${s.line}</span>
    ${s.on && html`<span class="ok-font-status" data-line="on">${s.status}</span>`}
    ${s.held && html`<span class="ok-font-status" data-line="held">${s.held}</span>`}
    ${s.aside && html`<span class="ok-font-status" data-line="aside">${s.aside}</span>`}
    ${said && html`<span class="ok-font-status" data-line="said" role="status">${said}</span>`}
    ${!s.on && html`<span><button type="button" class="ork-btn primary" data-board="on" onClick=${turnOn}>Turn it on</button>
      ${!s.asked && html`<button type="button" class="ork-btn" data-board="not-now" onClick=${notNow}>Not now</button>`}</span>`}
  </div>`;
}
