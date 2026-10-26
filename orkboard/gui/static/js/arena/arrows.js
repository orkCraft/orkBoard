// The arrows (docs/specs/50-parties-and-goals.md §3.4, docs/specs/82-the-field-at-a-glance.md §6): hovering a card (or a spread card) draws an arrow from each task it waits for to it and from it
// to each task that waits for it, between the cards that are shown — a dashed ink line in square steps (down from the bottom centre of the card waited for, across in the strip between the rows,
// down into the top centre of the waiting card), 2 px, with a head, over the field and under the drawer,
// drawn from its start in four steps when it comes (arena.css `arena-draw`; none when motion is reduced). An end
// that is not shown (a task under another card of its stack, or one the filter has taken away, or one scrolled out of its column) draws none. Only
// with a fine pointer (`(hover: hover)`); the keyboard's focus draws them too. The card's foot keeps the words (stacks.js `footParts`).
// The System's parts (systemmap.js, docs/specs/89-the-tech-lens-system.md §6.4) draw their uses with the same lines and heads: `across` routes one between two cards anywhere on its table, and a line
// may carry its goal's element (`el`: a use new since the last look is drawn in its goal's colour, systemmap.css).
import { useLayoutEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { spread, taskHover, taskHoverBy } from "./arenastate.js";
import { waitersOf, waitsForOf } from "./arenawords.js";

const HEAD = 9;                                       // the arrow head's length in px

export const fine = () => typeof matchMedia === "function" && matchMedia("(hover: hover)").matches;

/** Where the segment from the centre of `a` to the centre of `b` leaves `a`: the point on a's edge. */
function edgeOf(a, b) {
  const cx = a.x + a.w / 2, cy = a.y + a.h / 2, dx = b.x + b.w / 2 - cx, dy = b.y + b.h / 2 - cy;
  if (!dx && !dy) return { x: cx, y: cy };
  const k = Math.min(dx ? a.w / 2 / Math.abs(dx) : Infinity, dy ? a.h / 2 / Math.abs(dy) : Infinity);
  return { x: cx + dx * k, y: cy + dy * k };
}

/** The arrow from the box `a` to the box `b` (both {x, y, w, h} in the host's coordinates): its line, which stops short of the head, and the head's points. */
export function segment(key, a, b) {
  const p = edgeOf(a, b), q = edgeOf(b, a), ang = Math.atan2(q.y - p.y, q.x - p.x);
  const w = (d) => `${(q.x - HEAD * Math.cos(ang + d)).toFixed(1)},${(q.y - HEAD * Math.sin(ang + d)).toFixed(1)}`;
  return { key, x1: p.x, y1: p.y, x2: q.x - (HEAD - 1) * Math.cos(ang), y2: q.y - (HEAD - 1) * Math.sin(ang), tip: q, head: `${q.x.toFixed(1)},${q.y.toFixed(1)} ${w(0.45)} ${w(-0.45)}` };
}

const STRIP = 8;                                      // half the strip between two rows (the label's line, 16 px): the arrow crosses at its middle
const HALF = 4;                                       // half the width of a step's arrow head

/** The arrow of a wait, in square steps (spec 82 §6), from the box `a` of the card waited for to the box `b` of the waiting one (both {x, y, w, h} in the host's coordinates; `a.cell`: the bottom of
 *  a's row): down from a's bottom centre, across in the middle of the strip under a's row, down into b's top centre; `points` the polyline (which stops short of the head), `head` the head's
 *  points. null when b does not lie under a (the same row: nothing to draw). */
export function steps(key, a, b) {
  const x1 = a.x + a.w / 2, y1 = a.y + a.h, x2 = b.x + b.w / 2, y2 = b.y;
  if (y2 - y1 < 2) return null;
  const mid = Math.min(a.cell != null ? a.cell + STRIP : (y1 + y2) / 2, y2 - HEAD);
  const to = y2 - (HEAD - 1), at = (x, y) => `${x.toFixed(1)},${y.toFixed(1)}`;
  return { key, x1, y1, points: [at(x1, y1), at(x1, mid), at(x2, mid), at(x2, to)].join(" "), tip: { x: x2, y: y2 }, head: `${at(x2, y2)} ${at(x2 - HALF, y2 - HEAD)} ${at(x2 + HALF, y2 - HEAD)}` };
}

/** A part's use on the System's table (spec 89 §6.4), in square steps between two cards anywhere on it: out of the side of `a` that faces `b` (the right one for a card of its own column) into the
 *  gutter beside it, along the gutter to the gap over b's row, across that gap to b's centre, down into b's top. `gx`, `gy`: half the gutter between two columns and half the gap between two rows,
 *  so the line runs between the cards, never through them. The shape of `steps`'s answer. */
export function across(key, a, b, gx, gy) {
  const right = b.x + b.w / 2 >= a.x + a.w / 2 - 1;
  const x1 = right ? a.x + a.w : a.x, y1 = a.y + a.h / 2, side = right ? x1 + gx : x1 - gx;
  const x2 = b.x + b.w / 2, y2 = b.y, lane = y2 - gy, to = y2 - (HEAD - 1), at = (x, y) => `${x.toFixed(1)},${y.toFixed(1)}`;
  return { key, x1, y1, points: [at(x1, y1), at(side, y1), at(side, lane), at(x2, lane), at(x2, to)].join(" "), tip: { x: x2, y: y2 },
    head: `${at(x2, y2)} ${at(x2 - HALF, y2 - HEAD)} ${at(x2 + HALF, y2 - HEAD)}` };
}

/** The svg layer that draws `lines` (from `steps`, a field's; from `segment`, the project's diagonals; from `across`, the System's uses) over its positioned host. */
export function ArrowLines({ lines }) {
  return html`<svg class="arena-arrows" aria-hidden="true">${lines.map((l) => html`<g key=${l.key} class=${cls("arena-arrow", { "is-leaving": !!l.leaving })} data-edge=${l.key} data-kind=${l.kind || undefined} data-elem=${l.el || undefined}>
    ${l.points ? html`<polyline points=${l.points} fill="none" style=${`transform-origin: ${l.x1.toFixed(1)}px ${l.y1.toFixed(1)}px`} />`
      : html`<line x1=${l.x1} y1=${l.y1} x2=${l.x2} y2=${l.y2} style=${`transform-origin: ${l.x1.toFixed(1)}px ${l.y1.toFixed(1)}px`} />`}<polygon points=${l.head} /></g>`)}</svg>`;
}

/** The arrows between the cards shown: [{key, points, head}] (`steps`). `host`: the element the lines are drawn in. */
export function linesFor(host, nodes, hover, inSpread) {
  const slash = hover.lastIndexOf("/"), goal = hover.slice(0, slash), id = hover.slice(slash + 1);
  const n = nodes.find((x) => x.slug === goal), t = n?.tasks.find((x) => x.id === id);
  if (!n || !t) return [];
  const base = host.getBoundingClientRect(), attr = inSpread ? "data-spread-key" : "data-key";
  const rect = (task) => {                            // a card's box in the host's own coordinates; null when it is not shown
    const el = host.querySelector(`[${attr}="${CSS.escape(`${n.slug}/${task.id}`)}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect(), box = { x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height };
    const cell = el.closest(".arena-phase.is-cell");                // the row it lies in: its bottom is where the arrows below it cross (spec 82 §6)
    if (cell) box.cell = cell.getBoundingClientRect().bottom - base.top;
    const clip = el.closest(".arena-cols__grid, .arena-solo");        // the field scrolls inside itself: a card out of view is not shown
    if (clip) {
      const c = clip.getBoundingClientRect();
      if (r.bottom <= c.top || r.top >= c.bottom || r.right <= c.left || r.left >= c.right) return null;
    }
    return box;
  };
  const me = rect(t);
  if (!me) return [];
  const pairs = [...waitsForOf(n, t).map((s) => [s, t]), ...waitersOf(n, t).map((w) => [t, w])];
  const out = [];
  for (const [from, to] of pairs) {
    const a = from === t ? me : rect(from), b = to === t ? me : rect(to);
    if (!a || !b) continue;
    const arrow = steps(`${from.id}>${to.id}`, a, b);
    if (arrow) out.push(arrow);
  }
  return out;
}

/** The arrows layer over `host` (the field's body). Redrawn when the hovered card or the cards change. */
export function Arrows({ host, nodes }) {
  const hover = taskHover.value, by = taskHoverBy.value, inSpread = !!spread.value;
  const [lines, setLines] = useState([]);
  useLayoutEffect(() => {
    const el = host.current;
    const on = !!hover && !!el && (by === "focus" || fine());
    const next = on ? linesFor(el, nodes, hover, inSpread) : [];
    setLines((was) => (was.length === 0 && next.length === 0 ? was : next));
  }, [hover, by, inSpread, nodes]);
  return html`<${ArrowLines} lines=${lines} />`;
}
