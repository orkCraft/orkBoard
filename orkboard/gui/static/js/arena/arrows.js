// The System's arrows (docs/specs/89-the-tech-lens-system.md §6.4, systemmap.js): a part's use is drawn as a dashed ink line in square steps with a head, 2 px, over its table, drawn from its start in four steps when it comes
// (arena.css `arena-draw`; none when motion is reduced). Only with a fine pointer (`(hover: hover)`). `across` routes a line between two cards anywhere on its table, and a line may carry its goal's element (`el`: a use new
// since the last look is drawn in its goal's colour, systemmap.css).
import { html, cls } from "../html.js";

const HEAD = 9;                                       // the arrow head's length in px

export const fine = () => typeof matchMedia === "function" && matchMedia("(hover: hover)").matches;

const HALF = 4;                                       // half the width of an arrow head

/** A part's use on the System's table (spec 89 §6.4), in square steps between two cards anywhere on it: out of the side of `a` that faces `b` (the right one for a card of its own column) into the
 *  gutter beside it, along the gutter to the gap over b's row, across that gap to b's centre, down into b's top. `gx`, `gy`: half the gutter between two columns and half the gap between two rows,
 *  so the line runs between the cards, never through them.  */
export function across(key, a, b, gx, gy) {
  const right = b.x + b.w / 2 >= a.x + a.w / 2 - 1;
  const x1 = right ? a.x + a.w : a.x, y1 = a.y + a.h / 2, side = right ? x1 + gx : x1 - gx;
  const x2 = b.x + b.w / 2, y2 = b.y, lane = y2 - gy, to = y2 - (HEAD - 1), at = (x, y) => `${x.toFixed(1)},${y.toFixed(1)}`;
  return { key, x1, y1, points: [at(x1, y1), at(side, y1), at(side, lane), at(x2, lane), at(x2, to)].join(" "), tip: { x: x2, y: y2 },
    head: `${at(x2, y2)} ${at(x2 - HALF, y2 - HEAD)} ${at(x2 + HALF, y2 - HEAD)}` };
}

/** The svg layer that draws `lines` (from `across`, the System's uses) over its positioned host. */
export function ArrowLines({ lines }) {
  return html`<svg class="arena-arrows" aria-hidden="true">${lines.map((l) => html`<g key=${l.key} class=${cls("arena-arrow", { "is-leaving": !!l.leaving })} data-edge=${l.key} data-kind=${l.kind || undefined} data-elem=${l.el || undefined}>
    ${l.points ? html`<polyline points=${l.points} fill="none" style=${`transform-origin: ${l.x1.toFixed(1)}px ${l.y1.toFixed(1)}px`} />`
      : html`<line x1=${l.x1} y1=${l.y1} x2=${l.x2} y2=${l.y2} style=${`transform-origin: ${l.x1.toFixed(1)}px ${l.y1.toFixed(1)}px`} />`}<polygon points=${l.head} /></g>`)}</svg>`;
}
