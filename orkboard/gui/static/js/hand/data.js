// What the hand holds, read from the Board as the shell keeps it (docs/specs/98-the-table-and-the-hand.md §4): the goals in line (the deck), the
// stacks (a goal's Needs you rows, the urgent first), the goals done (the discard) and what dev holds that main lacks (the gate). Pure functions
// over `ideas.map`, `ideas.board` and `ideas.gate`, so that a face and a test read the same lists; the faces are the neighbouring modules.
// A node's `place` is the host's (realm/goal_place.py); nothing here decides where a goal lies.
import { board, goalList } from "../board/store.js";
import { gateData, mapData } from "../shell/store.js";
import { byUrgency, gateOf, goalsOf, nodesOf, resultStop, resultsOf, signInStopsOf, stopsOf } from "../arena/arenawords.js";
import { todoLast } from "../arena/stops.js";
import { ORKMASTER } from "../frame/state.js";

export const MANY = 7;                         // the deck's row shows this many goals, then *All · search* (§4.1)

/** The parties of the map in the Board's order. */
export const partiesOf = (map = mapData.value) => goalsOf(map, goalList().map((x) => x.slug));

/** A party as a card says it: its name, its leader's head and name. */
export function partyCard(g) {
  return { slug: g.slug, name: g.short || g.title, head: g.leader?.head || null, lead: g.leader?.name || "Taskmaster" };
}

/** The goals in line, in the Orkmaster's order (the order of the map's nodes): each its element and name; `reset` when it waits for the window's reset. */
export function lineOf(map = mapData.value) {
  const parties = Object.fromEntries((map?.goals || []).map((g) => [g.slug, g]));
  return (map?.nodes || []).filter((n) => n.place === "deck").map((n) => ({
    slug: n.slug, title: n.short || n.title, full: n.title, element: n.element || "", party: n.goal, partyName: parties[n.goal]?.short || parties[n.goal]?.title || "",
    waits: n.waits_as || "", reset: n.waits_as === "reset", at: n.held_until || n.start_at || "", state: n.state }));
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

/** The stacks (§4.2): one a goal that has Needs you rows, in the order of their top cards' urgency (the stops come in it), each `{key, goal, cards}`, the top first. */
export function stacksOf(stops) {
  const out = [], at = new Map();
  for (const s of stops) {
    const key = stackKey(s);
    if (!at.has(key)) { at.set(key, out.length); out.push({ key, goal: goalOfStop(s), cards: [] }); }
    out[at.get(key)].cards.push(s);
  }
  return out;
}

/** The card of the hand that a lifted key names (`hand:<stop key>`), null for none. */
export const stopByKey = (stops, key) => stops.find((s) => s.key === key) || null;

/** The parties by their slug, for a card that says its party and a field that addresses one. */
export const partyBy = (map = mapData.value) => Object.fromEntries(partiesOf(map).map((g) => [g.slug, partyCard(g)]));
