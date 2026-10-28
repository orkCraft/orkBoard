// The hand (docs/specs/101 §4, docs/specs/98-the-table-and-the-hand.md §4, decisions §116.2, §121.2, §124, §144.2, §145.3–§145.4, §159, §160, §167): under the table's lanes, on the grid the tabs and the Board stand on (the frame's `--cols`).
// Under the first lane the + card, with the Orkmaster's stacks fanned beside it; under each party's lane the stacks of who asks there (stacks.js: a goal a stack, two goals under one lane a fan); under the tabs' end the discard of the
// goals done with what is ready for main (discard.js). No deck: the goals in line lie on the table. A card shows its header and its window; the rest lies under the window's edge until it rises (hand.css). A card pressed is lifted
// over the pane's foot with its answers and its cost's words; the cards of the table it is about rise (about.js). A part comes when it has something to hold: no discard with nothing done and nothing ready for main, and with no
// goal at all the + card lies large in the pane's middle. What is opened over the pane (`discard`, `result`, `stop`) is drawn by the faces registered below (frame/kinds.js).
// Under the table: frame.js draws `Hand` under `Table`. Keyboard: a key typed with nothing focused opens the field; Esc closes the field and lowers a lifted card.
import { useEffect, useRef } from "preact/hooks";
import { html } from "../html.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { drawn } from "../frame/kinds.js";
import { lifted, lower, tab } from "../frame/state.js";
import { partiesOf, stacksOf, stopByKey, stopsOfProject } from "./data.js";
import { Discard, DiscardView } from "./discard.js";
import { Field, Middle, PlusCard, closeField, openField } from "./pluscard.js";
import { ResultFace } from "./resultface.js";
import { Lifted } from "./stopcard.js";
import { StopFace } from "./stopface.js";
import { Stacks } from "./stacks.js";
import { fieldOpen, stopKeyOf } from "./state.js";
import "./wayparts.js";                                   // the goal's way's cards (spec 100)

// The faces of what the hand opens over the pane; the table draws whichever `faceOf(kind)` has.
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
      if (stopKeyOf(lifted.value) && !t.closest?.(".hand-lifted, .hand-card")) lower();
    };
    const key = (e) => {
      if (e.key === "Escape" && !e.defaultPrevented && !aloud(document.activeElement)) {
        if (fieldOpen.value) { closeField(); e.preventDefault(); }
        else if (stopKeyOf(lifted.value)) { lower(); e.preventDefault(); }
        return;
      }
      if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey || e.key.length !== 1 || e.key === " ") return;
      const on = document.activeElement;
      if (on && on !== document.body && on !== document.documentElement) return;      // something has the focus: the key is its own
      if (typing(on) || aloud(on) || document.querySelector("[aria-modal='true']") || fieldOpen.value || !mapData.value || !partiesOf().length) return;
      e.preventDefault();
      lower();
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
  const stops = stopsOfProject(map, needs, open), stacks = stacksOf(stops), key = stopKeyOf(lifted.value), s = stopByKey(stops, key);
  useEffect(() => { if (key && !s && map) lower(); }, [key, !s]);                      // the stop was answered: the card goes with it
  useEffect(() => { if (key) fieldOpen.value = false; }, [key]);
  if (!map) return null;
  const none = !(map.nodes || []).length, parties = partiesOf(map).length > 0, middle = none && parties && !stacks.length;      // no goal at all and nothing asked: the + card lies large in the pane
  const plus = () => { lower(); fieldOpen.value = true; };
  const anchor = key ? root.current?.querySelector(`.hand-card[data-key="${CSS.escape(key)}"]`) : null;
  return html`<footer ref=${root} class="hand" aria-label="The hand" data-empty=${middle ? "1" : undefined}>
    ${!middle && html`<div class="hand-places"><div class="hand-row">
      <${Stacks} stacks=${stacks} plus=${html`<${PlusCard} onPress=${plus} />`} />
      <div class="hand-end"><${Discard} /></div>
    </div></div>`}
    ${fieldOpen.value && !middle && html`<${Field} />`}
    ${s && html`<${Lifted} s=${s} anchor=${anchor} />`}
    ${middle && html`<${Middle}>${fieldOpen.value ? html`<${Field} middle=${true} />` : html`<${PlusCard} large=${true} onPress=${plus} />`}<//>`}
  </footer>`;
}
