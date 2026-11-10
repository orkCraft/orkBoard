// The book (docs/specs/168-the-window-played-as-a-card-games-table.md A5, decisions §285.3): at the hand's right end, with the die and the backpack, the places that change the table: orkUI's `.ork-book` (0.37.0, 2 px a cell, about 48 × 50) in a box of 48 × 60, *History* under it, **drawn open (`.is-open`) while the past is on the table**, as the backpack is while the inventory is.
// Pressed it opens the history over the pane (table/history.js, kind `history`, spec 168 G3: a grid of goal cards, a row a day, through the open tab's eyes, a search above them), and pressed again, while it is open, it shuts it. Only from 760 px up (lane.js's column): under it the places stay as they were.
import { html, cls } from "../html.js";
import { closeOver, over } from "../frame/state.js";
import { openHistory } from "../table/history.js";

export const HISTORY_WORD = "History";

/** The past is on the table: the chronicle view open on the whole past. */
export const historyOn = () => over.value?.kind === "history";

export function Book() {
  const open = historyOn(), title = open ? "Close the history" : "History: the project's past";
  return html`<button type="button" class=${cls("hand-book", { "is-open": open })} data-book aria-pressed=${open ? "true" : "false"} title=${title} aria-label=${title}
    onClick=${() => (open ? closeOver() : openHistory())}><span class="place-box"><span class=${cls("ork-book", { "is-open": open })} aria-hidden="true"></span></span><span class="hand-book__word">${HISTORY_WORD}</span></button>`;
}
