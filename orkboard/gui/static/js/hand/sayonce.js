// A lifted card says its title once (docs/specs/140-the-window-made-lighter.md part A4, decisions §247.6): a line that repeats the card's title is not drawn, and what the card says is one sentence, the rest behind
// its **…** (a quiet button that opens it in place and closes it again). Used by the hand's lifted card (stopcard.js `Body`), the stop's whole view (stopface.js: the repeat is not drawn, it is the whole) and the
// Orkmaster's column's lifted card of To review (table/column.js `Acts`). Pure where it can be: `said` takes the title and the lines and gives the sentence and the rest. A caller keys `Said` by its card, so another card starts closed.
import { useState } from "preact/hooks";
import { html } from "../html.js";

const plain = (t) => String(t || "").toLowerCase().replace(/[\s.…!?:;,"'’“”-]+/g, " ").trim();

/** The lines that are not the title again (`title` one or several, a card's short name and its whole one; a line equal to the title, ignoring case and its closing stop, is not drawn). */
export const notTitle = (title, lines) => { const ts = [].concat(title).map(plain); return lines.filter((l) => l && plain(l) && !ts.includes(plain(l))); };

/** The first sentence of the lines left and the rest: `{first, rest}` (the rest "" when there is none). A sentence ends at a stop, a question mark or an exclamation mark followed by a space. */
export function said(title, lines) {
  const text = notTitle(title, lines).map((l) => String(l).trim()).join(" "), cut = text.search(/[.!?](\s|$)/);
  if (cut < 0 || cut + 1 >= text.length) return { first: text, rest: "" };
  return { first: text.slice(0, cut + 1), rest: text.slice(cut + 1).trim() };
}

/** One sentence in a `<p>` of the class `tag`, and when there is more, a **…** that opens the rest. */
export function Said({ title, lines, tag }) {
  const [open, setOpen] = useState(false), { first, rest } = said(title, lines);
  if (!first) return null;
  return html`<p class=${tag} data-said>${first}${rest && open ? ` ${rest}` : ""}${rest && html` <button type="button" class="ork-btn quiet hand-more" aria-expanded=${open ? "true" : "false"} aria-label=${open ? "Less" : "More"} onClick=${() => setOpen(!open)}>${open ? "–" : "…"}</button>`}</p>`;
}
