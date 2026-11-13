// The night's record (docs/specs/121-the-day-the-morning-and-the-night.md §5; docs/specs/128 C.3, decisions §206.9, §199.5): what the night did, which the host keeps (`ideas.night` → `{since, hours, into, goals: [{slug, short, title, goal, done, screens: [{screen, name, path}]}],
// failed: [{slug, short, title, task, why}], reverts: [{sha, subject, at}], checks: [{slug, short, title, task, check}], play, empty}`, null when the night did nothing). **There is no morning's card any more** (it repeated the discard): the goals done in the night
// lie in the discard, each with a small moon on its card until its result is seen (`nightMoons`, table/discard.js draws it), and on the first look at the project after the night they are dealt into the discard one by one (`nightFirst`, which the discard reads);
// a night's failure is a failed task, so it is in the hand as a failure (table/flight.js) like any other. `useNight()` (called by the hand) reads the record when the project is shown and again, at most every half minute, when the Board changes; the host is told
// once for a night, at its first look (`ideas.night {opened: true}`). The first look is kept on this device by the night's start, per project (a reload does not deal the night again). Under reduced motion, or on a page that is hidden, the goals lie in the discard at once.
// `playIt(g)` opens Play on a goal's first screen (the discard picked plays a goal with it: spec 128 F).
import { useEffect } from "preact/hooks";
import { signal } from "@preact/signals";
import { command } from "../link.js";
import { board } from "../board/store.js";
import { openOver, tab } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { mapName, partiesAll } from "../table/data.js";
import { uprightNow } from "../frame/upright.js";
import { doneOf } from "./data.js";
import { reduced } from "./motion.js";

const MIN_MS = 30_000, FIRST_MS = 400;                          // the record is asked again at most this often when the Board changes; the first ask waits a moment
const KEPT = "orkboard.night.dealt";

/** *The night: 3 goals in dev*, *The night: 1 goal in dev*, *The night: no goal reached dev* (a count of what was done). */
export function nightWords(r) {
  const n = (r?.goals || []).length;
  return n ? `The night: ${n} ${n === 1 ? "goal" : "goals"} in dev` : "The night: no goal reached dev";
}

// -- the record --------------------------------------------------------------------------------------------------------------------------------------------------------------------

export const nightRecord = signal(null);                        // ideas.night, null when the night did nothing (or the host does not know the command)
/** The night's first look, while its goals are dealt into the discard: `{since, goals: [slug…], n, at}` (`goals` the ones to deal, the oldest first; `n` how many are dealt, `at` when the last was); null before it and when nothing is dealt (reduced motion, a hidden page). */
export const nightFirst = signal(null);
const opened = new Set();                                        // the nights whose first look was told to the host in this run
let seq = 0, last = 0, timer = 0;

function readLooked() {
  try { return JSON.parse(localStorage.getItem(KEPT)) || {}; } catch { return {}; }
}
const projectKey = () => currentProject.value?.path || "";

/** The slugs of the goals the night did and that nobody has looked at yet: a moon on their card in the discard, until their result is seen (it leaves the discard then). */
export function nightMoons(r = nightRecord.value) {
  return new Set((r?.goals || []).filter((g) => g.done).map((g) => g.slug));
}

/** The night's first look at this project: kept on this device, the host told once, and the goals done dealt into the discard (the discard holds them back until their turn). */
function firstLook(r) {
  const project = projectKey(), looked = readLooked();
  if (looked[project] === r.since) return;
  try { localStorage.setItem(KEPT, JSON.stringify({ ...looked, [project]: r.since })); } catch { /* this run only */ }
  if (!opened.has(r.since)) {
    opened.add(r.since);
    command("ideas.night", { opened: true }, true).catch(() => {});
  }
  if (reduced() || document.hidden || uprightNow.value) return;                   // (a phone has no table: its discard is a row)
  const moons = nightMoons(r), goals = doneOf().map((g) => g.slug).filter((s) => moons.has(s)).reverse();      // the oldest first: the newest lands on top
  if (goals.length) nightFirst.value = { since: r.since, goals, n: 0, at: 0 };
}

function ask() {
  const mine = ++seq;
  last = Date.now();
  command("ideas.night", {}, true).then((r) => {
    if (mine !== seq) return;
    nightRecord.value = r && Array.isArray(r.goals) && !r.empty ? r : null;
    if (nightRecord.value) firstLook(nightRecord.value);
  }).catch(() => { if (mine === seq) nightRecord.value = null; });
}

/** Reads the night's record when the project is shown, and again when the Board changes (at most every half minute). Called by the hand. */
export function useNight() {
  const project = projectKey(), rev = board.value?.rev;
  useEffect(() => { nightRecord.value = null; nightFirst.value = null; seq += 1; clearTimeout(timer); timer = setTimeout(ask, FIRST_MS); return () => clearTimeout(timer); }, [project]);
  useEffect(() => {
    if (rev == null || !last) return undefined;                                       // the first ask is the project's; later ones follow the Board
    clearTimeout(timer);
    timer = setTimeout(ask, Math.max(FIRST_MS, last + MIN_MS - Date.now()));
    return () => clearTimeout(timer);
  }, [rev]);
}

/** Play opened over the pane on the goal's first screen (its route), or at the preview's first page; the die is thrown as the die throws it. */
export function playIt(g) {
  const first = (g.screens || []).find((s) => s.path);
  openOver("play", { ...(first ? { path: first.path } : {}), idea: g.slug }, { title: mapName(tab.peek(), partiesAll()), key: "" }, "Play");
}
