// The deck (docs/specs/98-the-table-and-the-hand.md §4.1, decisions §160.2–§160.4): the goals in line, one pile. Its top is orkUI's back (`.ork-card-back`), sealed with the
// element of the first goal in line (its `__seal` slot) and the moon beside it when that goal waits for the window's reset; its edges hint how many lie under it (five at
// most, never a number). The + card lies off it, face up (orkUI's `.ork-deck`). Pressed, the deck fans out in a row over the hand (deckrow.js). With nothing in line the deck is
// the + card alone; the part comes when it has something to hold (§4.5).
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { PlusCard } from "./pluscard.js";

export const EDGES = 5;

/** What the deck's first goal says: *In line: Short sound when a round starts, waits for the reset*. */
export function deckWords(line) {
  const first = line[0];
  return first ? `In line: ${first.title}${first.reset ? ", waits for the reset" : ""}${line.length > 1 ? ` and ${line.length - 1} more` : ""}` : "In line";
}

/** The pile: edges, the sealed top back (a button), and the + card off it. `line`: data.js `lineOf`; `lit`: the row or the list is open. */
export function Deck({ line, lit = false, open = false, onPress, onPlus }) {
  if (!line.length) return html`<div class="hand-deck is-alone"><${PlusCard} onPress=${onPlus} /></div>`;
  const first = line[0], edges = Math.min(EDGES, line.length - 1);
  return html`<div class="ork-deck hand-deck" data-n=${edges} title="In line">
    ${Array.from({ length: edges }, (_, k) => edges - k).map((i) => html`<i key=${i} class="ork-card-back edge hand-back" style=${`--ork-deck-i:${i}`} aria-hidden="true"></i>`)}
    <button type="button" class=${cls("ork-card-back hand-back hand-deckback", { "is-on": lit })} aria-label=${deckWords(line)} aria-expanded=${open ? "true" : "false"} onClick=${onPress}>
      <span class="ork-card-back__seal"><${Elem} name=${first.element} dim=${!first.element} big=${true} />${first.reset && html`<${Sign} name="moon" label="Waits for the reset" />`}</span>
    </button>
    ${!open && html`<${PlusCard} onPress=${onPlus} />`}
  </div>`;
}
