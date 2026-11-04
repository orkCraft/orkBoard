// A hypothesis tested is a card (docs/specs/116-hypotheses-on-products-tree.md §6.2; decisions §194): the row `hypothesis` (realm/board_rows.py: `{kind: "hypothesis", id, text, signal, evidence: [{text, ref, at}],
// tests: [{slug, title}], party, leader, blocks, priority, at}`), asked when every test of an open hypothesis is done: *Did it hold?* The host gives data only; the words are this face's. The row is a row of no goal's:
// `hypothesisStops` makes its stop, after the others, under its proposer's party's lane (the person's own, with no party, under the first; hand/data.js `stopsOfProject` calls it, as it calls `projectStops`). Its face is
// the hand's card (stopcard.js): orkUI's flask sign in the window, the hypothesis as its name, the proposer's leader's head as its asker (the Orkmaster's crowned head for the person's own), *Did it hold?* at its foot,
// no price. Lifted: the hypothesis, *Holds when* and its signal, the measures one line each against their bars (hand/hypothesisjudge.js, spec 146 B: a value not read asked, the condition code met marked), what was found as lines (each with its goal's element when it
// has one), the tests' names, a *Why* line and three answers — **Held** and **Refuted** (each writes a decision; with ways **Refuted** asks which, the draft is under **More**) and **Not sure yet** (it stays open, asks a day,
// the why kept as what was found) — each sends `ideas.hypothesis_judge {id, state, why?, way?, draft?, date?}`; answered, the Board is read again and the card leaves. Nothing here counts what waits.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Elem } from "../orkui.js";
import { mapData } from "../shell/store.js";
import { ORKMASTER } from "../frame/state.js";
import { way } from "./ways.js";
import { Judge, Measures } from "./hypothesisjudge.js";

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
const nodeOf = (ref) => (ref ? (mapData.value?.nodes || []).find((n) => n.slug === ref) : null);
const elementOf = (ref) => nodeOf(ref)?.element || "";

/** The lifted card: the hypothesis, its signal, the measures, what was found, the tests, a *Why* line and the answers. */
export function HypothesisLifted({ s, close }) {
  const row = s.row || {}, [why, setWhy] = useState(""), found = row.evidence || [], tests = row.tests || [];
  return html`<div class="hand-way hand-way--hypothesis" data-kind="hypothesis" data-hypothesis=${row.id}>
    <p class="ork-label">${ASK}</p>
    <p class="body hand-lifted__text hand-way__words" data-part="text">${row.text}</p>
    <div class="hand-way__why" data-part="signal"><span class="ork-label">Holds when</span><p class="body">${row.signal}</p></div>
    <${Measures} row=${row} />
    ${found.length > 0 && html`<div class="hand-way__why" data-part="evidence"><span class="ork-label">What was found</span>
      <ul class="hand-way__points" aria-label="What was found">${found.map((e, i) => html`<li key=${i} class="body">${elementOf(e.ref) && html`<${Elem} name=${elementOf(e.ref)} hue=${nodeOf(e.ref)?.hue || ""} /> `}${e.text}</li>`)}</ul></div>`}
    ${tests.length > 0 && html`<div class="hand-way__why" data-part="tests"><span class="ork-label">Tested by</span>
      <ul class="hand-way__points" aria-label="Tested by">${tests.map((t) => html`<li key=${t.slug} class="body">${t.title}</li>`)}</ul></div>`}
    <label class="hand-way__why"><span class="ork-label">Why</span>
      <input class="ork-field" name="why" maxlength=${WHY_CHARS} value=${why} onInput=${(e) => setWhy(e.target.value)} placeholder="One line, if you want one" /></label>
    <${Judge} row=${row} why=${why} close=${close} />
  </div>`;
}

// The face: the flask sign, the proposer's leader as its asker, *Did it hold?* at its foot, no price.
way("hypothesis", { sign: "flask", foot: () => ASK, price: () => null, Lifted: HypothesisLifted });
