// A tool's two windows (docs/specs/114-the-mana-in-two-windows.md §3, decisions §192): from the rows of a limit (`l.rows`: each window's `window` name, its share `left` and its `reset`) the
// **shortest window is the liquid** (Claude's 5 hours: *can I work now?*) and the **longest the bottle's size** (its week: *will I last until the reset?*): above 0.6 of the week left the large bottle, above 0.3
// the medium, above 0.1 the small, else the vial. A tool with one window keeps the large bottle and its level; a tool whose limits were not read has no windows. The colour follows whichever runs out first
// (`levelOf(min(now, week))`, the signals' levels as before). Pure: no signal, no DOM; mana.js and table/tabmarks.js draw and say it.
import { levelOf } from "../arena/limits.js";

const HOURS = { session: 5, "5h": 5, daily: 24, day: 24, weekly: 168, week: 168, monthly: 720, month: 720 };       // the windows the readers name, their length in hours

/** A window's name without its group (*Gemini · week* is *week*). */
const bare = (name) => String(name || "").split("·").pop().trim().toLowerCase();

/** A window's length in hours: by its name (*5h*, *12h*, *30m*, *week*, *daily*), else by how far its reset is (a window cannot be longer than the time to its reset); Infinity with neither. */
export function spanOf(row, at = new Date()) {
  const name = bare(row.window), named = HOURS[name];
  if (named) return named;
  const m = /^(\d+(?:\.\d+)?)\s*(m|h|d|w)$/.exec(name);
  if (m) return Number(m[1]) * { m: 1 / 60, h: 1, d: 24, w: 168 }[m[2]];
  const reset = new Date(row.reset).getTime();
  return row.reset && Number.isFinite(reset) ? Math.max(0, (reset - at.getTime()) / 3600000) : Infinity;
}

/** A window in words, to follow *of*: *the 5 hours*, *the week*, *the day*, *the month*; any other as the reader names it (*the 90m*). */
export function windowWords(window) {
  const name = bare(window), h = /^(\d+)\s*h$/.exec(name), m = /^(\d+)\s*m$/.exec(name);
  if (name === "5h" || name === "session") return "the 5 hours";
  if (h) return `the ${h[1]} hours`;
  if (m) return `the ${m[1]} minutes`;
  return { daily: "the day", day: "the day", weekly: "the week", week: "the week", monthly: "the month", month: "the month" }[name] || (name ? `the ${name}` : "");
}

/** The bottle's size by the share of the longest window left. */
export const sizeOf = (week) => (week > 0.6 ? "large" : week > 0.3 ? "medium" : week > 0.1 ? "small" : "vial");

const pct = (left) => `${Math.round(left * 100)}%`;
const within = (v) => (typeof v === "number" && Number.isFinite(v) ? Math.min(1, Math.max(0, v)) : null);

/**
 * What a tool's limit says of its windows: `{read, two, liquid, size, level, dry, now, week, back}`.
 * `read`: whether the host read it (`l.left` a number); `two`: whether it has two windows of different length; `liquid`: the shortest window's share (0 to 1; the one window's with one), the potion's liquid;
 * `size`: `large`, `medium`, `small` or `vial`; `level`: `ok`, `warn`, `danger` or `unread`, by the lower of the two shares; `dry`: a window is at 0 and the tool takes no work (`back`: when the last of them
 * comes back, an ISO time or ""); `now` and `week`: each window `{window, left, reset, share}` (`week` null with one window; `now` is then the one window, its name `window` kept for *of the month*).
 */
export function windowsOf(l, at = new Date()) {
  const read = typeof l?.left === "number";
  if (!read) return { read: false, two: false, liquid: 0, size: "large", level: "unread", dry: false, now: null, week: null, back: "" };
  const rows = (l.rows || []).map((r) => ({ window: r.window || "", left: within(r.left), reset: r.reset || "", span: spanOf(r, at) })).filter((r) => r.left !== null)
    .map((r, i) => ({ ...r, i })).sort((a, b) => (a.span === b.span ? a.i - b.i : a.span < b.span ? -1 : 1));          // the shortest first (Infinity - Infinity is no number)
  const mark = (r) => ({ window: r.window, left: r.left, reset: r.reset, share: pct(r.left) });
  const low = rows.length ? rows[0] : null, high = rows.length ? rows[rows.length - 1] : null;
  const two = !!low && low.span !== high.span;
  const only = rows.length ? [...rows].sort((a, b) => a.left - b.left)[0] : { window: "", left: within(l.left) ?? 0, reset: "" };         // one window (or equal ones): the tightest
  const now = two ? mark(low) : mark(only), week = two ? mark(high) : null;
  const level = levelOf(week ? Math.min(now.left, week.left) : now.left);
  const out = (two ? [low, high] : [only]).filter((r) => r.left <= 0);
  const back = out.map((r) => r.reset).filter((r) => r && Number.isFinite(new Date(r).getTime())).sort().pop() || "";
  return { read: true, two, liquid: now.left, size: two ? sizeOf(week.left) : "large", level, dry: out.length > 0, now, week, back };
}
