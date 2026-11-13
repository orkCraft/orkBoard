// The Orkmaster's hand in the phone's menu (hand/uppiles.js; docs/specs/147-one-card-four-corners.md part F.1, decisions §251.3): *In analysis* is a fan of small backs, 56 x 78. Every goal of the pile is a back, standing, with
// its goal's rune in its middle; each is turned 1.5 degrees from the one before about its foot, 44 px apart while they are few, tighter as they grow within the 144 px (`stepOf`), never a count. The goal being read is lifted out of the fan,
// its rune glowing (only where the page's one motion is: lit.js `movesOn`). A goal held (a pause) or put off to a later hour (a moon) lies at the fan's end with that sign on its back. A back hovered or focused rises and is previewed with its goal's name (preview.js; its words stay in its `aria-label`); a picked one
// rises with its ring (`.is-ringed`); a press picks its goal, as any card does. Layout is column.css; this file draws and counts.
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { movesOn } from "./lit.js";
import { backSpec, withPreview } from "./preview.js";

const BACK_W = 56, FAN_W = 144, MAX_STEP = 44, MIN_STEP = 10, TURN = 1.5;

/** The step between two backs of a fan of `n` (px): 44 while they are few, `88 / (n - 1)` as they grow so the fan stays within 144 px, never under 10. */
const stepOf = (n) => (n < 2 ? 0 : Math.max(MIN_STEP, Math.min(MAX_STEP, Math.floor((FAN_W - BACK_W) / (n - 1)))));

/** The turn of back `i` of `n` (degrees) about its foot: 1.5 apart, the middle one upright. */
const turnOf = (i, n) => Number(((i - (n - 1) / 2) * TURN).toFixed(2));

/** One back of the hand. `reading`: the goal being read (lifted, its rune glowing); `asks`: it waits for the person (the frame in the alert); `mark`: "hold" (a pause) or "later" (a moon) on its back; `words`: what its title and label say. */
function Back({ n, i, count, reading, asks, mark, words, line, dim, hatch, on, onPress }) {
  const el = n.element || "", hue = n.hue || el;
  return html`<button type="button" class=${cls("ork-card col-card col-card--down col-card--fan", { "is-reading": reading, "ork-picked": on, asks, "is-dim": dim })} ...${withPreview(hatch || {}, backSpec(n.title, line, n))} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="analysis" data-down="1" data-mark=${mark || undefined}
    style=${`--i:${i};--r:${turnOf(i, count)}deg;--z:${i + 1}`} aria-label=${words} aria-pressed=${String(on)} onClick=${() => onPress(n, "analysis")}>
    <span class=${cls("ork-card-back small col-fan__back", { "is-ringed": on })} aria-hidden="true"></span>
    <span class="col-fan__seal" aria-hidden="true"><${Elem} name=${el} hue=${hue} dim=${!el} glowing=${reading && movesOn(n.slug)} still=${false} /></span>
    ${mark && html`<span class="col-fan__held" aria-hidden="true"><${Sign} name=${mark === "later" ? "moon" : "pause"} /></span>`}
  </button>`;
}

/** The fan: `items` are the pile's `{n, mark}` in the Orkmaster's order, `reads` whether the first is being read (the pile's `ACTIVE`), `said(n)` a card's words for its title and label, `own(n)` its dim and hatch (piles.js `lit`). */
export function Fan({ items, reads, said, line = () => "", own, waits, picked, onPress }) {
  const count = items.length;
  return html`<div class="col-fan" style=${`--step:${stepOf(count)}px`} data-count=${count} role="group" aria-label="The Orkmaster's hand: press to read them in order">
    ${items.map(({ n, mark }, i) => {
      const o = own(n), m = mark ?? (n.held_for === "hold" ? "hold" : "");
      return html`<${Back} key=${n.slug} n=${n} i=${i} count=${count} reading=${reads && i === 0} asks=${waits(n)} mark=${m} words=${said(n)} line=${line(n)} dim=${o.dim} hatch=${o.hatch} on=${picked === n.slug} onPress=${onPress} />`;
    })}
  </div>`;
}
