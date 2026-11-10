// The discard's two piles and the plates over them (docs/specs/168 F2, decisions §283.27), through the open tab's eyes (table/lane.js lays them): **the upper pile** is today's discard, goals in dev waiting for main, under its plate *main*; **the lower pile** is the goals done on
// their own branch and waiting for dev (hand/devcard.js `waitsForDev`), drawn only while *Lands in dev by itself* is off, under its plate *dev*. A plate says its branch's name in the pixel face (the project's `merge_into`, its release branch); pressed, the branches are dealt to the hand
// (hand/devplay.js `PlateDeal`: the lower pile any branch or a new one from dev, the upper main or dev; a card warns first when goals are at work), and the choice is the project's setting, never a view. A card of the lower pile pressed is played (devplay.js `LowerPlay`): its way
// *To dev*, in its menu *To dev without the tests*. No count of what waits. Layout only: plates.css.
import { html, cls } from "../html.js";
import { lower, playCard, playing } from "../frame/state.js";
import { lowerOf } from "../hand/data.js";
import { devName, lowerOn } from "../hand/devcard.js";
import { gateData } from "../shell/store.js";
import { DoneFace } from "./discard.js";

/** The word under the lower plate's cards and in a card's foot. */
const WAITS_DEV = (dev) => `Waiting for ${dev}`, PRESS = "Choose the branch";

/** The branch a plate stands for now: `dev` the project's work branch, `main` its release branch. */
export const branchOf = (which) => (which === "dev" ? devName() : gateData.value?.main || "main");

/** The plate over a pile: the branch's name; pressed (again: put away) it deals the branches. `on`: its branches are dealt now. */
export function Plate({ which }) {
  const name = branchOf(which), on = playing.value?.dev === "plate" && playing.value.which === which;
  const press = () => { if (on) lower(); else playCard({ dev: "plate", which }); };
  return html`<button type="button" class=${cls("ork-plaque discard-plate", { "is-on": on })} data-plate=${which} aria-expanded=${on ? "true" : "false"} aria-label=${`${which === "dev" ? WAITS_DEV(name) : `Sent to ${name}`}. ${PRESS}`} title=${PRESS} onClick=${press}>${name}</button>`;
}

/** The goals of the lower pile that the open tab's eyes hold (`held`: lane.js), the last one first; none while *Lands in dev by itself* is on. */
export const lowerHeld = (held) => (lowerOn() ? lowerOf().filter((g) => held(g.slug)) : []);

/** The lower pile: its plate and its cards, each pressed to be played. */
export function LowerPile({ goals }) {
  if (!goals.length) return null;
  const dev = devName(), now = playing.value?.dev === "card" ? playing.value.slug : "";
  return html`<section class="discard-pile" data-pile="lower" aria-label=${WAITS_DEV(dev)}><${Plate} which="dev" />
    <ul class="discard-pile__cards" aria-label=${WAITS_DEV(dev)}>${goals.map((g) => html`<li key=${g.slug}><${DoneFace} g=${g} picked=${now === g.slug} line=${WAITS_DEV(dev)} label=${`${g.full}, ${WAITS_DEV(dev).toLowerCase()}`}
      onPress=${() => { if (now === g.slug) lower(); else playCard({ dev: "card", slug: g.slug }); }} /></li>`)}</ul></section>`;
}
