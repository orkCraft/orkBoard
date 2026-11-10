// A leader's seats and tools in its inventory (docs/specs/168 E1, decisions §283.16.2): what the leader's header showed (seats with their roles, each side's AI tool, the party's size) lies at the top of its stall, whole: a seat pressed opens its popover
// (seatpop.js), as it did in the header. Drawn only for a party's chair; the Orkmaster's has none. Reached from the party's … menu (*Seats and tools*, partymenu.js) and the backpack.
import { html } from "../html.js";
import { sizeTip, sizeWord } from "./data.js";
import { Squad } from "./header.js";

export function StallSeats({ g }) {
  const size = sizeWord(g);
  return html`<section class="stall-seats table-head" aria-label="Its seats and tools" data-seats=${g.slug}>
    <span class="ork-label stall-seats__label">Its seats</span>
    <${Squad} g=${g} from=${{ title: "Inventory", key: "" }} />
    ${size && html`<span class="ork-chip table-size" title=${sizeTip(g)}>${size}</span>`}
  </section>`;
}
