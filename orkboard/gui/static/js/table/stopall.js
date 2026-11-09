// Stop all under the lamp's chain (docs/specs/168 A4, decisions §285.2, §283.7; before it the die's word, §284.4, §261.12): in the right column's head, **not the hand**, so it stays pressable while a card is lifted (the hand's row is `inert` then; §266.10 is kept).
// *Stop all* while an ork works (`halt`, door.js: it asks the host to stop every run), *Resume* once stopped (`resume`: the orks go back to work), nothing else. A host that does not send `stopped` and was halted keeps no word here: there is nothing to press.
import { html, cls } from "../html.js";
import { halt, resume, useOrks } from "./door.js";
import { RESUME, RESUME_WORDS, STOP, STOP_WORDS } from "../hand/playdie.js";

export function StopAll() {
  const orks = useOrks(), toResume = orks.resumable && orks.stopped;
  if (!toResume && !orks.running) return null;
  return html`<button type="button" class=${cls("rh-stop", { "is-resume": toResume })} aria-label=${toResume ? RESUME_WORDS : STOP_WORDS} title=${toResume ? RESUME_WORDS : STOP_WORDS} onClick=${toResume ? resume : halt}>${toResume ? RESUME : STOP}</button>`;
}
