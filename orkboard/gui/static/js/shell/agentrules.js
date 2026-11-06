// Settings' line for the Board's rules (docs/specs/151 C.4, decisions §255.5): *Let any AI tool work the Board*, under *Keep the Board in the repository*. The host says
// whether to show it and what it reads (gui/agent_rules_switch.py `rules.switch`). *Write the rules* is the person's yes: AGENTS.md, CLAUDE.md, the Board's folder and
// Claude Code's roles and skill are written and committed with the Board's pages. *Not now* leaves *Write the rules* alone.
// F's question comes first (docs/specs/151 C.4, F.1): in a public or unreadable repository whose `in_code` is not said, the line shows the question (`question`: its words and its two answers, the ones the
// Orkmaster's card sends as `ideas.in_code`; a remote that cannot be read is asked *Is this repository private?* first) instead of *Write the rules*; with `in_code` false it says the rules would find no Board and offers nothing.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";

/** F's question in the line: the publish question and its two answers, or *Is this repository private?* first for a remote that cannot be read. */
function Question({ q, send, busy }) {
  const [asPublic, setPublic] = useState(false), w = q.words || {};
  if (q.step === "private" && !asPublic) {
    return html`<span data-in-code="private"><span class="ok-font-status" data-line="ask">${q.ask}</span>
      <button type="button" class="ork-btn primary" data-in-code-answer="private" disabled=${busy} onClick=${() => send("private")}>${w.private}</button>
      <button type="button" class="ork-btn" data-in-code-answer="public" disabled=${busy} onClick=${() => setPublic(true)}>${w.public}</button></span>`;
  }
  return html`<span data-in-code="publish"><span class="ok-font-status" data-line="ask">${q.text}</span>
    <button type="button" class="ork-btn primary" data-in-code-answer="publish" disabled=${busy} onClick=${() => send("publish")}>${w.publish}</button>
    <button type="button" class="ork-btn" data-in-code-answer="off" disabled=${busy} onClick=${() => send("off")}>${w.off}</button></span>`;
}

export function AgentRules() {
  const [s, setS] = useState(null);
  const [said, setSaid] = useState("");
  const [busy, setBusy] = useState(false);
  const read = () => command("rules.switch").then(setS, () => {});
  useEffect(() => { read(); }, []);
  if (!s || !s.show) return null;
  const write = () => command("rules.write").then((r) => { setSaid((r && r.line) || ""); read(); }, (e) => setSaid(String((e && e.message) || e)));
  const notNow = () => command("rules.not_now").then(read, () => {});
  const answer = (a) => { setBusy(true); command("ideas.in_code", { answer: a }).then(() => { setSaid(""); return read(); }, (e) => setSaid(String((e && e.message) || e))).finally(() => setBusy(false)); };
  const state = s.state || "ready";
  return html`<div class="shell-field" data-settings="agent-rules" data-state=${state} role="group" aria-label=${s.label}>
    <span class="ok-font-label">${s.label}</span>
    <span class="ok-font-status" data-line="about">${s.line}</span>
    ${s.on && html`<span class="ok-font-status" data-line="on">${s.status}</span>`}
    ${(s.said || []).map((line, n) => html`<span class="ok-font-status" data-line="by-hand" key=${n}>${line}</span>`)}
    ${said && html`<span class="ok-font-status" data-line="said" role="status">${said}</span>`}
    ${!s.on && state === "off" && html`<span class="ok-font-status" data-line="off">${s.status}</span>`}
    ${!s.on && state === "ask" && s.question && html`<${Question} q=${s.question} send=${answer} busy=${busy} />`}
    ${!s.on && state === "ready" && html`<span><button type="button" class="ork-btn primary" data-rules="write" onClick=${write}>${s.write}</button>
      ${!s.asked && html`<button type="button" class="ork-btn" data-rules="not-now" onClick=${notNow}>${s.not_now}</button>`}</span>`}
  </div>`;
}
