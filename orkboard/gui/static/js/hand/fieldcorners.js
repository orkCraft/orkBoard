// The new goal's corners to pick (docs/specs/150 F.1, decisions §254.9, docs/mockups/table-edge/ section 6): the card-field's three choices are its corners, each a button. **Top left the rune** (the next given; pressed, the five runes, the elements never named:
// *Rune 1* … *Rune 5*, the party's used ones faint but possible), **top right the kind** (*the Orkmaster reads it* by default; pressed, the addressed party's goal types, or every party's with none addressed, and *the Orkmaster reads it*), **bottom left who** (the crowned head and
// *the Orkmaster routes it* by default; pressed, the leaders' heads: a leader picked addresses the goal as *@Tech* or the open tab do). A corner left to its default is dashed and says it (orkUI's `ork-btn` is not used: it is a corner's index, 22 px); a picked one is drawn whole.
// A press opens its few choices **on the card itself** (a small list, `.hand-pick`, no dialog; `fieldRow` says which: "rune", "type" or "to"): the arrows move in it, Enter or a press chooses, Esc closes it and gives the focus back to its corner, a press on the corner again closes it too.
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { fieldRow, fieldRune, fieldText, fieldTo, fieldType, withoutAddress } from "./state.js";
import { ELEMENTS, RuneRow } from "./fieldsquares.js";
import { SLOT_KIND, SLOT_RUNE, SLOT_WHO } from "./openwords.js";

const CROWN = { race: "peon", tier: "crown" };                                      // the Orkmaster's head, as the tabs draw it
const KIND_ROW = "type";                                                           // the kind's row in `fieldRow` (the field's `type` of `ideas.add`)

/** Every goal type the parties offer, once each, in the order the parties give them (a goal addressed to no one: the kind is read against the party it is routed to). */
export function kindsOf(parties, address) {
  if (address.party) return parties.find((g) => g.slug === address.party)?.types || [];
  const seen = new Map();
  for (const g of parties) for (const t of g.types || []) if (!seen.has(t.id)) seen.set(t.id, t);
  return [...seen.values()];
}

/** One corner: a button, dashed while it holds its default (`set` false), whole once picked. */
function Pick({ id, set, label, open, children }) {
  return html`<button type="button" class=${cls("hand-corner", { "hand-field__rune": id === "rune", "is-set": set, "is-open": open })} data-corner=${id} data-set=${set ? "1" : "0"} aria-label=${label} aria-haspopup="true" aria-expanded=${String(open)}
    onClick=${() => { fieldRow.value = open ? "" : id; }}>${children}<span class="hand-corner__car" aria-hidden="true">${id === "to" ? "▴" : "▾"}</span></button>`;
}

/** Top left: the rune. `runes`: pluscard.js `runesOf`. */
export function RuneCorner({ runes }) {
  const open = fieldRow.value === "rune", set = !!fieldRune.value && fieldRune.value !== runes.base, at = ELEMENTS.indexOf(runes.shown);
  return html`<${Pick} id="rune" set=${set} open=${open} label=${at >= 0 ? `Its rune: Rune ${at + 1}, change it` : "Its rune: none yet, choose one"}>${runes.shown ? html`<${Elem} name=${runes.shown} hue=${runes.hue} />` : html`<span class="hand-corner__say" data-slot="rune">${SLOT_RUNE}</span>`}<//>`;
}

/** Top right: the kind. `taken`: the type taken for this address, or null. */
export function KindCorner({ taken }) {
  const open = fieldRow.value === KIND_ROW;
  return html`<${Pick} id=${KIND_ROW} set=${!!taken} open=${open} label=${taken ? `Its kind: ${taken.name}, change it` : "Its kind: the Orkmaster reads it, change it"}>${taken ? html`<${Sign} name=${taken.sign} /><span class="hand-corner__say">${taken.name}</span>` : html`<span class="hand-corner__say" data-slot="kind">${SLOT_KIND}</span>`}<//>`;
}

/** Bottom left: who. `who`: the addressed party (`partyCard` and its types) or null. */
export function WhoCorner({ who, address }) {
  const open = fieldRow.value === "to";
  return html`<${Pick} id="to" set=${!!who} open=${open} label=${`To: ${address.name || "the Orkmaster"}, change it`}>${who?.head ? html`<${Head} race=${who.head.race} tier=${who.head.tier} />` : html`<${Head} race=${CROWN.race} tier=${CROWN.tier} />`}<span class="hand-corner__say" data-slot=${who ? undefined : "who"}>${who ? address.name : SLOT_WHO}</span><//>`;
}

