// A log one reads (docs/specs/107-what-the-owners-day-said.md §3): a task's log, a stop's log and a result's test tail as sections, not a wall. A line starting `== ` begins a section
// (the host writes them: `== round 3 · …` and the prompt the session got, `== the session answered`, `== the gate, try 1`, `== installing: …`, `== at Review · …`); a round's section is folded,
// its heading only, the others are open, the last always; it opens at its foot, where the newest line is, and stays there while the text grows unless the person scrolled up.
import { useEffect, useRef } from "preact/hooks";
import { html } from "../html.js";
import { copyText, toast } from "../link.js";

const ANSI = /\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)/g;       // a terminal's colour and cursor codes, a title or link (the host strips them too)
const ROUND = /^== round\b/;
const NEAR = 24;                                                                    // px from the foot that still counts as being at it

export const plain = (text) => String(text ?? "").replace(ANSI, "");

/** The log's sections, `[{head, body}]`: the text before the first `== ` line has no head. */
export function sectionsOf(text) {
  const out = [];
  for (const line of plain(text).split(/\r?\n/)) {
    if (line.startsWith("== ")) out.push({ head: line, lines: [] });
    else {
      if (!out.length) out.push({ head: "", lines: [] });
      out[out.length - 1].lines.push(line);
    }
  }
  return out.map((s) => ({ head: s.head, body: s.lines.join("\n").replace(/^\n+|\s+$/g, "") })).filter((s, i, all) => s.head || s.body || i === all.length - 1);
}

/** What happened, in a line: the task's own `error`, else why its tests could not run (`tests.env`), else that they failed and the first failing name. "" when nothing failed. */
export function happened({ error = "", tests = null, red = false } = {}) {
  if (error) return error;
  if (tests?.env) return tests.env;
  if (!red) return "";
  const name = tests?.failing?.[0];
  return name ? `The tests failed: ${name}` : "The tests failed.";
}

/** A log: `text` (a task's `log`, a result's `tests.tail`) under its caption `label`, with Copy beside it. */
export function LogView({ text, label = "Log" }) {
  const clean = plain(text), secs = sectionsOf(clean), body = useRef(), foot = useRef(true);
  useEffect(() => { const el = body.current; if (el && foot.current) el.scrollTop = el.scrollHeight; }, [clean]);
  const scrolled = () => { const el = body.current; if (el) foot.current = el.scrollHeight - el.scrollTop - el.clientHeight <= NEAR; };
  const empty = !clean.trim();
  return html`<div class="shell-logview">
    <div class="shell-logview__bar"><h3 class="board-sub">${label}</h3>
      ${!empty && html`<button type="button" class="ork-btn quiet" onClick=${() => { copyText(clean); toast("Copied", "information"); }}>Copy</button>`}</div>
    ${empty ? html`<p class="ok-tone-muted">Nothing logged yet.</p>`
      : html`<div class="shell-logview__body" ref=${body} role="region" aria-label=${label} tabindex="0" onScroll=${scrolled}>${secs.map((s, i) => {
          const folded = i < secs.length - 1 && ROUND.test(s.head);
          return s.head ? html`<details key=${i} class="shell-logview__sec" open=${!folded}><summary>${s.head}</summary>${s.body && html`<pre>${s.body}</pre>`}</details>`
            : html`<pre key=${i}>${s.body}</pre>`;
        })}</div>`}
  </div>`;
}
