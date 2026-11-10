// What a leader decided by itself, as a card that can be overruled (docs/specs/168 H4, decisions §283.22, §283.33; the way of answering *Silent*, core/idea_ways.py): a leader whose way is Silent decides the questions of its Talk that are no lock (§266.5: going into main, money above
// what was agreed, dropping or holding a goal, a decision against an earlier one are always asked) and the goal's row says so (`decided`: `[{id, party, leader, q, answer, why, round}]`, realm/answer_ways.py `decided_of`). Each decision is a card of **its leader's stack** (the goal's,
// under that leader's lane): muted, no alert's ring, its leader's head, the sign of *decided* (a check), the question as its title, what it decided and why at its foot. Its ways are two: **Accepted** (`ideas.decided_accept {idea, id}`, the way's kind `go_on`: the decision
// stands as it is) and **Replay** (`ideas.decided_replay {idea, id}`, `ask_more`: the question is back as a card with its ways). The card leaves the hand by itself when the goal moves to its next stage (the row's `decided` is empty then). Wide only, as the concern card.
import { ORKMASTER } from "../frame/state.js";

if (typeof document !== "undefined") {
  const href = new URL("./decidedcard.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const DECIDED = "decided", ACCEPTED = "Accepted", REPLAY = "Replay";
export const ACCEPTED_LINE = "The decision stands as it is.", REPLAY_LINE = "The question comes back with its ways, and you answer it.";

/** *The Architect decided* (a leader as the page names it, with its article once: doubtcard.js says the same). */
export const decidedWords = (lead) => `${/^the\s/i.test(String(lead || "")) ? String(lead) : `The ${lead || "Taskmaster"}`} ${DECIDED}`;

/** The hand's stops of what leaders decided in Talk, one a decision, after the other stops. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `goal(slug)`, `open`). */
export function decidedStops(map, ctx) {
  const out = [];
  for (const n of map?.nodes || []) {
    for (const d of n.decided || []) {
      const party = ctx.party(d.party), g = ctx.goal(d.party);
      if (!party || !g) continue;
      const line = `${decidedWords(party.lead)}: ${d.answer}`, why = d.why ? `${line}. ${d.why}` : line;
      out.push({ key: `decided/${n.slug}/${d.id}`, kind: "decided", ref: { ...d, idea: n.slug }, row: { goal: d.party, idea: n.slug, kind: "decided", blocks: false }, node: n, task: null, label: "Decided", gem: "", tone: "", gemTip: "", head: party.head, small: true, whoTip: "",
        title: d.q, full: d.q, text: why, why, g, party, other: ctx.open !== ORKMASTER && ctx.open !== d.party });
    }
  }
  return out;
}
