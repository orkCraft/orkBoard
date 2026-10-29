// The hand upright, the first screen of a touch phone (docs/specs/103-the-phones-app-a-native-frame.md §1, decisions §174.1, §178, §179; the mockup docs/mockups/phone/): from the top, the Orkmaster's line when the work moved on (table/notice.js),
// the AI tools' row (mana.js `Tools`) at the left of *The Board*, the top card's context (context.js), the one stack — every stop in Needs you's order, a goal's cards together, the top one drawn as the lifted card with its answers on it, the
// ones under it only as the edges of their backs, never a count —, and the blank card with the microphone at the foot. With nothing in the hand there is no context: the blank card lies large in the middle, the tools' row and *The Board* stay.
// When the card on top is answered the next one comes at once, its context with it (no motion of its own). The card on top is also the picked goal, so turning the phone to its side lights the same goal on the table (§150.4).
// *The Board* is frame/upright.js `showBoard`: the native frame turns the phone, a browser says to turn it by hand.
import { useEffect } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { picked } from "../frame/state.js";
import { showBoard, turnLine } from "../frame/upright.js";
import { Notice } from "../table/notice.js";
import { Context } from "./context.js";
import { goalOfStop } from "./data.js";
import { Tools } from "./mana.js";
import { Field, PlusCard } from "./pluscard.js";
import { Lifted } from "./stopcard.js";
import { fieldOpen } from "./state.js";
import { VOICE_TIP, canSpeak, listening, toggleVoice } from "./voice.js";

const EDGES = 5;                                                  // the backs under the top that show (the stack's depth, never a number)
const FAN = [null, [7, 3], [-7, -3], [10, 4], [-10, -4], [9, 2]];       // each back's step aside in px and turn in degrees, by turns right and left (as stacks.js)

/** The backs of the cards under the top one, laid as a fan. */
function Edges({ n }) {
  return Array.from({ length: n }, (_, k) => n - k).map((i) => html`<i key=${i} class="ork-card-back up-edge" style=${`--dx:${FAN[i][0]};--rot:${FAN[i][1]};--ork-deck-i:${i}`} aria-hidden="true"></i>`);
}

/** The microphone on the blank card; none where the browser has no way to recognise a voice. */
function Mic({ big = false }) {
  if (!canSpeak) return null;
  return html`<button type="button" class=${cls("ork-btn quiet up-mic", { "is-on": listening.value, "is-big": big })} aria-label="Speak the goal" aria-pressed=${String(listening.value)} title=${VOICE_TIP} onClick=${toggleVoice}><${Icon} name="mic" /></button>`;
}

/** The blank card, full width at the foot (or large in the middle), with the microphone on it. */
function Blank({ big = false, onPress }) {
  return html`<div class=${cls("up-blank", { "is-big": big })}><${PlusCard} large=${big} onPress=${onPress} /><${Mic} big=${big} /></div>`;
}

/** The line that says the Board is on the phone's side (in a browser): a status, not a dialog. */
function TurnLine() {
  return turnLine.value ? html`<p class="up-turn" role="status" data-turn="1">${turnLine.value}</p>` : null;
}

/** The hand upright. `root`: the hand's element ref (the keys), `stacks`: data.js `stacksOf`, `plus`: opens the field. */
export function Upright({ root, stacks, plus }) {
  const flat = stacks.flatMap((st) => st.cards), top = flat[0] || null, under = Math.min(EDGES, Math.max(0, flat.length - 1));
  useEffect(() => { picked.value = top ? goalOfStop(top) : ""; }, [top?.key]);           // the card on top is the goal lit on the table when the phone turns (§150.4)
  const field = fieldOpen.value;
  return html`<footer ref=${root} class="hand hand-up" aria-label="The hand" data-upright="1" data-empty=${top ? undefined : "1"}>
    <${Notice} />
    <div class="up-top"><${Tools} /><button type="button" class="ork-btn up-board" onClick=${showBoard}>The Board</button></div>
    <${TurnLine} />
    ${top && html`<${Context} s=${top} />`}
    ${top ? html`<div class="up-stack" data-n=${under}><${Edges} n=${under} /><${Lifted} key=${top.key} s=${top} inline=${true} /></div>`
      : html`<div class="up-mid">${field ? html`<${Field} middle=${true} />` : html`<${Blank} big=${true} onPress=${plus} />`}</div>`}
    ${top && html`<div class="up-foot">${field ? html`<${Field} middle=${true} />` : html`<${Blank} onPress=${plus} />`}</div>`}
  </footer>`;
}
