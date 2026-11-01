// The mood of a leader (docs/specs/123-the-leaders-at-the-table.md §7.3, decisions §201.5): which of its five faces the tabs draw (orkUI 0.27.0 `races/<race>-<tier>-<mood>.png`; orkui.js `Head` `mood`). No face is drawn here: `moodOf(g)` says it.
// In the order of what wins: **asleep** when the AI tool of the party's leader has no window left (hand/windows.js `windowsOf`: the tool is dry) — a tool the snapshot's limits say nothing of is not asleep: nothing is read out of
// a missing answer —; **no** when the party's leader holds a side of an open hearing whose kind is *drop* or *smaller* (spec 120 §4: the Needs you rows of kind `hearing`, a side's `leaders` the parties' slugs; a hearing held for Undo is none);
// **worried** when the party's map has an alert (`hasAlert`); **focused** when one of its tasks is at work (`isWorking`) or its leader is looking at its map (the record's status *looking*); **pleased** for a minute after a goal of the party
// reached the discard *while this page was open* (never for one found there on coming back, decisions §89.0: the first read of the map is the baseline, a project switch starts again); else calm ("").
// The Orkmaster's (`g` null): asleep when the machine's main tool is dry (`town.mana.main`), focused while the Orkmaster reads, routes or talks a goal (a goal in the state `reading`, `planning` or `talk`), else calm.
// A face changes with its state and stands still: there is no idle motion (§149.1). Pure but for the signals it reads, and the one watcher of the discard below.
import { effect, signal } from "@preact/signals";
import { town } from "../link.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { isHeld } from "../hand/hearingstate.js";
import { windowsOf } from "../hand/windows.js";
import { groupsOf, laneOf, toolOf } from "./data.js";
import { hasAlert, lookOf, recordOf } from "./concerns.js";

const PLEASED_MS = 60000;                                         // a goal done pleases its party's leader for this long
const OWN_WORK = ["reading", "planning", "talk"];                // the goal states in which the Orkmaster itself is at work

/** A party has an ork at work: one of its goals has a task running or being tested (a task that asks or has failed is not at work). */
export const isWorking = (g) => laneOf(g).some(({ tasks }) => tasks.some((t) => t.state === "running" || t.state === "testing"));

// -- pleased: a goal of the party reached the discard while the page was open --------------------------------------------------------------------------------------------------------------------------
const pleased = signal({});                                        // party slug → the time (ms) its pleasure ends
let known = null;                                                   // the slugs in the discard at the first read of this project's map: what is found there is never news

effect(() => {
  const nodes = mapData.value?.nodes;
  if (!Array.isArray(nodes)) { known = null; return; }              // another project (the map is let go) or none yet
  const lying = new Set(nodes.filter((n) => n.place === "discard").map((n) => n.slug));
  if (known === null) { known = lying; return; }
  const fresh = nodes.filter((n) => n.place === "discard" && !known.has(n.slug) && n.goal);
  known = lying;
  if (!fresh.length) return;
  const until = Date.now() + PLEASED_MS, now = { ...pleased.peek() };
  for (const n of fresh) now[n.goal] = until;
  pleased.value = now;
  setTimeout(() => {                                                // the minute is over: the face is calm again
    const left = Object.fromEntries(Object.entries(pleased.peek()).filter(([, t]) => t > Date.now()));
    if (Object.keys(left).length !== Object.keys(pleased.peek()).length) pleased.value = left;
  }, PLEASED_MS + 50);
});

// -- what a mood reads --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

/** Whether the tool has no window left, by the snapshot's limits; false when they say nothing of it. */
const spent = (tool, snapshot) => {
  const l = (snapshot?.limits || []).find((x) => x.provider === tool);
  return !!l && windowsOf(l).dry;
};

/** The AI tool the party's leader runs on, or null when the party has no leader seat to ask. */
function leaderTool(g) {
  const seat = groupsOf(g).find((x) => x.band === "lead")?.seats[0];
  return seat ? toolOf(g, seat).id : null;
}

/** Whether the party's leader says no in an open hearing: a side of kind *drop* or *smaller* that it holds. */
const saysNo = (g) => (board.value?.needs_you || []).some((row) => row?.kind === "hearing" && !isHeld(row)
  && (row.sides || []).some((s) => (s.kind === "drop" || s.kind === "smaller") && (s.leaders || []).includes(g.slug)));

/**
 * The face a leader wears: `""` (calm), `asleep`, `no`, `worried`, `focused` or `pleased`. `g`: a party of the map (`mapData` goals[]), or null/undefined for the Orkmaster's. `snapshot`: the host's last snapshot (`town.value`:
 * its `limits` and `mana`); the Board's rows, the maps' records and the discard are read from their signals.
 */
export function moodOf(g, snapshot = town.value) {
  if (!g) {
    const main = snapshot?.mana?.main || "";
    if (main && spent(main, snapshot)) return "asleep";
    return (mapData.value?.nodes || []).some((n) => OWN_WORK.includes(n.state)) ? "focused" : "";
  }
  const tool = leaderTool(g);
  if (tool === "" || (tool && spent(tool, snapshot))) return "asleep";
  if (saysNo(g)) return "no";
  if (recordOf(g.slug) ? lookOf(g.slug).alerts > 0 : hasAlert(g)) return "worried";               // the record when the page has read one, else the snapshot's count
  if (isWorking(g) || lookOf(g.slug).status === "looking") return "focused";
  return (pleased.value[g.slug] || 0) > Date.now() ? "pleased" : "";
}
