// What the hand holds, read from the Board as the shell keeps it (docs/specs/98-the-table-and-the-hand.md §4, docs/specs/101 §4): the stacks (a goal's Needs you rows, the urgent first, each under
// the lane of who asks: `laneOf`), the goals done (the discard) and what dev holds that main lacks (the gate). The goals in line are the table's (table/data.js `lineNow`: no deck).
// Pure functions over `ideas.map`, `ideas.board` and `ideas.gate`, so that a face and a test read the same lists; the faces are the neighbouring modules.
// A node's `place` is the host's (realm/goal_place.py); nothing here decides where a goal lies.
import { board, goalList } from "../board/store.js";
import { town } from "../link.js";
import { gateData, mapData } from "../shell/store.js";
import { byUrgency, gateOf, goalsOf, nodesOf, paidStopsOf, resultStop, resultsOf, signInStopsOf, stopsOf, todoLast } from "../arena/arenawords.js";
import { inCodeStopsOf } from "../arena/incodewords.js";
import { ORKMASTER } from "../frame/state.js";
import { partiesNow, roadSlugs, waitRuns, wide } from "../table/data.js";
import { groupsStops } from "./groupscard.js";
import { askStops } from "./askcard.js";
import { concernStops } from "./concerncard.js";
import { doubtStops } from "./doubtcard.js";
import { decidedStops } from "./decidedcard.js";
import { nightProposalStops } from "./nightproposalcard.js";
import { devStops, waitsForDev } from "./devcard.js";
import { hypothesisStops } from "./hypothesiscard.js";
import { cascadeStops } from "./cascadecard.js";
import { projectStops, questionStops } from "./questions.js";
import { cardsOn } from "../cards/on.js";
import { battleStops, turnStops } from "./turnstops.js";

/** The parties of the map in the Board's order. */
export const partiesOf = (map = mapData.value) => goalsOf(map, goalList().map((x) => x.slug));

/** A party as a card says it: its name, its leader's head and name. */
export function partyCard(g) {
  return { slug: g.slug, name: g.short || g.title, head: g.leader?.head || null, lead: g.leader?.name || "Taskmaster" };
}

const doneFace = (n) => ({ slug: n.slug, title: n.short || n.title, full: n.title, element: n.element || "", hue: n.hue || "", party: n.goal, usd: n.usd, seen: n.seen || "", tasks: n.tasks || [], type: n.type || null, picture: n.picture || "" });
const newest = (a, b) => String(b.updated || "").localeCompare(String(a.updated || ""));

/** The goals done and not yet seen, the last one first. At the wide width a goal done on its own branch that waits for dev is not among them: it lies in the discard's lower pile (`lowerOf`, spec 168 F2); the narrow page keeps it here, as it was. */
export function doneOf(map = mapData.value) {
  return [...(map?.nodes || [])].filter((n) => n.place === "discard" && !(wide.value && waitsForDev(n.slug))).sort(newest).map(doneFace);
}

