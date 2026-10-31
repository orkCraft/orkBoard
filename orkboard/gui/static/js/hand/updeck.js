// The phone's field (docs/decisions.md §180.4, §195.4, docs/specs/103 "Changed since", docs/specs/117 §3): *New goal* is the + card at the hand's row's right end (uprow.js); a press opens the hand's field (pluscard.js) over the keyboard with the
// microphone in it (voice.js). The field sits on the visual viewport's foot, so the keyboard does not cover it. (The crown and its menu of the leaders are upmenu.js's; **…** and its rows went to that menu, spec 117 C.)
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { Field } from "./pluscard.js";
import { VOICE_TIP, canSpeak, listening, toggleVoice } from "./voice.js";

/** The microphone in the field; none where the browser has no way to recognise a voice (decisions §125.3). */
function Mic() {
  if (!canSpeak) return null;
  return html`<button type="button" class=${cls("ork-btn quiet up-mic", { "is-on": listening.value })} aria-label="Speak the goal" aria-pressed=${String(listening.value)} title=${VOICE_TIP} onClick=${toggleVoice}><${Icon} name="mic" /></button>`;
}

/** Keeps the field's foot on the visual viewport's, the height the keyboard takes of the layout viewport, so the field lies over it. */
function useKeyboard(box) {
  useEffect(() => {
    const vv = window.visualViewport, el = box.current;
    if (!vv || !el) return undefined;
    const set = () => { el.style.bottom = `${Math.max(0, Math.round(window.innerHeight - vv.height - vv.offsetTop))}px`; };
    set();
    vv.addEventListener("resize", set);
    vv.addEventListener("scroll", set);
    return () => { vv.removeEventListener("resize", set); vv.removeEventListener("scroll", set); };
  }, []);
}

/** The field the + card opens, over the keyboard, the microphone in its corner. */
export function DeckField() {
  const box = useRef();
  useKeyboard(box);
  return html`<div class="up-field" ref=${box}><${Field} middle=${true} /><${Mic} /></div>`;
}
