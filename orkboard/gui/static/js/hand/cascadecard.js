// A leader's proposal to change a decision, run down the other leaders' parts, is a card (docs/specs/131-a-leaders-slices-and-the-cascade.md §C; decisions §233.8–§233.9, §237.6): the row `cascade` (realm/cascades.py `rows`,
// laid by realm/board_rows.py: `{kind: "cascade", id, party (the proposer's), title, line, proposal: {party, says, why, before}, chain: [{party, name, before, after}], forks: [{party, name, slice, says, now, why}], stopped,
// cost, sections: [{idea, party}], usd_low, usd_high, blocks: false}`) is a row of no goal's: `cascadeStops` makes its stop, under its proposer's party's lane (hand/data.js `stopsOfProject` calls it, as it calls
// `hypothesisStops`). Its face is the hand's card (stopcard.js): the page sign, the proposer's head as its asker, *Proposes* as its label, the new decision's title as its name, the one line (*Tech and Art agree*) at its foot,
// the cost of what follows as its gem. Lifted: the proposal and its why; with no fork the one line and **More**, which opens the chain (the heads in order, each part before and after); with a fork the fork first (what the leader
// holds now, what it would say, its why) and the choice to keep it, to take its words or to write the person's own; *Stopped after <n> steps* when it stopped; the cost of what follows and the goals whose sections are written
// again; **Confirm and start** (`ideas.cascade_confirm {id, fork_answers?}`, held here while a fork has no answer) and **Put it back** (`ideas.cascade_back {id}`: nothing changes). No list of the parts is drawn anywhere (§237.5).
// The phone's hand is this card too: the installed app is the desktop's page (pwa/frame.js), its upright hand (upright.js) draws the same stops.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { toast } from "../link.js";
import { act, mapData } from "../shell/store.js";
import { ORKMASTER } from "../frame/state.js";
import { partiesAll } from "../table/data.js";
import { way } from "./ways.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as changecard.js links its own
  const href = new URL("./cascadecard.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const PROPOSES = "Proposes";
const WORDS_CHARS = 300;                                                // realm/slices.py SAYS_CHARS: the person's own words for a part

/** The hand's stops of the `cascade` rows among `rows` (the Needs you rows), one for each, after the others. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `goal(slug)`, `open`). */
export function cascadeStops(rows, ctx) {
  return rows.filter((r) => r.kind === "cascade").map((row) => {
    const g = ctx.goal(row.party), party = ctx.party(row.party) || { slug: "", name: "Orkmaster", head: null, lead: "Orkmaster" };
    return { key: `cascade/${row.id}`, kind: "cascade", ref: row, row: { ...row, goal: row.party, idea: undefined }, node: null, task: null, label: PROPOSES, gem: "", tone: "", gemTip: "",
      head: party.head, small: true, whoTip: "", title: row.title, full: row.title, text: row.line, why: "", g: g || null, party, other: ctx.open !== ORKMASTER && ctx.open !== party.slug };
  });
}

const headOf = (slug) => partiesAll().find((g) => g.slug === slug)?.leader?.head || { race: "peon", tier: "laborer" };
const titleOf = (idea) => { const n = (mapData.value?.nodes || []).find((x) => x.slug === idea); return n ? n.short || n.title : idea; };

/** The goals whose sections are written again, each once, by their titles. */
export const againWords = (sections) => [...new Set((sections || []).map((x) => x.idea))].map(titleOf);

/** One leader's disagreement: what it holds now, what it would say, why; and the person's answer (`keep`, `change`, or their own words). */
function Fork({ f, answer, set }) {
  const own = answer && answer !== "keep" && answer !== "change" ? answer : "", head = headOf(f.party);
  return html`<section class="hand-cascade__fork" data-fork=${f.slice} aria-label=${`${f.name} disagrees`}>
    <p class="body hand-way__words"><${Head} race=${head.race} tier=${head.tier} /> <b>${f.name}</b> disagrees: ${f.why}</p>
    ${f.now && html`<p class="cap hand-cascade__now" data-part="now">Now: ${f.now}</p>`}
    ${f.says && html`<p class="cap" data-part="would">It would say: ${f.says}</p>`}
    <div class="hand-answers" role="group" aria-label=${`${f.name}: your answer`}>
      <button type="button" class="ork-btn" data-fork-answer="keep" aria-pressed=${String(answer === "keep")} title="Its part stays as it is" onClick=${() => set("keep")}>Keep it</button>
      ${f.says && html`<button type="button" class="ork-btn" data-fork-answer="change" aria-pressed=${String(answer === "change")} title="Its part takes its words" onClick=${() => set("change")}>Take its words</button>`}
    </div>
    <input class="ork-field" type="text" maxlength=${WORDS_CHARS} aria-label=${`${f.name}: your own words`} placeholder="Or your own words" value=${own} onInput=${(e) => set(e.currentTarget.value.trim() ? e.currentTarget.value : "")} />
  </section>`;
}

/** The chain: the heads in order, each part before and after. */
function Chain({ chain }) {
  return html`<ol class="hand-cascade__chain" aria-label="What changes, in order" data-part="chain">${chain.map((c, i) => { const head = headOf(c.party); return html`<li key=${i} class="hand-cascade__step" data-party=${c.party}>
    <span class="hand-cascade__who"><${Head} race=${head.race} tier=${head.tier} /><b>${c.name}</b></span>
    ${c.before && html`<span class="cap hand-cascade__before">${c.before}</span>`}<span class="body hand-way__words hand-cascade__after">${c.after}</span></li>`; })}</ol>`;
}

/** The lifted card. */
export function CascadeLifted({ s, close }) {
  const row = s.row || {}, forks = row.forks || [], [answers, setAnswers] = useState({}), [open, setOpen] = useState(false), [busy, setBusy] = useState(false);
  const again = againWords(row.sections), waiting = forks.some((f) => !answers[f.slice]), who = s.party?.name || "The leader";
  const confirm = async () => {
    if (busy || waiting) return;
    setBusy(true);
    try {
      const got = await act("ideas.cascade_confirm", { id: row.id, via: "hand", ...(forks.length ? { fork_answers: answers } : {}) });
      if (got) {
        const n = (got.sections || []).length;
        toast(`Kept: decision ${got.number} is written${n ? `; ${n} ${n === 1 ? "section is" : "sections are"} written again` : ""}.`);
        close?.();
      }
    } finally { setBusy(false); }
  };
  const back = async () => {
    if (busy) return;
    setBusy(true);
    try { if (await act("ideas.cascade_back", { id: row.id, via: "hand" })) { toast("Put back: nothing changes."); close?.(); } } finally { setBusy(false); }
  };
  return html`<div class="hand-way hand-cascade" data-kind="cascade" data-cascade=${row.id}>
    <p class="ork-label">${PROPOSES}</p>
    <p class="body hand-lifted__text hand-way__words" data-part="title">${row.title}</p>
    <p class="cap hand-way__words" data-part="why">${who} proposes it because ${row.proposal?.why}</p>
    ${forks.length === 0 && html`<p class="body hand-way__words" data-part="line">${row.line}</p>`}
    ${forks.map((f) => html`<${Fork} key=${f.slice} f=${f} answer=${answers[f.slice] || ""} set=${(a) => setAnswers((o) => ({ ...o, [f.slice]: a }))} />`)}
    ${row.stopped && html`<p class="cap hand-way__words" data-part="stopped">${row.stopped}</p>`}
    ${(row.chain || []).length > 0 && html`<button type="button" class=${cls("ork-btn quiet hand-cascade__more", { "is-open": open })} aria-expanded=${String(open)} data-act="more" onClick=${() => setOpen(!open)}>More</button>`}
    ${open && html`<${Chain} chain=${row.chain || []} />`}
    ${again.length > 0 && html`<p class="cap hand-way__words" data-part="again">Written again: ${again.join(" · ")}</p>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      <button type="button" class="ork-btn primary" disabled=${busy || waiting} data-act="confirm" title=${waiting ? "Answer the fork first" : "The decision is written, and what rests on it is written again"} onClick=${confirm}>Confirm and start</button>
      <button type="button" class="ork-btn quiet" disabled=${busy} data-act="back" title="Nothing changes" onClick=${back}>Put it back</button>
    </div>
  </div>`;
}

// The face: the page sign, the proposer's leader as its asker, the one line at its foot, the cost of what follows as its gem. It has its own *Put it back* (the host's), so the card adds none (stopcard.js `puts`).
way("cascade", {
  sign: "page",
  puts: true,
  foot: (s) => s.row?.line || "",
  price: (s) => { const low = Number(s.row?.usd_low), high = Number(s.row?.usd_high); return (low || high) ? { low, high, saves: false } : null; },
  Lifted: CascadeLifted,
});
