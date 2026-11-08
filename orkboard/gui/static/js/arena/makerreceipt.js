// A maker's receipt and the cap stop's one-press way to its plate (spec 158 J).
import { html } from "../html.js";
import { closeOver, openInventory, openTab } from "../frame/state.js";
import { makerPlate } from "../table/stallstate.js";

export const money = (m) => m ? `${m.estimate ? "about " : ""}${m.amount} ${m.currency}` : "";

export function MakerReceipt({ maker }) {
  return maker?.cost && maker?.cap ? html`<p class="pick-receipt">Made by the ${maker.word} · ${money(maker.cost)} of a ${money(maker.cap)} cap</p>` : null;
}

export function MakerStop({ stop }) {
  if (!stop) return null;
  const open = () => {
    closeOver();
    openTab(stop.party);
    makerPlate.value = stop.tool;
    openInventory(stop.party);
  };
  return html`<div class="pick-receipt"><p>The next request costs ${money(stop.price)}; with ${money(stop.held)} already held, it would exceed the ${money(stop.cap)} cap.</p>
    <button type="button" class="ork-btn" onClick=${open}>Change the cap</button></div>`;
}
