// The window's own errors go to the host as crash reports (core/crashes.py, docs/crash-reports.md), which
// sends them only after a yes and only as file, function and line of Orkline's scripts. A few per page.
// The page also keeps its last errors, a message and the first line of the stack each, console.error's too, for the logs
// Save logs writes (`recentErrors`, shell/errors.js `saveLogs`; docs/specs/107-what-the-owners-day-said.md §2.4).
import { command } from "./link.js";

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

function report(message, stack) {
  note(message, stack);
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
