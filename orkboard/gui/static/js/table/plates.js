// The discard's two piles and the plates over them (docs/specs/168 F2, decisions §283.27), through the open tab's eyes (table/lane.js lays them): **the upper pile** is today's discard, goals in dev waiting for main, under its plate *main*; **the lower pile** is the goals done on
// their own branch and waiting for dev (hand/devcard.js `waitsForDev`), drawn only while *Lands in dev by itself* is off, under its plate *dev*. A plate says its branch's name in the pixel face (the project's `merge_into`, its release branch); pressed, the branches are dealt to the hand
// (hand/devplay.js `PlateDeal`: the lower pile any branch or a new one from dev, the upper main or dev; a card warns first when goals are at work), and the choice is the project's setting, never a view. A card of the lower pile pressed is played (devplay.js `LowerPlay`): its way
// *To dev*, in its menu *To dev without the tests*. No count of what waits. Layout only: plates.css.
import { html, cls } from "../html.js";
import { lower, playCard, playing } from "../frame/state.js";
import { lowerOf } from "../hand/data.js";
import { devName, lowerOn } from "../hand/devcard.js";
import { gateData } from "../shell/store.js";
import { Icon } from "../orkui.js";

/** The word under the lower plate's cards and in a card's foot. */
const WAITS_DEV = (dev) => `Waiting for ${dev}`, PRESS = "Choose the branch";
export const PLATE_WORDS = { main: "done in dev · waits for main", dev: "done · waits for dev" };      // the words under a plate (no count: decisions §293.4)

/** The branch a plate stands for now: `dev` the project's work branch, `main` its release branch. */
export const branchOf = (which) => (which === "dev" ? devName() : gateData.value?.main || "main");

/** The plate over a pile: the branch's name; pressed (again: put away) it deals the branches. `on`: its branches are dealt now. */
export function Plate({ which }) {
  const name = branchOf(which), on = playing.value?.dev === "plate" && playing.value.which === which;
  const press = () => { if (on) lower(); else playCard({ dev: "plate", which }); };
  return html`<button type="button" class=${cls("ork-plaque discard-plate", { "is-on": on })} data-plate=${which} aria-expanded=${on ? "true" : "false"} aria-label=${`${which === "dev" ? WAITS_DEV(name) : `Sent to ${name}`}. ${PRESS}`} title=${PRESS} onClick=${press}><${Icon} name="git-merge" /><span>${name}</span></button>`;
}

/** The goals of the lower pile that the open tab's eyes hold (`held`: lane.js), the last one first; none while *Lands in dev by itself* is on. */
export const lowerHeld = (held) => (lowerOn() ? lowerOf().filter((g) => held(g.slug)) : []);

