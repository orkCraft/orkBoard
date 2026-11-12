// The hand follows the mat open (goal 171 stage K; decisions §302.1, §302.4): while a mat is open on the desktop the hand is that mat's, a fan of its ways (the battle's, the gate's, a turn's, a question's),
// and the cards of the moves that wait lie as a pile at the hand's left, its thickness and never a number; the pile pressed puts the mat away and they come back (the mat closed, every card is back).
// `matFrame.js` says what the open mat holds (`matHand`: its ways and how it closes); hand/hand.js draws `MatHand` in the hand's place. On a phone the mat is the whole screen and its ways stay the foot of
// its screen, a row that scrolls (§302.6). The mat's focus takes in the hand: Tab goes through the mat and the hand's ways only (`handRoots`). Layout: mathand.css.
import { signal } from "@preact/signals";
import { html } from "../html.js";

if (typeof document !== "undefined") {                         // this sheet loads with its module, as the places' does
  const href = new URL("./mathand.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const matHand = signal(null);            // while a mat is open on the desktop: {ways: its ways (a node or null), close: puts it away}

/** The hand's part of the open mat, for the focus to take in: the elements Tab may go through besides the mat's own. */
export const handRoots = () => [...document.querySelectorAll(".frame-hand .mathand")];

/** The pile of the moves that wait: up to six backs, each a little higher than the one under it, pressed it puts the mat away; nothing when none waits. */
function Pile({ n, close }) {
  if (n < 1) return null;
  return html`<button type="button" class="mathand__pile" data-act="pile" aria-label="The moves that wait, a pile. Press to put the mat away and bring them back." onClick=${close}>
    <span class="mathand__backs" aria-hidden="true">${Array.from({ length: Math.min(n, 6) }, (_, i) => html`<span key=${i} style=${`--dx:${i * 2}px;--dy:${-i * 2}px`}></span>`)}</span>
    <span class="mathand__cap">Waiting</span></button>`;
}

/** The hand while a mat is open: the pile of the moves that wait at its left, the mat's ways. `waiting`: how many cards the moves that wait come to. */
export function MatHand({ waiting }) {
  const m = matHand.value;
  if (!m) return null;
  return html`<div class="mathand" aria-label="The hand of the open mat"><div class="mathand__row">
    <${Pile} n=${waiting} close=${m.close} />
    ${m.ways && html`<div class="sp-cards mathand__ways" role="group" aria-label="Your hand">${m.ways}</div>`}
  </div></div>`;
}
