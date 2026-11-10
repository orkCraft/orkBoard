// A slot's ways dealt to the hand (docs/specs/168 H1, decisions §283.30; the look: docs/mockups/table-template/ shots 13 to 15, D1's way of playing: handplace.js, answercards.js): the slot pressed on the table (table/slots.js, `dealt`) rises
// out of the table as the 144 x 202 card it is, at the table's foot at the left, and its ways lie in the hand's row from the same left edge, cut by the hand's rim and rising when hovered (hand/openedcard.css). Each way is a card of the same size:
// its picture (the owner's where orkUI has it, else its kind's sign), its name (the pixel face), what it does (the body face, whole), its price in its bottom right (what the host says: lighter, heavier, same cost, a share of the week, money),
// *Yours* at its top left for the way carried, *Yours before* for the one carried before the last take, *Default* for the slot's default, a star for the Orkmaster's pick. A way pressed is written (`ideas.stall_take`) and the ways go back;
// *Put it back* and Esc send nothing. *Undo* is on the table's line (table/slots.js `SlotsLine`). A way the host says is not here is shown dimmed and presses nothing. The rest of the hand sinks (hand.js), its places stay. Wide only.
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { dealt, inventory } from "../frame/state.js";
import { partiesNow } from "../table/data.js";
import { CornerFoot, CornerTop } from "../table/corners.js";
import { SlotPic, priceWords } from "../table/slotface.js";
import { cardOf, pointAt, shelfOf, take } from "../table/stallstate.js";
import { usePlace } from "./handplace.js";

const ORKMASTER = { race: "peon", tier: "crown" };
export const MARK = { yours: "Yours", before: "Yours before", default: "Default" }, PICK = "The Orkmaster's pick";

/** The marks a way wears at its top left: what is carried, what was carried before, the default; in that order. */
export const marksOf = (w) => [w.price?.mine && MARK.yours, w.before && !w.price?.mine && MARK.before, w.default && MARK.default].filter(Boolean);

function WayCard({ shelf, w, race, run }) {
  const marks = marksOf(w), cost = priceWords(w.price), locked = !!w.price?.locked, mine = !!w.price?.mine, star = !!w.star;
  const star_node = star ? html`<span class="ork-sign pick slot-way__star" role="img" aria-label=${PICK} title=${PICK}></span>` : null;
  return html`<button type="button" class=${cls("ork-card hand-ans slot-way el-meadow", { "is-yours": mine, "is-pick": star, "is-locked": locked })} data-way=${w.id} data-slot=${shelf.slot} data-yours=${mine ? "1" : undefined} data-before=${w.before && !mine ? "1" : undefined}
      data-default=${w.default ? "1" : undefined} data-pick=${star ? "1" : undefined} aria-disabled=${locked || mine ? "true" : undefined} aria-label=${`${shelf.label}: ${w.word}${marks.length ? `, ${marks.join(", ").toLowerCase()}` : ""}${star ? `, ${PICK.toLowerCase()}` : ""}. ${w.line || ""}${cost ? ` ${locked ? cost.why : cost.text}` : ""}`}
      title=${locked ? cost.why : w.line || undefined} onClick=${() => { if (!locked && !mine) run(w); }} onMouseEnter=${() => pointAt(shelf.slot, w.id, w.price)} onMouseLeave=${() => pointAt(null)} onFocus=${() => pointAt(shelf.slot, w.id, w.price)} onBlur=${() => pointAt(null)}>
    <${CornerTop} name=${marks.join(" · ")} kindNode=${star_node} />
    <${SlotPic} slot=${shelf.slot} w=${w} race=${race} />
    <span class="hand-ans__name">${w.word}</span>
    <span class="hand-ans__line">${w.line}</span>
    <${CornerFoot} muchNode=${cost ? html`<span class=${cls("corner__much slot-price", `is-${cost.kind}`)} data-price=${cost.kind}>${cost.text}</span>` : null} />
  </button>`;
}

/** The slot pressed: its card risen, its ways in the hand's row, *Put it back*. */
export function SlotDeal() {
  const box = useRef(), row = useRef(), slot = dealt.value, chair = inventory.value ?? "", shelf = shelfOf(slot), card = cardOf(slot);
  const g = partiesNow().find((x) => x.slug === chair), race = g?.leader?.head?.race || "";
  const at = usePlace(box, row, [slot, shelf?.wares.length]);                    // the card and the ways from the table's left edge; the ways cut by the hand's rim
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, [slot]);
  useEffect(() => () => {                                                      // put back: the focus goes back to the slot it came from
    setTimeout(() => { const back = document.querySelector(`.slots [data-slot="${CSS.escape(slot)}"]`); if (back && !document.querySelector(".slot-deal")) back.focus({ preventScroll: true }); }, 0);
    pointAt(null);
  }, [slot]);
  useEffect(() => {                                                            // Esc puts them back (a dialog's Esc is its own: frame/state.js leaves it)
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); dealt.value = ""; } };
    addEventListener("keydown", esc);
    return () => removeEventListener("keydown", esc);
  }, []);
  if (!shelf) return null;
  const back = () => { dealt.value = ""; };
  const run = async (w) => { if (await take(chair, slot, w.id)) back(); };
  const way = shelf.wares.find((w) => w.price?.mine) || null, word = card?.word || way?.word || "", line = card?.line || way?.line || "";
  return html`<aside ref=${box} class="ork-card hand-card hand-card--stop hand-card--face hand-lifted hand-lifted--asked asks is-play slot-deal el-meadow" role="dialog" tabindex="-1" aria-label=${`Lifted: ${shelf.label}`} data-slot-deal=${slot} style=${at ? `left:${at.left}px` : undefined}>
    <${CornerTop} kindNode=${html`<${Sign} name="tune" />`} signal="alert" />
    <span class="hand-card__name" title=${shelf.label}>${shelf.label}</span>
    <span class="hand-card__foot">${shelf.sub || line}</span>
    <${CornerFoot} who=${{ heads: [ORKMASTER], word: "" }} muchNode=${word ? html`<span class="corner__much slot-price is-same" data-now="1">${word}</span>` : null} />
  </aside>
  <div ref=${row} class="hand-ways-row is-play slot-ways" role="group" aria-label=${`${shelf.label}: its ways`} data-slot-ways=${slot}>
    <div class="hand-ways-cards">
      ${shelf.wares.map((w) => html`<${WayCard} key=${w.id} shelf=${shelf} w=${w} race=${race} run=${run} />`)}
    </div>
    <div class="hand-ways-acts">
      <button type="button" class="ork-btn hand-put" data-act="put" onClick=${back}>Put it back</button>
    </div>
  </div>`;
}
