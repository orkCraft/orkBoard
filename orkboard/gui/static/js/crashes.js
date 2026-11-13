// The window's own errors go to the host as crash reports (core/crashes.py, docs/crash-reports.md), which
// sends them only after a yes and only as file, function and line of Orkboard's scripts. A few per page.
// The page also keeps its last errors, a message and the first line of the stack each, console.error's too, for the logs
// Save logs writes (`recentErrors`, shell/errors.js `saveLogs`; docs/specs/107-what-the-owners-day-said.md §2.4).
// **A crash the page shows** (docs/specs/139-the-die-the-door-and-the-bug.md A.5, decisions §246.6): a window error or an unhandled rejection is said at the window's top right (`CrashNote`, mounted by frame/frame.js): *Something broke: <its words>*, with
// **Report** (it opens the bug's panel, hand/logsbtn.js `openReport`, with the crash's text in its line) and **Close**. A newer crash replaces it; an error the page logged and went on (console.error) is never shown.
import { signal } from "@preact/signals";
import { html } from "./html.js";
import { command } from "./link.js";
import { openReport } from "./hand/logsbtn.js";

const MAX = 10;
const KEEP = 20;
const WORDS = 300;
let sent = 0;
const recent = [];

/** The page's last errors, oldest first: `message @ the stack's first line`. */
export const recentErrors = () => recent.slice();

const frameOf = (stack) => String(stack || "").split("\n").map((l) => l.trim()).find((l) => /^at |@/.test(l)) || "";

function note(message, stack) {
  const frame = frameOf(stack);
  recent.push(`${String(message || "").replace(/\s+/g, " ").trim().slice(0, WORDS)}${frame ? ` @ ${frame.slice(0, WORDS)}` : ""}`);
  if (recent.length > KEEP) recent.shift();
}

/** The crash the page shows, or null: the words of the last window error that is not a browser's own noise. */
export const crash = signal(null);
const NOISE = /^(ResizeObserver loop|Script error)/;

function report(message, stack) {
  note(message, stack);
  if (!NOISE.test(String(message || ""))) crash.value = String(message || "").replace(/\s+/g, " ").trim().slice(0, 200);
  if (sent >= MAX) return;
  sent += 1;
  command("crash.window", { message: String(message || "").slice(0, 2000), stack: String(stack || "").slice(0, 8000) })
    .catch(() => {});
}

export function watchErrors() {
  window.addEventListener("error", (e) => {
    if (e.error || e.message) report(e.error ? `${e.error.name}: ${e.error.message}` : e.message, e.error && e.error.stack);
  });
  window.addEventListener("unhandledrejection", (e) => {
    const r = e.reason;
    if (r && r.refused) return;                             // a command the town refused (js/link.js): not a crash
    report(r instanceof Error ? `${r.name}: ${r.message}` : String(r), r && r.stack);
  });
  const say = (a) => { try { return a instanceof Error ? `${a.name}: ${a.message}` : typeof a === "string" ? a : JSON.stringify(a); } catch { return String(a); } };
  const was = console.error;                                // an error the page logged and went on: kept for the logs, never reported as a crash
  console.error = (...args) => {
    try {
      const err = args.find((a) => a instanceof Error);
      note(args.map(say).join(" "), err && err.stack);
    } catch { /* a log never troubles the page */ }
    return was.apply(console, args);
  };
}

/** The crash's card: its words, **Report** (the bug's panel with the words in its line) and **Close**. */
export function CrashNote() {
  const said = crash.value;
  if (!said) return null;
  return html`<div class="table-crash" role="alert" data-crash="1"><p class="table-crash__why">Something broke: ${said}</p><p class="table-logs__label">Its logs are kept with the report.</p>
    <span class="table-crash__acts"><button type="button" class="ork-btn" data-crash="report" onClick=${() => { crash.value = null; openReport(said); }}>Report</button>
      <button type="button" class="ork-btn quiet" data-crash="close" onClick=${() => { crash.value = null; }}>Close</button></span></div>`;
}
