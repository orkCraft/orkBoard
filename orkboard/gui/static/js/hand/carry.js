// What you carry (docs/specs/157-the-inventory-a-merchants-stall.md D.3–D.4, decisions §267.1): while the inventory is open the hand is this and not the stacks: a card a slot of `stall.hand` (the slot's label, its word, its line), fanned
// as the stacks fan, in the mockup's look (docs/mockups/merchant/). A card pressed is lifted (the service takes it back to its default); dragged, it can be dropped on the service or on the discard (table/stalldrop.js). A ware hovered
// on the rug shows in its card as a ghost (dashed), the card's own words laid aside. Layout and look: carry.css.
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { carried, inventory } from "../frame/state.js";
import { partiesNow } from "../table/data.js";
import { Mark } from "../table/stallfaces.js";
import { dragging, hover, stall, wareOf } from "../table/stallstate.js";

if (typeof document !== "undefined") {
  const href = new URL("./carry.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** One card: the slot's label, what it carries (or the ware hovered, as a ghost), its line. */
function Card({ c, i, n, race, ghost }) {
  const mid = (n - 1) / 2, on = carried.value === c.slot;
  const word = ghost ? ghost.word : c.word, line = ghost ? ghost.line : c.line, head = ghost ? ghost.head || c.head : c.head, id = ghost ? ghost.id : c.yours;
  const press = () => { if (!c.fixed) carried.value = on ? "" : c.slot; };
  return html`<div class=${cls("carry-card", { "is-on": on, "is-fixed": c.fixed, "is-ghost": !!ghost })} data-slot=${c.slot} role="button" tabindex="0" aria-pressed=${on ? "true" : "false"} aria-label=${`${c.label}: ${word}`}
      draggable=${c.fixed ? undefined : "true"} style=${`--i:${i};--rot:${((i - mid) * 1.4).toFixed(2)};--dy:${(Math.abs(i - mid) * 2.5).toFixed(1)};--z:${i + 1}`}
      onClick=${press} onKeyDown=${(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); press(); } }}
      onDragStart=${(e) => { dragging.value = c.slot; e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", c.slot); }} onDragEnd=${() => { dragging.value = ""; }}>
    <div class="carry-card__idx">${head ? html`<${Head} race=${head.race} tier=${head.tier} />` : html`<${Mark} slot=${c.slot} id=${id} race=${race} />`}</div>
    <div class="carry-card__body"><span class="carry-card__what">${c.label}</span><span class="carry-card__val">${word}</span>${line && html`<span class="carry-card__line">${line}</span>`}
      ${c.fixed && html`<span class="carry-card__mark">the project's own</span>`}</div>
  </div>`;
}

export function Carry() {
  const chair = inventory.value ?? "", s = stall.value && stall.value.chair === chair ? stall.value : null, g = partiesNow().find((x) => x.slug === chair), race = g?.leader?.head?.race;
  const h = hover.value, ware = h && s ? wareOf(h.slot, h.id) : null, n = s?.hand.length || 0;
  const whose = chair === "" ? "the whole project" : s?.whose || g?.title || "";
  return html`<div class="carry" data-carry=${chair || "orkmaster"}>
    <p class="carry__lab"><b>Your hand</b>what you carry of ${whose}</p>
    <div class="carry__fan" style=${`--step:min(122px, calc((100cqw - 112px) / ${Math.max(1, n - 1)}))`}>
      ${s && s.hand.map((c, i) => html`<${Card} key=${c.slot} c=${c} i=${i} n=${n} race=${race} ghost=${ware && ware.slot === c.slot && !ware.price?.mine && !ware.price?.locked ? ware : null} />`)}
      ${s && !n && html`<span class="carry__none">Nothing of this chair is in your hand.</span>`}
    </div>
  </div>`;
}
