// A concern in the hand (docs/specs/168 D4, decisions §283.21): a concern of a party's leader at the alert's level is a card in the hand, **one stack a leader under its lane** (data.js `stackKey`: `concerns:<party>`, behind a goal's own stack); the hand's card, the card
// in the header (table/concernrow.js) and the mark on the scheme (table/concerns.js) are one thing: one hovered or lifted lights the others (table/concernlit.js), and it is answered once. A note stays on the scheme and in the header; a concern laid *Later* is
// face down in the header, out of the hand, until the leader's next look finds it again (realm/concerns.py `lay_later`). The record is the snapshot's (`goals[].concerns.list`, each `{id, on, name, level, what, why, fix, aspect, later, in_hand}`).
// **Played** as any card is (spec 168 D1, sayplay.js `PlayWays`): it rises at the table's foot at its left, the leader's tab opened (it has no goal of its own to pick), its ways the hand's row: **Not a problem** (`not_a_problem`, `ideas.concern_dismiss`),
// **Later** (`later`, `ideas.concern_later`) and **Make it a goal** (`make_it_a_goal`, `ideas.concern_goal`), each carrying `data-way-kind`. A refusal is the host's toast and the card stays. Wide only: the narrow page and the phone do not deal it.
import { ORKMASTER } from "../frame/state.js";
import { concernKey } from "../table/concernrow.js";

export const CONCERN = "Concern";
export const CONCERN_ACTS = [
  { kind: "not_a_problem", name: "Not a problem", line: "It is dropped and not raised again unless its part changes." },
  { kind: "later", name: "Later", line: "It leaves the hand and lies face down in the header until the leader looks again." },
  { kind: "make_it_a_goal", name: "Make it a goal", line: "Its words and its fix become a goal of this party." },
];

/** The hand's stops of the open concerns at the alert's level (the snapshot's `goals[].concerns.list`, `in_hand`), one after another, after the other stops, each under its leader's lane. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `goal(slug)`, `open`). */
export function concernStops(map, ctx) {
  const out = [];
  for (const g of map?.goals || []) {
    const party = ctx.party(g.slug);
    if (!party) continue;
    for (const c of g.concerns?.list || []) {
      if (!c.in_hand) continue;
      out.push({ key: concernKey(g.slug, c.id), kind: "concern", ref: c, row: { ...c, goal: g.slug, idea: undefined, blocks: false, concern: c.id }, node: null, task: null, label: CONCERN, gem: "", tone: "alert", gemTip: "", head: party.head, small: true, whoTip: "",
        title: c.what, full: c.what, text: c.why, why: c.why, g: ctx.goal(g.slug) || null, party, other: ctx.open !== ORKMASTER && ctx.open !== g.slug });
    }
  }
  return out;
}
