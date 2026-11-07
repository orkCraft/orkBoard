// The backpack (docs/specs/157-the-inventory-a-merchants-stall.md D.1, decisions §267.1): at the tabs' end, before *New party*; shut, a pack with its flap down, open, its flap up and the pouch showing. Pixel art of rects in orkUI's ink tokens
// (the mockup's PACK_SHUT and PACK_OPEN; the letters are classes of stall.css), 40 x 40. Pressed it opens the stall on the open tab's chair, or shuts it.
import { html, cls } from "../html.js";
import { closeInventory, inventory, openInventory } from "../frame/state.js";

const BODY = [".X############X.", ".X#PPPP##PPPP#X.", ".X#P..P##P..P#X.", ".X#PPPP##PPPP#X.", ".X############X.", ".X############X.", "..XXXXXXXXXXXX..", "................"];
const SHUT = ["................", ".....XXXXXX.....", "....X......X....", "..XXXXXXXXXXXX..", ".X#FFFFFFFFFF#X.", ".X#F........F#X.", ".X#FFFFFoFFFF#X.", ".X#####oo#####X."].concat(BODY);
const OPEN = ["..FFFFFFFFFFFF..", "..F..........F..", "..FFFFFFoFFFFF..", "..XXXXXXXXXXXX..", ".X##CC###ii###X.", ".X##CC##iiii##X.", ".X##CC##iiii##X.", ".X############X."].concat(BODY);

function Art({ open }) {
  const cells = [];
  (open ? OPEN : SHUT).forEach((row, y) => [...row].forEach((ch, x) => { if (ch !== ".") cells.push(html`<rect key=${`${x}.${y}`} class=${`pk-${ch}`} x=${x} y=${y} width="1" height="1" />`); }));
  return html`<svg class="stall-pack__art" width="40" height="40" viewBox="0 0 16 16" aria-hidden="true" shape-rendering="crispEdges">${cells}</svg>`;
}

export function Backpack({ small = false }) {
  const open = inventory.value !== null;
  const title = open ? "Close the inventory" : "Inventory: how the project is set";
  return html`<button type="button" class=${cls("stall-pack", { "is-open": open, "is-small": small })} data-backpack aria-pressed=${open ? "true" : "false"} title=${title} aria-label=${title}
    onClick=${() => (open ? closeInventory() : openInventory())}><${Art} open=${open} /><span class="stall-pack__word">Inventory</span></button>`;
}
