// The Orkmaster's hand (docs/specs/168-the-window-played-as-a-card-games-table.md B2, decisions §283.13; before: docs/specs/147-one-card-four-corners.md part B.2, decisions §251.3): *Ideas* is a fan of small backs, 56 x 78, turned like a hand's and held back to the person as a hand is seen across the table. Every goal of the pile is a back, standing, with
// its goal's rune in its middle; each is turned 4 to 6 degrees from the one before about its foot, on an arc (the ends lower), 12 to 16 px apart: 16 while they are few, up to seven within the column's 160 px (14 px at seven), tighter after (`stepOf`), never a count. The goal being read is lifted 12 px out of the fan,
// its rune glowing (only where the page's one motion is: lit.js `movesOn`). A goal held (a pause) or put off to a later hour (a moon) lies at the fan's end with that sign on its back. A back hovered or focused rises and is previewed with its goal's name (preview.js; its words stay in its `aria-label`); a picked one
// rises with its ring (`.is-ringed`); a press picks its goal, as any card does (column.js). `legacy`: the phone's menu keeps the fan it had (1.5 degrees, 44 px apart). Layout is column.css; this file draws and counts.
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { everBack } from "./backcard.js";
import { movesOn } from "./lit.js";
import { backSpec, withPreview } from "./preview.js";

export const BACK_W = 56, FAN_W = 144, MAX_STEP = 16, MIN_STEP = 6, SINK = 0.7;
const OLD = { turn: 1.5, max: 44, min: 10 };

/** The step between two backs of a fan of `n` (px): 16 while they are few, `88 / (n - 1)` as they grow so the fan stays within the column (14 at seven, 12 at eight), never under 6. `legacy`: 44, never under 10. */
export function stepOf(n, legacy = false) {
  const max = legacy ? OLD.max : MAX_STEP, min = legacy ? OLD.min : MIN_STEP;
  return n < 2 ? 0 : Math.max(min, Math.min(max, Math.floor((FAN_W - BACK_W) / (n - 1))));
}

/** The turn between two neighbours (degrees): 6 while there are few, 5 up to seven, 4 after. */
export const turnStep = (n, legacy = false) => (legacy ? OLD.turn : n <= 4 ? 6 : n <= 7 ? 5 : 4);

/** The turn of back `i` of `n` (degrees) about its foot: `turnStep` apart, the middle one upright. */
export const turnOf = (i, n, legacy = false) => Number(((i - (n - 1) / 2) * turnStep(n, legacy)).toFixed(2));

/** How far back `i` of `n` sinks (px): the arc's ends lie lower than its middle. */
export const sinkOf = (i, n, legacy = false) => (legacy ? 0 : Number((((i - (n - 1) / 2) ** 2) * SINK).toFixed(1)));

/** One back of the hand. `reading`: the goal being read (lifted, its rune glowing); `asks`: it waits for the person (the frame in the alert); `mark`: "hold" (a pause) or "later" (a moon) on its back; `words`: what its title and label say. */
function Back({ n, i, count, legacy, reading, asks, mark, words, line, dim, hatch, on, onPress }) {
  const el = n.element || "", hue = n.hue || el;
  everBack.add(n.slug);                                                                                    // seen face down: its turn up and its flight to a lane are played once (backcard.js)
  return html`<button type="button" class=${cls("ork-card col-card col-card--down col-card--fan", { "is-reading": reading, "ork-picked": on, asks, "is-dim": dim })} ...${withPreview(hatch || {}, backSpec(n.title, line, n))} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="analysis" data-down="1" data-mark=${mark || undefined}
    style=${`--i:${i};--r:${turnOf(i, count, legacy)}deg;--z:${i + 1};--sink:${sinkOf(i, count, legacy)}px`} aria-label=${words} aria-pressed=${String(on)} onClick=${() => onPress(n, "analysis")}>
    <span class=${cls("ork-card-back small col-fan__back", { "is-ringed": on })} aria-hidden="true"></span>
    <span class="col-fan__seal" aria-hidden="true"><${Elem} name=${el} hue=${hue} dim=${!el} glowing=${reading && movesOn(n.slug)} still=${false} /></span>
    ${mark && html`<span class="col-fan__held" aria-hidden="true"><${Sign} name=${mark === "later" ? "moon" : "pause"} /></span>`}
  </button>`;
}

/** The fan: `items` are the pile's `{n, mark}` in the Orkmaster's order, `reads` whether the first is being read (the pile's `ACTIVE`), `said(n)` a card's words for its title and label, `own(n)` its dim and hatch (piles.js `lit`). */
export function Fan({ items, reads, said, line = () => "", own, waits, picked, onPress, legacy = false }) {
  const count = items.length;
  return html`<div class="col-fan" style=${`--step:${stepOf(count, legacy)}px`} data-count=${count} role="group" aria-label="The Orkmaster's hand: press to read them in order">
    ${items.map(({ n, mark }, i) => {
      const o = own(n), m = mark ?? (n.held_for === "hold" ? "hold" : "");
      return html`<${Back} key=${n.slug} n=${n} i=${i} count=${count} legacy=${legacy} reading=${reads && i === 0} asks=${waits(n)} mark=${m} words=${said(n)} line=${line(n)} dim=${o.dim} hatch=${o.hatch} on=${picked === n.slug} onPress=${onPress} />`;
    })}
  </div>`;
}
