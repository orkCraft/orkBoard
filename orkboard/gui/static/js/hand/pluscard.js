// The + card and the field it grows into (docs/specs/101 §4.2, docs/specs/98-the-table-and-the-hand.md §4.1, decisions §160.2, §167.5): the new goal's card lies at the first lane's left end, whole and face up, a + on its face, in its own frame (hand.css, spec 107 §13): the Orkmaster's stacks fan to its right, nothing lies over it.
// Under the + lies the seal of summoning (docs/specs/110-runes-on-the-table.md §3.3, decisions §185.4, §186.3): orkUI's `.ork-sigil`, its top holding the rune the goal being written would be given — the one the person chose in the field, else the addressed party's `next_element`
// (the map says it; none on the Orkmaster's tab until a party is named with *@*, and then the place is empty). **The choice of the rune** (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.2, decisions §187.3): the party's free runes — those none of its open goals has
// (`free_elements` of its map node; all five when none is free), except the one at the top — stand in the seal's band, at most four (`.ork-sigil__free`), shown when the card is hovered or focused and held while the field is open (`.is-choosing`); the choice itself is made in the field, a row of
// five radios (*Its rune*: *Rune 1* … *Rune 5*, the elements never named, §63.4), each 40 x 40 with the rune at 28 px, the default checked, the used ones faint but possible; arrows move the choice, Tab leaves the row. Sending passes `element` to `ideas.add` only when the choice is not the default.
// **The rite** (§3.3, decisions §187.4): when the goal is sent the seal plays orkUI's summoning rite in the goal's element (`is-summoning rite-<element>`, state.js `summon`), once, and nothing under reduced motion. The seal is `small` at the narrow width.
// Pressed (or a key typed with nothing focused), it grows into the field over the hand: one field, *Write a goal…*. Enter sends, Shift+Enter is a new line, a picture pasted goes with
// it (`photos`, as the old New goal took them), Esc or a press away closes it and keeps its text and its rune. No priority, no kind. On a party's tab it is addressed to that party (*→ Tech ×*,
// one press takes it off); *@Tech* in the text addresses it too; on the Orkmaster's tab it is general and the Orkmaster routes it by code (`ideas.add` with no party). The page has no
// microphone, so the field has none. While there is no goal at all, the + card lies large in the pane's middle. *@* in the text offers a party, a file or a folder, and a party's goal types and map parts (mention.js, spec 107 §11): a type
// taken is a chip and `type` of `ideas.add`, a part a mark as picking's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon, Sign } from "../orkui.js";
import { toast } from "../link.js";
import { act } from "../shell/store.js";
import { MAX_PICTURES, PICTURE_TYPES, shrink } from "../board/pictures.js";
import { tab } from "../frame/state.js";
import { fieldOff, fieldOpen, fieldPhotos, fieldRune, fieldText, fieldType, rite, summon, withoutAddress } from "./state.js";
import { partiesOf, partyCard } from "./data.js";
import { MarkChips, addressNow, marks, marksToSend, resetMarks } from "../table/picking.js";       // picking on the addressed party's map (spec 102 §6): its marks lie on the field as chips
import { leans } from "./motion.js";
import { MentionList, useMention } from "./mention.js";
import { mapData } from "../shell/store.js";
import { Elem } from "../orkui.js";
import { useNarrow } from "../table/portal.js";

const ELEMENTS = ["meadow", "ice", "dust", "void", "lava"];                  // realm/idea_element.py `ELEMENTS`: the order of the field's radios
const FREE_PLACES = ["at-90", "at-270", "at-180", "at-45"];                  // the seal's band, in the order the free runes use it (orkUI 0.21.0)

/** The runes of the goal being written (decisions §187.3), for the address `address` (`addressNow()`): `base` the one it would be given (the party's `next_element`, "" with no party), `shown` the one the seal holds and the field checks (the person's
 *  choice, else `base`), `free` the party's free runes (all five when none is free), `used` the elements to show faint in the field (none when all five are used: nothing then tells them apart). */
export function runesOf(address) {
  const g = address.party ? partiesOf(mapData.value).find((x) => x.slug === address.party) : null;
  const base = g?.next_element || "", shown = fieldRune.value || base;
  const free = g ? ((g.free_elements || []).length ? g.free_elements : ELEMENTS) : [];
  return { base, shown, free, used: g && (g.free_elements || []).length ? ELEMENTS.filter((e) => !g.free_elements.includes(e)) : [] };
}

