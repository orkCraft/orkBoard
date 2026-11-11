// The discard in the table of cards' look (goal 170, the talk of 11 November 2026; docs/mockups/table-cards/ the right column), drawn only while `cardsOn()` (cards/on.js; table/lane.js switches). Its goals are S cards (card.js):
// under the plate *main* (done in dev · waits for main) the goal ready for main with the portal's ring and its act **To main** beside it, the other goals ready, then the goals done and not yet seen; under the plate *dev* (done · waits for dev) the goals
// waiting on their branch, two to a row. The act, the pick, the portal and the plates are the lane's own (portal.js `toMain`, plates.js); only the look of the goals changes. No count anywhere. Layout only: discard.css.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Icon } from "../orkui.js";
import { lower, playCard, playing } from "../frame/state.js";
import { devName } from "../hand/devcard.js";
import { redOf } from "../table/checks.js";
import { mainLine } from "../table/discard.js";
import { PLATE_WORDS, Plate } from "../table/plates.js";
import { alongOf, chosenSlug, dissolving, going, toMain } from "../table/portal.js";
import { RingAround } from "../table/ring.js";
import { CardS } from "./card.js";

/** One goal of the discard as an S card; `g` as table/lane.js has it (`slug`, `title`, `party` or `goal`, `element`, `hue`, `type`). */
function GoalCard({ g, line, picked = false, ready = false, along = false, moon = false, onOpen }) {
  const card = { slug: g.slug, title: g.title || g.short || g.slug, element: g.element, hue: g.hue, sign: g.type?.sign || "check", leader: g.party || g.goal };
  return html`<${CardS} n=${card} line=${line} ready=${ready} onOpen=${onOpen} data-portal-card=${ready ? g.slug : undefined} data-picked=${picked ? "true" : undefined}
    data-along=${along ? "1" : undefined} data-melting=${dissolving.value.includes(g.slug) ? "1" : undefined} data-going=${going.value === g.slug ? "1" : undefined} data-moon=${moon ? "1" : undefined} />`;
}

/** The goal ready for main: its card ringed by the portal, *To main* beside it (the very act the post had). */
function ReadyTop({ g, main, on, press }) {
  const [busy, setBusy] = useState(false), red = redOf(g.slug, g);
  const go = async () => { setBusy(true); try { if (on !== g.slug) press(g.slug); await toMain(g.slug); } finally { setBusy(false); } };
  return html`<div class="cards-row cards-ready" data-portal="1">
    <${RingAround} slug=${g.slug}><${GoalCard} g=${g} ready=${true} picked=${on === g.slug} line=${red ? "checks failed" : "ready"} onOpen=${() => press(g.slug)} /><//>
    <div class="cards-ready__acts"><button type="button" class="ork-btn primary" data-act="to_main" data-to-main disabled=${busy}
      title=${`Sends the goal through the portal to ${main}: its checks run first, nothing reaches ${main} without you`} onClick=${go}><${Icon} name="git-merge" /><span>To ${main}</span></button></div>
  </div>`;
}

/** The upper pile's goals (ready for main, then done and not yet seen) and the lower pile (waiting for dev); `p` is what table/lane.js has worked out. */
export function CardsPiles({ p }) {
  const { upper, goals, ready, own, done, lowerGoals, now, press, moons } = p, held = chosenSlug() || now, dev = devName(), playingNow = playing.value?.dev === "card" ? playing.value.slug : "";
  const more = goals.slice(1);
  return html`<div class="cards-pile" data-cards="discard">
    ${upper && html`<${Plate} which="main" /><p class="discard-pile__words">${PLATE_WORDS.main}</p>`}
    ${goals.length > 0 && html`<${ReadyTop} g=${goals[0]} main=${ready.main} on=${now} press=${press} />`}
    ${more.length + done.length > 0 && html`<div class="cards-row is-wrap">
      ${more.map((g) => html`<${GoalCard} key=${g.slug} g=${g} line=${redOf(g.slug, g) ? "checks failed" : "ready"} picked=${now === g.slug} along=${!!held && held !== g.slug && alongOf(held).has(g.slug)} onOpen=${() => press(g.slug)} />`)}
      ${done.map((g) => html`<${GoalCard} key=${g.slug} g=${g} line=${mainLine(g) || (moons.has(g.slug) ? "done in the night" : "done")} moon=${moons.has(g.slug)} picked=${now === g.slug} onOpen=${() => press(g.slug)} />`)}</div>`}
    ${own}
    ${lowerGoals.length > 0 && html`<section class="discard-pile cards-lower" data-pile="lower" aria-label=${`Waiting for ${dev}`}><${Plate} which="dev" /><p class="discard-pile__words">${PLATE_WORDS.dev}</p>
      <div class="cards-row is-wrap">${lowerGoals.map((g) => html`<${GoalCard} key=${g.slug} g=${g} line="done" picked=${playingNow === g.slug} onOpen=${() => { if (playingNow === g.slug) lower(); else playCard({ dev: "card", slug: g.slug }); }} />`)}</div></section>`}
  </div>`;
}
