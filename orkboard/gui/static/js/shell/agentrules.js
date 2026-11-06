// Settings' line for the Board's rules (docs/specs/151 C.4, decisions §255.5): *Let any AI tool work the Board*, under *Keep the Board in the repository*. The host says
// whether to show it and what it reads (gui/agent_rules_switch.py `rules.switch`). *Write the rules* is the person's yes: AGENTS.md, CLAUDE.md, the Board's folder and
// Claude Code's roles and skill are written and committed with the Board's pages. *Not now* leaves *Write the rules* alone.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";

export function AgentRules() {
  const [s, setS] = useState(null);
  const [said, setSaid] = useState("");
  const read = () => command("rules.switch").then(setS, () => {});
  useEffect(() => { read(); }, []);
  if (!s || !s.show) return null;
  const write = () => command("rules.write").then((r) => { setSaid((r && r.line) || ""); read(); }, (e) => setSaid(String((e && e.message) || e)));
  const notNow = () => command("rules.not_now").then(read, () => {});
  return html`<div class="shell-field" data-settings="agent-rules" role="group" aria-label=${s.label}>
    <span class="ok-font-label">${s.label}</span>
    <span class="ok-font-status" data-line="about">${s.line}</span>
    ${s.on && html`<span class="ok-font-status" data-line="on">${s.status}</span>`}
    ${(s.said || []).map((line, n) => html`<span class="ok-font-status" data-line="by-hand" key=${n}>${line}</span>`)}
    ${said && html`<span class="ok-font-status" data-line="said" role="status">${said}</span>`}
    ${!s.on && html`<span><button type="button" class="ork-btn primary" data-rules="write" onClick=${write}>${s.write}</button>
      ${!s.asked && html`<button type="button" class="ork-btn" data-rules="not-now" onClick=${notNow}>${s.not_now}</button>`}</span>`}
  </div>`;
}
