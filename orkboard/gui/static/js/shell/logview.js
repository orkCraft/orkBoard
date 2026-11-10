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

// -- a task's log in a terminal's face (docs/specs/168-the-window-played-as-a-card-games-table.md I1, decisions §283.16.9) -----------------------------------------------------------
// xterm (vendored, loaded when the first log is opened), read only: no keyboard goes to it, no cursor is drawn. The text is the host's (`ideas.task`, `ideas.task_log`: the escape codes taken out, the values of the goal's secrets
// masked before it left the host); the terminal only draws it. A round's prompt is not drawn (its heading and the count of its lines; Copy has all), the other sections' headings are bold. The text grows by its end: what is new is
// written after what is shown, and when the text is not the old one with more at its end (the host cut its first lines) the terminal is reset and written again. It stays at its foot unless the person scrolled up (xterm's own).

/** What the terminal is told to draw for a log: the sections' headings bold, a round's body (the prompt the session got) replaced by the count of its lines. Pure. */
export function termText(text) {
  const BOLD = (s) => `\x1b[1m${s}\x1b[22m`, DIM = (s) => `\x1b[2m${s}\x1b[22m`;
  return sectionsOf(text).map((s) => {
    if (s.head && ROUND.test(s.head)) return `${BOLD(s.head)}\n${DIM(`  ${s.body ? s.body.split("\n").length : 0} lines of what the session was told, not shown here (Copy has them)`)}`;
    return (s.head ? `${BOLD(s.head)}\n` : "") + s.body;
  }).join("\n");
}

const colour = (probe, name) => { probe.style.color = `var(${name})`; return getComputedStyle(probe).color; };      // orkUI's token as a colour the terminal can read

/** The terminal's colours, read from orkUI's tokens (the page carries none of its own). */
function themeOf(el) {
  const probe = document.createElement("i");
  el.appendChild(probe);
  const t = { background: colour(probe, "--ork-panel"), foreground: colour(probe, "--ork-ink"), cursor: colour(probe, "--ork-panel"), cursorAccent: colour(probe, "--ork-panel"),
    selectionBackground: colour(probe, "--ork-raised"), brightBlack: colour(probe, "--ork-ink-muted"), red: colour(probe, "--ork-danger"), green: colour(probe, "--ork-success"), yellow: colour(probe, "--ork-warning") };
  probe.remove();
  return t;
}

/** A log in a terminal's face: `text` is the task's `log`; `label` its caption; Copy beside it takes the whole text. `empty`: what is said when nothing is logged yet. */
export function LogTerm({ text, label = "Log", empty = "Nothing logged yet." }) {
  const clean = plain(text), host = useRef(), live = useRef({ term: null, shown: "", view: "" }), view = termText(clean), nothing = !clean.trim();
  live.current.view = view;                                                          // the newest text, for a terminal that finishes loading after it changed
  const draw = () => {
    const t = live.current;
    if (!t.term || t.shown === t.view) return;
    if (t.shown && t.view.startsWith(t.shown)) t.term.write(t.view.slice(t.shown.length));
    else { t.term.reset(); t.term.write("\x1b[?25l" + t.view); }
    t.shown = t.view;
  };
  useEffect(() => {
    if (nothing || !host.current) return undefined;
    let dead = false, resize = null;
    const state = live.current;
    (async () => {
      const [{ Terminal }, { FitAddon }] = await Promise.all([import("@xterm/xterm"), import("@xterm/addon-fit")]);
      const family = getComputedStyle(host.current).fontFamily;                       // the code face (shell.css), measured once it is loaded: a grid drawn in a face that comes later is spaced wrong
      try { await Promise.race([document.fonts.load(`13px ${family}`), new Promise((r) => setTimeout(r, 1500))]); } catch { /* the fallback face then */ }
      if (dead || !host.current) return;
      const term = new Terminal({ disableStdin: true, cursorBlink: false, cursorInactiveStyle: "none", convertEol: true, scrollback: 4000, screenReaderMode: false,
        fontFamily: family, fontSize: 13, lineHeight: 1.35, theme: themeOf(host.current) });
      const fit = new FitAddon();
      term.loadAddon(fit);
      term.open(host.current);
      term.textarea?.setAttribute("aria-label", label);
      term.textarea?.setAttribute("readonly", "");
      state.term = term; state.shown = "";
      const refit = () => { try { fit.fit(); } catch { /* not laid out yet */ } };
      refit();
      resize = new ResizeObserver(refit);
      resize.observe(host.current);
      draw();
    })();
    return () => { dead = true; resize?.disconnect(); state.term?.dispose(); state.term = null; state.shown = ""; };
  }, [nothing]);
  useEffect(() => { draw(); }, [view]);
  return html`<div class="shell-logterm">
    <div class="shell-logview__bar"><h3 class="board-sub">${label}</h3>
      ${!nothing && html`<button type="button" class="ork-btn quiet" onClick=${() => { copyText(clean); toast("Copied", "information"); }}>Copy</button>`}</div>
    ${nothing ? html`<p class="ok-tone-muted">${empty}</p>`
      : html`<div class="shell-logterm__screen" ref=${host} role="region" aria-label=${label} data-terminal="xterm"></div>`}
  </div>`;
}
