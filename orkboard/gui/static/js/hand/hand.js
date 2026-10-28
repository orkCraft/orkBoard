// The hand (docs/specs/98-the-table-and-the-hand.md §4, decisions §116.2, §121.2, §124, §144.2, §145.3–§145.4, §159, §160): three places along the window's foot, under everything
// opened. Left to right: the deck with the + card drawn off it (deck.js, pluscard.js, deckrow.js), the stacks of the stops that wait for the person (stacks.js, stopcard.js, answers.js) and
// the discard of the goals done with what is ready for main (discard.js). A card pressed is lifted over the pane's foot with its answers and its cost's words; the cards of the table it is
// about rise (about.js). A part comes when it has something to hold: the deck is the + card alone with nothing in line, no discard with nothing done and nothing ready for main, and with no
// goal at all the + card lies large in the pane's middle. What is opened over the pane (`deck`, `discard`, `result`, `stop`) is drawn by the faces registered below (frame/kinds.js).
// Under the table: frame.js draws `Hand` under `Table`. Keyboard: a key typed with nothing focused opens the field; Esc closes the field, lowers a lifted card, closes a fan or the row.
import { useEffect, useRef } from "preact/hooks";
import { html } from "../html.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { drawn } from "../frame/kinds.js";
import { lifted, lower, tab } from "../frame/state.js";
import { lineOf, partiesOf, stacksOf, stopByKey, stopsOfProject } from "./data.js";
import { Deck } from "./deck.js";
import { DeckList, DeckRow } from "./deckrow.js";
import { Discard, DiscardView } from "./discard.js";
import { Field, Middle, PlusCard, closeField, openField } from "./pluscard.js";
import { ResultFace } from "./resultface.js";
import { Lifted } from "./stopcard.js";
import { StopFace } from "./stopface.js";
import { Stacks } from "./stacks.js";
import { fanned, fieldOpen, rowOpen, stopKeyOf } from "./state.js";

// The faces of what the hand opens over the pane; the table draws whichever `faceOf(kind)` has.
drawn("deck", DeckList);
drawn("discard", DiscardView);
drawn("result", ResultFace);
drawn("stop", StopFace);

const typing = (el) => !!el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable);
const aloud = (t) => t?.closest?.("[aria-modal='true'], [role='dialog']:not(.hand-lifted), .ork-toast, .shell-toasts");

/** Esc, a press away and a key typed with nothing focused (§4.1): the hand's own keys; the window's (Esc lowers, closes, picks none) are spec 98 E's. */
function useKeys(root) {
  useEffect(() => {
    const away = (e) => {
      const t = e.target;
      if (!root.current || aloud(t)) return;
      if (fieldOpen.value && !t.closest?.(".hand-field, .hand-plus")) closeField();
      if (rowOpen.value && !t.closest?.(".hand-row, .hand-deckback, .hand-plus")) rowOpen.value = false;
      if (fanned.value && !t.closest?.(".hand-stack.is-fanned, .hand-lifted")) fanned.value = "";
      if (stopKeyOf(lifted.value) && !t.closest?.(".hand-lifted, .hand-card")) lower();
    };
    const key = (e) => {
      if (e.key === "Escape" && !e.defaultPrevented && !aloud(document.activeElement)) {
        if (fieldOpen.value) { closeField(); e.preventDefault(); }
        else if (stopKeyOf(lifted.value)) { lower(); e.preventDefault(); }
        else if (fanned.value) { fanned.value = ""; e.preventDefault(); }
        else if (rowOpen.value) { rowOpen.value = false; e.preventDefault(); }
        return;
      }
      if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey || e.key.length !== 1 || e.key === " ") return;
      const on = document.activeElement;
      if (on && on !== document.body && on !== document.documentElement) return;      // something has the focus: the key is its own
      if (typing(on) || aloud(on) || document.querySelector("[aria-modal='true']") || fieldOpen.value || !mapData.value || !partiesOf().length) return;
      e.preventDefault();
      rowOpen.value = false; fanned.value = ""; lower();
      openField(e.key);
    };
    document.addEventListener("pointerdown", away, true);
    window.addEventListener("keydown", key);
    return () => { document.removeEventListener("pointerdown", away, true); window.removeEventListener("keydown", key); };
  }, []);
}

export function Hand() {
  const root = useRef(), map = mapData.value, needs = board.value?.needs_you || [], open = tab.value;
  useKeys(root);
  const stops = stopsOfProject(map, needs, open), stacks = stacksOf(stops), line = lineOf(map), key = stopKeyOf(lifted.value), s = stopByKey(stops, key);
  useEffect(() => { if (key && !s && map) lower(); }, [key, !s]);                      // the stop was answered: the card goes with it
  useEffect(() => { if (key) { fieldOpen.value = false; rowOpen.value = false; } }, [key]);
  if (!map) return null;
  const none = !(map.nodes || []).length, parties = partiesOf(map).length > 0, middle = none && parties && !stacks.length;      // no goal at all and nothing asked: the + card lies large in the pane
  const plus = () => { rowOpen.value = false; fanned.value = ""; lower(); fieldOpen.value = true; };
  const deck = () => { fieldOpen.value = false; fanned.value = ""; lower(); rowOpen.value = !rowOpen.value; };
  const anchor = key ? root.current?.querySelector(`.hand-card[data-key="${CSS.escape(key)}"]`) : null;
  return html`<footer ref=${root} class="hand" aria-label="The hand" data-empty=${middle ? "1" : undefined}>
    ${!middle && html`<div class="hand-places">
      <div class="hand-end hand-end--deck"><${Deck} line=${line} lit=${rowOpen.value} open=${rowOpen.value} onPress=${deck} onPlus=${plus} /></div>
      <div class="hand-mid"><${Stacks} stacks=${stacks} /></div>
      <div class="hand-end hand-end--discard"><${Discard} /></div>
    </div>`}
    ${rowOpen.value && !middle && html`<${DeckRow} line=${line} onPlus=${plus} />`}
    ${fieldOpen.value && !middle && html`<${Field} />`}
    ${s && html`<${Lifted} s=${s} anchor=${anchor} />`}
    ${middle && html`<${Middle}>${fieldOpen.value ? html`<${Field} middle=${true} />` : html`<${PlusCard} large=${true} onPress=${plus} />`}<//>`}
  </footer>`;
}