/** The goals done on their own branch and waiting for dev (the Board's row says `waits_for_dev`), the last one first: the discard's lower pile (table/plates.js). */
export function lowerOf(map = mapData.value) {
  return [...(map?.nodes || [])].filter((n) => waitsForDev(n.slug)).sort(newest).map(doneFace);
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

/** The kinds of old card that ask a question of the person: a spec's or a party's (`asks`, `goal`), Talk's and a bug's cause (`talk`, `cause`). */
const QUESTIONS = new Set(["asks", "goal", "talk", "cause"]);

/** Every stop of the project, the most urgent first, a to-do last of all: each Needs you row, a failed task and a pick, a result to look at, the tools' sign-ins
 *  (arenawords.js, as the old hand read them). `open`: the tab that is open: a party's slug, or "orkmaster" for the Board's (every party at once, so no card says its party:
 *  its leader's head does). On a party's tab a stop of another party says its party. */
export function stopsOfProject(map = mapData.value, rows = board.value?.needs_you || [], open = "", ask = town.value?.ask || null) {
  const running = new Set((map?.nodes || []).filter(waitRuns).map((n) => n.slug));                       // a decision all the leaders agreed on, its wait running: it goes on by itself, no card in the hand (decisions §240); it lies in the column
  const needs = rows.filter((r) => !(r.kind === "decision" && running.has(r.idea))), out = [], ork = map?.project?.orkmaster || null, byParty = partyBy(map), ctx = { party: (slug) => (slug ? byParty[slug] || null : null), open };
  for (const g of partiesOf(map)) {
    const nodes = nodesOf(map, g.slug), party = partyCard(g);
    const whole = (s) => (s.kind === "leader_change" && !s.node ? { ...s, node: (map?.nodes || []).find((n) => n.slug === s.row?.idea) || null } : s);      // a change asked of this leader about a goal that lies in another party's lane: the goal's rune is still its card's
    const mine = [...stopsOf(needs, g, nodes, ork).map(whole), ...resultsOf(nodes).map((r) => resultStop(r, nodes))];
    out.push(...mine.flatMap((s) => questionStops({ ...s, g, party, other: open !== ORKMASTER && open !== party.slug }, ctx)));      // a Talk's and a bug's questions: one card a question (questions.js)
  }
  out.push(...signInStopsOf(needs, open), ...paidStopsOf(needs, open, ork), ...inCodeStopsOf(needs, open, ork));
  const after = { ...ctx, goal: (slug) => partiesOf(map).find((g) => g.slug === slug) || null, ork };
  const asked = cardsOn() ? battleStops(out.filter((s) => !QUESTIONS.has(s.kind))) : out;      // on the table of cards a question is its turn card (turnstops.js): its way is one press with its Undo, no pass; the old card of it is not dealt
  const first = [...todoLast(byUrgency(asked)), ...projectStops(needs, after), ...hypothesisStops(needs, after), ...groupsStops(needs, after), ...cascadeStops(needs, after), ...askStops(ask, after), ...concernStops(map, after), ...doubtStops(map, after), ...decidedStops(map, after)];
  const moves = cardsOn() ? turnStops(map, after) : [];      // the moves that wait (ideas.turns, turnstops.js)
  return [...first, ...moves, ...nightProposalStops(needs, { ...after, window: String(board.value?.night || "") }), ...devStops(map, after)];          // the project's questions hold nothing back: after the others, under their leader's party's lane; so does *Did it hold?* (spec 116 E)
}

/** The goal a stop belongs to ("" for a stop of no goal), and the stack it lies in: a goal's; a party's own question (`party:<slug>`); a sign-in alone. */
export const goalOfStop = (s) => (s.kind === "sign_in" ? "" : s.node?.slug || s.row?.idea || (s.kind === "pick" ? s.row?.slug : "") || s.result?.idea || "");
export function stackKey(s) {
  if (s.kind === "battle") return s.key;                                           // a battle is a stack of its own, beside its goal's questions (decisions §298.7); a move that waits lies in its goal's stack (§300.2)
  const goal = goalOfStop(s);
  return goal || (s.kind === "sign_in" ? s.key : s.kind === "concern" ? `concerns:${s.row.goal}` : s.row?.goal ? `party:${s.row.goal}` : s.key);      // a leader's concerns are one stack of their own (spec 168 D4)
}

/** What is the whole goal's, not one party's: the route, Talk of several leaders, the decision, a fork, the Orkmaster's collision (docs/specs/101 §4.2) and its *Go on paid?* (docs/specs/105 §3): they lie under the first lane. */
const WHOLE = new Set(["route", "talk", "hearing", "decision", "fork", "conflict", "collide", "paid", "in_code", "groups", "spec_change", "turn", "battle"]);

/** The party a row belongs to ("" for a row of no party of its own). */
const partyOfRow = (row) => row?.g?.slug || row?.row?.goal || row?.goal || "";
/** Whether a row is one of a road party at a width where that party has no lane (Release at the wide width: its lane is the discard, docs/specs/156 D.1): it lies in the hand's last lane. */
const onRoad = (row, parties) => !WHOLE.has(row?.kind || row?.row?.kind || "") && !parties.some((g) => g.slug === partyOfRow(row)) && roadSlugs().has(partyOfRow(row));

/** The lane a row lies under (docs/specs/101 §4.3): 0 the first (the project's), else 1 + the place of its party among the tabs' parties (table/data.js `partiesNow`, the order of the lanes after the first).
 *  A failure lies under its task's party, a party's question under its party, the project's questions (no goal of their own) under their leader's party; what is the whole goal's, a sign-in and a row
 *  of a party the tabs do not have lie under the first. The exception is Release's row at the wide width (no lane of its own: its lane is the discard): it lies in the last lane (spec 156 D.1).
 *  `row`: a stop (`stopsOfProject`) or a Needs you row (`{kind, goal}`). */
export function laneOf(row, parties = partiesNow()) {
  if (WHOLE.has(row?.kind || row?.row?.kind || "")) return 0;
  const at = parties.findIndex((g) => g.slug === partyOfRow(row));
  return at < 0 ? (onRoad(row, parties) ? parties.length : 0) : at + 1;
}

/** The stacks (§4.3): one a goal and a lane that has Needs you rows, in the order of their top cards' urgency (the stops come in it), each `{key, goal, lane, road, cards}`, the top first. A goal's cards from one party are
 *  one stack; the cards of a goal that two parties ask about lie in a stack each, under each one's lane. `road`: a road party's stack in the last lane, which lies at its right end (hand/stacks.js). */
export function stacksOf(stops, parties = partiesNow()) {
  const out = [], at = new Map();
  for (const s of stops) {
    const lane = laneOf(s, parties), key = `${stackKey(s)}@${lane}`;
    if (!at.has(key)) { at.set(key, out.length); out.push({ key, goal: goalOfStop(s), lane, road: onRoad(s, parties), cards: [] }); }
    out[at.get(key)].cards.push(s);
  }
  return out;
}

/** A party's own question that blocks nothing (a stack of `party:<slug>`, every card `blocks: false`): in its lane it lies behind a goal's own stack, a result, a stop, a decision (spec 143 E.2, decisions §250.6); what blocks keeps its urgency's place. */
export const lieBehind = (st) => /^(party|concerns):/.test(String(st.key)) && st.cards.length > 0 && st.cards.every((c) => c.row?.blocks === false);

/** The card of the hand that a lifted key names (`hand:<stop key>`), null for none. */
export const stopByKey = (stops, key) => stops.find((s) => s.key === key) || null;

/** The parties by their slug, for a card that says its party and a field that addresses one. */
export const partyBy = (map = mapData.value) => Object.fromEntries(partiesOf(map).map((g) => [g.slug, partyCard(g)]));