/** The + card. `large`: the card in the pane's middle, with no goal at all. */
export function PlusCard({ large = false, onPress }) {
  const narrow = useNarrow(), address = addressNow(), r = runesOf(address), play = rite.value;
  const frees = r.free.filter((e) => e !== r.shown).slice(0, FREE_PLACES.length);
  return html`<button type="button" class=${cls("ork-card ork-plus ork-leans hand-plus", { "is-large": large, "is-choosing": fieldOpen.value })} aria-label="New goal" title="New goal" aria-haspopup="dialog"
    aria-expanded=${fieldOpen.value ? "true" : "false"} onClick=${onPress} ...${leans}>
    <span class=${cls("ork-sigil", { small: narrow, "is-summoning": !!play, [`rite-${play}`]: !!play })} aria-hidden="true"><span class="ork-sigil__seal">${r.shown && html`<${Elem} name=${r.shown} />`}</span>${!narrow && frees.map((e, i) => html`<span key=${e} class=${`ork-sigil__free ${FREE_PLACES[i]}`}><${Elem} name=${e} /></span>`)}</span><${Icon} name="plus" /></button>`;
}

/** Pictures pasted or chosen: shrunk as the old form shrank them, at most four. */
async function addPictures(files) {
  const got = [];
  for (const f of files.filter((x) => PICTURE_TYPES.includes(x.type)).slice(0, Math.max(0, MAX_PICTURES - fieldPhotos.value.length))) {
    try { got.push(await shrink(f)); } catch { toast("That picture could not be read: try another.", "warning"); }
  }
  if (got.length) fieldPhotos.value = [...fieldPhotos.value, ...got].slice(0, MAX_PICTURES);
}

/** Where the goal in the field goes now: the party its text names, else the open tab's (unless taken off), else none. */
export const useAddress = addressNow;

export function closeField() { fieldOpen.value = false; }
export function openField(first = "") {
  if (first) fieldText.value += first;
  fieldOpen.value = true;
}

/** The row of the five runes in the field (decisions §187.3): a radio group, each rune a 40 x 40 button, the chosen one checked (the default until the person chooses), the used ones faint but possible. The arrows move the choice and its focus (a radio group's), Tab leaves the row;
 *  with no party addressed none is checked, and Tab enters on the first. The elements are never named: a screen reader hears *Rune 1* … *Rune 5*. */
function RuneRow({ runes }) {
  const row = useRef();
  const move = (e) => {
    const at = ELEMENTS.indexOf(runes.shown), forward = e.key === "ArrowRight" || e.key === "ArrowDown";
    if (!forward && e.key !== "ArrowLeft" && e.key !== "ArrowUp") return;
    e.preventDefault();
    e.stopPropagation();
    const next = at < 0 ? (forward ? 0 : ELEMENTS.length - 1) : (at + (forward ? 1 : -1) + ELEMENTS.length) % ELEMENTS.length;     // none checked yet: the first, or the last
    fieldRune.value = ELEMENTS[next];
    row.current?.querySelectorAll("[role=radio]")[next]?.focus();
  };
  return html`<div ref=${row} class="hand-field__runes" role="radiogroup" aria-label="Its rune" onKeyDown=${move}>
    ${ELEMENTS.map((e, i) => html`<button key=${e} type="button" role="radio" class=${cls("hand-rune", { "is-used": runes.used.includes(e) })} data-rune=${e} aria-checked=${String(runes.shown === e)} aria-label=${`Rune ${i + 1}`}
      tabindex=${(runes.shown ? runes.shown === e : i === 0) ? 0 : -1} onClick=${() => { fieldRune.value = e; }}><${Elem} name=${e} big=${true} /></button>`)}
  </div>`;
}

