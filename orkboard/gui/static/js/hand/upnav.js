// Along the goals on the phone's hand (docs/decisions.md §180.3): the arrows ← → at the two sides of the context, each a 44 px target drawing the neighbour goal's leader head and its element (no number, no sign: `Neighbour` is the one
// small piece to change if the owner decides to show more), and a horizontal swipe on the top card, which does the same; and the *Spec* button under the context, which opens the goal's way straight on its Spec page
// (or, while no spec is written, on Talk, saying so). A swipe starts on the card only, never at the screen's edge (the system's back), and a vertical move is a scroll, not a swipe.
import { html, cls } from "../html.js";
import { Elem, Head, Icon } from "../orkui.js";
import { openOver } from "../frame/state.js";
import { phaseOf } from "../table/data.js";
import { step } from "./entries.js";

const EDGE = 24;               // px from the screen's side where a swipe does not begin
const FAR = 56;                // px a swipe goes sideways at least

/** What an arrow draws of the goal beyond it: its leader's head and its element; a card of no goal, the Orkmaster's crowned head and no element. */
function Neighbour({ e }) {
  return html`<${Head} race=${e.head?.race || "peon"} tier=${e.head?.tier || "crown"} />${e.element && html`<${Elem} name=${e.element} />`}`;
}

/** One arrow: `to` the entry beyond it (none: it is disabled and not drawn), `dir` -1 or 1. */
export function Arrow({ dir, to, onPress }) {
  const word = dir < 0 ? "Previous" : "Next";
  return html`<button type="button" class=${cls("ork-btn quiet up-nav", dir < 0 ? "is-prev" : "is-next")} data-dir=${dir < 0 ? "prev" : "next"} disabled=${!to} aria-label=${to ? `${word} goal: ${to.name}` : `${word} goal`}
    title=${to ? `${word} goal: ${to.name}` : undefined} onClick=${onPress}><${Icon} name=${dir < 0 ? "arrow-left" : "arrow-right"} />${to && html`<span class="up-nav__who"><${Neighbour} e=${to} /></span>`}</button>`;
}

/** The pointer handlers of the top card's place: a sideways swipe steps to the previous or next goal. */
export function swipeOf(entries) {
  let from = null;
  return {
    onPointerDown: (e) => {
      const x = e.clientX;
      from = x < EDGE || x > innerWidth - EDGE || !e.target.closest?.(".hand-lifted") ? null : { x, y: e.clientY };
    },
    onPointerUp: (e) => {
      const f = from; from = null;
      if (!f) return;
      const dx = e.clientX - f.x, dy = e.clientY - f.y;
      if (Math.abs(dx) >= FAR && Math.abs(dx) > Math.abs(dy) * 1.5) step(entries, dx < 0 ? 1 : -1);
    },
    onPointerCancel: () => { from = null; },
  };
}

/** *Spec* under the context: the goal's Spec page; *The spec is written after your answers* (opening Talk) while it is not decided. Nothing for a card of no goal. */
export function SpecButton({ idea }) {
  if (!idea || idea.startsWith("party:")) return null;
  const talk = phaseOf(idea) === "talk";
  const open = () => openOver(talk ? "talk" : "spec", { idea }, { title: "", key: "" }, talk ? "Talk" : "Spec");
  return html`<button type="button" class="ork-btn quiet up-spec" data-page=${talk ? "talk" : "spec"} onClick=${open}>${talk ? "The spec is written after your answers" : "Spec"}</button>`;
}
