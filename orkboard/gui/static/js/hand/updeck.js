// The phone's crown and field (docs/decisions.md §180.4–§180.5, §195.1, §195.4, docs/specs/103 "Changed since", docs/specs/117 §3).
// **The crown** (`More`) is the Orkmaster's crowned head at the top row's left: until the menu of the leaders lands (spec 117 C) it opens the page's menu (table/menu.js) in a 44 px target: *Stop all* (the tabs' own halt), the project's name and
// *Switch project*, *Settings*; Esc or a press away closes it. *New goal* is the + card at the hand's row's right end (uprow.js): a press opens the hand's field (pluscard.js) over the keyboard with the microphone in it (voice.js).
// The field sits on the visual viewport's foot, so the keyboard does not cover it.
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { command } from "../link.js";
import { openOver } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { Menu } from "../table/menu.js";
import { orkHeadOf } from "./context.js";
import { Field } from "./pluscard.js";
import { VOICE_TIP, canSpeak, listening, toggleVoice } from "./voice.js";

/** The crown: the Orkmaster's crowned head, a 44 px button; its label says what it opens. */
export function More() {
  const from = { title: "", key: "" }, name = currentProject.value?.name || "", o = orkHeadOf();
  const items = [["Stop all", () => command("halt").catch(() => {}), true, "stop"], ["Switch project", () => openOver("projects", {}, from, "Projects"), false, "list-box"], ["Settings", () => openOver("settings", {}, from, "Settings"), false, "sliders"]];
  return html`<${Menu} label="The leaders and their goals" own="up-crown" face=${html`<${Head} race=${o.race} tier=${o.tier} />`} items=${items} top=${name ? html`<p class="up-menu__project" data-project="1">${name}</p>` : null} />`;
}

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