/** The field the + card grew into. `middle`: it grows in the pane's middle (no goal at all), else over the hand. */
export function Field({ middle = false }) {
  const area = useRef(), file = useRef(), [busy, setBusy] = useState(false), address = useAddress(), runes = runesOf(address);
  const mention = useMention(area, partiesOf(mapData.value).map((g) => ({ ...partyCard(g), types: g.types || [] })));
  const taken = fieldType.value && fieldType.value.party === address.party ? fieldType.value : null;     // the type taken with @ stays the goal's while it goes to the party it was taken from
  useEffect(() => {                                                                   // opened: the caret at the end of what was kept
    const el = area.current;
    if (!el) return;
    el.focus({ preventScroll: true });
    el.setSelectionRange(el.value.length, el.value.length);
  }, []);
  const send = async () => {
    const text = withoutAddress(fieldText.value, address.by === "text" ? address.name : "");
    if (!text || busy) return;
    setBusy(true);
    const sent = marksToSend();
    const chosen = fieldRune.value && fieldRune.value !== runes.base ? fieldRune.value : "";            // the rune goes only when it is not the one the goal would be given anyway
    const got = await act("ideas.add", { text, ...(address.party ? { party: address.party } : {}), ...(taken ? { type: taken.id } : {}), ...(chosen ? { element: chosen } : {}), ...(fieldPhotos.value.length ? { photos: fieldPhotos.value } : {}), ...(sent.length ? { marks: sent } : {}) });
    setBusy(false);
    if (!got) return;                                                                 // refused: the host said why in a toast, the words stay
    fieldText.value = ""; fieldPhotos.value = []; resetMarks(); fieldType.value = null; fieldRune.value = ""; fieldOpen.value = false;
    summon(got.element || chosen);                                                    // the seal fills from the goal's rune (decisions §187.4)
    toast(address.party ? `Sent to ${address.name}.` : "Sent: the Orkmaster finds its party in a moment.");
  };
  const off = () => { if (address.by === "text") fieldText.value = withoutAddress(fieldText.value, address.name); else fieldOff.value = tab.value; area.current?.focus(); };
  const key = (e) => {
    if (mention.onKey(e)) return;                                                     // the @ list took it (↑ ↓ Enter Tab Esc)
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeField(); return; }
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); }
  };
  const paste = (e) => {
    const pics = [...(e.clipboardData?.files || [])].filter((f) => PICTURE_TYPES.includes(f.type));
    if (pics.length) { e.preventDefault(); addPictures(pics); }
  };
  const photos = fieldPhotos.value;
  return html`<div class=${cls("ork-card hand-field", { "is-middle": middle })} role="group" aria-label="The new goal’s card, grown into the field"
      onDragOver=${(e) => e.preventDefault()} onDrop=${(e) => { e.preventDefault(); addPictures([...(e.dataTransfer?.files || [])]); }}>
    ${(address.name || taken || photos.length > 0 || marks.value.length > 0) && html`<div class="hand-field__chips">
      ${address.name && html`<span class="ork-chip hand-chip" data-by=${address.by}><${Icon} name="arrow-right" />${address.name}
        <button type="button" class="ork-btn quiet hand-chip__off" aria-label=${`Take off ${address.name}`} title=${`Take off ${address.name}`} onClick=${off}><${Icon} name="close" /></button></span>`}
      ${taken && html`<span class="ork-chip hand-chip" data-type=${taken.id}><${Sign} name=${taken.sign} />${taken.name}
        <button type="button" class="ork-btn quiet hand-chip__off" aria-label=${`Take ${taken.name} off`} title=${`Take ${taken.name} off`} onClick=${() => { fieldType.value = null; area.current?.focus(); }}><${Icon} name="close" /></button></span>`}
      <${MarkChips} />
      ${photos.map((url, i) => html`<span key=${i} class="hand-pic"><img src=${url} alt=${`Picture ${i + 1}`} draggable="false" />
        <button type="button" class="ork-btn quiet hand-chip__off" aria-label=${`Remove picture ${i + 1}`} onClick=${() => { fieldPhotos.value = photos.filter((_, k) => k !== i); }}><${Icon} name="close" /></button></span>`)}
    </div>`}
    <textarea ref=${area} class="ork-field hand-field__text" aria-label="Write a goal" placeholder="Write a goal…" rows="3" value=${fieldText.value}
      onInput=${(e) => { fieldText.value = e.currentTarget.value; mention.look(); }} onKeyDown=${key} onKeyUp=${mention.look} onClick=${mention.look} onFocus=${mention.look} onPaste=${paste}></textarea>
    <${MentionList} ...${mention} />
    <${RuneRow} runes=${runes} />
    <div class="hand-field__row">
      <span class="cap hand-field__hint">Enter sends · Shift+Enter a new line</span>
      <button type="button" class="ork-btn quiet" disabled=${photos.length >= MAX_PICTURES} onClick=${() => file.current?.click()}>Add a picture</button>
      <button type="button" class="ork-btn primary" disabled=${!fieldText.value.trim() || busy} onClick=${send}>Send</button>
      <input ref=${file} type="file" accept=${PICTURE_TYPES.join(",")} multiple hidden onChange=${(e) => { addPictures([...e.currentTarget.files]); e.currentTarget.value = ""; }} />
    </div>
  </div>`;
}

/** With no goal at all (§4.1, §145.8): the + card large in the pane's middle, and the field grown there. It lies over the table's box, whose middle is the pane's. */
export function Middle({ children }) {
  const box = useRef(), [rect, setRect] = useState(null);
  useLayoutEffect(() => {
    const table = box.current?.closest(".frame")?.querySelector(".frame-table");
    if (!table) return undefined;
    const set = () => { const r = table.getBoundingClientRect(); setRect({ top: r.top, left: r.left, width: r.width, height: r.height }); };
    set();
    const watch = typeof ResizeObserver === "function" ? new ResizeObserver(set) : null;
    watch?.observe(table);
    window.addEventListener("resize", set);
    return () => { watch?.disconnect(); window.removeEventListener("resize", set); };
  }, []);
  return html`<div ref=${box} class="hand-middle" style=${rect ? `top:${rect.top}px;left:${rect.left}px;width:${rect.width}px;height:${rect.height}px` : "visibility:hidden"}>${children}</div>`;
}
