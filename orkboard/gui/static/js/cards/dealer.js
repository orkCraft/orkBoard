// The Orkmaster's lane of the table of cards (goal 170 D; decision §295: the table's dealer; docs/mockups/table-cards/):
// *Starts by itself* (decisions §240.2, §296.6: a spec that starts by itself: its card, its clock, its acts), *Goals* (the deck it deals from, *Being
// read: <goal>*), *At work* (every goal at work, S cards with their bars). Whole cards, no list, no count.
import { html } from "../html.js";
import { command } from "../link.js";
import { pick } from "../frame/state.js";
import { ACTS } from "../table/post.js";
import { Back, CardS, openCard } from "./card.js";
import { feed, nodeOf, nodes } from "./feed.js";
import { WorkCard } from "./lanes.js";
import { Shape } from "./mat.js";
import { openSpread } from "./spreads/open.js";

/** The Orkmaster's mats (decisions §298.6): the spread each opens, its shape on the mat (a fan: the costs and the deal; two: weighing; four: sorting) and its word. */
const MATS = [["What each card costs", "cost", "dispute"], ["Weigh two at a time", "duel", "diff"], ["Sort the new goals", "sort", "table"], ["The deal", "deal", "dispute"]];
const IN_TALK = new Set(["new", "talk", "spec", "idea"]);

function Waits() {
  const waits = feed.value?.waits || [];
  if (!waits.length) return null;
  return html`<p class="cards-lab">Starts by itself</p>${waits.map((w) => {
    const n = nodeOf(w.goal) || { slug: w.goal, title: w.short || w.goal };
    const card = { slug: n.slug, title: n.short || n.title, element: n.element, hue: n.hue, sign: n.type?.sign || "", leader: w.leader || "orkmaster" };
    const acts = (w.acts || []).map((a) => ({ label: ACTS[a.act] || a.act, main: a.act !== "change_spec", run: () => command(a.command, a.args || {}) }));
    const start = (w.acts || []).find((a) => a.act === "start_now");
    const act = start && { label: ACTS.start_now, run: () => command(start.command, start.args || {}) };
    return html`<div class="cards-wait" key=${w.goal}><${CardS} n=${card} when=${w.at ? `starts ${w.at.slice(11, 16)}` : ""} act=${act}
        onOpen=${(e) => { const from = e.currentTarget; openCard({ kind: "goal", n: { ...card, title: n.title }, line: "starts by itself", from,
          acts: [...acts, ...(IN_TALK.has(n.state) ? [{ label: "The deal", mat: true, run: () => openSpread({ kind: "deal", slug: n.slug, from }) }] : []), ...(w.kind === "main" ? [{ label: "At the gate", mat: true, run: () => openSpread({ kind: "gate", slug: n.slug, from }) }] : [])] }); }} />
      <div class="cards-wait__acts">${acts.filter((a) => a.label !== ACTS.start_now).map((a) => html`<button type="button" class="ork-btn quiet" onClick=${a.run}>${a.label}</button>`)}</div></div>`;
  })}`;
}

function Deck() {
  const deck = nodes().filter((n) => IN_TALK.has(n.state));
  if (!deck.length) return null;
  const top = deck[0];
  return html`<p class="cards-lab">Goals</p>
    <button type="button" class="cards-deck" aria-label=${`The goals the Orkmaster deals; being read: ${top.title}`} onClick=${() => pick(top.slug)}>
      ${deck.slice(0, 5).map((_, i) => html`<${Back} key=${i} tilt=${(i - 2) * 4} x=${i * 30} />`)}</button>
    <p class="cards-read">Being read: <b>${top.short || top.title}</b></p>
    <p class="cards-lab">Its mats</p>
    <div class="cards-deckacts" role="group" aria-label="The Orkmaster's mats">${MATS.map(([label, kind, shape]) =>
      html`<button type="button" class="cards-matrow" data-spread-act=${kind} onClick=${(e) => openSpread({ kind, slug: top.slug, from: e.currentTarget })}><${Shape} shape=${shape} /><span>${label}</span></button>`)}</div>`;
}

export function CardsColumn() {
  const work = nodes().filter((n) => ["ready", "running", "testing", "picking", "failed", "review"].includes(n.state));
  return html`<section class="cards-lane cards-dealer" data-race="orkmaster" aria-label="The Orkmaster's lane">
    <${Waits} /><${Deck} />
    <p class="cards-lab">At work</p>
    ${work.length ? html`<div class="cards-row is-wrap">${work.map((n, i) => html`<${WorkCard} key=${n.slug} n=${n} tilt=${i % 2 ? 2 : -2} />`)}</div>`
      : html`<p class="cards-quiet">Nothing is at work.</p>`}
  </section>`;
}
