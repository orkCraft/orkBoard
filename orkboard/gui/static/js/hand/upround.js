// The phone's round button (goal 169 H, decisions §292.1, §292.4, §293.6; the mockup docs/mockups/phone/feed.html v3, screens 7 and 8): at the foot's right, where the die stood, **one round button whose face is the die in its state** (§223.7: faint while nothing can be
// run, `asleepNow`; white while dev can; in the picked goal's rune while a goal done or at work is picked, `runeGoal`; orkUI's cartoon die, `die/die-rest.png`, tumbling, `die-tumble.png`, while dev has something new to play: `faceNow`). No count on it. Pressed, **the fan rises
// over the foot** (decisions §298.9): the moves only, *New goal* (what the + card does: the + card is drawn only while there is no goal) and *Play* (on a phone Play runs on the computer, so it says so, `PLAY_UP`, and throws nothing), two small cards each with its word in a label beside it,
// the button showing a cross while it is open; the backpack and the book are under *Yours* (upyours.js). A second press, a tap outside (the scrim) or Esc closes it, the focus back on the button; the arrows walk the two. Layout only (upround.css); every colour, face and corner is orkUI's.
import { useEffect, useRef } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Icon, ORKUI } from "../orkui.js";
import { toast } from "../link.js";
import { ASLEEP, FAILED_WORDS, NEW_WORDS, asleepNow, faceNow, goalPlayWords, newCount, newGoalsWords, runeGoal } from "./playdie.js";

export const PLAY_UP = "Play it on the computer";       // the die's line on a phone
export const roundOpen = signal(false);                 // the selector is up
export const FAN = "New goal, Play";                    // the round button's name (decisions §298.9)

/** One of orkUI's cartoon pictures (office/<thing>/<name>.png, its @2x and @3x). */
export const Pic = ({ thing, name, w, h }) => {
  const src = `${ORKUI}/${thing}/${name}`;
  return html`<img class="up-round__pic" src=${`${src}.png`} srcset=${`${src}@2x.png 2x, ${src}@3x.png 3x`} width=${w} height=${h} alt="" draggable="false" />`;
};

/** The die's state as the button wears it: `{state: "faint" | "white" | "rune", elem, face, tumbling, words}`. */
export function dieState() {
  const asleep = asleepNow(), goal = asleep ? null : runeGoal(), face = faceNow(), news = newCount(), tumbling = !asleep && (news > 0 || face === "new");
  const words = asleep ? ASLEEP : goal ? goalPlayWords(goal) : face === "no" ? FAILED_WORDS : news ? newGoalsWords(news) : face === "new" ? NEW_WORDS : "";
  return { state: asleep ? "faint" : goal ? "rune" : "white", elem: goal ? goal.hue || goal.element || "" : "", face, tumbling, words };
}

const close = (back = true) => {
  roundOpen.value = false;
  if (back) document.querySelector(".up-round")?.focus();
};

/** The fan (decisions §298.9): the moves only, two small cards rising over the foot, each with its word in a label beside it; *New goal* does what the + card does (`plus`), *Play* what the die does. */
const MOVES = [
  { key: "new", word: "New goal", label: "New goal", go: (plus) => plus?.() },
  { key: "play", word: "Play", label: PLAY_UP, go: () => toast(PLAY_UP, "information") },
];

function Selector({ plus }) {
  const box = useRef();
  useEffect(() => {
    box.current?.querySelector("button")?.focus();
    const keys = (e) => {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); return; }
      if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
      const all = [...(box.current?.querySelectorAll("button") || [])], at = all.indexOf(document.activeElement);
      if (at < 0) return;
      e.preventDefault();
      all[(at + (e.key === "ArrowDown" ? 1 : all.length - 1)) % all.length].focus();
    };
    document.addEventListener("keydown", keys, true);
    return () => document.removeEventListener("keydown", keys, true);
  }, []);
  return html`<div class="up-round__scrim" aria-hidden="true" onClick=${() => close()}></div>
    <div class="up-sel up-fan" id="up-sel" ref=${box} role="group" aria-label=${FAN}>${MOVES.map((o) => html`
      <button key=${o.key} type="button" class="up-fan__opt" data-place=${o.key} aria-label=${o.label} title=${o.label} onClick=${() => { close(false); o.go(plus); }}>
        <b class="up-fan__lab">${o.word}</b>
        <span class="ork-card up-fan__card" aria-hidden="true">${o.key === "new" ? html`<${Icon} name="plus" />` : html`<${Pic} thing="die" name="die-rest" w=${31} h=${32} />`}</span></button>`)}</div>`;
}

/** The round button and, while it is pressed, its selector. */
export function Round({ plus }) {
  const d = dieState(), open = roundOpen.value, name = FAN;
  useEffect(() => () => { roundOpen.value = false; }, []);
  return html`${open && html`<${Selector} plus=${plus} />`}
    <button type="button" class=${cls("up-round", { "is-open": open })} data-state=${d.state} data-elem=${d.elem || undefined} data-face=${d.face} aria-label=${name} title=${d.words ? `${name} · ${d.words}` : name}
      aria-expanded=${open ? "true" : "false"} aria-controls="up-sel" onClick=${() => { if (roundOpen.peek()) close(); else roundOpen.value = true; }}>
      <span class="up-round__face">${open ? html`<${Icon} name="close" />` : html`<${Pic} thing="die" name=${d.tumbling ? "die-tumble" : "die-rest"} w=${31} h=${32} />`}</span></button>`;
}
