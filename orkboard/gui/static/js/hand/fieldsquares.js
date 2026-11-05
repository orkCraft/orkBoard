// The one square of the card-field that is left (docs/specs/150 F.1, decisions §254.9; before: docs/specs/128 A.2, §206.1): the rune, the kind (type) and who moved into the card's corners (fieldcorners.js), *Files* stays, in the window's row,
// its caption under it (the label face). A square pressed opens its row of choices under it (`fieldRow`): *Files* *From this computer* (pictures, as pasting takes them) and some files of the project (`files.find`, what the *@* list offers),
// taken as chips in the window. Esc closes the row first and the card after, a press on the square again closes it. While the row is open the words give it room (pluscard.js puts `has-row` on the card). Layout only (hand.css); every face is orkUI's.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Icon } from "../orkui.js";
import { command } from "../link.js";
import { MAX_PICTURES } from "../board/pictures.js";
import { fieldFiles, fieldPhotos, fieldRow, fieldRune } from "./state.js";

export const ELEMENTS = ["meadow", "ice", "dust", "void", "lava"];                  // realm/idea_element.py `ELEMENTS`: the order of the field's radios
const FILES_SHOWN = 5;                                                              // the project's files offered in the row (one row of them, with *From this computer*)
export const FILES_SAY = "Pictures from this computer, or a file of the project";

const ID = { rune: "hand-field-runes", files: "hand-field-files" };
const base = (path) => String(path || "").replace(/\/$/, "").split("/").pop();

/** Closes the open row and gives the focus back to its square (or the words when none). */
export function closeRow(then = "square") {
  const was = fieldRow.value;
  fieldRow.value = "";
  const field = document.querySelector(".hand-field");
  (then === "square" && was ? field?.querySelector(`[data-sq="${was}"], [data-corner="${was}"]`) : field?.querySelector(".hand-field__text"))?.focus({ preventScroll: true });
}

/** One square: its button (a head, a sign, a rune or an icon) and its caption. */
function Square({ id, caption, label, faint = false, badge = 0, children }) {
  const open = fieldRow.value === id;
  return html`<div class="hand-sq"><button type="button" class=${cls("hand-sq__btn", { "hand-field__rune": id === "rune", "is-open": open, "is-faint": faint })} data-sq=${id} aria-label=${label} aria-expanded=${String(open)} aria-controls=${ID[id]}
    onClick=${() => { fieldRow.value = open ? "" : id; }}>${children}${badge > 0 && html`<span class="hand-sq__n">${badge}</span>`}</button><span class="hand-sq__cap">${caption}</span></div>`;
}

/** The one square left (spec 150 F.1, decisions §254.9: the rune, the kind and who moved into the card's corners, fieldcorners.js): *Files*, in the window's row. */
export function Squares() {
  const count = fieldPhotos.value.length + fieldFiles.value.length;
  return html`<div class="hand-field__squares" role="group" aria-label="Its files">
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
export function RuneRow({ runes }) {
  const row = useRef();
  useEffect(() => { row.current?.querySelector('[role=radio][tabindex="0"]')?.focus({ preventScroll: true }); }, []);       // opened by a press on the rune: the focus is in the row
  const keys = useRowKeys((b) => { fieldRune.value = b.dataset.rune; });
  return html`<div ref=${row} id=${ID.rune} class="hand-field__runes hand-field__choices" role="radiogroup" aria-label="Its rune" onKeyDown=${keys}>
    ${ELEMENTS.map((e, i) => html`<${Choice} key=${e} checked=${runes.shown === e} label=${`Rune ${i + 1}`} used=${runes.used.includes(e)} tab=${runes.shown ? runes.shown === e : i === 0} data=${{ "data-rune": e }}
      onPick=${() => { fieldRune.value = e; fieldRow.value = ""; }}><${Elem} name=${e} big=${true} /><//>`)}
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
export function Choices({ pick }) {
  const open = fieldRow.value;
  if (!open) return null;
  return html`<div class="hand-field__row-open" data-open=${open}>
    ${open === "files" && html`<span class="hand-field__say">${FILES_SAY}</span>`}
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
