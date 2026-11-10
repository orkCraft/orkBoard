// The inventory as slots (docs/specs/168 H1, decisions §283.30; the look: docs/mockups/table-template/ scenes `inventory` and `leader-inventory`, shots 13 to 15): the table while the backpack is open, on the desktop. **A row of slots**, each its
// chosen way as a big card, 144 x 202: its label over it, its picture (the owner's where orkUI has it, else its kind's sign), its way's name and what it does, the pips of its ways, a coin where a cheaper way exists, *as set* at its foot.
// The Orkmaster's chair has six (How deep, The build starts, The night, Lands in dev by itself, Push, Goals at once), a leader's its hero, its AI tool, its tier (for its own calls), its party's size and how it answers (spec 168 H4); under a leader's slots its seats (stallseats.js), and its makers (slotmakers.js).
// Pressed, a slot deals its ways to the hand (hand/slotdeal.js: `dealt`, frame/state.js); pressed again, it puts them back. A way played is written by `ideas.stall_take` and Undo, on the table's line (`SlotsLine`, in the pane's title),
// takes the old one back. The host's data and calls: stallstate.js; the faces: slotface.js; the sheet: slots.css. The narrow page and the phone keep the stall (stall.js).
import { useEffect } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { board } from "../board/store.js";
import { dealt, inventory } from "../frame/state.js";
import { Pips, SlotPic } from "./slotface.js";
import { Makers } from "./slotmakers.js";
import { readPictures } from "./slotpics.js";
import { StallSeats } from "./stallseats.js";
import { cardOf, load, receipt, reset, stall, undo } from "./stallstate.js";

export const COIN_TITLE = "A cheaper way exists";
export const AS_SET = "as set";

/** The slot a hand card says: its shelf of ways, or, for a card that has none (a hero with no choice), an empty one. */
export const shelfFor = (card, shelves) => shelves.find((x) => x.slot === card.slot) || { id: card.slot, slot: card.slot, label: card.label, sub: "", kind: "small", wares: [], at: -1, cheaper: false };

/** One slot: its label over its chosen way as a big card. `card`: what the slot carries (the host's `hand`), `shelf`: its ways. */
function SlotCard({ card, shelf, race }) {
  const at = Number.isInteger(shelf.at) ? shelf.at : shelf.wares.findIndex((w) => w.id === card.yours), w = at >= 0 ? shelf.wares[at] : null, on = dealt.value === shelf.slot;
  const fixed = !!card.fixed, still = !fixed && !shelf.wares.length, word = card.word || w?.word || "", line = card.line || w?.line || "";
  const press = () => { if (!fixed && !still) dealt.value = on ? "" : shelf.slot; };
  return html`<figure class="slot" data-slot-of=${shelf.slot}>
    <span class="ork-plaque slot-label">${shelf.label}</span>
    <button type="button" class=${cls("ork-card slot-card el-meadow", { "is-pressed": on, "is-fixed": fixed || still })} data-slot=${shelf.slot} data-way=${card.yours ?? ""} aria-pressed=${on ? "true" : "false"} aria-disabled=${fixed || still ? "true" : undefined}
        aria-label=${`${shelf.label}: ${word}${line ? `. ${line}` : ""}${shelf.cheaper ? `. ${COIN_TITLE}` : ""}`} title=${shelf.sub || undefined} onClick=${press}>
      <span class="slot-card__top"><${Pips} n=${shelf.wares.length} at=${at} />${shelf.cheaper && html`<span class="slot-card__coin" data-cheaper="1" title=${COIN_TITLE}><${Icon} name="coins" /></span>`}</span>
      <${SlotPic} slot=${shelf.slot} w=${w || { id: card.yours ?? "", head: card.head }} race=${race} />
      <span class="slot-card__name">${word}</span>
      <span class="slot-card__line">${line}</span>
      <span class="slot-card__foot">${fixed ? "fixed" : still ? "no choice" : AS_SET}</span>
    </button>
  </figure>`;
}

/** The inventory of the chair open (`inventory`: "" the Orkmaster's, a party's slug a leader's); `g` the leader's party, null for the Orkmaster's. */
export function Slots({ g = null }) {
  const chair = inventory.value ?? "", rev = board.value?.rev, s = stall.value && stall.value.chair === chair ? stall.value : null;
  useEffect(() => { load(chair); }, [chair, rev]);
  useEffect(() => { readPictures(); return reset; }, []);
  const race = g?.leader?.head?.race || "", shelves = s?.shelves || [], makers = shelves.filter((x) => x.kind === "makers");
  return html`<div class="slots-table" data-stall=${chair || "orkmaster"} data-slots=${chair || "orkmaster"}>
    ${!s ? html`<p class="slots-empty">The slots are being laid out…</p>` : html`
      <div class="slots" role="group" aria-label=${chair ? "Its slots" : "The project's slots"}>${(s.hand || []).map((c) => html`<${SlotCard} key=${c.slot} card=${c} shelf=${shelfFor(c, shelves)} race=${race} />`)}</div>`}
    ${g && chair && html`<${StallSeats} g=${g} />`}
    ${makers.map((x) => html`<${Makers} key=${x.id} shelf=${x} chair=${chair} />`)}
  </div>`;
}

/** The table's line (the pane's title row) after a way is played: what changed, and Undo, which takes the old way back. */
export function SlotsLine() {
  const r = receipt.value, chair = inventory.value ?? "";
  if (!r) return null;
  return html`<span class="slots-line" role="status" data-receipt>${r.text}${r.undo && html` <button type="button" class="ork-btn quiet" data-undo onClick=${() => undo(chair)}>Undo</button>`}</span>`;
}
