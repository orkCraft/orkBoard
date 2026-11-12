// What a card in the hand and in a battle draws that is no button (decisions §298.3, §298.6): a craft's token that only shows (`TokenDot`: its leader's tool in its
// party's ring, its checks as squares under it; a hand card is one button, so a token on it cannot be a second), the tokens of a goal in a row (`TokenDots`), and the
// battle's emblem, one card upright and two backs crossed behind it (`Emblem`, drawn in CSS: handcards.css). Layout: verdict.css and handcards.css.
import { html } from "../html.js";
import { KINDS, Square, TOOLS, raceIn, saysOf, verdictsOf } from "./verdict.js";

/** One verdict as a token that only shows; a screen reader reads its words (*Tech: 2 approved, 1 question*). */
export function TokenDot({ v }) {
  const race = raceIn(v.leader), tool = TOOLS[race] || TOOLS.ork;
  return html`<span class="cards-ct is-still" role="img" data-race=${race || "orkmaster"} data-leader=${v.leader} aria-label=${saysOf(v.leader, v.checks)}>
    <span class="cards-ct__ring"><span class=${`ork-tool ${tool}`} aria-hidden="true"></span></span>
    <span class="cards-ct__sq" aria-hidden="true">${KINDS.flatMap((k) => v.checks.filter((c) => c.kind === k).slice(0, 5).map((_, i) => html`<${Square} key=${`${k}${i}`} kind=${k} />`))}</span></span>`;
}

/** A goal's tokens in a row, its route's order. */
export const TokenDots = ({ slug }) => html`<span class="cards-cts hands-toks">${verdictsOf(slug).map((v) => html`<${TokenDot} key=${v.leader} v=${v} />`)}</span>`;

/** The battle's emblem: a card upright and two backs crossed behind it. */
export const Emblem = () => html`<span class="cards-emblem" aria-hidden="true"><i class="is-b1"></i><i class="is-b2"></i><i class="is-f"></i></span>`;