/** Closes the open list and gives the focus back to its corner (the words when `to` is "text"). */
function closeList(to = "corner") {
  const was = fieldRow.value;
  fieldRow.value = "";
  const field = document.querySelector(".hand-field");
  (to === "corner" && was ? field?.querySelector(`[data-corner="${was}"]`) : field?.querySelector(".hand-field__text"))?.focus({ preventScroll: true });
}

/** One item of a list: its face, its word and a note; `checked` marks the one in force. */
function Item({ checked, label, note = "", faint = false, data = {}, onPick, children }) {
  return html`<button type="button" role="menuitemradio" class=${cls("hand-pick__item", { "is-checked": checked, "is-faint": faint })} aria-checked=${String(checked)} aria-label=${label} tabindex=${checked ? 0 : -1} ...${data} onClick=${onPick}>
    <span class="hand-pick__face">${children}</span><span class="hand-pick__word">${label}</span>${note && html`<small class="hand-pick__note">${note}</small>`}${checked && html`<${Sign} name="check" />`}</button>`;
}

/** The list a corner opens, on the card: under the two top corners, over the foot's one. `open`: "rune", "type" or "to". */
export function CornerList({ open, runes, address, parties, taken }) {
  const root = useRef();
  useEffect(() => {                                                                 // opened: the focus goes into the list, on the item in force
    const items = [...root.current?.querySelectorAll("[role=menuitemradio]") || []];
    (items.find((b) => b.getAttribute("aria-checked") === "true") || items[0])?.focus({ preventScroll: true });
  }, [open]);
  const keys = (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeList(); return; }                // Esc closes the list first, the card after
    const down = e.key === "ArrowDown" || e.key === "ArrowRight", up = e.key === "ArrowUp" || e.key === "ArrowLeft";
    if (!down && !up && e.key !== "Home" && e.key !== "End") return;
    const items = [...e.currentTarget.querySelectorAll("[role=menuitemradio]")], now = items.indexOf(document.activeElement);
    e.preventDefault();
    e.stopPropagation();
    items[e.key === "Home" ? 0 : e.key === "End" ? items.length - 1 : (now + (down ? 1 : -1) + items.length) % items.length]?.focus({ preventScroll: true });
  };
  const done = () => closeList();
  let items = null;
  if (open === "rune") {
    return html`<div class="hand-pick hand-pick--rune" data-open="rune"><${RuneRow} runes=${runes} /></div>`;                 // the five runes, a row of radios (fieldsquares.js): arrows move and choose, Esc closes
  } else if (open === KIND_ROW) {
    const kinds = kindsOf(parties, address);
    items = [
      ...kinds.map((t) => html`<${Item} key=${t.id} checked=${taken?.id === t.id} label=${t.name} note=${t.id === "bug" ? "the short way" : ""} data=${{ "data-type": t.id }}
        onPick=${() => { fieldType.value = { id: t.id, name: t.name, sign: t.sign, party: address.party }; done(); }}><${Sign} name=${t.sign} /><//>`),
      html`<${Item} key="read" checked=${!taken} label=${SLOT_KIND} note="default" data=${{ "data-type": "" }} onPick=${() => { fieldType.value = null; done(); }}><${Icon} name="close" /><//>`,
    ];
  } else if (open === "to") {
    const pick = (slug) => {
      if (address.by === "text") fieldText.value = withoutAddress(fieldText.value, address.name);
      fieldTo.value = slug;
      const to = parties.find((g) => g.slug === slug);
      if (fieldType.value && fieldType.value.party !== (slug === "ork" ? "" : slug)) {                 // a type belongs to its party: it stays when the one chosen offers it too
        const same = to?.types?.find((t) => t.id === fieldType.value.id);
        fieldType.value = same ? { id: same.id, name: same.name, sign: same.sign, party: slug } : null;
      }
      done();
    };
    items = [
      html`<${Item} key="ork" checked=${!address.party} label=${SLOT_WHO} note="default" data=${{ "data-to": "ork" }} onPick=${() => pick("ork")}><${Head} race=${CROWN.race} tier=${CROWN.tier} /><//>`,
      ...parties.map((g) => html`<${Item} key=${g.slug} checked=${address.party === g.slug} label=${g.name} data=${{ "data-to": g.slug }} onPick=${() => pick(g.slug)}>${g.head && html`<${Head} race=${g.head.race} tier=${g.head.tier} />`}<//>`),
    ];
  }
  return html`<div ref=${root} class=${cls("hand-pick", `hand-pick--${open}`)} role="menu" aria-label=${open === "rune" ? "Its rune" : open === KIND_ROW ? "Its kind" : "To"} data-open=${open} onKeyDown=${keys}>${items}</div>`;
}
