// The discard takes a card of what you carry (docs/specs/157-the-inventory-a-merchants-stall.md D.4, decisions §267.1): while the inventory is open, a card of the hand dropped on the discard (the lane at the wide width, the pile at the
// narrow) goes back to its default, as on the merchant's service. HTML drag and drop, as the potions' order (hand/mana.js `useDragOrder`); with the inventory shut it adds nothing, and nothing else on the discard changes.
import { inventory } from "../frame/state.js";
import { cardOf, dragging, giveBack } from "./stallstate.js";

/** The drop handlers of a discard's element, or none while the stall is shut. */
export function backDrop() {
  if (inventory.value === null) return {};
  const off = (e) => e.currentTarget.classList.remove("is-over");
  return {
    onDragOver: (e) => { if (dragging.peek()) { e.preventDefault(); e.currentTarget.classList.add("is-over"); } },
    onDragLeave: (e) => { if (!e.currentTarget.contains(e.relatedTarget)) off(e); },
    onDrop: (e) => {
      e.preventDefault();
      off(e);
      const slot = dragging.peek() || e.dataTransfer?.getData("text/plain");
      if (slot && cardOf(slot)) giveBack(inventory.peek(), slot);
    },
  };
}
