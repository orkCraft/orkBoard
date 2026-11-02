// The squares of the card-field (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part A.2, decisions §206.1, docs/mockups/goal-card/): under the card's top a row of 44 x 44 squares, each with its caption under it (the label face):
// *Rune* (the goal's rune, large), *To* (the addressed leader's head, the Orkmaster's crown when none), *Type* (the type's sign, faint while the party chooses it) and *Files* (the file icon, the number of files attached at its corner). A square pressed
// opens its row of choices under it, one row open at a time (`fieldRow`): a radio group each (the arrows move in it and choose, Tab leaves it), Esc closes the row first and the card after, a press on the square again closes it.
//   Rune  the five runes (the elements are never named: *Rune 1* … *Rune 5*; the party's used ones faint but possible);
//   To    the Orkmaster's crown and the leaders' heads, their names under them; a leader chosen is the goal's address (what *@Tech* and the open tab give too), the crown is a general goal;
//   Type  the addressed party's goal types by their signs, their names under them; none to choose from until a party is named (*Name a party to choose its type*);
//   Files *From this computer* (pictures, as pasting takes them) and some files of the project (`files.find`, what the *@* list offers), taken as chips in the row of *Send*.
// While a row is open the words give it room (pluscard.js puts `has-row` on the card), so *Send* stays above the window's edge. Layout only (hand.css); every face is orkUI's.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { command } from "../link.js";
import { MAX_PICTURES } from "../board/pictures.js";
import { fieldFiles, fieldPhotos, fieldRow, fieldRune, fieldText, fieldTo, fieldType, withoutAddress } from "./state.js";

export const ELEMENTS = ["meadow", "ice", "dust", "void", "lava"];                  // realm/idea_element.py `ELEMENTS`: the order of the field's radios
const CROWN = { race: "peon", tier: "crown" };                                      // the Orkmaster's head, as the tabs draw it
const FILES_SHOWN = 5;                                                              // the project's files offered in the row (one row of them, with *From this computer*)
export const FILES_SAY = "Pictures from this computer, or a file of the project";

const ID = { rune: "hand-field-runes", to: "hand-field-to", type: "hand-field-type", files: "hand-field-files" };
const base = (path) => String(path || "").replace(/\/$/, "").split("/").pop();

/** Closes the open row and gives the focus back to its square (or the words when none). */
export function closeRow(then = "square") {
  const was = fieldRow.value;
  fieldRow.value = "";
  const field = document.querySelector(".hand-field");
  (then === "square" && was ? field?.querySelector(`[data-sq="${was}"]`) : field?.querySelector(".hand-field__text"))?.focus({ preventScroll: true });
}

/** One square: its button (a head, a sign, a rune or an icon) and its caption. */
function Square({ id, caption, label, faint = false, badge = 0, children }) {
  const open = fieldRow.value === id;
  return html`<div class="hand-sq"><button type="button" class=${cls("hand-sq__btn", { "hand-field__rune": id === "rune", "is-open": open, "is-faint": faint })} data-sq=${id} aria-label=${label} aria-expanded=${String(open)} aria-controls=${ID[id]}
    onClick=${() => { fieldRow.value = open ? "" : id; }}>${children}${badge > 0 && html`<span class="hand-sq__n">${badge}</span>`}</button><span class="hand-sq__cap">${caption}</span></div>`;
}

/** The row of squares. `runes`: pluscard.js `runesOf`; `address`: `addressNow()`; `parties`: the map's parties; `taken`: the type taken for this address, or null. */
export function Squares({ runes, address, parties, taken }) {
  const at = ELEMENTS.indexOf(runes.shown), who = address.party ? parties.find((g) => g.slug === address.party) : null, kinds = who?.types || [];
  const count = fieldPhotos.value.length + fieldFiles.value.length;
  return html`<div class="hand-field__squares" role="group" aria-label="Its choices">
    <${Square} id="rune" caption="Rune" label=${at >= 0 ? `Its rune: Rune ${at + 1}, change it` : "Its rune: none yet, choose one"}><${Elem} name=${runes.shown} big=${true} dim=${!runes.shown} /><//>
    <${Square} id="to" caption="To" label=${`To: ${address.name || "the Orkmaster"}, change it`}>${who?.head ? html`<${Head} race=${who.head.race} tier=${who.head.tier} />` : html`<${Head} race=${CROWN.race} tier=${CROWN.tier} />`}<//>
    <${Square} id="type" caption="Type" faint=${!taken} label=${taken ? `Its type: ${taken.name}, change it` : kinds.length ? "Its type: chosen by its party, change it" : "Its type: name a party to choose it"}><${Sign} name=${taken ? taken.sign : "feature"} big=${true} /><//>
    <${Square} id="files" caption="Files" badge=${count} label=${count ? `Files: ${count} attached, change them` : "Attach files"}><${Icon} name="file" /><//>
  </div>`;
}

