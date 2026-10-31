// *Spec* under the card on the phone's hand (docs/decisions.md §180.3, §195.4, docs/specs/117 §3.4): the goal's way, straight on its Spec page (or, while no spec is written, on Talk, saying so). The arrows and the swipe along the goals are gone with
// spec 117 B (the hand's row is one card an entry: uprow.js); this button goes when the goal's way is the middle's (spec 117 D).
import { html } from "../html.js";
import { openOver } from "../frame/state.js";
import { phaseOf } from "../table/data.js";

/** *Spec* under the context: the goal's Spec page; *The spec is written after your answers* (opening Talk) while it is not decided. Nothing for a card of no goal. */
export function SpecButton({ idea }) {
  if (!idea || idea.startsWith("party:")) return null;
  const talk = phaseOf(idea) === "talk";
  const open = () => openOver(talk ? "talk" : "spec", { idea }, { title: "", key: "" }, talk ? "Talk" : "Spec");
  return html`<button type="button" class="ork-btn quiet up-spec" data-page=${talk ? "talk" : "spec"} onClick=${open}>${talk ? "The spec is written after your answers" : "Spec"}</button>`;
}
