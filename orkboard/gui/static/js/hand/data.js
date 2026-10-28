// What the hand holds, read from the Board as the shell keeps it (docs/specs/98-the-table-and-the-hand.md §4, docs/specs/101 §4): the stacks (a goal's Needs you rows, the urgent first, each under
// the lane of who asks: `laneOf`), the goals done (the discard) and what dev holds that main lacks (the gate). The goals in line are the table's (table/data.js `lineNow`: no deck).
// Pure functions over `ideas.map`, `ideas.board` and `ideas.gate`, so that a face and a test read the same lists; the faces are the neighbouring modules.
// A node's `place` is the host's (realm/goal_place.py); nothing here decides where a goal lies.
import { board, goalList } from "../board/store.js";
import { gateData, mapData } from "../shell/store.js";
import { byUrgency, gateOf, goalsOf, nodesOf, resultStop, resultsOf, signInStopsOf, stopsOf, todoLast } from "../arena/arenawords.js";
import { ORKMASTER } from "../frame/state.js";
import { partiesNow } from "../table/data.js";

/** The parties of the map in the Board's order. */
export const partiesOf = (map = mapData.value) => goalsOf(map, goalList().map((x) => x.slug));

/** A party as a card says it: its name, its leader's head and name. */
export function partyCard(g) {
  return { slug: g.slug, name: g.short || g.title, head: g.leader?.head || null, lead: g.leader?.name || "Taskmaster" };
}

/** The goals done and not yet seen, the last one first. */
export function doneOf(map = mapData.value) {
  const at = (n) => String(n.updated || "");
  return [...(map?.nodes || [])].filter((n) => n.place === "discard").sort((a, b) => at(b).localeCompare(at(a))).map((n) => ({
    slug: n.slug, title: n.short || n.title, full: n.title, element: n.element || "", party: n.goal, usd: n.usd, seen: n.seen || "", tasks: n.tasks || [], type: n.type || null }));
}

/** What dev holds that main lacks, said for the discard: `{n, into, main, goals, commits, files, off}`; null with nothing to merge. */
export function readyOf(gate = gateData.value) {
  const shape = gateOf(gate);
  if (!shape || shape.off) return null;
  const n = (gate.ideas || []).length;
  return { n, into: gate.into, main: gate.main, goals: gate.ideas || [], commits: gate.commits, files: gate.files };
}

/** *3 goals ready for main*, *1 goal ready for main*; a gate that holds commits and no goal says its commits. */
export function readyWords(r) {
  if (!r) return "";
  if (r.n) return `${r.n} ${r.n === 1 ? "goal" : "goals"} ready for ${r.main}`;
  return `${r.commits} ${r.commits === 1 ? "commit" : "commits"} ready for ${r.main}`;
}

/** Every stop of the project, the most urgent first, a to-do last of all: each Needs you row, a failed task and a pick, a result to look at, the tools' sign-ins
 *  (arenawords.js, as the old hand read them). `open`: the tab that is open: a party's slug, or "orkmaster" for the Board's (every party at once, so no card says its party:
 *  its leader's head does). On a party's tab a stop of another party says its party. */
export function stopsOfProject(map = mapData.value, needs = board.value?.needs_you || [], open = "") {
  const out = [], ork = map?.project?.orkmaster || null;
  for (const g of partiesOf(map)) {
    const nodes = nodesOf(map, g.slug), party = partyCard(g);
    const mine = [...stopsOf(needs, g, nodes, ork), ...resultsOf(nodes).map((r) => resultStop(r, nodes))];
    out.push(...mine.map((s) => ({ ...s, g, party, other: open !== ORKMASTER && open !== party.slug })));
  }
  out.push(...signInStopsOf(needs, open));
  return todoLast(byUrgency(out));
}

/** The goal a stop belongs to ("" for a stop of no goal), and the stack it lies in: a goal's; a party's own question (`party:<slug>`); a sign-in alone. */
export const goalOfStop = (s) => (s.kind === "sign_in" ? "" : s.node?.slug || s.row?.idea || (s.kind === "pick" ? s.row?.slug : "") || s.result?.idea || "");
export function stackKey(s) {
  const goal = goalOfStop(s);
  return goal || (s.kind === "sign_in" ? s.key : s.row?.goal ? `party:${s.row.goal}` : s.key);
}

/** What is the whole goal's, not one party's: the route, Talk of several leaders, the decision, a fork, and the Orkmaster's collision (docs/specs/101 §4.2): they lie under the first lane. */
const WHOLE = new Set(["route", "talk", "decision", "fork", "collide"]);

/** The lane a row lies under (docs/specs/101 §4.3): 0 the first (the project's), else 1 + the place of its party among the tabs' parties (table/data.js `partiesNow`, the order of the lanes after the first).
 *  A failure lies under its task's party, a party's question under its party, the project's questions (no goal of their own) under their leader's party; what is the whole goal's, a sign-in and a row
 *  of a party the tabs do not have lie under the first. `row`: a stop (`stopsOfProject`) or a Needs you row (`{kind, goal}`). */
export function laneOf(row, parties = partiesNow()) {
  if (WHOLE.has(row?.kind || row?.row?.kind || "")) return 0;
  const slug = row?.g?.slug || row?.row?.goal || row?.goal || "";
  const at = parties.findIndex((g) => g.slug === slug);
  return at < 0 ? 0 : at + 1;
}

/** The stacks (§4.3): one a goal and a lane that has Needs you rows, in the order of their top cards' urgency (the stops come in it), each `{key, goal, lane, cards}`, the top first. A goal's cards from one party are
 *  one stack; the cards of a goal that two parties ask about lie in a stack each, under each one's lane. */
export function stacksOf(stops, parties = partiesNow()) {
  const out = [], at = new Map();
  for (const s of stops) {
    const lane = laneOf(s, parties), key = `${stackKey(s)}@${lane}`;
    if (!at.has(key)) { at.set(key, out.length); out.push({ key, goal: goalOfStop(s), lane, cards: [] }); }
    out[at.get(key)].cards.push(s);
  }
  return out;
}

/** The card of the hand that a lifted key names (`hand:<stop key>`), null for none. */
export const stopByKey = (stops, key) => stops.find((s) => s.key === key) || null;

/** The parties by their slug, for a card that says its party and a field that addresses one. */
export const partyBy = (map = mapData.value) => Object.fromEntries(partiesOf(map).map((g) => [g.slug, partyCard(g)]));
