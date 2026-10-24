// A fold of the left column as one 28 px row (docs/specs/73-a-lighter-column.md §3): orkUI's chevron (› folded, ⌄ open), the word in the pixel face's small caps as the groups'
// headings are, the count in the text face, and at its right what the row offers (*Process now*, *k wait for main*). Shared by the party's body (goals.js) and Ideation's (pitches.js).
import { html, cls } from "../html.js";
import { Chev } from "../orkui.js";

/** `word`: *New*, *Flags*, *Sent*; `n`: how many it holds; `open`/`toggle`: its state; `kind`: a class of the row; `children`: at its right. */
export function FoldRow({ word, n, open, toggle, kind = "", children = null }) {
  return html`<div class=${cls("arena-frow", kind)} data-fold=${word.toLowerCase()}>
    <button type="button" class="arena-fold arena-frow__main" aria-expanded=${open} aria-label=${`${word} · ${n}`} onClick=${toggle}>
      <${Chev} dir=${open ? "down" : "right"} /><span class="arena-frow__word">${word}</span><span class="arena-frow__n" aria-hidden="true">· ${n}</span></button>
    ${children}
  </div>`;
}
