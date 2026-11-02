// The + card and the field it grows into (docs/specs/101 §4.2, docs/specs/98-the-table-and-the-hand.md §4.1, decisions §160.2, §167.5): the new goal's card lies at the first lane's left end, whole and face up, a + on its face, in its own frame (hand.css, spec 107 §13): the Orkmaster's stacks fan to its right, nothing lies over it.
// Under the + lies the seal of summoning (docs/specs/110-runes-on-the-table.md §3.3, decisions §185.4, §186.3): orkUI's `.ork-sigil`, its top holding the rune the goal being written would be given — the one the person chose in the field, else the addressed party's `next_element`
// (the map says it; none on the Orkmaster's tab until a party is named with *@*, and then the place is empty). **The choice of the rune** (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.2, decisions §187.3): the party's free runes — those none of its open goals has
// (`free_elements` of its map node; all five when none is free), except the one at the top — stand in the seal's band, at most four (`.ork-sigil__free`), shown when the card is hovered or focused and held while the field is open (`.is-choosing`); the choice itself is made in the field, in the *Rune* square's row of five radios
// (fieldsquares.js: *Rune 1* … *Rune 5*, the elements never named, §63.4), each 40 x 40 with the rune at 28 px, the default checked, the used ones faint but possible; arrows move the choice, Tab leaves the row. Sending passes `element` to `ideas.add` only when the choice is not the default.
// **The ring is whole while the runes are offered** (docs/specs/128 A.4, decisions §206.1): with some free runes in their places, three of orkUI's own runes (`.ork-rune` eye, key, hourglass) stand in the three places left (135°, 225°, 315°: `.ork-sigil__free` too, `hand-deco`),
// lit with them at three quarters, so the eight places are lit; their places are layout (hand.css).
// **The rite** (§3.3, decisions §187.4): when the goal is sent the seal plays orkUI's summoning rite in the goal's element (`is-summoning rite-<element>`, state.js `summon`), once, and nothing under reduced motion. The seal is `small` at the narrow width.
// **The card-field** (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.1–§6.2, docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md A, decisions §198.1, §198.8, §206.1): the + card is a card's back; pressed (or a key typed with nothing focused), **the + card itself turns over and grows
// where it lies** (fieldturn.js `growFrom`: a perspective turn of 180° and a growth from its box; it is hidden, `is-under`, while the field is open) into **a card** 5 : 7, about 2.8 times its width, its left edge on the + card's, its top so that 330 px show above the window's edge (its foot goes under it:
// `placeField`); on a phone (under 760 px) as wide as the screen less the gutters, as before. On it, under its top, **the squares** *Rune*, *To*, *Type*, *Files* (fieldsquares.js: each opens its row of choices; one row at a time; Esc closes the row first), then *Write a goal…* its body,
// **Send** at its foot with the files taken as chips beside it; the focus is taken inside the press itself (fieldturn.js), and Esc or a press away turns it back (`closeField`), Send turns it to its back and sends the back to the Orkmaster's lane. Its text: Enter sends, Shift+Enter is a new line, a picture pasted goes with
// it (`photos`, as the old New goal took them; the *Files* square takes them from the computer too), Esc or a press away closes it and keeps its text, its rune, its address and its files. No priority, no kind. On a party's tab it is addressed to that party (*→ Tech ×*,
// one press takes it off); *@Tech* in the text addresses it too, and the *To* square chooses a leader; on the Orkmaster's tab it is general and the Orkmaster routes it by code (`ideas.add` with no party). The page has no
// microphone, so the field has none. While there is no goal at all, the + card lies large in the pane's middle (and the field grows there, as it did). *@* in the text offers a party, a file or a folder, and a party's goal types and map parts (mention.js, spec 107 §11): a type
// taken is a chip and `type` of `ideas.add`, a part a mark as picking's; a project file taken with *Files* is written *@path* after the words when it is sent, as the *@* list writes it.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon, Sign } from "../orkui.js";
import { toast } from "../link.js";
import { act } from "../shell/store.js";
import { MAX_PICTURES, PICTURE_TYPES, shrink } from "../board/pictures.js";
import { tab } from "../frame/state.js";
import { fieldFiles, fieldOff, fieldOpen, fieldPhotos, fieldRow, fieldRune, fieldText, fieldTo, fieldType, plusDealt, rite, summon, withoutAddress } from "./state.js";
import { focusInPress, growFrom, placeField, releaseProxy, sendBack, turnBack } from "./fieldturn.js";
import { Choices, ELEMENTS, FileChips, Squares, closeRow } from "./fieldsquares.js";
import { partiesOf, partyCard } from "./data.js";
import { MarkChips, addressNow, marks, marksToSend, resetMarks } from "../table/picking.js";       // picking on the addressed party's map (spec 102 §6): its marks lie on the field as chips
import { leans } from "./motion.js";
import { MentionList, useMention } from "./mention.js";
import { mapData } from "../shell/store.js";
import { Elem } from "../orkui.js";
import { useNarrow } from "../table/portal.js";

