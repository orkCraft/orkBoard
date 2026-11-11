// The phone's feed in cards (goal 170 stage P; docs/mockups/table-cards/ ?face=phone): the same reader (`ideas.feed`, hand/upfeed.js) drawn
// as the table of cards draws it: no section of what asks (decisions §296.5: the person's move lies in the hand only); a spec that starts by itself (table/post.js `Wait`, §240.2); what is
// at work a shelf of S cards that scrolls sideways; the news M cards, one leader's posts in a row one stack. The heads in rings above and the
// seen line below are upfeed.js's own, given here as nodes. A card pressed opens as an L over the whole screen (card.js `CardL`, which frame.js
// lays when `cardsOn()`; cards.css makes it fill a phone). Drawn only while `cardsOn()` (cards/on.js); layout in phone.css.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Wait, whoOf } from "../table/post.js";
import { CardM } from "./card.js";
import { AT_WORK, WorkCard } from "./lanes.js";
import { nodes } from "./feed.js";
import { ORKMASTER } from "../frame/state.js";

/** One stack: the leader's post as an M, its later posts under it when *More from <leader>* is pressed. */
function One({ s, onPick }) {
  const [spread, setSpread] = useState(false), more = s.more || [];
  return html`<${CardM} p=${s.post} more=${spread ? 0 : more.length} onPick=${onPick} onMore=${() => setSpread(true)} />
    ${spread && more.map((p, i) => html`<${CardM} key=${i} p=${p} onPick=${onPick} />`)}`;
}

/** The feed in cards. `heads`/`seen`/`concerns`: nodes upfeed.js draws; `waits`, `stacks`: the reader's, narrowed already; the shelf is the goals the lanes of the
 *  table of cards show at work (lanes.js `AT_WORK`), those of `party` when the feed is narrowed to one. */
export function PhoneCards({ only, party, heads, waits, stacks, news, seen, empty, onPick, reload, concerns }) {
  const rest = stacks, shelf = only && only !== ORKMASTER && only !== party ? [] : nodes().filter((n) => AT_WORK.has(n.state) && (!party || n.goal === party));
  return html`<div class="up-look up-feed up-ct" data-look="feed" data-only=${only || undefined}>
    ${heads}
    ${only && html`<p class="up-fd__only" role="status">The feed shows only ${whoOf(only).name}</p>`}
    ${concerns}
    ${waits.length > 0 && html`<p class="cards-lab up-ct__lab">Starts by itself</p>${waits.map((w) => html`<${Wait} key=${`${w.kind}:${w.goal}`} w=${w} onPick=${onPick} onDone=${reload} />`)}`}
    ${shelf.length > 0 && html`<p class="cards-lab up-ct__lab">At work</p><div class="up-ct__shelf" role="group" aria-label="Goals at work">${shelf.map((n, i) => html`<${WorkCard} key=${n.slug} n=${n} tilt=${i % 2 ? 2 : -2} />`)}</div>`}
    ${rest.length > 0 && html`<p class="cards-lab up-ct__lab">${news}</p>${rest.map((s, i) => html`<${One} key=${`n${i}${s.post.at}`} s=${s} onPick=${onPick} />`)}`}
    ${seen}
    ${empty && html`<p class="up-none" role="status">Nothing waits for you.</p>`}
  </div>`;
}
