// A quick question comes back as a card in the hand (docs/specs/168 D3, decisions §283.20): the card of the kind **?** was asked on the open tab (table/ask.js), went through the Orkmaster to whoever knows
// (the open tab's leader; on the Orkmaster's tab the Orkmaster, or one hop to the leader whose part it is) and is answered. The record is the host's `town.ask` (`{status, party, tab, hop, ways, q, answer, sources, goal, at}`,
// realm/board_ask.py); it is a read, not a goal: no file, no rune, no place in the column, and not on the Board. `askStops` makes its stop, one at most, after the others, under the lane of whoever answered (the first
// lane for the Orkmaster); the hand's card shows the answering leader's head and the question, and lifted it lays the answer (plain text, never Markdown) and its sources and, in the hand, its three ways, **Make it a goal**,
// **Ask more** and **Got it** (table/ask.js `ASK_WAYS` and `askActs`: the same acts as the bubble's). Nothing here counts what waits; *Got it* puts the card away.
import { html } from "../html.js";
import { mapData } from "../shell/store.js";
import { ORKMASTER } from "../frame/state.js";
import { Linked } from "../table/asklinks.js";
import { ASK_WAYS, askActs } from "../table/ask.js";
import { way } from "./ways.js";

export const ASK = "Quick question";

/** The Orkmaster's head, crowned: the asker when the Orkmaster answered itself. */
const orkish = () => {
  const ork = mapData.value?.project?.orkmaster || null;
  return { race: ork?.race || "peon", tier: ork?.tier || "crown" };
};

/** The hand's stop of an answered quick question `ask` (the host's `town.ask`), as an array of none or one. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `goal(slug)`, `open`). */
export function askStops(ask, ctx) {
  if (!ask || ask.status !== "answered") return [];
  const slug = ask.party || "", g = slug ? ctx.goal(slug) : null, party = (slug && ctx.party(slug)) || { slug: "", name: "Orkmaster", head: orkish(), lead: "Orkmaster" };
  const row = { ...ask, record: ask, kind: "ask", goal: slug, idea: undefined, blocks: false };      // `goal` is the stack's key (the lane), so the answer's suggested goal stays in `record.goal`
  return [{ key: `ask/${ask.at}`, kind: "ask", ref: row, row, node: null, task: null, label: ASK, gem: "?", tone: "", gemTip: "A question costs nothing", head: party.head, small: true, whoTip: "",
    title: ask.q, full: ask.q, text: "", why: "", g: g || null, party, other: ctx.open !== ORKMASTER && ctx.open !== party.slug }];
}

/** The lifted card: the question, the answer on the table and the three ways in the hand. */
export function AskLifted({ s, close }) {
  const row = s.row || {}, rec = row.record || row, acts = askActs(rec, close), pick = { make_it_a_goal: acts.goal, ask_more: acts.more, take: acts.got }, sources = Array.isArray(row.sources) ? row.sources : [];
  return html`<div class="hand-way hand-way--ask" data-kind="ask" data-hop=${row.hop ? "yes" : "no"}>
    <p class="ork-label">${ASK}</p>
    <p class="cap hand-way__words" data-part="question">${row.q}</p>
    <p class="body hand-lifted__text hand-way__words" data-part="answer"><${Linked} text=${row.answer} /></p>
    ${sources.length > 0 && html`<ul class="hand-way__points" aria-label="Where it is said">${sources.map((x) => html`<li key=${x} class="body"><${Linked} text=${x} /></li>`)}</ul>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      ${ASK_WAYS.map((w) => html`<button type="button" key=${w.kind} class=${w.kind === "make_it_a_goal" ? "ork-btn primary" : "ork-btn quiet"} data-way-kind=${w.kind} data-act=${w.kind}
        title=${w.kind === "take" ? "Takes the answer in; nothing changes" : w.kind === "ask_more" ? "Asks again, on the same tab" : rec.goal || rec.q} onClick=${pick[w.kind]}>${w.name}</button>`)}
    </div>
  </div>`;
}

// The face: the question mark as its gem, the answering leader as its asker, the question at its foot, no price.
way("ask", { sign: "question", foot: () => ASK, price: () => null, Lifted: AskLifted });
