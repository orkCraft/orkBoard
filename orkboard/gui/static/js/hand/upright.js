// The hand on a phone, its one screen (docs/specs/117-the-phone-a-menu-of-the-leaders.md §3, docs/specs/103-the-phones-app-a-native-frame.md §1, decisions §174.1, §178, §179, §180, §195; the mockups docs/mockups/phone/): from the top, the Orkmaster's line when
// the work moved on (table/notice.js), the top row (uptop.js: the crown, the potions as bottles, the die, the discard), the middle — it scrolls — and the hand's row at the foot (uprow.js). The middle shows the picked entry: the card's context
// (context.js), the card with its answers on it (stopcard.js `Lifted` with `inline`, or readycard.js `ReadyCard` for a goal ready for main), full width less the gutters, and *Spec* under it (upnav.js) until the goal's way is the middle's (spec 117 D).
// The row is one card an entry (entries.js); a press picks one, and answering the last card of an entry picks the next one at once (no motion of its own). The goal of the entry on the screen is also the picked goal (`picked`), so a thing
// opened over the pane knows it. With nothing in the hand: the line *Nothing waits for you.*; the + card at the row's right end is the way on.
import { useEffect } from "preact/hooks";
import { html } from "../html.js";
import { picked } from "../frame/state.js";
import { Notice } from "../table/notice.js";
import { Context } from "./context.js";
import { goalOfStop, readyOf } from "./data.js";
import { entriesOf, placeOf } from "./entries.js";
import { ReadyCard, readyStop } from "./readycard.js";
import { Lifted } from "./stopcard.js";
import { fieldOpen } from "./state.js";
import { SpecButton } from "./upnav.js";
import { DeckField } from "./updeck.js";
import { Row } from "./uprow.js";
import { Top } from "./uptop.js";
import { Sheet } from "./upmenu.js";

/** The hand on a phone. `root`: the hand's element ref (the keys), `stacks`: data.js `stacksOf`, `plus`: opens the field. */
export function Upright({ root, stacks, plus }) {
  const entries = entriesOf(stacks.flatMap((st) => st.cards), readyOf()?.goals || []), i = placeOf(entries), cur = entries[i] || null, field = fieldOpen.value;
  const stop = cur ? (cur.kind === "ready" ? readyStop(cur) : cur.stops[0]) : null;
  const goal = cur?.kind === "ready" ? cur.ready.slug : stop ? goalOfStop(stop) : "";
  useEffect(() => { picked.value = goal; }, [cur?.key, goal]);
  return html`<footer ref=${root} class="hand hand-up" aria-label="The hand" data-upright="1" data-empty=${cur ? undefined : "1"}>
    <${Notice} />
    <${Top} />
    ${cur ? html`<div class="up-look" data-entry=${cur.key}><${Context} s=${stop} />
        ${cur.kind === "ready" ? html`<${ReadyCard} key=${cur.key} e=${cur} />` : html`<${Lifted} key=${stop.key} s=${stop} inline=${true} />`}
        <${SpecButton} idea=${goal} /></div>`
      : html`<div class="up-mid"><p class="up-none" role="status">Nothing waits for you.</p></div>`}
    <${Row} entries=${entries} cur=${cur} plus=${plus} />
    <${Sheet} entries=${entries} />
    ${field && html`<${DeckField} />`}
  </footer>`;
}
