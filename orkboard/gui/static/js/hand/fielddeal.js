// The new goal's corners deal their choices to the hand (docs/specs/168 D2, decisions §286.2): a corner pressed (its rune; its kind; who; *Now* or *Later*; the files) lays its choices as cards in the hand's row in the field's place, cut by the rim and rising when hovered
// as the ways are (answercards.js); one played, the field comes back with its words as they were (they are the field's signal: state.js `fieldText`). Esc, or the corner pressed again, brings the field back without a choice. Each choice keeps the attributes the old list's items had
// (`data-rune`, `data-type`, `data-to`, `data-go`), so the same things find them. Nothing here sends a command but *Now* and *Later*, which are the field's own `send`.
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon } from "../orkui.js";
import { CornerFoot, CornerTop } from "../table/corners.js";
import { fieldRow, fieldRune } from "./state.js";
import { ELEMENTS, Choices } from "./fieldsquares.js";
import { chooseTo, chooseType, kindsOf } from "./fieldcorners.js";
import { LATER, NOW, SLOT_KIND, SLOT_WHO } from "./openwords.js";

const CROWN = { race: "peon", tier: "crown" };                                      // the Orkmaster's head, as the tabs draw it
export const NOW_LINE = "The Orkmaster talks it over at once, as far as the limits allow.", LATER_LINE = "It lies in line and talks by itself at the hour the Board says.";      // the lexicon's `field_now_line` and `field_later_line`

/** The corner at the foot's right: *Now* (Enter sends it), pressed it deals *Now* and *Later*. */
export function GoCorner({ open }) {
  return html`<button type="button" class=${cls("hand-corner is-set", { "is-open": open })} data-corner="go" data-set="1" aria-label="Send it: Now or Later" aria-haspopup="true" aria-expanded=${String(open)}
    onClick=${() => { fieldRow.value = open ? "" : "go"; }}><span class="hand-corner__say">${NOW}</span><span class="hand-corner__car" aria-hidden="true">▾</span></button>`;
}

/** One dealt choice: a hand card of the ways' size, its face at the top (a rune, a sign or a head), its name and its line; `checked`: the one in force. */
function Deal({ name, line = "", label = name, checked = false, faint = false, off = false, data = {}, face = null, fig = null, onPick }) {
  return html`<button type="button" role="menuitemradio" class=${cls("ork-card hand-ans hand-deal", { "is-pick": checked, "is-faint": faint })} aria-checked=${String(checked)} aria-label=${label} title=${line || name} disabled=${off} ...${data} onClick=${onPick}>
    <${CornerTop} ...${face || {}} />
    ${fig && html`<span class="hand-deal__fig">${fig}</span>`}
    <span class="hand-ans__name">${name}</span>
    ${line && html`<span class="hand-ans__line">${line}</span>`}
    <${CornerFoot} who=${checked ? { heads: [], word: "now" } : null} />
  </button>`;
}

/** The choices of the corner `open` ("rune", "type", "to", "go", "files"), dealt in the field's place. Arrows move, Esc brings the field back and gives the focus to the corner; `runes`, `address`, `parties`, `taken`: the field's (pluscard.js); `send`: its send. */
export function Dealt({ open, runes, address, parties, taken, send, empty, pick, style = undefined }) {
  const root = useRef();
  useEffect(() => {                                                                 // dealt: the focus goes onto the choice in force
    const items = [...root.current?.querySelectorAll("[role=menuitemradio]") || []];
    (items.find((b) => b.getAttribute("aria-checked") === "true" && !b.disabled) || items.find((b) => !b.disabled) || root.current)?.focus({ preventScroll: true });
  }, [open]);
  const done = () => { fieldRow.value = ""; };
  const keys = (e) => {
    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      const was = fieldRow.value;
      done();
      setTimeout(() => document.querySelector(`.hand-field [data-corner="${was}"], .hand-field [data-sq="${was}"]`)?.focus({ preventScroll: true }), 0);
      return;
    }
    const down = e.key === "ArrowDown" || e.key === "ArrowRight", up = e.key === "ArrowUp" || e.key === "ArrowLeft";
    if (!down && !up) return;
    const items = [...root.current.querySelectorAll("[role=menuitemradio]:not(:disabled)")], now = items.indexOf(document.activeElement);
    if (!items.length) return;
    e.preventDefault();
    items[(now + (down ? 1 : -1) + items.length) % items.length]?.focus({ preventScroll: true });
  };
  let cards = null;
  if (open === "rune") {
    cards = ELEMENTS.map((e, i) => html`<${Deal} key=${e} name=${`Rune ${i + 1}`} label=${`Rune ${i + 1}`} checked=${runes.shown === e} faint=${runes.used.includes(e)} data=${{ "data-rune": e }} face=${{ rune: { name: e } }} fig=${html`<${Elem} name=${e} big=${true} />`}
      onPick=${() => { fieldRune.value = e; done(); }} />`);
  } else if (open === "type") {
    cards = [...kindsOf(parties, address).map((t) => html`<${Deal} key=${t.id} name=${t.name} line=${t.id === "bug" ? "The short way." : ""} checked=${taken?.id === t.id} data=${{ "data-type": t.id }} face=${{ kind: t.sign }} onPick=${() => { chooseType(t, address); done(); }} />`),
      html`<${Deal} key="read" name=${SLOT_KIND} checked=${!taken} data=${{ "data-type": "" }} face=${{ kindNode: html`<${Icon} name="close" />` }} onPick=${() => { chooseType(null, address); done(); }} />`];
  } else if (open === "to") {
    cards = [html`<${Deal} key="ork" name=${SLOT_WHO} checked=${!address.party} data=${{ "data-to": "ork" }} face=${{ kindNode: html`<${Head} race=${CROWN.race} tier=${CROWN.tier} />` }} onPick=${() => { chooseTo("ork", address, parties); done(); }} />`,
      ...parties.map((g) => html`<${Deal} key=${g.slug} name=${g.name} checked=${address.party === g.slug} data=${{ "data-to": g.slug }} face=${{ kindNode: g.head ? html`<${Head} race=${g.head.race} tier=${g.head.tier} /> ` : null }} onPick=${() => { chooseTo(g.slug, address, parties); done(); }} />`)];
  } else if (open === "go") {
    cards = [html`<${Deal} key="now" name=${NOW} line=${NOW_LINE} off=${empty} data=${{ "data-go": "now" }} face=${{ kind: "play" }} onPick=${() => send({ now: true })} />`,
      html`<${Deal} key="later" name=${LATER} line=${LATER_LINE} off=${empty} data=${{ "data-go": "later" }} face=${{ kind: "after" }} onPick=${() => send({ later: true })} />`];
  }
  if (open === "files") return html`<div ref=${root} class="hand-fieldbox hand-dealt is-files" role="group" aria-label="Files" style=${style} onKeyDown=${keys}><${Choices} pick=${pick} /></div>`;
  return html`<div ref=${root} class="hand-ways-row is-play hand-dealt" tabindex="-1" role="menu" aria-label=${open === "rune" ? "Its rune" : open === "type" ? "Its kind" : open === "to" ? "To" : "Send"} data-open=${open} onKeyDown=${keys}>
    <div class="hand-ways-cards">${cards}</div></div>`;
}
