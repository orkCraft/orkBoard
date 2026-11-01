// The goal's card flies to its lane (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.5, decisions §198.8): a goal this page saw face down (backcard.js `everBack`) that turned up in the Orkmaster's lane and now has its card in a party's lane — its work is planned —
// flies there **once**, from where it lay to its place, and the lane it left closes behind it. One card flies at a time: a second goal whose turn comes meanwhile waits for the first to land. Not seen — the page hidden, the card's old place out of the window's view, reduced
// motion — no flight: the card is in its lane (§89.0: a motion plays once, never for what changed unseen). The card that flies is a copy over everything; the real one is hidden until the copy lands and takes the pointer only then. orkUI's `.ork-play` draws a
// card's flight from one place to another with `--ork-play-x/-y`; the page sets them on the copy, which is what the Web Animations API gives when the end is not known before the card is drawn.
import { useLayoutEffect, useRef } from "preact/hooks";
import { boxIn, reduced, spring, tokenMs } from "../hand/motion.js";
import { everBack } from "./backcard.js";

const left = new Map();                                   // goal → {rect, copy, at}: the card that has just left the Orkmaster's lane
const FRESH_MS = 2000;                                    // a card that left more than this ago was not seen to leave for a lane
let chain = Promise.resolve();                            // one flight at a time
export const flights = { now: 0, done: 0 };               // how many fly now, how many have landed (what a test reads)

/** The Orkmaster's lane gives its card up (the goal's work is planned, it lies in a party's lane): its box and a copy of it are kept for the lane that takes it. `ref`: the card's wrapper. */
export function useDeparture(slug, ref) {
  useLayoutEffect(() => () => {
    const el = ref.current?.querySelector(".table-card");
    const rect = el && everBack.has(slug) ? boxIn(el) : null;
    if (rect) left.set(slug, { rect: { left: rect.left, top: rect.top, width: rect.width, height: rect.height }, copy: el.cloneNode(true), at: Date.now() });
  }, [slug]);
}

/** A party's lane takes the goal's card: when the card has just left the Orkmaster's lane it flies from there, once, and the real card is hidden until it lands. `ref`: the goal's block. */
export function useArrival(slug, ref) {
  const done = useRef(false);
  useLayoutEffect(() => {
    const was = left.get(slug), root = ref.current;
    if (done.current || !was || !root) return;
    left.delete(slug);
    done.current = true;
    if (Date.now() - was.at > FRESH_MS || reduced() || document.hidden) return;
    root.style.visibility = "hidden";
    chain = chain.then(() => fly(was, root)).catch(() => {}).finally(() => { root.style.visibility = ""; });
  }, [slug]);
}

async function fly(was, root) {
  const to = root.querySelector(".table-card, .table-gstrip")?.getBoundingClientRect() || root.getBoundingClientRect();
  if (!to.width) return;
  const g = was.copy;
  g.classList.add("table-flyer");
  g.setAttribute("aria-hidden", "true");
  g.inert = true;
  g.style.cssText = `position:fixed;left:${was.rect.left}px;top:${was.rect.top}px;width:${was.rect.width}px;height:${was.rect.height}px;margin:0;z-index:90;pointer-events:none;transform-origin:0 0;`;
  document.body.appendChild(g);
  flights.now++;
  try {
    const dx = to.left - was.rect.left, dy = to.top - was.rect.top, sx = to.width / was.rect.width;
    await g.animate([{ transform: "none" }, { transform: `translateY(${-4 * 3}px) rotate(3deg)`, offset: 0.35 }, { transform: `translate(${dx}px, ${dy}px) scale(${sx})` }],
      { duration: tokenMs("--ork-motion-play", 400) * 1.4, easing: spring(), fill: "forwards" }).finished;
  } finally { g.remove(); flights.now--; flights.done++; }
}
