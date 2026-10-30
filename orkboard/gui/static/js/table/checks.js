// The checks on the way into main, as the page keeps them (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4.3, decisions §188.3–§188.5): when a goal is chosen for main at the wide width the page asks
// `ideas.to_main_checks` (the host runs the checks in a trial worktree, realm/main_checks.py) and follows them in the snapshot's `main_checks` (`{slug: [{name, state: waiting | running | passed | failed, words}]}`, the host
// publishes each step as `main.check` and the snapshot carries it: the page has no other channel for the bus). What the command answered stands in until the snapshot has moved on from what it was when the question was asked.
// Each check is one skeleton (Release's members, the laborer, the warrior and the elder in that order; the fourth and more fold into the third, *and n more*); the portal (portal.js) draws them in the gate while they run or are red
// and road.js in Release's corner, with a tick, once passed. A check that calls a model would carry its tool's mark; no check runs a model yet, so none does (decisions §188.5).
import { signal } from "@preact/signals";
import { town } from "../link.js";
import { ask } from "../board/store.js";

export const SKELETONS = ["laborer", "warrior", "elder"];               // the heads, in the order of the checks (orkUI races/skeleton-<tier>)
export const pending = signal("");                                      // the goal whose checks were asked, before the host answered
let asked = Promise.resolve();                                           // the last question to the host, answered or not
const told = signal({});                                                // slug → {checks, was}: what the command answered, and the snapshot's list of that goal when it was asked

const snap = (slug) => town.value?.main_checks?.[slug] || null;

/** A goal's checks as they stand: the snapshot's, else (until it has moved on) what the command answered; [] when none were asked. */
export function checksOf(slug) {
  const mine = told.value[slug], now = snap(slug);
  if (mine && (!now || JSON.stringify(now) === mine.was)) return mine.checks;
  return now || [];
}

/** Whether a check of the goal is red. */
export const isRed = (list) => list.some((c) => c.state === "failed");

/** Asks the host to run (or to answer the last results of) the checks of the goal; `again` after a red one. */
export function startChecks(slug) {
  const was = JSON.stringify(snap(slug)), again = isRed(checksOf(slug));
  pending.value = slug;
  asked = ask("ideas.to_main_checks", { idea: slug, ...(again ? { again: true } : {}) }).then((got) => {
    if (got && Array.isArray(got.checks) && got.checks.length) told.value = { ...told.value, [slug]: { checks: got.checks, was } };
  }).finally(() => { if (pending.value === slug) pending.value = ""; });
  return asked;
}

/** Until the host has answered the last question (a press that comes before the answer waits for it, then looks at what stands). */
export const whenAsked = () => asked;

/** Forgets what the command answered (the choice was dropped). */
export function forgetChecks() {
  pending.value = "";
  told.value = {};
}

const STATE = { failed: 3, running: 2, waiting: 1, passed: 0 };

/** The skeletons of a list of checks: one for each of the first two and one for the rest (the third and, folded into it, the fourth and more). Each is `{at, tier, name, state, words, label}`: `state` the worst of the
 *  checks it stands for (failed, then running, then waiting, passed), `label` its words for the title and a screen reader (*Tests: checking*, *Tests: passed*, *Regression: 2 tests fail*). */
export function skeletonsOf(list) {
  const out = [];
  for (let at = 0; at < Math.min(3, list.length); at += 1) {
    const mine = at < 2 ? [list[at]] : list.slice(2);
    const worst = mine.reduce((a, c) => (STATE[c.state] > STATE[a.state] ? c : a), mine[0]);
    const name = mine.length > 1 ? `${mine[0].name} and ${mine.length - 1} more` : mine[0].name;
    const words = worst.state === "failed" ? `${worst.name}: ${worst.words || "red"}` : `${name}: ${worst.state === "passed" ? "passed" : "checking"}`;
    out.push({ at, tier: SKELETONS[at], name, state: worst.state, words, label: words });
  }
  return out;
}

/** The line over the portal while the checks run, and the sealed line when one is red (*Sealed: Regression is red: 2 tests fail*). */
export const CHECKING = "Checking the way into main";
export function sealedWords(list) {
  const red = list.find((c) => c.state === "failed");
  return red ? `${red.name} is red: ${red.words || "it failed"}` : "";
}
