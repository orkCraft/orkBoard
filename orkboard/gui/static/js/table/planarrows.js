// A goal's plan, the order of its tasks as arrows (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.1, decisions §206.4; mockup docs/mockups/goal-card/ `arrows`): over the Orkmaster's Board with a goal picked, an SVG
// lies over the lanes, behind the cards' own pointer (it takes no press), and draws from each task a curve to every task that waits for it (the snapshot's task `after`). A task to the right of the one it waits for is reached along the
// row (from the card's right edge to the next's left), one below it or in its own lane from the card's foot to the other's head; one to the left from its left edge to the other's right. **An arrow from a task done is dashed.**
// The cards are measured where they lie (`[data-plan-task]`, drawn by planboard.js), so the lanes' widths and the cards' heights cannot throw it off; it is drawn again whenever the plan or the lanes change size.
import { useLayoutEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";

const GAP = 2;                                                              // how far an arrow stops short of the card it ends at

/** The path of an arrow from the card `a` to the card `b` (each `{x, y, w, h}` in the lanes' own coordinates): along the row when `b` lies to the right of `a`, from a left edge to a right edge when it lies to the left, else from `a`'s foot to `b`'s head. */
export function pathOf(a, b) {
  if (b.x > a.x + a.w - 4) {
    const x1 = a.x + a.w, y1 = a.y + a.h / 2, x2 = b.x - GAP, y2 = b.y + b.h / 2, mx = (x1 + x2) / 2;
    return `M${x1} ${y1} C${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`;
  }
  if (b.x + b.w < a.x + 4) {
    const x1 = a.x, y1 = a.y + a.h / 2, x2 = b.x + b.w + GAP, y2 = b.y + b.h / 2, mx = (x1 + x2) / 2;
    return `M${x1} ${y1} C${mx} ${y1} ${mx} ${y2} ${x2} ${y2}`;
  }
  const sx = a.x + a.w / 2, sy = a.y + a.h, ex = b.x + b.w / 2, ey = b.y - GAP, my = (sy + ey) / 2;
  return `M${sx} ${sy} C${sx} ${my} ${ex} ${my} ${ex} ${ey}`;
}

/** The arrows of a plan: `[{key, from, to, d, done}]` for each pair of drawn tasks `a` → `t` where `t` waits for `a`; `rects` is `{task id: {x, y, w, h}}`, `tasks` the plan's tasks (`id`, `after`, `state`). */
export function arrowsOf(tasks, rects) {
  const state = new Map(tasks.map((t) => [t.id, t.state]));
  return tasks.flatMap((t) => (t.after || []).filter((a) => rects[a] && rects[t.id] && a !== t.id)
    .map((a) => ({ key: `${a}>${t.id}`, from: a, to: t.id, d: pathOf(rects[a], rects[t.id]), done: state.get(a) === "merged" })));
}

/** The SVG over `host` (the element the cards lie in, a positioned scroller): measured after each draw of `tasks` and whenever `host` changes its size. */
export function PlanArrows({ host, tasks }) {
  const [at, setAt] = useState({ w: 0, h: 0, rects: {} });
  useLayoutEffect(() => {
    const el = host.current;
    if (!el) return undefined;
    const measure = () => {
      const base = el.getBoundingClientRect(), rects = {};
      el.querySelectorAll("[data-plan-task]").forEach((c) => {
        const r = c.getBoundingClientRect();
        rects[c.dataset.planTask] = { x: Math.round(r.left - base.left + el.scrollLeft), y: Math.round(r.top - base.top + el.scrollTop), w: Math.round(r.width), h: Math.round(r.height) };
      });
      const next = { w: el.scrollWidth, h: el.scrollHeight, rects };
      setAt((was) => (JSON.stringify(was) === JSON.stringify(next) ? was : next));
    };
    measure();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(measure) : null;
    ro?.observe(el);
    el.querySelectorAll("[data-plan-task]").forEach((c) => ro?.observe(c));
    return () => ro?.disconnect();
  });
  const list = arrowsOf(tasks, at.rects);
  return html`<svg class="plan-arrows" width=${at.w} height=${at.h} aria-hidden="true" data-arrows=${String(list.length)}>
    <defs><marker id="plan-ah" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 8 4 0 8z" /></marker></defs>
    ${list.map((a) => html`<path key=${a.key} d=${a.d} class=${cls("plan-arrow", { "is-done": a.done })} data-from=${a.from} data-to=${a.to} marker-end="url(#plan-ah)" />`)}
  </svg>`;
}