const FREE_PLACES = ["at-90", "at-270", "at-180", "at-45"];                  // the seal's band, in the order the free runes use it (orkUI 0.21.0)
const DECO = [["at-135", "eye"], ["at-225", "key"], ["at-315", "hourglass"]];     // the three places left, held by orkUI's own runes (spec 128 A.4; hand.css gives their places)

/** The runes of the goal being written (decisions §187.3), for the address `address` (`addressNow()`): `base` the one it would be given (the party's `next_element`, "" with no party), `shown` the one the seal holds and the field checks (the person's
 *  choice, else `base`), `free` the party's free runes (all five when none is free), `used` the elements to show faint in the field (none when all five are used: nothing then tells them apart). */
export function runesOf(address) {
  const g = address.party ? partiesOf(mapData.value).find((x) => x.slug === address.party) : null;
  const base = g?.next_element || "", shown = fieldRune.value || base;
  const free = g ? ((g.free_elements || []).length ? g.free_elements : ELEMENTS) : [];
  return { base, shown, free, used: g && (g.free_elements || []).length ? ELEMENTS.filter((e) => !g.free_elements.includes(e)) : [] };
}

/** The + card. `large`: the card in the pane's middle, with no goal at all. While the field is open the card lies under it, unseen (`is-under`, hand.css): the field grew out of it and turns back into it. */
export function PlusCard({ large = false, onPress }) {
  const narrow = useNarrow(), address = addressNow(), r = runesOf(address), play = rite.value;
  const frees = r.free.filter((e) => e !== r.shown).slice(0, FREE_PLACES.length);
  return html`<button type="button" class=${cls("ork-card ork-plus ork-leans hand-plus", { "is-large": large, "is-choosing": fieldOpen.value, "is-under": fieldOpen.value, "ork-deal": plusDealt.value })} aria-label="New goal" title="New goal" aria-haspopup="dialog"
    aria-expanded=${fieldOpen.value ? "true" : "false"} onClick=${(e) => { if (!fieldOpen.value) focusInPress(); onPress?.(e); }} ...${leans}>
    <${Seal} narrow=${narrow} play=${play} shown=${r.shown} frees=${frees} /><${Icon} name="plus" /></button>`;
}

