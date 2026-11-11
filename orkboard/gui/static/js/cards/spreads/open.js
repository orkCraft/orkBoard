// The spreads' signal (goal 170, the talk of 11 November 2026; docs/mockups/spreads/): `openSpread({kind, slug, from})` as `openCard`
// (card.js) opens an L. `kind`: "track" (the stages of a goal), "gate" (a goal at the gate of main), "diff" (a post's words before and
// after; `p` the post instead of a `slug`); `from` the element the focus goes back to. Nothing imports here but the signal.
import { signal } from "@preact/signals";

export const spread = signal(null);
export const openSpread = (what) => { spread.value = what; };
export const closeSpread = () => { const was = spread.peek(); spread.value = null; was?.from?.focus?.(); };
