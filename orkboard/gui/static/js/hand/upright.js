// The hand on a phone, its one screen (docs/specs/103-the-phones-app-a-native-frame.md §1, decisions §174.1, §178, §179, §180; the mockups docs/mockups/phone/): from the top, the Orkmaster's line when the work moved on (table/notice.js),
// the AI tools' row (mana.js `Tools`) with **…** at its right (updeck.js), the top card's context between the two arrows (context.js, upnav.js) with *Spec* under it, and ONE goal's cards: its first on top as the lifted card with its answers on
// it, narrower than the screen, the rest of that goal's cards only the edges of their backs under it, never a count (§180.3). The arrows and a swipe go to the previous or next goal in Needs you's order (entries.js); a card of no goal and each goal
// ready for main (readycard.js, §180.2) are entries of their own. *New goal* is the green deck under the thumb (updeck.js). With nothing in the hand: the line *Nothing waits for you.* and the deck.
// When the card on top is answered the next one comes at once, its context with it (no motion of its own). The goal on the screen is also the picked goal (`picked`), so a thing opened over the pane knows it.
import { useEffect } from "preact/hooks";
import { html } from "../html.js";
import { picked } from "../frame/state.js";
import { Notice } from "../table/notice.js";
import { Context } from "./context.js";
import { goalOfStop, readyOf } from "./data.js";
import { Tools } from "./mana.js";
import { entriesOf, placeOf, step } from "./entries.js";
import { ReadyCard, readyStop } from "./readycard.js";
import { Lifted } from "./stopcard.js";
import { fieldOpen } from "./state.js";
import { Arrow, SpecButton, swipeOf } from "./upnav.js";
import { Deck, DeckField, More } from "./updeck.js";

const EDGES = 5;                                                  // the backs under the top that show (the goal's depth, never a number)
const FAN = [null, [7, 3], [-7, -3], [10, 4], [-10, -4], [9, 2]];       // each back's step aside in px and turn in degrees, by turns right and left (as stacks.js)

/** The backs of the goal's other cards, laid as a fan under the top card. */
function Edges({ n }) {
  return Array.from({ length: n }, (_, k) => n - k).map((i) => html`<i key=${i} class="ork-card-back up-edge" style=${`--dx:${FAN[i][0]};--rot:${FAN[i][1]};--ork-deck-i:${i}`} aria-hidden="true"></i>`);
}

/** The hand on a phone. `root`: the hand's element ref (the keys), `stacks`: data.js `stacksOf`, `plus`: opens the field. */
export function Upright({ root, stacks, plus }) {
  const entries = entriesOf(stacks.flatMap((st) => st.cards), readyOf()?.goals || []), i = placeOf(entries), cur = entries[i] || null, field = fieldOpen.value;
  const stop = cur ? (cur.kind === "ready" ? readyStop(cur) : cur.stops[0]) : null, under = cur ? Math.min(EDGES, Math.max(0, cur.stops.length - 1)) : 0;
  const goal = cur?.kind === "ready" ? cur.ready.slug : stop ? goalOfStop(stop) : "";
  useEffect(() => { picked.value = goal; }, [cur?.key, goal]);
  const swipe = swipeOf(entries);
  return html`<footer ref=${root} class="hand hand-up" aria-label="The hand" data-upright="1" data-empty=${cur ? undefined : "1"}>
    <${Notice} />
    <div class="up-top"><${Tools} /><${More} /></div>
    ${cur ? html`<div class="up-body"><div class="up-navrow">
        <${Arrow} dir=${-1} to=${entries[i - 1]} onPress=${() => step(entries, -1)} />
        <div class="up-navmid"><${Context} s=${stop} /><${SpecButton} idea=${goal} /></div>
        <${Arrow} dir=${1} to=${entries[i + 1]} onPress=${() => step(entries, 1)} />
      </div>
      <div class="up-stack" data-n=${under} data-entry=${cur.key} ...${swipe}><${Edges} n=${under} />
        ${cur.kind === "ready" ? html`<${ReadyCard} key=${cur.key} e=${cur} />` : html`<${Lifted} key=${stop.key} s=${stop} inline=${true} />`}</div></div>`
      : html`<div class="up-mid"><p class="up-none" role="status">Nothing waits for you.</p></div>`}
    ${field ? html`<${DeckField} />` : html`<${Deck} onPress=${plus} />`}
  </footer>`;
}
