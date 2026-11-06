// The Orkmaster's hand (docs/specs/147-one-card-four-corners.md part B.2, decisions §251.3; mockup docs/mockups/card-ratio/): *In analysis* is a near-straight fan of small backs, 56 x 78, held back to the person as a hand is seen across the table. Every goal of the pile is a back, standing, with
// orkUI's small seal and its goal's rune in its middle; they are spread while they are few (usually one to three, 44 px apart) and tighter as they grow (`stepOf`), turned 1.5 degrees apart about their foot, the later over the earlier, never wider than 144 px and never a count. The goal being read is
// lifted 12 px out of the fan, its rune glowing (only where the page's one motion is: lit.js `movesOn`). A back hovered or focused rises and says its goal's name; a press lifts the pile's list in the Orkmaster's order (column.js). Layout is column.css; this file draws and counts.
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { everBack } from "./backcard.js";
import { movesOn } from "./lit.js";

export const BACK_W = 56, FAN_W = 144, TURN = 1.5, MAX_STEP = 44, MIN_STEP = 10;

/** The step between two backs of a fan of `n` (px): 44 while they are few, `88 / (n - 1)` as they grow so the fan stays within 144 px, never under 10. */
export function stepOf(n) {
  return n < 2 ? 0 : Math.max(MIN_STEP, Math.min(MAX_STEP, Math.floor((FAN_W - BACK_W) / (n - 1))));
}

/** The turn of back `i` of `n` (degrees) about its foot: 1.5 degrees apart, the middle one upright. */
export const turnOf = (i, n) => Number(((i - (n - 1) / 2) * TURN).toFixed(2));

/** One back of the hand. `reading`: the goal being read (lifted, its rune glowing); `asks`: it waits for the person (the frame in the alert); `words`: what its title and label say. */
function Back({ n, i, count, reading, asks, held, words, dim, hatch, open, onPress }) {
  const el = n.element || "", hue = n.hue || el;
  everBack.add(n.slug);                                                                                    // seen face down: its turn up and its flight to a lane are played once (backcard.js)
  return html`<button type="button" class=${cls("ork-card col-card col-card--down col-card--fan", { "is-reading": reading, asks, "is-dim": dim })} ...${hatch} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="analysis" data-down="1"
    style=${`--i:${i};--r:${turnOf(i, count)}deg;--z:${i + 1}`} title=${words} aria-label=${words} aria-haspopup="dialog" aria-expanded=${String(open)} onClick=${() => onPress(n, "analysis")}>
    <span class="ork-card-back small col-fan__back" aria-hidden="true"></span>
    <span class="col-fan__seal" aria-hidden="true"><${Elem} name=${el} hue=${hue} dim=${!el} glowing=${reading && movesOn(n.slug)} still=${false} /></span>
    ${held && html`<span class="col-fan__held" aria-hidden="true"><${Sign} name="pause" /></span>`}
  </button>`;
}

/** The fan: `items` are the pile's `{n}` in the Orkmaster's order, `reads` whether the first is being read (the pile's `ACTIVE`), `said(n)` a card's words for its title and label, `own(n)` its dim and hatch (piles.js `lit`). */
export function Fan({ items, reads, said, own, waits, open, onPress }) {
  const count = items.length;
  return html`<div class="col-fan" style=${`--step:${stepOf(count)}px`} data-count=${count} role="group" aria-label="The Orkmaster's hand: press to read them in order">
    ${items.map(({ n }, i) => {
      const o = own(n);
      return html`<${Back} key=${n.slug} n=${n} i=${i} count=${count} reading=${reads && i === 0} asks=${waits(n)} held=${n.held_for === "hold"} words=${said(n)} dim=${o.dim} hatch=${o.hatch} open=${open} onPress=${onPress} />`;
    })}
  </div>`;
}
