// What a task made, in its card's window (docs/specs/142-a-cards-window-where-it-has-something-to-show.md part D, decisions §249.3; the look: docs/mockups/card-windows/index.html, section 3). A task done or at Review carries
// `craft_made` in the snapshot (the host reads it by code from what the Board has, realm/task_made.py: never a model) and the window draws it by its `kind`, 92 px high and the card's width, inside the same frame as the
// other windows (card.js `TaskWin`): **diff** (Tech) the three files it touched, each name in the code face cut with an ellipsis and six pixel bars of 4 x 6 px, the added in orkUI's success, the taken in its danger, the rest in its
// frame; **asset** (Art) the image itself at its pixels (`image-rendering: pixelated`, scaled by a whole number that fits) on a checker of tokens, with its name and size small; **screen** (Design) the screen it changed, a thumbnail,
// *before* faint and an arrow to *after* when a before is kept; **checks** (Release) its checks on the way into main as ticks; **hypothesis** (Product) the hypothesis the goal tests, quoted, and its state as a chip. A kind the
// page does not know, or one with nothing to draw, is none (null): the card keeps the type's sign. (Run's and LiveOps' dated event waits for §215's events: the host serves none yet.) Pure functions first (`barsOf`, `scaleOf`,
// `madeOf`), then the little windows card.js draws.
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";

/** The states a task has made something in: done or being checked, at the gate or at Review (the host serves `craft_made` for these only). */
export const MADE_STATES = ["merged", "review", "testing"];

const BARS = 6, ASSET_BOX = 64;

/** The six bars of a file's row: `a` added, `x` taken, `o` the rest, by its lines against the file of the three with most (the one with most fills the row); a file with both keeps one of each. */
export function barsOf(f, most) {
  const a = Math.max(0, Number(f?.added) || 0), x = Math.max(0, Number(f?.removed) || 0), total = a + x;
  if (!total) return Array(BARS).fill("o");
  const lit = Math.max(a && x ? 2 : 1, Math.min(BARS, Math.ceil((BARS * total) / Math.max(total, most || total))));
  let ra = Math.round((lit * a) / total);
  if (a && !ra) ra = 1;
  if (x && ra >= lit) ra = lit - 1;
  return [...Array(ra).fill("a"), ...Array(lit - ra).fill("x"), ...Array(BARS - lit).fill("o")];
}

/** The whole-number scale at which an image of `w` x `h` pixels fits a square of `box` px: 1 or more; 0 where even one is too large (the page then fits it, still pixelated). */
export const scaleOf = (w, h, box = ASSET_BOX) => (w > 0 && h > 0 ? Math.floor(Math.min(box / w, box / h)) : 0);

/** What the window draws of a task: its `craft_made` when it is of a kind the page knows and has something to draw, else null (the card keeps the type's sign). A task not done nor at Review has none. */
export function madeOf(t) {
  const m = t?.craft_made;
  if (!m || typeof m !== "object" || !MADE_STATES.includes(t.state)) return null;
  if (m.kind === "diff") { const files = (Array.isArray(m.files) ? m.files : []).filter((f) => f && f.path).slice(0, 3); return files.length ? { ...m, files } : null; }
  if (m.kind === "asset") return m.url && m.w > 0 && m.h > 0 ? m : null;
  if (m.kind === "screen") return m.after ? m : null;
  if (m.kind === "checks") { const items = (Array.isArray(m.items) ? m.items : []).filter((c) => c && c.name); return items.length ? { ...m, items } : null; }
  if (m.kind === "hypothesis") return m.text ? m : null;
  return null;
}

const STATE_WORDS = { proposed: "Proposed", open: "Open", testing: "Testing", held: "Held", refuted: "Refuted" };

function Diff({ m }) {
  const most = Math.max(...m.files.map((f) => (f.added || 0) + (f.removed || 0)));
  return html`<span class="made-diff">${m.files.map((f) => html`<span class="made-diff__row" key=${f.path} title=${`${f.path}: +${f.added || 0} −${f.removed || 0}`}>
    <span class="made-diff__file">${f.path.split("/").pop()}</span><span class="made-diff__bars" aria-hidden="true">${barsOf(f, most).map((b, k) => html`<i key=${k} class=${`is-${b}`}></i>`)}</span></span>`)}</span>`;
}

function Asset({ m }) {
  const s = scaleOf(m.w, m.h), style = s ? `width:${m.w * s}px;height:${m.h * s}px` : `width:${ASSET_BOX}px;height:${ASSET_BOX}px;object-fit:contain`;
  return html`<span class="made-asset"><img class="made-asset__img" src=${m.url} alt="" style=${style} data-scale=${s} /><span class="made-asset__cap"><span class="made-asset__name" title=${m.name}>${m.name}</span><span>${m.w} × ${m.h}</span></span></span>`;
}

function Screen({ m }) {
  return html`<span class="made-screen">${m.before && html`<img class="made-screen__img is-before" src=${m.before} alt="" /><span class="made-screen__arrow" aria-hidden="true">→</span>`}<img class="made-screen__img is-after" src=${m.after} alt="" /></span>`;
}

function Checks({ m }) {
  return html`<span class="made-checks">${m.items.slice(0, 5).map((c) => html`<span class=${cls("made-checks__row", `is-${c.state}`)} key=${c.name} data-state=${c.state}>
    ${c.state === "passed" ? html`<${Sign} name="check" />` : c.state === "failed" ? html`<${Sign} name="cross" />` : html`<i class="made-checks__dot" aria-hidden="true"></i>`}<span class="made-checks__name" title=${c.name}>${c.name}</span></span>`)}</span>`;
}

function Hypothesis({ m }) {
  return html`<span class="made-hyp"><q class="made-hyp__text" title=${m.text}>${m.text}</q><span class="made-hyp__state"><span class=${cls("ork-chip", "made-hyp__chip", `is-${m.state}`)}>${STATE_WORDS[m.state] || m.state}</span></span></span>`;
}

const KINDS = { diff: Diff, asset: Asset, screen: Screen, checks: Checks, hypothesis: Hypothesis };

/** The window's inside for a task that made something, or null. */
export function MadeWindow({ t }) {
  const m = madeOf(t), Kind = m && KINDS[m.kind];
  return Kind ? html`<${Kind} m=${m} />` : null;
}
