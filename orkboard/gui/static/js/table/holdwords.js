// The hour on a pile's row (docs/specs/138-the-day-read-from-the-resets.md B.5, decisions §245.4, §206.3): a goal put off for the window that fits it says **not before 14:05** (its `held_until`, the machine's local time; the
// day's name when it is not today), and a goal at work held by a spent window says **the work goes on at 14:00**. Always the earliest hour, never a span and never a countdown (§224). Pure: a node in, words out; "" when the goal
// is not held, or its hour has passed (it waits for its turn in the queue, and a past hour would say a thing that is not so). Drawn by `column.js`'s list rows alone.

import { say } from "../link.js";

const two = (n) => String(n).padStart(2, "0");

/** *14:05* today, else *Mon 09:00*: the hour of an ISO local time, in the machine's local time. "" when it is not a time. */
export function hourOf(iso, now = new Date()) {
  const at = new Date(iso);
  if (!iso || Number.isNaN(at.getTime())) return "";
  const clock = `${two(at.getHours())}:${two(at.getMinutes())}`;
  return at.toDateString() === now.toDateString() ? clock : `${at.toLocaleDateString("en-US", { weekday: "short" })} ${clock}`;
}

/** What a goal's row says of the hour it is held until: *not before 14:05* for a goal put off, *the work goes on at 14:00* for one at work; *Held* for one the person holds (no hour: spec 130 E.3); "" with none. */
export function holdWords(n, now = new Date()) {
  if (n?.taken) return n.taken;                                 // another tool holds the goal (spec 151 D.1; the map's `taken`): *Taken by codex until 14:05*, its hour in this computer's clock
  if (n?.held_for === "hold") return "Held";
  const until = n?.held_until || "";
  if (!until || new Date(until).getTime() <= now.getTime()) return "";
  const when = hourOf(until, now);
  if (!when) return "";
  return n.state === "working" ? `the work goes on at ${when}` : `not before ${when}`;
}

/** What a goal kept off the repository says on its row (spec 151 F.4; the map's `kept_off`): *Kept off the repository: on this computer only*; "" for a goal that goes with the rest. */
export const offWords = (n) => n?.kept_off || "";

/** The line under In analysis while goals put off wait for the reset (spec 130 E.4, decisions §239.4): *waits for the reset · Mon 09:00*, the earliest of them, a state and never a count; "" with none. A held goal has no reset to wait for, and a reset passed says nothing. */
export function waitsWords(nodes, now = new Date()) {
  const at = nodes.filter((n) => n.state === "routed" && n.held_until && !n.held_for).map((n) => n.held_until).filter((iso) => new Date(iso).getTime() > now.getTime())
    .sort((a, b) => new Date(a) - new Date(b))[0];
  return at ? `${say("waits for the reset")} · ${hourOf(at, now)}` : "";
}
