// The hand as whole cards (goal 170, stage M; docs/mockups/table-cards/ ?face=desk): on the table of cards (`cardsOn()`) a stop of the
// hand is an S card, upright 2.5:3.5, wholly seen and about 120 px wide: its goal's rune and the kind's sign in two corners, its title,
// the line under it, the leader's head small at its foot; the card that asks is lifted and ringed in the alert's yellow with its "!".
// This is only the card's face: the press, the keys, the stacks and every command stay hand/stopcard.js's and hand/stacks.js's, which
// draw this face in place of their own where `cardsOn()` says so. Layout: handcards.css.
import { html } from "../html.js";
import { Head, headWords } from "../orkui.js";
import { Index } from "./card.js";
import { whoOf } from "../table/post.js";

/** The race whose colour is the card's party (the Orkmaster's for a card of no party). */
export const raceOfStop = (s) => (s.party?.slug ? whoOf(s.party.slug).race : "") || "orkmaster";

/** The S face of a stop of the hand: `sign` the kind's sign (stopcard.js `actionOf`), `asks` it waits for the person (its "!"), `head` the asker's head, `line` the line under the title. */
export function HandFace({ s, sign, asks = false, head = null, line = "" }) {
  const n = { element: s.node?.element || "", hue: s.node?.hue || s.node?.element || "", sign };
  return html`<${Index} n=${n} />${asks && html`<span class="hands-asks" aria-hidden="true">!</span>`}
    <span class="hand-card__name hands-name" title=${s.full || s.title}>${s.title || s.full}</span>
    ${line ? html`<small class="hand-card__foot hands-line">${line}</small>` : null}
    ${head && html`<span class="hands-head" title=${headWords(head)}><${Head} race=${head.race} tier=${head.tier} /></span>`}
    <${Index} n=${n} turned=${true} />`;
}
