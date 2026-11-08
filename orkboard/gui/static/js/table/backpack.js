// The backpack (docs/specs/157-the-inventory-a-merchants-stall.md D.1, decisions §267.1): at the left of the discard column's head (lane.js; under 760 px, small, at the tabs' end), spec 160 H, decisions §272.1: orkUI's `.ork-pack`, shut and `.is-open` while the stall is open
// (the pane then wears `.ork-leather`: pane.js); under 760 px (`small`) its word is in `aria-label` and `title` only. Pressed it opens the stall on the open tab's chair, or shuts it.
import { html, cls } from "../html.js";
import { closeInventory, inventory, openInventory } from "../frame/state.js";

export function Backpack({ small = false }) {
  const open = inventory.value !== null;
  const title = open ? "Close the inventory" : "Inventory: how the project is set";
  return html`<button type="button" class=${cls("stall-pack", { "is-open": open, "is-small": small })} data-backpack aria-pressed=${open ? "true" : "false"} title=${title} aria-label=${title}
    onClick=${() => (open ? closeInventory() : openInventory())}><span class=${cls("ork-pack", { "is-open": open, small })} aria-hidden="true"></span><span class="stall-pack__word">Inventory</span></button>`;
}
