// The Pen: a field as large as the hand in the ways' place (docs/specs/168 D1, decisions §286.1, §286.3; openedcard.css `.hand-pen.is-play`), for *Your own words…* of a card in play (a question's: answercards.js; a conflict's *Other…*: sayplay.js). It lies from the card's left edge to the strip the sunk hand
// keeps (`at`: handplace.js `usePlace`), focused at once, its *Send to <who>* beside it. An empty field sends nothing; Enter sends, Shift+Enter is a new line, Esc closes it (`onClose`). The words are the field's own while it lies; closed, they go.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";

/** `who`: the name of whom the words go to (*Design lead*); `send(text)`: sends the trimmed words; `value`: the words it opens with; `close()`: Esc. */
export function PenField({ at, who, send, close, ask = null, value = "" }) {
  const field = useRef(), [words, setWords] = useState(value);
  useEffect(() => { field.current?.focus({ preventScroll: true }); }, []);
  const go = () => { const text = words.trim(); if (text) send(text); };
  const key = (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); }
    else if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); go(); }
  };
  return html`<div class="hand-pen is-play" role="group" aria-label="Your own words" style=${at ? `left:${at.left}px;right:${at.right}px` : undefined}>
    <textarea ref=${field} class="ork-field hand-pen__text" rows=${ask?.rows || 4} aria-label=${ask?.label || `Your words to ${who}`} placeholder=${ask?.hold || `Your words to ${who}…`} value=${words} onInput=${(e) => setWords(e.currentTarget.value)} onKeyDown=${key}></textarea>
    <div class="hand-pen__side"><span class="cap hand-pen__hint">${ask?.note || "Enter sends · Shift+Enter a new line"}</span>
      <button type="button" class="ork-btn primary" data-act="send-words" onClick=${go}>${ask?.button || `Send to ${who}`}</button></div>
  </div>`;
}