/** The arrows in a row of radios (or of checkboxes): the focus moves, and `choose(i)` is called for a radio (the arrows choose too). Esc closes the row. */
function useRowKeys(choose) {
  return (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeRow(); return; }          // Esc closes the row first, the card after
    const forward = e.key === "ArrowRight" || e.key === "ArrowDown";
    if (!forward && e.key !== "ArrowLeft" && e.key !== "ArrowUp") return;
    const items = [...e.currentTarget.querySelectorAll(".hand-ch > button:not(:disabled)")];
    if (!items.length) return;
    e.preventDefault();
    e.stopPropagation();
    const now = items.findIndex((b) => b === document.activeElement), checked = items.findIndex((b) => b.getAttribute("aria-checked") === "true");
    const from = items[0].getAttribute("role") === "radio" ? checked : now, next = from < 0 ? (forward ? 0 : items.length - 1) : (from + (forward ? 1 : -1) + items.length) % items.length;
    items[next].focus({ preventScroll: true });
    if (choose && items[next].getAttribute("role") === "radio") choose(items[next]);
  };
}

/** One choice: a 40 x 40 button and its name under it. `checked`: null for a button that is not a radio. */
function Choice({ role = "radio", checked = null, label, name = "", used = false, off = false, tab = false, data = {}, onPick, children }) {
  return html`<div class="hand-ch"><button type="button" role=${role} class=${cls("hand-rune", { "is-used": used })} aria-checked=${checked === null ? undefined : String(checked)} aria-label=${label} disabled=${off} tabindex=${tab ? 0 : -1} ...${data} onClick=${onPick}>${children}</button>${name && html`<span class=${cls("hand-ch__cap", { "is-file": role === "checkbox" })} title=${role === "checkbox" ? label : undefined}>${name}</span>`}</div>`;
}

