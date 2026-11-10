// The phone's round button (goal 169 H, decisions §292.1, §292.4, §293.6; the mockup docs/mockups/phone/feed.html v3, screens 7 and 8): at the foot's right, where the die stood, **one round button whose face is the die in its state** (§223.7: faint while nothing can be
// run, `asleepNow`; white while dev can; in the picked goal's rune while a goal done or at work is picked, `runeGoal`; orkUI's cartoon die, `die/die-rest.png`, tumbling, `die-tumble.png`, while dev has something new to play: `faceNow`). No count on it. Pressed, **a selector of
// three rises over the foot**, each a pill with its picture, its word and its line, 44 px at least: **Play** (the die: on a phone Play runs on the computer, so it says so, `PLAY_UP`, and throws nothing), **Inventory** (the backpack: table/backpack.js's `openInventory`)
// and **History** (the book: table/history.js `openHistory`). A second press, a tap outside (the scrim) or Esc closes it, the focus back on the button; the arrows walk the three. Layout only (upround.css); every colour, face and corner is orkUI's.
import { useEffect, useRef } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { ORKUI } from "../orkui.js";
import { toast } from "../link.js";
import { openInventory } from "../frame/state.js";
import { openHistory } from "../table/history.js";
import { ASLEEP, FAILED_WORDS, NEW_WORDS, asleepNow, faceNow, goalPlayWords, newCount, newGoalsWords, runeGoal } from "./playdie.js";

export const PLAY_UP = "Play it on the computer";       // the die's line on a phone
export const ROUND = "Play, Inventory, History";        // the round button's name
export const roundOpen = signal(false);                 // the selector is up

/** One of orkUI's cartoon pictures (office/<thing>/<name>.png, its @2x and @3x). */
const Pic = ({ thing, name, w, h }) => {
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

/** The selector's three: each its picture, its word and its line; a press closes the selector and does what the place does today. */
const OPTIONS = [
  { key: "play", word: "Play", line: "on the computer", label: PLAY_UP, pic: ["die", "die-rest", 31, 32], go: () => toast(PLAY_UP, "information") },
  { key: "inventory", word: "Inventory", line: "how the project is set", label: "Inventory: how the project is set", pic: ["pack", "pack-shut", 32, 32], go: () => openInventory() },
  { key: "history", word: "History", line: "what was done, by day", label: "History: what was done, by day", pic: ["book", "book-shut", 47, 40], go: () => openHistory() },
];

function Selector() {
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
    <div class="up-sel" id="up-sel" ref=${box} role="group" aria-label=${ROUND}>${OPTIONS.map((o) => html`
      <button key=${o.key} type="button" class="up-sel__opt" data-place=${o.key} aria-label=${o.label} title=${o.label} onClick=${() => { close(false); o.go(); }}>
        <span class="up-sel__words"><b class="up-sel__word">${o.word}</b><span class="up-sel__line">${o.line}</span></span><${Pic} thing=${o.pic[0]} name=${o.pic[1]} w=${o.pic[2]} h=${o.pic[3]} /></button>`)}</div>`;
}

/** The round button and, while it is pressed, its selector. */
export function Round() {
  const d = dieState(), open = roundOpen.value;
  useEffect(() => () => { roundOpen.value = false; }, []);
  return html`${open && html`<${Selector} />`}
    <button type="button" class=${cls("up-round", { "is-open": open })} data-state=${d.state} data-elem=${d.elem || undefined} data-face=${d.face} aria-label=${ROUND} title=${d.words ? `${ROUND} · ${d.words}` : ROUND}
      aria-expanded=${open ? "true" : "false"} aria-controls="up-sel" onClick=${() => { if (roundOpen.peek()) close(); else roundOpen.value = true; }}>
      <span class="up-round__face"><${Pic} thing="die" name=${d.tumbling ? "die-tumble" : "die-rest"} w=${31} h=${32} /></span></button>`;
}
