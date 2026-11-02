// The moves of the Orkmaster's column (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part B.4, decisions §206.3): a goal agreed turns upright where it lay and goes to To review; its wait over it goes to At work and its tasks fly to their leaders' lanes
// (the card's copy flies from the column to the goal's strip, once). A card that changes pile is moved with the Web Animations API from where it was (the page keeps no state of its own for it: each layout is measured, the next one compared); a sideways card turns
// a quarter on its way up. Nothing is played for a page that is hidden, for a card first seen, or under reduced motion (§89.0: a motion plays once, never for what changed unseen); a goal done goes to the discard as today (discard.js).
import { useLayoutEffect, useRef } from "preact/hooks";
import { boxIn, ease, reduced, spring, tokenMs } from "../hand/motion.js";
import { everBack } from "./backcard.js";
import { cascadeOf } from "./data.js";

const center = (r) => ({ x: r.left + r.width / 2, y: r.top + r.height / 2 });
const seen = () => !reduced() && typeof document !== "undefined" && !document.hidden;
const box = (el) => { const r = el.getBoundingClientRect(); return { left: r.left, top: r.top, width: r.width, height: r.height }; };

/** One card moved from where it was (`from`: its box and its pile) to where it lies now: translated, and a face-down card of In analysis turned a quarter up on the way. */
function move(el, from, now) {
  const a = center(from.rect), b = center(now), dx = a.x - b.x, dy = a.y - b.y, up = from.pile === "analysis" && el.dataset.pile === "review";
  if (!dx && !dy) return;
  const at = `translate(${dx}px, ${dy}px)`;
  const frames = up ? [{ transform: `${at} rotate(90deg)` }, { transform: `${at} rotate(0deg)`, offset: 0.4 }, { transform: "none" }] : [{ transform: at }, { transform: "none" }];
  el.animate(frames, { duration: tokenMs("--ork-motion-play", 400) * (up ? 1.8 : 1.2), easing: ease() });
}

/** A goal's tasks are dealt to its leaders' lanes: a copy of its card in the column flies to its strip in the lane, once, over everything. */
function fly(card, to) {
  const r = boxIn(card);
  if (!r) return Promise.resolve();
  const g = card.cloneNode(true);
  g.classList.add("table-flyer");
  g.setAttribute("aria-hidden", "true");
  g.inert = true;
  g.style.cssText = `position:fixed;left:${r.left}px;top:${r.top}px;width:${r.width}px;height:${r.height}px;margin:0;z-index:90;pointer-events:none;transform-origin:0 0;`;
  document.body.appendChild(g);
  const dx = to.left - r.left, dy = to.top - r.top, sx = to.width / r.width;
  const done = g.animate([{ transform: "none" }, { transform: "translateY(-12px) rotate(3deg)", offset: 0.35 }, { transform: `translate(${dx}px, ${dy}px) scale(${sx})` }],
    { duration: tokenMs("--ork-motion-play", 400) * 1.4, easing: spring(), fill: "forwards" }).finished;
  return done.catch(() => {}).finally(() => g.remove());
}

/** The strip (or card) of a goal in a lane of the Board, once it is drawn. */
const laneOf = (slug) => document.querySelector(`.table-board .table-goal[data-goal="${CSS.escape(slug)}"] .table-gstrip, .table-board .table-goal[data-goal="${CSS.escape(slug)}"] .table-card`);

/** Plays the column's moves after each layout. `root`: the column's element; `work`: the goals of At work · later (`{n}`), whose lanes the tasks reach. */
export function useColumnMotion(root, work) {
  const last = useRef(null), laned = useRef(new Set()), chain = useRef(Promise.resolve());
  useLayoutEffect(() => {
    const el = root.current;
    if (!el) return;
    const now = new Map();
    el.querySelectorAll(".col-card[data-goal]").forEach((c) => now.set(c.dataset.goal, { el: c, pile: c.dataset.pile, rect: box(c) }));
    const before = last.current;
    last.current = new Map([...now].map(([slug, v]) => [slug, { pile: v.pile, rect: v.rect }]));
    const lanes = new Set(work.filter(({ n }) => cascadeOf(n).length > 0).map(({ n }) => n.slug)), fresh = before ? [...lanes].filter((s) => !laned.current.has(s)) : [];
    laned.current = lanes;
    if (!before || !seen()) return;                                                          // the first layout of the page, a hidden page, reduced motion: everything is where it is
    now.forEach((v, slug) => { const was = before.get(slug); if (was && was.pile !== v.pile) move(v.el, was, v.rect); });
    fresh.filter((s) => everBack.has(s) && now.has(s)).forEach((s) => requestAnimationFrame(() => {      // the lane draws in the same turn: look for its strip once it has
      const strip = laneOf(s), card = root.current?.querySelector(`.col-card[data-goal="${CSS.escape(s)}"]`);
      const to = strip?.getBoundingClientRect();
      if (card && to?.width) chain.current = chain.current.then(() => fly(card, to));
    }));
  });
}
