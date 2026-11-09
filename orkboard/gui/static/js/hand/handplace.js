// Where a card in play and the hand's own place lie on the desktop (docs/specs/168 D1, D2; decisions §283.19, §286): the card stands at the table's foot at the left, 144 x 202, over the hand; what the person plays or writes lies in the hand's place, from the
// column's right edge to the sunk hand at the right, as tall as the hand. Everything is measured from the hand's box, so the card, the ways and the field share one left edge. The ways are cut by the hand's rim: `cutOf` is how much of a 202 px card the rim hides.
// The hand's cards, sunk, lie hidden under what is played; the places at the hand's right end stay at their size and in their place (openedcard.css `is-sunk`; decisions §283.5, §284.4), and what is played reaches them.

import { useLayoutEffect, useState } from "preact/hooks";

const RIM = 11;                                                  // the hand's border and the gap under it: a way's top shows this far under the hand's top edge
export const SUNK = 0.25;                                          // the share of the hand's width the sunk hand keeps, when a field or a body lies in its place

/** `{left, right, height, cut}` of the hand `hand` (an element), in px from its left edge: the table's left edge (the first lane's) plus a gutter, the strip the sunk hand keeps at the right, the hand's height and what of a card its rim hides. */
export function handSpan(hand, sunk = SUNK) {
  const h = hand.getBoundingClientRect(), pane = hand.closest(".frame")?.querySelector(".frame-table")?.getBoundingClientRect();
  const left = Math.max(0, Math.round((pane ? pane.left - h.left : 160) + 32));
  const card = parseFloat(getComputedStyle(hand).getPropertyValue("--hc-h")) || 202;
  const end = hand.querySelector(".hand-end")?.getBoundingClientRect(), stop = end && end.width ? end.left - h.left : h.width * (1 - sunk);      // the places stay where they are: what is played reaches them
  return { left, right: Math.round(stop) - 16, height: h.height, cut: Math.max(0, Math.round(card - (h.height - RIM))) };
}

/** Sets `--hc-ways` (the ways' bottom: negative, so the rim cuts them) and `--hc-wleft` (their left) on the hand. */
export function setSpan(hand, span) {
  hand.style.setProperty("--hc-ways", `${-span.cut}px`);
  hand.style.setProperty("--hc-wleft", `${span.left}px`);
}
export function clearSpan(hand) {
  hand?.style.removeProperty("--hc-ways");
  hand?.style.removeProperty("--hc-wleft");
  hand?.style.removeProperty("--hc-sunk-s");
}

/** The card at the table's foot, its ways' row and the strip the sunk hand keeps, placed from the hand's box and kept so while the window changes (`deps`: what makes it place again; `writing`: a field lies in the ways' place, so the sunk hand keeps its fixed strip).
 *  Returns `{left, right, width, height}` (px; left and right from the hand's edges) of where a field lies, or null before the first layout. `box`: a ref to the card (its parent is the hand); `row`: a ref to the ways' row, or null for none. */
export function usePlace(box, row, deps, writing = false) {
  const [at, setAt] = useState(null);
  useLayoutEffect(() => {
    const place = () => {
      const hand = box.current?.parentElement, r = row?.current?.getBoundingClientRect();
      if (!hand) { setAt(null); return; }
      const h = hand.getBoundingClientRect(), span = handSpan(hand), end = r && r.width ? r.right - h.left : h.width;
      setSpan(hand, span);
      hand.style.setProperty("--hc-sunk-s", String(writing || !row ? SUNK : Math.max(0.2, Math.min(0.5, (h.width - end - 16) / h.width))));
      setAt({ left: span.left, right: h.width - span.right, width: span.right - span.left, height: hand.clientHeight });
    };
    place();
    const watch = typeof ResizeObserver === "function" && row?.current ? new ResizeObserver(place) : null;
    if (row?.current) watch?.observe(row.current);
    window.addEventListener("resize", place);
    return () => { watch?.disconnect(); window.removeEventListener("resize", place); };
  }, [...deps, writing]);
  useLayoutEffect(() => () => clearSpan(box.current?.parentElement), []);
  return at;
}
