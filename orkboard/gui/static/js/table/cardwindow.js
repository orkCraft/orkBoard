// A card's window, never empty (docs/specs/148-a-window-on-every-card.md part A, decisions §252): one frame, the lanes' window frame of card.js (`.table-card__win.is-window`), holding what the place has, in one order: what the work
// made (§249.3, drawn by made.js), else the goal's first attached picture (`picture`, a URL the host serves: realm/idea_photos.py), else its words (real text in the reading face, clamped to the lines that fit `h`), else nothing.
// `windowOf` is pure; `CardWindow` draws it. Where it lies on a card is part B's.
import { html, cls } from "../html.js";
import { madeOf, MadeInside } from "./made.js";

const LINE = 15, PAD = 12;       // the words' line height and the frame's padding, top and bottom (cardwindow.css)

/** What the window shows, in §252.2's order: `made` (a task's `craft_made`, if the page knows its kind and it has something to draw), else `picture` (a URL), else `words`, else none. */
export function windowOf({ made, picture, words } = {}) {
  const m = madeOf({ craft_made: made, state: "merged" });
  if (m) return { kind: "made", made: m };
  const url = typeof picture === "string" ? picture.trim() : "";
  if (url) return { kind: "picture", url };
  const text = typeof words === "string" ? words.replace(/\s+/g, " ").trim() : "";
  if (text) return { kind: "words", text };
  return { kind: "none" };
}

/** What the work made last, for a goal's card: the `craft_made` of the last of its `tasks` that has something to draw (a task done or at Review, made.js `madeOf`), else null. */
export function lastMade(tasks) {
  const list = Array.isArray(tasks) ? tasks : [];
  for (let i = list.length - 1; i >= 0; i--) if (madeOf(list[i])) return list[i].craft_made;
  return null;
}

/** How many lines of words a window `h` px high holds: at least one. */
export const linesOf = (h) => Math.max(1, Math.floor(((Number(h) || 0) - PAD) / LINE));

/** The window: `of` is `{ made, picture, words, name }` (`name` the goal's, the picture's alt); `h` its height in px from the place (omitted: the place's CSS sets it). Nothing to show draws nothing. */
export function CardWindow({ of, h }) {
  const w = windowOf(of || {});
  if (w.kind === "none") return null;
  const style = h ? `height:${h}px` : undefined, lines = linesOf(h || 70);
  const inside = w.kind === "made" ? html`<${MadeInside} m=${w.made} />`
    : w.kind === "picture" ? html`<img class="card-win__img" src=${w.url} alt=${of?.name || ""} loading="lazy" decoding="async" />`
    : html`<span class="card-win__words" title=${w.text} style=${`-webkit-line-clamp:${lines};line-clamp:${lines}`}>${w.text}</span>`;
  return html`<span class=${cls("table-card__win is-window card-win", `is-${w.kind}`)} data-window=${w.kind === "made" ? "made" : "card-" + w.kind} style=${style}>${inside}</span>`;
}
