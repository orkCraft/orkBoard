// The hour on a pile's row (docs/specs/138-the-day-read-from-the-resets.md B.5, decisions §245.4, §206.3): a goal put off for the window that fits it says **not before 14:05** (its `held_until`, the machine's local time; the
// day's name when it is not today), and a goal at work held by a spent window says **the work goes on at 14:00**. Always the earliest hour, never a span and never a countdown (§224). Pure: a node in, words out; "" when the goal
// is not held, or its hour has passed (it waits for its turn in the queue, and a past hour would say a thing that is not so). Drawn by `column.js`'s list rows alone.

const two = (n) => String(n).padStart(2, "0");

/** *14:05* today, else *Mon 09:00*: the hour of an ISO local time, in the machine's local time. "" when it is not a time. */
export function hourOf(iso, now = new Date()) {
  const at = new Date(iso);
  if (!iso || Number.isNaN(at.getTime())) return "";
  const clock = `${two(at.getHours())}:${two(at.getMinutes())}`;
  return at.toDateString() === now.toDateString() ? clock : `${at.toLocaleDateString("en-US", { weekday: "short" })} ${clock}`;
}

/** What a goal's row says of the hour it is held until: *not before 14:05* for a goal put off, *the work goes on at 14:00* for one at work; "" with none. */
export function holdWords(n, now = new Date()) {
  const until = n?.held_until || "";
  if (!until || new Date(until).getTime() <= now.getTime()) return "";
  const when = hourOf(until, now);
  if (!when) return "";
  return n.state === "working" ? `the work goes on at ${when}` : `not before ${when}`;
}