/** The five runes (decisions §187.3): the default checked until the person chooses, the used ones faint but possible. With no party addressed none is checked, and Tab enters on the first. */
function RuneRow({ runes }) {
  const row = useRef();
  useEffect(() => { row.current?.querySelector('[role=radio][tabindex="0"]')?.focus({ preventScroll: true }); }, []);       // opened by a press on the rune: the focus is in the row
  const keys = useRowKeys((b) => { fieldRune.value = b.dataset.rune; });
  return html`<div ref=${row} id=${ID.rune} class="hand-field__runes hand-field__choices" role="radiogroup" aria-label="Its rune" onKeyDown=${keys}>
    ${ELEMENTS.map((e, i) => html`<${Choice} key=${e} checked=${runes.shown === e} label=${`Rune ${i + 1}`} used=${runes.used.includes(e)} tab=${runes.shown ? runes.shown === e : i === 0} data=${{ "data-rune": e }}
      onPick=${() => { fieldRune.value = e; fieldRow.value = ""; }}><${Elem} name=${e} big=${true} /><//>`)}
  </div>`;
}

/** *To*: the Orkmaster's crown and the leaders' heads. A leader chosen is the address; if the text names another with *@*, the *@* goes (the choice is the person's last word). */
function ToRow({ address, parties }) {
  const row = useRef();
  useEffect(() => { row.current?.querySelector('[role=radio][tabindex="0"]')?.focus({ preventScroll: true }); }, []);
  const pick = (slug) => {
    if (address.by === "text") fieldText.value = withoutAddress(fieldText.value, address.name);
    fieldTo.value = slug;
    if (fieldType.value && fieldType.value.party !== (slug === "ork" ? "" : slug)) fieldType.value = null;     // a type belongs to its party
  };
  const keys = useRowKeys((b) => pick(b.dataset.to));
  return html`<div ref=${row} id=${ID.to} class="hand-field__choices" role="radiogroup" aria-label="To" onKeyDown=${keys}>
    <${Choice} checked=${!address.party} label="Orkmaster" name="Orkmaster" tab=${!address.party} data=${{ "data-to": "ork" }} onPick=${() => pick("ork")}><${Head} race=${CROWN.race} tier=${CROWN.tier} /><//>
    ${parties.map((g) => html`<${Choice} key=${g.slug} checked=${address.party === g.slug} label=${g.name} name=${g.name} tab=${address.party === g.slug} data=${{ "data-to": g.slug }} onPick=${() => pick(g.slug)}>${g.head && html`<${Head} race=${g.head.race} tier=${g.head.tier} />`}<//>`)}
  </div>`;
}

/** *Type*: the addressed party's types by their signs; pressing the one taken again leaves the choice to the party. */
function TypeRow({ address, parties, taken }) {
  const row = useRef(), kinds = address.party ? (parties.find((g) => g.slug === address.party)?.types || []) : [];
  useEffect(() => { row.current?.querySelector('[role=radio][tabindex="0"]')?.focus({ preventScroll: true }); }, []);
  const pick = (t) => { fieldType.value = taken?.id === t.id ? null : { id: t.id, name: t.name, sign: t.sign, party: address.party }; };
  const keys = useRowKeys((b) => { const t = kinds.find((x) => x.id === b.dataset.type); if (t && taken?.id !== t.id) fieldType.value = { id: t.id, name: t.name, sign: t.sign, party: address.party }; });
  if (!address.party) return html`<div id=${ID.type} class="hand-field__choices" role="group" aria-label="Its type"><span class="hand-field__say">Name a party to choose its type</span></div>`;
  return html`<div ref=${row} id=${ID.type} class="hand-field__choices" role="radiogroup" aria-label="Its type" onKeyDown=${keys}>
    ${kinds.length === 0 && html`<span class="hand-field__say">${address.name} chooses the type itself</span>`}
    ${kinds.map((t, i) => html`<${Choice} key=${t.id} checked=${taken?.id === t.id} label=${t.name} name=${t.name} tab=${taken ? taken.id === t.id : i === 0} data=${{ "data-type": t.id }} onPick=${() => pick(t)}><${Sign} name=${t.sign} big=${true} /><//>`)}
  </div>`;
}

/** *Files*: *From this computer* (a picture, `pick` opens the file box) and some files of the project. */
function FilesRow({ pick }) {
  const row = useRef(), [found, setFound] = useState([]), taken = fieldFiles.value, full = fieldPhotos.value.length >= MAX_PICTURES;
  useEffect(() => { row.current?.querySelector("button:not(:disabled)")?.focus({ preventScroll: true }); }, []);
  useEffect(() => {                                                                 // the project's files, as the @ list asks for them
    let live = true;
    command("files.find", { q: "", limit: FILES_SHOWN + 3 }, true).then((r) => { if (live) setFound((r?.entries || []).filter((f) => !f.dir).slice(0, FILES_SHOWN)); }).catch(() => {});
    return () => { live = false; };
  }, []);
  const toggle = (f) => { fieldFiles.value = taken.some((x) => x.path === f.path) ? taken.filter((x) => x.path !== f.path) : [...taken, { path: f.path, dir: !!f.dir }]; };
  const keys = useRowKeys(null);
  return html`<div ref=${row} id=${ID.files} class="hand-field__choices" role="group" aria-label="Files" onKeyDown=${keys}>
    <${Choice} role="button" label="From this computer" name="From this computer" off=${full} tab=${true} data=${{ "data-pick": "disk" }} onPick=${pick}><${Icon} name="file" /><//>
    ${found.map((f) => html`<${Choice} key=${f.path} role="checkbox" checked=${taken.some((x) => x.path === f.path)} label=${f.path} name=${base(f.path)} data=${{ "data-file": f.path }} onPick=${() => toggle(f)}><${Icon} name="file" /><//>`)}
  </div>`;
}

/** The open row under the squares, or nothing. `pick`: opens the box of pictures. */
export function Choices({ runes, address, parties, taken, pick }) {
  const open = fieldRow.value;
  if (!open) return null;
  return html`<div class="hand-field__row-open" data-open=${open}>
    ${open === "files" && html`<span class="hand-field__say">${FILES_SAY}</span>`}
    ${open === "rune" && html`<${RuneRow} runes=${runes} />`}
    ${open === "to" && html`<${ToRow} address=${address} parties=${parties} />`}
    ${open === "type" && html`<${TypeRow} address=${address} parties=${parties} taken=${taken} />`}
    ${open === "files" && html`<${FilesRow} pick=${pick} />`}
  </div>`;
}

/** The files taken, as chips for the row of *Send*: a picture with its thumbnail, a file of the project as a mark. */
export function FileChips() {
  const photos = fieldPhotos.value, files = fieldFiles.value;
  if (!photos.length && !files.length) return null;
  return html`<div class="hand-field__files">
    ${photos.map((url, i) => html`<span key=${`p${i}`} class="hand-pic"><img src=${url} alt=${`Picture ${i + 1}`} draggable="false" />
      <button type="button" class="ork-btn quiet hand-chip__off" aria-label=${`Remove picture ${i + 1}`} onClick=${() => { fieldPhotos.value = photos.filter((_, k) => k !== i); }}><${Icon} name="close" /></button></span>`)}
    ${files.map((f) => html`<span key=${f.path} class="ork-chip hand-chip hand-file" data-file=${f.path} title=${f.path}><${Icon} name="file" /><span class="hand-file__name">${base(f.path)}</span>
      <button type="button" class="ork-btn quiet hand-chip__off" aria-label=${`Take ${f.path} off`} onClick=${() => { fieldFiles.value = files.filter((x) => x.path !== f.path); }}><${Icon} name="close" /></button></span>`)}
  </div>`;
}
