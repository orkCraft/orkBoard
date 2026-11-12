// The leaders' lanes of the table of cards (goal 170 E, F; the talk of 11 November 2026; docs/mockups/table-cards/): a lane a
// party, its leader's words as M cards in the feed's order (what the person decides is the hand's only, decisions §296.5), one leader's posts in a row one stack with
// *More from <leader>*; a goal of the party at work an S card with its bar and its tokens. No list, no count.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { pick } from "../frame/state.js";
import { nameOf } from "../table/data.js";
import { raceOf } from "../table/felt.js";
import { CardM, CardS, openCard } from "./card.js";
import { openSpread } from "./spreads/open.js";
import { nodes, postsOf, shareOf } from "./feed.js";
import { FrameSwitch } from "./tables/index.js";      // a leader's framework, a mat over the pane (goal 171 H)
import { frameworkOf } from "./tables/state.js";

export const AT_WORK = new Set(["ready", "running", "testing", "picking", "failed", "review"]);

/** A goal at work of a party, as an S card. */
export function WorkCard({ n, tilt = 0 }) {
  const line = `${n.state === "review" ? "to review" : "at work"}`;
  const card = { slug: n.slug, title: n.short || n.title, element: n.element, hue: n.hue, sign: n.type?.sign || "", leader: n.goal };
  return html`<${CardS} n=${card} when=${line} bar=${shareOf(n) ?? 0} tilt=${tilt}
    onOpen=${(e) => { const from = e.currentTarget; openCard({ kind: "goal", n: { ...card, title: n.title }, line, from, acts: [{ label: "Open its plan", main: true, run: () => pick(n.slug) },
      { label: "Its stages", mat: true, run: () => openSpread({ kind: "track", slug: n.slug, from }) },
      ...(n.state === "review" || n.state === "done" ? [{ label: "At the gate", mat: true, run: () => openSpread({ kind: "gate", slug: n.slug, from }) }] : [])] }); }} />`;
}

function Lane({ g }) {
  const [spread, setSpread] = useState({}), posts = postsOf(g.slug), work = nodes().filter((n) => n.goal === g.slug && AT_WORK.has(n.state));
  const one = (s, i) => [html`<${CardM} key=${i} p=${s.p} more=${spread[i] ? 0 : s.more.length} onPick=${pick} onMore=${() => setSpread({ ...spread, [i]: true })} />`,
    ...(spread[i] ? s.more.map((p, j) => html`<${CardM} key=${`${i}-${j}`} p=${p} onPick=${pick} />`) : [])];
  return html`<section class="cards-lane" data-race=${raceOf(g)} data-party=${g.slug} aria-label=${`${nameOf(g)}'s lane`}>
    ${frameworkOf(g) && html`<header class="cards-lane__head"><b>${nameOf(g)}</b><${FrameSwitch} g=${g} /></header>`}
    ${posts.length > 0 && html`<p class="cards-lab">New since your last look</p>${posts.flatMap((s, i) => one(s, i))}`}
    ${work.length > 0 && html`<p class="cards-lab">At work</p><div class="cards-row is-wrap">${work.map((n, i) => html`<${WorkCard} key=${n.slug} n=${n} tilt=${i % 2 ? 2 : -2} />`)}</div>`}
    ${!posts.length && !work.length && html`<p class="cards-quiet">Quiet: nothing new from ${nameOf(g)}.</p>`}
  </section>`;
}

/** The lanes, one a party, in the tabs' order. */
export function CardsLanes({ parties }) {
  return html`<div class="cards-lanes" style=${`--lanes:${Math.max(parties.length, 1)}`}>${parties.map((g) => html`<${Lane} key=${g.slug} g=${g} />`)}</div>`;
}
