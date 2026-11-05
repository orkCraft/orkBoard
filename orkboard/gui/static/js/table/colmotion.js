// The moves of the Orkmaster's column (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part B.4, docs/specs/147-one-card-four-corners.md part E, decisions §206.3, §251.7, §70): a goal agreed turns upright where it lay and goes to To review; its
// wait over it goes to At work, and that is **the start**: its back turns face up and stands at At work, then a card of the goal flies to the strip of each party doing it and folds into it, where its tasks rise (`deal`, turnfly.js). A card that changes pile
// otherwise is moved with the Web Animations API from where it was (the page keeps no state of its own for it: each layout is measured, the next one compared); a sideways card turns a quarter on its way up. Nothing is played for a page that is hidden, for a card first
// seen, or under reduced motion (§89.0: a motion plays once, never for what changed unseen); several starts in one snapshot deal the first and lay the rest; a goal done goes to the discard as today (discard.js).
import { useLayoutEffect, useRef } from "preact/hooks";
import { boxIn, ease, reduced, tokenMs } from "../hand/motion.js";
import { foldInto, turnFly } from "./turnfly.js";

const MAX_LANES = 6;                                                                       // a start is told to six parties at most (§70.1)
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

/** The strips of a goal in the lanes of the Board, one a party (in view; a lane under the pointer takes none, §70.2). */
const stripsOf = (slug) => [...document.querySelectorAll(`.table-board .table-goal[data-goal="${CSS.escape(slug)}"] .table-gstrip`)]
  .filter((s) => boxIn(s) && !s.closest(".table-lane")?.matches(":hover")).slice(0, MAX_LANES);

/** The start of a goal (spec 147 E.1): its back in To review (`was`: where it lay) turns face up and stands at At work (two steps), then a card of it flies to the strip of each party doing it and folds into it (two more, every card at once): four steps of about
 *  0.3 s, one motion that travels. The real card is hidden until it stands. */
async function deal(card, was) {
  const step = tokenMs("--ork-motion-play", 400) * 0.75, to = boxIn(card);
  if (!to) return;
  card.style.visibility = "hidden";
  try {
    await turnFly({ from: was.rect, to, face: card, sideways: true, ms: step * 2, easing: ease(), kind: "start" }).finished;
    if (!card.isConnected) return;
    card.style.visibility = "";
    const from = boxIn(card), strips = from ? stripsOf(card.dataset.goal) : [];                  // the lanes have been drawn meanwhile
    await Promise.all(strips.map((strip) => foldInto(card, from, strip.getBoundingClientRect(), { ms: step * 2, easing: ease(), kind: "deal" })));
  } finally { card.style.visibility = ""; }
}

/** Plays the column's moves after each layout. `root`: the column's element. */
export function useColumnMotion(root) {
  const last = useRef(null), dealing = useRef(false);
  useLayoutEffect(() => {
    const el = root.current;
    if (!el) return;
    const now = new Map();
    el.querySelectorAll(".col-card[data-goal]").forEach((c) => now.set(c.dataset.goal, { el: c, pile: c.dataset.pile, rect: box(c) }));
    const before = last.current;
    last.current = new Map([...now].map(([slug, v]) => [slug, { pile: v.pile, rect: v.rect }]));
    if (!before || !seen()) return;                                                          // the first layout of the page, a hidden page, reduced motion: everything is where it is
    const starts = [...now].filter(([slug, v]) => before.get(slug)?.pile === "review" && v.pile === "work" && !v.el.classList.contains("is-off"));
    let first = !dealing.current ? starts[0]?.[0] : "";                                      // the first start is dealt, the others are laid; one deal at a time
    now.forEach((v, slug) => {
      const was = before.get(slug);
      if (!was || was.pile === v.pile) return;
      if (slug === first) { dealing.current = true; deal(v.el, was).catch(() => {}).finally(() => { dealing.current = false; }); first = ""; return; }
      move(v.el, was, v.rect);
    });
  });
}