/** The seal of summoning on the + card: the goal's rune at its top, the party's free runes in the band's places and, when there are some, orkUI's own runes in the three places left, so the ring is whole (spec 128 A.4). */
function Seal({ narrow, play, shown, frees }) {
  return html`<span class=${cls("ork-sigil", { small: narrow, "is-summoning": !!play, [`rite-${play}`]: !!play })} aria-hidden="true"><span class="ork-sigil__seal">${shown && html`<${Elem} name=${shown} />`}</span>${!narrow && frees.map((e, i) => html`<span key=${e} class=${`ork-sigil__free ${FREE_PLACES[i]}`}><${Elem} name=${e} /></span>`)}${!narrow && frees.length > 0 && DECO.map(([at, name]) => html`<span key=${at} class=${`ork-sigil__free ${at} hand-deco`}><span class=${`ork-rune ${name}`}></span></span>`)}</span>`;
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

/** Esc or a press away: the card turns back into the + card where it lay, its text, rune, address and files kept (fieldturn.js). */
export function closeField() {
  const box = fieldOpen.value ? document.querySelector(".hand-field")?.getBoundingClientRect() : null;
  fieldOpen.value = false;
  fieldRow.value = "";
  releaseProxy();
  if (box) turnBack(box);
}
export function openField(first = "") {
  if (first) fieldText.value += first;
  fieldOpen.value = true;
}

/** The field the + card grew into. `middle`: it grows in the pane's middle (no goal at all) or in the phone's deck, else it lies where the + card lay (placeField). */
export function Field({ middle = false }) {
  const root = useRef(), area = useRef(), file = useRef(), [busy, setBusy] = useState(false), address = useAddress(), runes = runesOf(address);
  const parties = partiesOf(mapData.value).map((g) => ({ ...partyCard(g), types: g.types || [] }));
  const mention = useMention(area, parties);
  const taken = fieldType.value && fieldType.value.party === address.party ? fieldType.value : null;     // the type taken with @ or the *Type* square stays the goal's while it goes to the party it was taken from
  useLayoutEffect(() => {
    if (!middle) placeField(root.current);                                           // its left edge on the + card's, its foot under the window's edge
    growFrom(root.current);                                                          // the + card turns over and grows into it (fieldturn.js)
    if (middle) return undefined;
    const set = () => placeField(root.current);
    window.addEventListener("resize", set);
    return () => window.removeEventListener("resize", set);
  }, []);
  useEffect(() => {                                                                   // opened: the caret at the end of what was kept
    const el = area.current;
    if (!el) return;
    fieldRow.value = "";
    el.focus({ preventScroll: true });
    releaseProxy();                                                                   // the focus the press gave moves here: the phone's keyboard stays up
    el.setSelectionRange(el.value.length, el.value.length);
  }, []);
  const send = async () => {
    const words = withoutAddress(fieldText.value, address.by === "text" ? address.name : "");
    if (!words || busy) return;
    const text = fieldFiles.value.length ? `${words} ${fieldFiles.value.map((f) => `@${f.path}`).join(" ")}` : words;     // a file of the project is written as the @ list writes it (the host turns it into the path)
    setBusy(true);
    const sent = marksToSend();
    const chosen = fieldRune.value && fieldRune.value !== runes.base ? fieldRune.value : "";            // the rune goes only when it is not the one the goal would be given anyway
    const got = await act("ideas.add", { text, ...(address.party ? { party: address.party } : {}), ...(taken ? { type: taken.id } : {}), ...(chosen ? { element: chosen } : {}), ...(fieldPhotos.value.length ? { photos: fieldPhotos.value } : {}), ...(sent.length ? { marks: sent } : {}) });
    setBusy(false);
    if (!got) return;                                                                 // refused: the host said why in a toast, the words stay
    const box = root.current?.getBoundingClientRect(), goal = { slug: got.slug || "", element: got.element || chosen || runes.shown, name: words.replace(/\s+/g, " ").slice(0, 60) };
    fieldText.value = ""; fieldPhotos.value = []; fieldFiles.value = []; resetMarks(); fieldType.value = null; fieldRune.value = ""; fieldTo.value = ""; fieldOpen.value = false; fieldRow.value = "";
    summon(got.element || chosen);                                                    // the seal fills from the goal's rune (decisions §187.4)
    plusDealt.value = true;                                                           // a new + card is dealt at the lane's end, its rune the next goal's
    setTimeout(() => { plusDealt.value = false; }, 700);
    if (box && goal.slug) sendBack(box, goal);                                        // it turns to its back and goes face down to the Orkmaster's lane (§6.2)
    toast(address.party ? `Sent to ${address.name}.` : "Sent: the Orkmaster finds its party in a moment.");
  };
  const off = () => {
    if (address.by === "text") fieldText.value = withoutAddress(fieldText.value, address.name);
    else if (address.by === "to") fieldTo.value = "ork";                              // the *To* square's choice taken off: the goal is general
    else fieldOff.value = tab.value;
    area.current?.focus();
  };
  const key = (e) => {
    if (mention.onKey(e)) return;                                                     // the @ list took it (↑ ↓ Enter Tab Esc)
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); if (fieldRow.value) closeRow("text"); else closeField(); return; }          // a row of choices open: Esc closes it first, the card after
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); }
  };
  const paste = (e) => {
    const pics = [...(e.clipboardData?.files || [])].filter((f) => PICTURE_TYPES.includes(f.type));
    if (pics.length) { e.preventDefault(); addPictures(pics); }
  };
  const attached = fieldPhotos.value.length + fieldFiles.value.length > 0;
  return html`<div ref=${root} class=${cls("ork-card hand-field", { "is-middle": middle, "has-row": !!fieldRow.value })} role="group" aria-label="The new goal’s card, grown into the field"
      onDragOver=${(e) => e.preventDefault()} onDrop=${(e) => { e.preventDefault(); addPictures([...(e.dataTransfer?.files || [])]); }}>
    <div class="hand-field__top"><${Squares} runes=${runes} address=${address} parties=${parties} taken=${taken} />
    ${(address.name || taken || marks.value.length > 0) && html`<div class="hand-field__chips">
      ${address.name && html`<span class="ork-chip hand-chip" data-by=${address.by}><${Icon} name="arrow-right" />${address.name}
        <button type="button" class="ork-btn quiet hand-chip__off" aria-label=${`Take off ${address.name}`} title=${`Take off ${address.name}`} onClick=${off}><${Icon} name="close" /></button></span>`}
      ${taken && html`<span class="ork-chip hand-chip" data-type=${taken.id}><${Sign} name=${taken.sign} />${taken.name}
        <button type="button" class="ork-btn quiet hand-chip__off" aria-label=${`Take ${taken.name} off`} title=${`Take ${taken.name} off`} onClick=${() => { fieldType.value = null; area.current?.focus(); }}><${Icon} name="close" /></button></span>`}
      <${MarkChips} />
    </div>`}</div>
    <${Choices} runes=${runes} address=${address} parties=${parties} taken=${taken} pick=${() => file.current?.click()} />
    <textarea ref=${area} class="ork-field hand-field__text" aria-label="Write a goal" placeholder="Write a goal…" rows="3" value=${fieldText.value}
      onInput=${(e) => { fieldText.value = e.currentTarget.value; mention.look(); }} onKeyDown=${key} onKeyUp=${mention.look} onClick=${mention.look} onFocus=${mention.look} onPaste=${paste}></textarea>
    <${MentionList} ...${mention} />
    <div class="hand-field__row">
      ${attached ? html`<${FileChips} />` : html`<span class="cap hand-field__hint">Enter sends · Shift+Enter a new line</span>`}
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
