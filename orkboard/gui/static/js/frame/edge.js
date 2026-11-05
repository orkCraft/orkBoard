// The table's edge (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md D, decisions §254.3–§254.4; mockup docs/mockups/table-edge/): at the wide width (760 px and up) the window has a third column, 212 px wide, at the right of the table and
// the hand and as tall as both (frame.css `--edge-w`): a strip of objects, top to bottom, with no list and no count: **the ring** (table/portal.js: the portal's ring, with Live's imp at twelve and Release's lich at six; always drawn from Start while the project has a gate),
// **the discard** (table/discard.js), **the die** (hand/playdie.js) and **the potions** (hand/mana.js, with the empty slot). They stood in the table's end (`.table-end`) and the hand's (`.hand-end`); under 760 px, where this is not drawn, they stand there still.
// A form over the whole table (settings, a party) leaves the ring and the discard out, as it left the end; the die and the potions are the hand's and stay. Layout only: frame/edge.css.
import { html } from "../html.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { lifted, over, tab } from "./state.js";
import { uprightNow } from "./upright.js";
import { noGate, wide } from "../table/data.js";
import { laidNow } from "../table/laying.js";
import { isForm } from "../table/over.js";
import { Portal } from "../table/portal.js";
import { EdgeDiscard } from "../table/discard.js";
import { PlayDie } from "../hand/playdie.js";
import { Mana } from "../hand/mana.js";
import { stopByKey, stopsOfProject } from "../hand/data.js";
import { stopKeyOf } from "../hand/state.js";

/** Whether the edge is drawn: the wide width, and not a phone (frame/upright.js). Else the end and the hand's end keep their objects. */
export const edgeOn = () => wide.value && !uprightNow.value;

/** The stop now lifted in the hand, whose cost the potions show (hand/mana.js `Mana`); null when none is. */
function liftedStop() {
  const key = stopKeyOf(lifted.value);
  return key ? stopByKey(stopsOfProject(mapData.value, board.value?.needs_you || [], tab.value), key) : null;
}

export function Edge() {
  const laid = laidNow(), form = isForm(over.value), s = liftedStop();
  return html`<aside class="frame-edge" aria-label="The table's edge">
    ${laid && !form && !noGate() && html`<${Portal} />`}
    ${laid && !form && html`<${EdgeDiscard} />`}
    ${laid && html`<${PlayDie} />`}
    <${Mana} lifted=${s} />
  </aside>`;
}
