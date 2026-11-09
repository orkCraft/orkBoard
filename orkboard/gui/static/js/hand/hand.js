// The hand (docs/specs/101 §4, docs/specs/98-the-table-and-the-hand.md §4, decisions §116.2, §121.2, §124, §144.2, §145.3–§145.4, §159, §160, §167): under the table's lanes, on the grid the tabs and the Board stand on (the frame's `--cols`).
// At the first lane's left end the + card, whole, with the Orkmaster's stacks fanned to its right (spec 107 M); under each party's lane the stacks of who asks there (stacks.js: a goal a stack, two goals under one lane a fan); at the right end the Play die (playdie.js: Play is a die lying in the hand, left of the potions, its word under it; spec 112 §3.3, decisions §190.2) and the AI tools' limits as
// the mana's potions, flush against the window's edge (mana.js: spec 104 B). The bug under the glass (Save logs) left the hand's end for the end of the tabs' row, to make room for the die (table/tabs.js, hand/logsbtn.js: decisions §190.6). A failure comes after a beat, thrown from its card (flight.js). The discard of the goals done lies on the table, not here (table/discard.js: spec 104 C). No deck: the goals in line lie on the table. A card shows its header and its window; the rest lies under the window's edge until it rises (hand.css). A card pressed is lifted
// over the pane's foot with its answers and its cost's words; the cards of the table it is about rise (about.js). With no
// goal at all the + card lies large in the pane's middle. What is opened over the pane (`result`, `stop`) is drawn by the faces registered below (frame/kinds.js).
// On a touch phone (frame/upright.js, docs/specs/103 §1, decisions §180) the hand is the whole screen instead (upright.js): the tools' row and the …, the top card's context between the arrows, one goal's cards, the green deck for a new goal.
// Under the table: frame.js draws `Hand` under `Table`. Keyboard: a key typed with nothing focused opens the field; Esc closes the field and lowers a lifted card.
import { useEffect, useRef } from "preact/hooks";
import { html } from "../html.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { drawn } from "../frame/kinds.js";
import { PLAY, inventory, lift, lifted, lower, tab } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { lanesBeforeEnd } from "../table/data.js";
import { partiesOf, stacksOf, stopByKey, stopsOfProject } from "./data.js";
import { Mana } from "./mana.js";
import { PotionRow, liftedStop } from "./potionrow.js";
import { Backpack } from "../table/backpack.js";
import { Book } from "./book.js";
import { useNight } from "./nightcard.js";                       // the night's record: its goals done go to the discard under a moon (spec 128 C.3; no card of the morning's)
import { useThrown } from "../table/flight.js";                   // a failure is thrown to the hand from its lane's card, which leaves a place (spec 128 C.2)
import { PlayDie } from "./playdie.js";
import { Field, Middle, PlusCard, closeField, openField } from "./pluscard.js";
import { ResultFace } from "./resultface.js";
import { Lifted } from "./stopcard.js";
import { SayLifted } from "./sayplay.js";
import { ConflictPlay } from "./conflictcard.js";                          // a decision's conflict in play: its ways the hand (spec 168 D1)
import { LiftedWide } from "./liftedwide.js";                  // any other card lifted on the desktop: the 144 x 202 card and a body in the hand's place (spec 168 D1)
import { ProjectDeal, dealt as headerDeal } from "../table/projectdeal.js";                       // the header's kind or stage dealt to the hand (spec 161 J)
import { ChairDeal, dealing } from "./chairdeal.js";                                     // the new chair deals its crafts (spec 161 I)
import { AnswerLifted, answerSet, useWide } from "./answercards.js";           // a lifted question or failure stays a hand card, its ways the hand (spec 158 F, decisions §270)
import { StopFace } from "./stopface.js";
import { Stacks } from "./stacks.js";
import { Carry } from "./carry.js";                         // the inventory open: what you carry, instead of the stacks (spec 157 D.3)
import { Upright } from "./upright.js";
import { ADD_TOOL, TOOL, fieldOpen, isToolKey, liftDecision, liftKey, stopKeyOf } from "./state.js";
import { AddTool } from "./addtool.js";
import { ToolCard } from "./toolcard.js";
import { SetupBubble, SetupCard, setupNow } from "./setupcards.js";
import { columnOn } from "../table/data.js";
import { laidNow, layLine } from "../table/laying.js";
import { said } from "./motion.js";
if (typeof document !== "undefined") {                         // the places' sheet (places.css), as carry.js loads its own
  const href = new URL("./places.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}
import "./wayparts.js";                                   // the goal's way's cards (spec 100)

// The faces of what the hand opens over the pane; the table draws whichever `faceOf(kind)` has.
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
      if (fieldOpen.value && !t.closest?.(".hand-field, .hand-plus, .hand-fieldbox, .hand-dealt, .up-mic, [data-picking]")) closeField();           // a press on the map in picking is the pick's (table/picking.js)
      if ((stopKeyOf(lifted.value) || lifted.value === PLAY) && !t.closest?.(".hand-lifted, .hand-body, .hand-card, .hand-ways-row, .hand-pen, .hand-tool, .hand-pot, .pot-s, .pots__all, .rh-stop")) lower();
    };
    const key = (e) => {
      if (e.key === "Escape" && !e.defaultPrevented && !aloud(document.activeElement)) {
        if (fieldOpen.value) { closeField(); e.preventDefault(); }
        else if (stopKeyOf(lifted.value) || lifted.value === PLAY) { lower(); e.preventDefault(); }
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
  useNight();
  const wide = useWide();
  const all = stopsOfProject(map, needs, open), stops = useThrown(all, !!map), stacks = stacksOf(stops), key = stopKeyOf(lifted.value), s = stopByKey(stops, key);
  useEffect(() => { if (key && !s && map && !isToolKey(key)) lower(); }, [key, !s]);   // the stop was answered: the card goes with it (a tool's card is no stop: it goes by its own)
  useEffect(() => { liftedStop.value = s || null; }, [s]);                                // the right column's potions hatch the share the lifted card takes (potionrow.js)
  useEffect(() => () => { liftedStop.value = null; }, []);
  const asks = setupNow.value?.step;
  useEffect(() => { if (asks === "tools") lift(liftKey(ADD_TOOL)); }, [asks]);          // the Orkmaster asks for a tool: the adding card comes up by itself (spec 130 B.4)
  const want = liftDecision.value, dealt = want ? stops.find((x) => x.kind === "decision" && x.row?.idea === want) : null;
  useEffect(() => { if (dealt) { liftDecision.value = ""; lift(liftKey(dealt.key)); } }, [dealt?.key]);        // *Change…* in the column: the decision's card, dealt now its wait is held, comes up (decisions §240.2)
  useEffect(() => { if (key || lifted.value === PLAY) fieldOpen.value = false; }, [key, lifted.value === PLAY]);
  const bare = !laidNow();                                                              // not laid yet: only the Orkmaster's cards and the AI tools (spec 130 C.6)
  useEffect(() => { if (layLine.value && (fieldOpen.value || (map?.nodes || []).length)) layLine.value = ""; }, [fieldOpen.value, (map?.nodes || []).length]);      // the laid table's line goes with the first goal
  if (!map && !bare) return null;
  const carrying = inventory.value !== null && !bare && !uprightNow.value;                  // the inventory open: the hand is what you carry of the chair (carry.js)
  const none = !(map?.nodes || []).length, parties = partiesOf(map).length > 0, middle = none && parties && !stacks.length && !bare && !layLine.value && !carrying;      // no goal at all and nothing asked: the + card lies large in the pane
  const plus = () => { lower(); fieldOpen.value = true; };
  if (uprightNow.value) return html`<${Upright} root=${root} stacks=${stacks} plus=${plus} />`;                  // a touch phone upright: the hand is the first screen (upright.js)
  const deal = wide && !s && !carrying && headerDeal.value ? headerDeal.value : "";                   // the Orkmaster's header pressed: the kinds or the stages are the hand
  useEffect(() => { if ((key || fieldOpen.value || !wide) && headerDeal.value) headerDeal.value = ""; }, [key, fieldOpen.value, wide]);
  const chair = dealing.value && wide && !carrying && !middle && !bare && !s;                                   // the new chair pressed: its crafts are the hand (spec 161 I)
  const cards = s && wide ? answerSet(s) : null;                                           // a card with one open question, or a failure: it rises and its ways lie in the hand; the rest of the hand sinks, grey and inert
  const sayOn = wide && lifted.value === PLAY;                                                                  // a leader's card of the say in play: its ways are the hand (sayplay.js)
  const fieldWide = fieldOpen.value && wide && !middle;                                                   // the new goal's field lies in the hand's place (spec 168 D2)
  const sunk = !!(cards || deal || chair || (s && wide) || fieldWide || sayOn);                                    // what the person plays lies in the hand's place: the hand's own cards sink (spec 168 D1, D2)
  const places = columnOn() && !bare ? html`<${Backpack} /><${Book} />` : null;                                // the places that change the table: the die, the backpack, the book (spec 168 A5)
  const pots = !columnOn() ? html`<${Mana} lifted=${s} />` : bare ? html`<${PotionRow} above=${true} />` : null;
  const anchor = key ? root.current?.querySelector(`.hand-places .hand-card[data-key="${CSS.escape(key)}"]`) : null;
  return html`<footer ref=${root} class="hand" aria-label="The hand" data-empty=${middle ? "1" : undefined}>
    ${carrying && html`<div class="hand-places"><div class="hand-row is-carrying" style=${`--hc-rest:${Math.max(1, lanesBeforeEnd())}`}><${Carry} /><div class="hand-end"><${PlayDie} />${places}${pots}</div></div></div>`}
    ${!middle && !carrying && html`<div class="hand-places"><div class=${sunk ? "hand-row is-sunk" : "hand-row"} inert=${sunk ? true : undefined} style=${`--hc-rest:${Math.max(1, lanesBeforeEnd())}`}>
      <${Stacks} stacks=${stacks} plus=${bare ? null : html`<${PlusCard} onPress=${plus} />`} />
      <div class="hand-end">${!bare && html`<${PlayDie} />`}${places}${pots}</div>
    </div></div>`}
    ${fieldOpen.value && !middle && html`<${Field} />`}
    ${chair && html`<${ChairDeal} />`}
    ${s && (cards ? html`<${AnswerLifted} s=${s} anchor=${anchor} set=${cards} />` : wide ? (s.kind === "conflict" ? html`<${ConflictPlay} s=${s} />` : html`<${LiftedWide} s=${s} />`) : html`<${Lifted} s=${s} anchor=${anchor} />`)}
    ${sayOn && html`<${SayLifted} />`}
    ${deal && html`<${ProjectDeal} which=${deal} />`}
    ${key === ADD_TOOL && html`<${AddTool} />`}
    ${key.startsWith(TOOL) && html`<${ToolCard} tool=${key.slice(TOOL.length)} />`}
    <${SetupCard} />
    ${!columnOn() && html`<${SetupBubble} />`}
    ${middle && html`<div class="hand-mana-only"><${PlayDie} />${places}${pots}</div>`}
    <span class="hand-live" role="status" aria-live="polite">${said.value}</span>
    ${middle && html`<${Middle}>${fieldOpen.value ? html`<${Field} middle=${true} />` : html`<${PlusCard} large=${true} onPress=${plus} />`}<//>`}
  </footer>`;
}
