// The phone's hand: **…** at the top right and *New goal* under the thumb (docs/decisions.md §180.4–§180.5, docs/specs/103 "Changed since").
// **…** is the page's menu (table/menu.js) in a 44 px target: *Stop all* (the tabs' own halt), the project's name and *Switch project*, *Settings*; Esc or a press away closes it. *New goal* is the green deck at the bottom right
// over everything (the old phone's button, pwa/shell-fab.js: two edges behind a back with the plus in the action colour): a press opens the hand's field (pluscard.js) over the keyboard with the microphone in it (voice.js).
// The field sits on the visual viewport's foot, so the keyboard does not cover it.
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { command } from "../link.js";
import { openOver } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { Menu } from "../table/menu.js";
import { Field } from "./pluscard.js";
import { VOICE_TIP, canSpeak, listening, toggleVoice } from "./voice.js";
import { fieldOpen } from "./state.js";

/** The top row's **…**. */
export function More() {
  const from = { title: "", key: "" }, name = currentProject.value?.name || "";
  const items = [["Stop all", () => command("halt").catch(() => {}), true, "stop"], ["Switch project", () => openOver("projects", {}, from, "Projects"), false, "list-box"], ["Settings", () => openOver("settings", {}, from, "Settings"), false, "sliders"]];
  return html`<${Menu} label="More" items=${items} top=${name ? html`<p class="up-menu__project" data-project="1">${name}</p>` : null} />`;
}

/** *New goal*: the green deck. */
export function Deck({ onPress }) {
  return html`<button type="button" class="up-deck" aria-label="New goal" title="New goal" aria-haspopup="dialog" aria-expanded=${fieldOpen.value ? "true" : "false"} onClick=${onPress}>
    <i class="up-deck__edge e2" aria-hidden="true"></i><i class="up-deck__edge e1" aria-hidden="true"></i><span class="up-deck__back"><${Icon} name="plus" /></span></button>`;
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

/** The field the deck opens, over the keyboard, the microphone in its corner. */
export function DeckField() {
  const box = useRef();
  useKeyboard(box);
  return html`<div class="up-field" ref=${box}><${Field} middle=${true} /><${Mic} /></div>`;
}
