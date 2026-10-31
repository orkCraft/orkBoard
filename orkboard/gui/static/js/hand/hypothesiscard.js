// A hypothesis tested is a card (docs/specs/116-hypotheses-on-products-tree.md §6.2; decisions §194): the row `hypothesis` (realm/board_rows.py: `{kind: "hypothesis", id, text, signal, evidence: [{text, ref, at}],
// tests: [{slug, title}], party, leader, blocks, priority, at}`), asked when every test of an open hypothesis is done: *Did it hold?* The host gives data only; the words are this face's. The row is a row of no goal's:
// `hypothesisStops` makes its stop, after the others, under its proposer's party's lane (the person's own, with no party, under the first; hand/data.js `stopsOfProject` calls it, as it calls `projectStops`). Its face is
// the hand's card (stopcard.js): orkUI's flask sign in the window, the hypothesis as its name, the proposer's leader's head as its asker (the Orkmaster's crowned head for the person's own), *Did it hold?* at its foot,
// no price. Lifted: the hypothesis, *We'll know when* and its signal, what was found as lines (each with its goal's element when it has one), the tests' names, a *Why* line and three answers — **Held** and **Refuted**
// (each writes a decision) and **Not sure yet** (it stays open, the why kept as what was found) — each sends `ideas.hypothesis_judge {id, state, why?}`; answered, the Board is read again and the card leaves. Nothing
// here counts what waits.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Elem } from "../orkui.js";
import { act, mapData } from "../shell/store.js";
import { ORKMASTER } from "../frame/state.js";
import { way } from "./ways.js";

export const ASK = "Did it hold?";
const WHY_CHARS = 200;

/** The Orkmaster's head, crowned: the asker of the person's own hypothesis (it has no party's leader). */
const orkish = () => {
  const ork = mapData.value?.project?.orkmaster || null;
  return { race: ork?.race || "peon", tier: ork?.tier || "crown" };
};

/** The hand's stops of the `hypothesis` rows among `rows` (the Needs you rows), one for each, after the others. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `goal(slug)`, `open`). */
export function hypothesisStops(rows, ctx) {
  return rows.filter((r) => r.kind === "hypothesis").map((row) => {
    const g = ctx.goal(row.party), party = ctx.party(row.party) || { slug: "", name: "Orkmaster", head: orkish(), lead: "Orkmaster" };
    return { key: `hypothesis/${row.id}`, kind: "hypothesis", ref: row, row: { ...row, goal: row.party, idea: undefined }, node: null, task: null, label: ASK, gem: "", tone: "alert", gemTip: "",
      head: party.head, small: true, whoTip: "", title: row.text, full: row.text, text: row.signal, why: "", g: g || null, party, other: ctx.open !== ORKMASTER && ctx.open !== party.slug };
  });
}

/** The element of the goal an evidence line came from (`ref` is its slug), "" for a line from no goal the Board has. */
const elementOf = (ref) => (ref ? (mapData.value?.nodes || []).find((n) => n.slug === ref)?.element || "" : "");

/** The lifted card: the hypothesis, its signal, what was found, the tests, a *Why* line and the three answers. */
export function HypothesisLifted({ s, close }) {
  const row = s.row || {}, [why, setWhy] = useState(""), [busy, setBusy] = useState(false), found = row.evidence || [], tests = row.tests || [];
  const answer = async (state) => {
    setBusy(true);
    try {
      if (await act("ideas.hypothesis_judge", { id: row.id, state, ...(why.trim() ? { why: why.trim() } : {}) })) close?.();
    } finally { setBusy(false); }
  };
  return html`<div class="hand-way hand-way--hypothesis" data-kind="hypothesis" data-hypothesis=${row.id}>
    <p class="ork-label">${ASK}</p>
    <p class="body hand-lifted__text hand-way__words" data-part="text">${row.text}</p>
    <div class="hand-way__why" data-part="signal"><span class="ork-label">We'll know when</span><p class="body">${row.signal}</p></div>
    ${found.length > 0 && html`<div class="hand-way__why" data-part="evidence"><span class="ork-label">What was found</span>
      <ul class="hand-way__points" aria-label="What was found">${found.map((e, i) => html`<li key=${i} class="body">${elementOf(e.ref) && html`<${Elem} name=${elementOf(e.ref)} /> `}${e.text}</li>`)}</ul></div>`}
    ${tests.length > 0 && html`<div class="hand-way__why" data-part="tests"><span class="ork-label">Tested by</span>
      <ul class="hand-way__points" aria-label="Tested by">${tests.map((t) => html`<li key=${t.slug} class="body">${t.title}</li>`)}</ul></div>`}
    <label class="hand-way__why"><span class="ork-label">Why</span>
      <input class="ork-field" name="why" maxlength=${WHY_CHARS} value=${why} onInput=${(e) => setWhy(e.target.value)} placeholder="One line, if you want one" /></label>
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      <button type="button" class="ork-btn primary" disabled=${busy} data-answer="held" title="It holds: a decision is written" onClick=${() => answer("held")}>Held</button>
      <button type="button" class="ork-btn danger" disabled=${busy} data-answer="refuted" title="It does not hold: a decision is written" onClick=${() => answer("refuted")}>Refuted</button>
      <button type="button" class="ork-btn quiet" disabled=${busy} data-answer="unsure" title="It stays open; the why is kept as what was found" onClick=${() => answer("unsure")}>Not sure yet</button>
    </div>
  </div>`;
}

// The face: the flask sign, the proposer's leader as its asker, *Did it hold?* at its foot, no price.
way("hypothesis", { sign: "flask", foot: () => ASK, price: () => null, Lifted: HypothesisLifted });
