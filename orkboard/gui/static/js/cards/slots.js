// A closed mat's slots (goal 171 stage J; decisions §299.5, §300.1; docs/mockups/mats/?v=closed): its layout's slots, thin dashed outlines in orkUI's frame, faint behind the mat's words,
// `aria-hidden` (the mat's line still says what it is), each layout its own. Where its words leave under a third of its height the slots are a simpler form of three at its right.
// A word has none. Layout only: the colours and the frame are orkUI's (cards.css).
import { useLayoutEffect } from "preact/hooks";
import { html } from "../html.js";

const sl = (x, y, w, h, c = "") => [x, y, w, h, c];       // percent of the slots' area; `ln` a line

/** The layouts of the closed mats: what a mat of a kind lays behind its words. */
export const LAYOUTS = {
  two: [sl(12, 0, 34, 100), sl(54, 0, 34, 100)],                                                      // What changed; compare's pair: two cards
  layers: [sl(38, 0, 24, 40), sl(18, 52, 20, 48), sl(40, 52, 20, 48), sl(62, 52, 20, 48), sl(20, 46, 60, 0, "ln")],   // Architecture: a layer and rows
  columns: [sl(0, 0, 30, 44), sl(34, 0, 30, 44), sl(68, 0, 30, 44), sl(0, 54, 22, 44), sl(25, 54, 22, 44), sl(50, 54, 22, 44), sl(75, 54, 23, 44)],   // Jobs to be done: columns
  battle: [sl(30, 0, 18, 40), sl(52, 0, 18, 40), sl(10, 50, 80, 0, "ln"), sl(41, 60, 18, 40)],     // one against two
  stages: [sl(0, 20, 18, 60), sl(27, 20, 18, 60), sl(54, 20, 18, 60), sl(81, 20, 18, 60)],            // its stages: a row
  small: [sl(0, 0, 30, 100), sl(36, 0, 30, 100), sl(72, 0, 28, 100)],                                 // where little is left: three
};

/** Which layout a mat of a post lays: `diff` two cards, a framework by its own (Architecture a layer and rows, Jobs to be done columns). */
export const layoutOf = (kind, framework = "") => (kind === "diff" ? "two" : framework === "jtbd" ? "columns" : framework === "architecture" ? "layers" : LAYOUTS[kind] ? kind : "two");

const cell = ([x, y, w, h, c], i) => html`<i key=${i} class=${c} style=${`left:${x}%;top:${y}%;width:${w}%;height:${h}%`}></i>`;

/** The slots behind a mat's words: its layout's, and the three that take their place where little is left (shown by the M's `data-fit`). */
export const Slots = ({ layout }) => html`<span class="cards-slots" aria-hidden="true" data-layout=${layout}>
  <span class="cards-slots__full">${(LAYOUTS[layout] || LAYOUTS.two).map(cell)}</span><span class="cards-slots__small">${LAYOUTS.small.map(cell)}</span></span>`;

/** Sets the M's `data-fit` to `small` where its words leave under a third of its height, else `full`: measured at the full form, again when its size changes. */
export function useSlotsFit(ref, on) {
  useLayoutEffect(() => {
    const el = ref.current;
    if (!on || !el) return undefined;
    const fit = () => {
      el.dataset.fit = "full";
      const body = el.querySelector(".cards-m__body"), foot = el.querySelector(".cards-mat");
      if (!body || !foot) return;
      el.dataset.fit = foot.offsetTop - (body.offsetTop + body.offsetHeight) < el.clientHeight / 3 ? "small" : "full";
    };
    fit();
    if (typeof ResizeObserver !== "function") return undefined;
    let width = el.clientWidth;
    const ro = new ResizeObserver(() => { if (el.clientWidth !== width) { width = el.clientWidth; fit(); } });
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref, on]);
}
