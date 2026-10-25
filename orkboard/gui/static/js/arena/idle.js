// Why nothing is at work (docs/specs/82-the-field-at-a-glance.md §3): when no task of the party is running or testing, one line over the table says why, the first that
// holds of — results at Review wait for the person's look, the tool's window is spent, the night, a sign-in —, else no line. Pure words in `idleOf`; `IdleLine` draws it.
import { html } from "../html.js";
import { town } from "../link.js";
import { hhmm } from "../board/store.js";
import { RUN, heldOf, openTasks, plural } from "./arenawords.js";

/** The tool whose window is the tightest of the snapshot's limits, with what it has used and when it is back: {name, used: percent|null, back: "HH:MM"|""}. */
function windowOf(limits, until) {
  const read = (limits || []).filter((l) => typeof l.left === "number").sort((a, b) => a.left - b.left)[0];
  const tight = read && [...(read.rows || [])].sort((a, b) => a.left - b.left)[0];
  return { name: read?.name || "The tool", used: read ? Math.round((1 - read.left) * 100) : null, back: hhmm(until) || hhmm(tight?.reset) };
}

/** The line over the table: "" when something is at work or nothing is known to hold the work back. `nodes`: the party's goals, `limits`: the snapshot's. */
export function idleOf(nodes, limits = []) {
  const tasks = nodes.flatMap((n) => openTasks(n).map((t) => ({ n, t })));
  if (tasks.some(({ t }) => RUN.includes(t.state))) return "";
  const reviews = tasks.filter(({ t }) => t.state === "review").length;
  if (reviews) return `Nothing at work: ${plural(reviews, "result", "results")} ${reviews === 1 ? "waits" : "wait"} for your look`;
  const held = tasks.filter(({ t }) => t.state === "held").map(({ n, t }) => ({ n, h: heldOf(t, n) }));
  const window = held.find((x) => x.h.kind === "window");
  if (window) {
    const w = windowOf(limits, window.n.waits?.until || window.n.held_until);
    return `Nothing at work: ${w.name}’s window is ${w.used == null ? "spent" : `at ${w.used} %`}${w.back ? `, back at ${w.back}` : ""}`;
  }
  const night = held.find((x) => x.h.kind === "night");
  if (night) return `Nothing at work: held for tonight${night.n.waits?.until ? ` (${hhmm(night.n.waits.until)})` : ""}`;
  const sign = held.find((x) => x.h.kind === "sign_in");
  if (sign) return `Nothing at work: ${sign.n.waits?.tool || sign.n.waits?.title || "the tool"} waits for its sign-in`;
  return "";
}

/** The line, over the table; nothing when there is nothing to say. */
export function IdleLine({ nodes }) {
  const words = idleOf(nodes, town.value?.limits || []);
  return words ? html`<p class="arena-idle" role="status">${words}</p>` : null;
}
