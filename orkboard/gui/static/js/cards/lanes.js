// The leaders' lanes of the table of cards (goal 170 E, F; the talk of 11 November 2026; docs/mockups/table-cards/): a lane a
// party, its leader's words as M cards in the feed's order (what asks first), one leader's posts in a row one stack with
// *More from <leader>*; a goal of the party at work an S card with its bar and its tokens. No list, no count.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { pick } from "../frame/state.js";
import { nameOf } from "../table/data.js";
import { raceOf } from "../table/felt.js";
import { CardM, CardS, openCard } from "./card.js";
import { openSpread } from "./spreads/open.js";
import { nodes, postsOf, shareOf, tokensOf, viewsOf } from "./feed.js";
import { FrameSwitch, TablesView } from "./tables/index.js";      // a leader's framework instead of the lanes (goal 170 T)
import { frameworkOf, laid } from "./tables/state.js";

const AT_WORK = new Set(["ready", "running", "testing", "picking", "failed", "review"]);

/** A goal at work of a party, as an S card. */
export function WorkCard({ n, tilt = 0 }) {
  const t = tokensOf(n.slug), line = `${n.state === "review" ? "to review" : "at work"}`;
  const card = { slug: n.slug, title: n.short || n.title, element: n.element, hue: n.hue, sign: n.type?.sign || "", leader: n.goal };
  return html`<${CardS} n=${card} line=${line} bar=${shareOf(n) ?? 0} tokens=${t} tilt=${tilt}
    onOpen=${(e) => { const from = e.currentTarget; openCard({ kind: "goal", n: { ...card, title: n.title }, line, tokens: t, from, acts: [{ label: "Open its plan", main: true, run: () => pick(n.slug) },
      { label: "Its stages", run: () => openSpread({ kind: "track", slug: n.slug, from }) },
      ...(viewsOf(n.slug).length > 1 ? [{ label: "Who says what", run: () => openSpread({ kind: "dispute", slug: n.slug, from }) }] : []),
      ...(n.state === "review" || n.state === "done" ? [{ label: "At the gate", run: () => openSpread({ kind: "gate", slug: n.slug, from }) }] : [])] }); }} />`;
}

function Lane({ g }) {
  const [spread, setSpread] = useState({}), posts = postsOf(g.slug), work = nodes().filter((n) => n.goal === g.slug && AT_WORK.has(n.state));
  const asks = posts.filter((s) => s.p.asks), news = posts.filter((s) => !s.p.asks);
  const one = (s, i) => [html`<${CardM} key=${i} p=${s.p} more=${spread[i] ? 0 : s.more.length} onPick=${pick} onMore=${() => setSpread({ ...spread, [i]: true })} />`,
    ...(spread[i] ? s.more.map((p, j) => html`<${CardM} key=${`${i}-${j}`} p=${p} onPick=${pick} />`) : [])];
  return html`<section class="cards-lane" data-race=${raceOf(g)} data-party=${g.slug} aria-label=${`${nameOf(g)}'s lane`}>
    ${frameworkOf(g) && html`<header class="cards-lane__head"><b>${nameOf(g)}</b><${FrameSwitch} g=${g} /></header>`}
    ${asks.length > 0 && html`<p class="cards-lab">Asks you</p>${asks.flatMap((s) => one(s, posts.indexOf(s)))}`}
    ${news.length > 0 && html`<p class="cards-lab">New since your last look</p>${news.flatMap((s) => one(s, posts.indexOf(s)))}`}
    ${work.length > 0 && html`<p class="cards-lab">At work</p><div class="cards-row is-wrap">${work.map((n, i) => html`<${WorkCard} key=${n.slug} n=${n} tilt=${i % 2 ? 2 : -2} />`)}</div>`}
    ${!posts.length && !work.length && html`<p class="cards-quiet">Quiet: nothing new from ${nameOf(g)}.</p>`}
  </section>`;
}

/** The lanes, one a party, in the tabs' order. */
export function CardsLanes({ parties }) {
  if (laid.value && parties.some((g) => g.slug === laid.value)) return html`<${TablesView} parties=${parties} />`;
  return html`<div class="cards-lanes" style=${`--lanes:${Math.max(parties.length, 1)}`}>${parties.map((g) => html`<${Lane} key=${g.slug} g=${g} />`)}</div>`;
}
