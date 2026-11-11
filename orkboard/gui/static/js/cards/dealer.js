// The Orkmaster's lane of the table of cards (goal 170 D; decision §295: the table's dealer; docs/mockups/table-cards/):
// *Waits for you* (a spec that starts by itself: its card, its clock, its acts), *Goals* (the deck it deals from, *Being
// read: <goal>*), *At work* (every goal at work, S cards with their bars). Whole cards, no list, no count.
import { html } from "../html.js";
import { command } from "../link.js";
import { pick } from "../frame/state.js";
import { ACTS } from "../table/post.js";
import { Back, CardS, openCard } from "./card.js";
import { feed, nodeOf, nodes, viewsOf } from "./feed.js";
import { WorkCard } from "./lanes.js";
import { openSpread } from "./spreads/open.js";

const IN_TALK = new Set(["new", "talk", "spec", "idea"]);

function Waits() {
  const waits = feed.value?.waits || [];
  if (!waits.length) return null;
  return html`<p class="cards-lab">Waits for you</p>${waits.map((w) => {
    const n = nodeOf(w.goal) || { slug: w.goal, title: w.short || w.goal };
    const card = { slug: n.slug, title: n.short || n.title, element: n.element, hue: n.hue, sign: n.type?.sign || "", leader: w.leader || "orkmaster" };
    const acts = (w.acts || []).map((a) => ({ label: ACTS[a.act] || a.act, main: a.act !== "change_spec", run: () => command(a.command, a.args || {}) }));
    return html`<div class="cards-wait" key=${w.goal}><${CardS} n=${card} asks=${true} line=${w.at ? `starts by itself ${w.at.slice(11, 16)}` : "waits for you"}
        onOpen=${(e) => { const from = e.currentTarget; openCard({ kind: "goal", n: { ...card, title: n.title }, line: "waits for you", from,
          acts: [...acts, ...(viewsOf(n.slug).length > 1 ? [{ label: "Who says what", run: () => openSpread({ kind: "dispute", slug: n.slug, from }) }] : []),
            ...(IN_TALK.has(n.state) ? [{ label: "The deal", run: () => openSpread({ kind: "deal", slug: n.slug, from }) }] : []), ...(w.kind === "main" ? [{ label: "At the gate", run: () => openSpread({ kind: "gate", slug: n.slug, from }) }] : [])] }); }} />
      <div class="cards-wait__acts">${acts.map((a) => html`<button type="button" class="ork-btn quiet" onClick=${a.run}>${a.label}</button>`)}</div></div>`;
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
    <div class="cards-deckacts">${[["What each card costs", "cost"], ["Weigh two at a time", "duel"], ["Sort the new goals", "sort"], ["The deal", "deal"]].map(([label, kind]) =>
      html`<button type="button" class="ork-btn quiet" data-spread-act=${kind} onClick=${(e) => openSpread({ kind, slug: top.slug, from: e.currentTarget })}>${label}</button>`)}</div>`;
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
