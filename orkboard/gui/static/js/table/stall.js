// The stall (docs/specs/157-the-inventory-a-merchants-stall.md D.2–D.4, decisions §267.1; the look is docs/mockups/merchant/): the table while the inventory is open. The Orkmaster stands at the rug's left, crowned, and says in a line what it
// would take; every ware of the chair lies on the rug at once (a leader's heroes on the top shelf, the small things below; the Orkmaster's own wares), a price plate under each; *Back to default* is its service at its feet. What you
// carry is the hand's (hand/carry.js). Pressed, a ware flies into the hand over the card it replaces (a clone, `--ork-motion-play`, none under reduced motion) and `ideas.stall_take` is sent; the receipt under the table says what
// changed, with Undo. Layout and look: stall.css; the host's data and calls: stallstate.js; the faces: stallfaces.js.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { board } from "../board/store.js";
import { carried, inventory } from "../frame/state.js";
import { HeroFace, Relic, Plate } from "./stallfaces.js";
import { cardOf, dragging, giveBack, hover, load, pleased, pointAt, receipt, reset, service, stall, take, undo, wareOf } from "./stallstate.js";

if (typeof document !== "undefined") {
  const href = new URL("./stall.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const still = () => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/** A ware pressed flies into the hand over the card it replaces: its face cloned, carried over, thinned. Nothing moves under reduced motion; the take is sent either way. */
export function fly(from, slot) {
  const to = document.querySelector(`.carry-card[data-slot="${CSS.escape(slot)}"]`);
  if (!from || !to || still() || !from.animate) return;
  const r = from.getBoundingClientRect(), t = to.getBoundingClientRect(), cl = from.cloneNode(true), k = Math.min(t.width / r.width, t.height / r.height);
  const style = getComputedStyle(document.documentElement), ms = parseFloat(style.getPropertyValue("--ork-motion-play")) || 400, ease = style.getPropertyValue("--ork-motion-ease").trim() || "ease-out";
  cl.classList.add("stall-flying");
  Object.assign(cl.style, { left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px`, transformOrigin: "0 0" });
  document.body.appendChild(cl);
  const gone = () => cl.remove();
  cl.animate([{ transform: "none" }, { transform: `translate(${t.left - r.left}px, ${t.top - r.top - 40}px) scale(${(1 + k) / 2})`, offset: 0.6 }, { transform: `translate(${t.left - r.left}px, ${t.top - r.top}px) scale(${k})`, opacity: 0.4 }],
    { duration: ms, easing: ease }).onfinish = gone;
  setTimeout(gone, ms + 200);
}

function Ware({ shelf, w, chair, head }) {
  const mine = !!w.price?.mine, locked = !!w.price?.locked, heroes = shelf.kind === "heroes", on = hover.value?.slot === shelf.slot && hover.value?.id === w.id;
  const press = (e) => {
    if (mine || locked) return;
    fly(e.currentTarget.querySelector(".stall-face"), shelf.slot);
    pointAt(null);
    take(chair, shelf.slot, w.id);
  };
  const point = () => pointAt(mine || locked ? null : shelf.slot, w.id, w.price), leave = () => pointAt(null);
  return html`<div class=${cls("stall-ware", { "is-mine": mine, "is-locked": locked, "is-on": on })} data-ware=${w.id} data-slot=${shelf.slot} onMouseEnter=${point} onMouseLeave=${leave} onFocusIn=${point} onFocusOut=${leave}>
    <button type="button" class="stall-ware__press" aria-disabled=${mine || locked ? "true" : undefined} title=${locked ? w.price.locked : w.line || undefined} aria-label=${`${shelf.label}: ${w.word}`} onClick=${press}>
      ${heroes ? html`<${HeroFace} w=${w} fallback=${head} />` : html`<${Relic} w=${w} slot=${shelf.slot} race=${head?.race} />`}
    </button>
    <${Plate} price=${w.price} />
    ${w.before && !mine && html`<small class="stall-ware__before">Yours before</small>`}
  </div>`;
}

function Shelf({ shelf, chair, head }) {
  return html`<div class=${cls(`stall-shelf is-${shelf.kind}`, { "is-on": carried.value === shelf.slot })} data-shelf=${shelf.slot}>
    <p class="stall-shelf__lab"><b>${shelf.label}</b>${shelf.sub}</p>
    <div class="stall-wares">${shelf.wares.map((w) => html`<${Ware} key=${w.id} shelf=${shelf} w=${w} chair=${chair} head=${head} />`)}</div>
  </div>`;
}

/** The merchant's service at his feet: *Back to default*, free. A card of the hand dropped on it, or the service pressed with a card lifted, writes the slot's default. */
function Service({ chair }) {
  const [over, setOver] = useState(false), lifted = carried.value;
  const drop = (e) => { e.preventDefault(); setOver(false); const slot = dragging.peek() || e.dataTransfer?.getData("text/plain"); if (slot && cardOf(slot)) giveBack(chair, slot); };
  const press = () => { if (lifted) giveBack(chair, lifted); else service.value = "Lift a card of your hand first, or drop one here: it goes back to its default, for nothing."; };
  return html`<button type="button" class=${cls("stall-service", { "is-can": !!lifted, "is-over": over })} data-service="back" title="Back to default: free" onClick=${press}
      onDragOver=${(e) => { if (dragging.peek()) { e.preventDefault(); setOver(true); } }} onDragLeave=${() => setOver(false)} onDrop=${drop}>
    <span class="stall-service__card"><span><b>Back to default</b>drop a card of your hand here, or press it with one lifted</span></span>
    <span class="stall-price is-same">free</span>
  </button>`;
}

export function Stall({ g = null }) {
  const chair = inventory.value ?? "", rev = board.value?.rev, s = stall.value && stall.value.chair === chair ? stall.value : null, [mood, setMood] = useState("");
  useEffect(() => { load(chair); }, [chair, rev]);
  useEffect(() => reset, []);
  const gone = pleased.value;
  useEffect(() => {
    if (!gone) return undefined;
    setMood("pleased");
    const t = setTimeout(() => setMood(""), 1800);
    return () => clearTimeout(t);
  }, [gone]);
  const on = hover.value, ware = on && s ? wareOf(on.slot, on.id) : null;
  const face = mood || (ware && (ware.price?.share ?? 0) >= 2 ? "worried" : carried.value || ware ? "focused" : "");
  const said = service.value || (ware ? `${ware.word}: ${ware.line}` : s?.say || "");
  const head = g?.leader?.head ? { race: g.leader.head.race, tier: "elder" } : null;
  const heroes = (s?.shelves || []).filter((x) => x.kind === "heroes"), small = (s?.shelves || []).filter((x) => x.kind !== "heroes");
  const r = receipt.value;
  return html`<div class="stall" data-stall=${chair || "orkmaster"} data-mood=${face || undefined}>
    <p class="stall-bubble" aria-live="polite">${said}</p>
    <div class="stall-merchant">
      <div class="stall-merchant__who"><${Head} race="peon" tier="crown" size="big" mood=${face} /></div>
      <span class="stall-merchant__name">Orkmaster</span><span class="stall-merchant__role">lays out the wares</span>
      <${Service} chair=${chair} />
    </div>
    <div class="stall-rug" data-rug=${chair || "orkmaster"}>
      <span class="stall-rug__weave"></span>
      ${!s ? html`<p class="stall-empty">The wares are being laid out…</p>` : html`
        ${heroes.map((x) => html`<${Shelf} key=${x.id} shelf=${x} chair=${chair} head=${head} />`)}
        ${small.length > 0 && html`<div class=${cls("stall-low", { "is-solo": !heroes.length })}>${small.map((x) => html`<${Shelf} key=${x.id} shelf=${x} chair=${chair} head=${head} />`)}</div>`}`}
    </div>
    <p class="stall-receipt" role="status" data-receipt>${r && html`${r.text}${r.undo && html` <button type="button" class="ork-btn quiet" data-undo onClick=${() => undo(chair)}>Undo</button>`}`}</p>
  </div>`;
}
