// A doubt left is a card in the hand (docs/specs/168 D5, decisions §283.25; the frame's rule that what the person decides is in the hand): the leaders judged a goal again once and a leader still doubts or says no, with nothing of its say left to answer, so Talk waits
// for the person (core/idea_verdict.py `say_release`). The goal's row says so (`say.doubts`: `[{party, verdict, why}]`, realm/idea_say.py `doubts`); each doubting leader's is a card of **its stack** (the goal's, under that leader's lane), *<Leader> still doubts* (or *still says no*)
// with its why at its foot. Its ways are two: **Judge again now** (`ideas.judge_again {idea}`, the way's kind `ask_more`: the leaders are asked again) and **To the hearing** (`ideas.to_hearing {idea}`, `go_on`: the Talk goes on to its hearing, where the person
// throws it; no kind is nearer, `leader_decides` is the leader deciding, and here the person does). The card leaves the hand when the goal leaves Talk, is judged again or goes to the hearing (the row's `doubts` is empty then). Wide only, as the concern card.
import { ORKMASTER } from "../frame/state.js";
/** *The Architect* (a leader as the page names it, with its article once; table/concerns.js `theLeader` says the same, which this does not import: the hand's data stays light). */
const theLeader = (name) => { const n = String(name || "Taskmaster"); return /^the\s/i.test(n) ? n : `The ${n}`; };

export const STILL_DOUBTS = "still doubts", STILL_NO = "still says no", JUDGE_AGAIN = "Judge again now", TO_HEARING = "To the hearing";

/** The card's words: *The Architect still doubts*, *The Architect still says no*. */
export const doubtWords = (lead, verdict) => `${theLeader(lead)} ${verdict === "no" ? STILL_NO : STILL_DOUBTS}`;

/** The hand's stops of the goals that wait for the person's doubt, one a doubting leader, after the other stops. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `goal(slug)`, `open`). */
export function doubtStops(map, ctx) {
  const out = [];
  for (const n of map?.nodes || []) {
    if (n.state !== "talk") continue;
    for (const d of n.say?.doubts || []) {
      const party = ctx.party(d.party), g = ctx.goal(d.party);
      if (!party || !g) continue;
      const title = doubtWords(party.lead, d.verdict);
      out.push({ key: `doubt/${n.slug}/${d.party}`, kind: "doubt", ref: { ...d, idea: n.slug }, row: { goal: d.party, idea: n.slug, kind: "doubt", blocks: true }, node: n, task: null, label: "Doubt", gem: "", tone: "alert", gemTip: "", head: party.head, small: true, whoTip: "",
        title, full: title, text: d.why, why: d.why, g, party, other: ctx.open !== ORKMASTER && ctx.open !== d.party });
    }
  }
  return out;
}
