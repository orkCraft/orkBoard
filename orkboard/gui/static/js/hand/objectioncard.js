// A leader's no (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §4.3, decisions §183.3): the `objection` row's card, one for each leader of a goal's route that said no in Talk, before the decision.
// The row is `{kind: "objection", idea, party, leader, why, instead, after, after_title, answers: [drop|smaller|later|go]}` (realm/idea_objections.py). Its face is the hand's card (stopcard.js): the question sign, the
// leader's own head as its asker, *<Leader> says no* at its foot, under the first lane (data.js `laneOf`: it is the whole goal's). Lifted: the leader's why, the smaller goal it would do when it named one, and the answers
// the row offers — **Drop the goal** (danger), **Do the smaller one** (the goal's words become that one; Talk is not run again), **Not now** (Product's, when it named a goal in line: this goal waits for that one) and
// **Go on anyway** (the decision goes on and says whom the person overruled) — each sends `ideas.objection {idea, party, answer}`. A doubt is no card: the decision's card says it.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { act } from "../shell/store.js";
import { partiesAll } from "../table/data.js";
import { way } from "./ways.js";

const partyBy = (slug) => partiesAll().find((g) => g.slug === slug) || null;

/** The leader of the party that said no, as the page shows leaders: `{name, head}` (the Taskmaster where the party has no leader of its own). */
export const objector = (row) => {
  const lead = partyBy(row?.party)?.leader || null;
  return { name: lead?.name || "The Taskmaster", head: lead?.head || null };
};

/** *The Architect says no*. */
export const saysNo = (row) => `${objector(row).name} says no`;

/** The answers, in the order the card offers them: `[label, what it does]`; the row says which apply. */
const answerWords = (row) => ({
  drop: ["Drop the goal", "The goal is dropped"],
  smaller: ["Do the smaller one", `The goal becomes: ${row.instead}`],
  later: ["Not now", `The goal waits for ${row.after_title || "that goal"}`],
  go: ["Go on anyway", "The decision goes on and says whom you overruled"],
});

function Objection({ s, close }) {
  const row = s.row || {}, [busy, setBusy] = useState(false), words = answerWords(row);
  const send = async (answer) => {
    setBusy(true);
    try {
      if (await act("ideas.objection", { idea: row.idea, party: row.party, answer })) close?.();
    } finally { setBusy(false); }
  };
  return html`<div class="hand-way hand-way--objection" data-kind="objection" data-party=${row.party || ""}>
    <p class="ork-label hand-way__no">${saysNo(row)}</p>
    <p class="body hand-lifted__text hand-way__words">${row.why}</p>
    ${row.instead && html`<p class="cap hand-way__instead"><span class="ork-label">Instead</span> ${row.instead}</p>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      ${(row.answers || []).filter((a) => words[a]).map((a) => html`<button type="button" key=${a} data-answer=${a} class=${`ork-btn${a === "drop" ? " danger" : a === "smaller" ? " primary" : ""}`}
        disabled=${busy} title=${words[a][1]} onClick=${() => send(a)}>${words[a][0]}</button>`)}
    </div>
  </div>`;
}

// The face: the question sign, the leader that said no as its asker, *<Leader> says no* at its foot, no price.
way("objection", { sign: "question", head: (s) => objector(s.row).head, foot: (s) => saysNo(s.row), price: () => null, Lifted: Objection });
