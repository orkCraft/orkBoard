// The Play die (docs/specs/112-the-bars-marks-and-the-play-die.md §3.2–§3.3, decisions §190.2–§190.3): Play is a die lying in the hand, at its right end, left of the potions — orkUI's `.ork-die` (0.22.0), seen from above, the card's greys with
// pips in the muted ink, turned by the lean token — and its word under it, as a potion's share is: *Play*, *Playing* while the preview is open and its build plays. The pane's head has no Play any more. Hovered, it wobbles once (`is-wobbling`, put on
// at pointer enter and taken off at its `animationend`) and stays lifted; not under reduced motion. Pressed it opens the `play` view over the pane (as the title's button did), and pressed again, while that view is open, it closes it (`aria-label`
// *Play: the project's preview of dev*, *Close the preview* while open). It is a `<button>`; the die inside is `aria-hidden`. On a touch phone upright (frame/upright.js) and in the phone's app there is no Play: no die.
// The seam with the play view (arena/play.js): three signals and the die's rectangle. `thrown`: the die is out on the pane (it flew from here and rolls), so this one is hidden (kept in its place: `visibility`) until the frame rises or the failure
// takes its place; `playing`: the view is open and its build plays (the pips glow, the word says *Playing*); `warmed`: the view opened on a build already playing, so the die wobbles twice. `dieRect()` is where the throw starts.
import { useEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { closeOver, openOver, over, tab } from "../frame/state.js";
import { leaving } from "../shell/store.js";
import { litKey } from "../table/card.js";
import { mapName, partiesAll } from "../table/data.js";

export const thrown = signal(false);          // the die is out on the pane: this one is hidden
export const playing = signal(false);         // the play view is open and its build plays
export const warmed = signal(0);              // counts the views opened on a build already playing: the die wobbles twice

export const PLAY = "Play", PLAYING = "Playing", PLAY_WORDS = "Play: the project's preview of dev", CLOSE_WORDS = "Close the preview";

let rectOf = () => null;
/** Where the throw starts: the hand's die as a rectangle (null when it is not drawn). */
export const dieRect = () => rectOf();

const reduced = () => { try { return !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches; } catch { return false; } };

/** Opens the play view over the pane, or closes it when it is the one open. */
export function pressPlay() {
  const o = over.peek();
  if (o?.kind === "play") {
    leaving(() => { const key = closeOver(); if (key) litKey.value = key; });
    return;
  }
  openOver("play", {}, o?.from || { title: mapName(tab.peek(), partiesAll()), key: "" }, "Play");
}

export function PlayDie() {
  const [wob, setWob] = useState({ key: 0, left: 0 }), button = useRef(null);
  const open = over.value?.kind === "play", glow = open && playing.value, gone = thrown.value, words = open ? CLOSE_WORDS : PLAY_WORDS;
  useEffect(() => {
    rectOf = () => button.current?.querySelector(".ork-die")?.getBoundingClientRect() || null;
    return () => { rectOf = () => null; };
  }, []);
  const seen = useRef(warmed.peek());
  useEffect(() => { if (warmed.value !== seen.current) { seen.current = warmed.value; if (!reduced()) setWob((w) => ({ key: w.key + 1, left: 2 })); } }, [warmed.value]);
  const hover = () => { if (!reduced()) setWob((w) => (w.left ? w : { key: w.key + 1, left: 1 })); };
  const ended = (e) => { if (e.animationName === "ork-die-wobble") setWob((w) => (w.left > 1 ? { key: w.key + 1, left: w.left - 1 } : { key: w.key, left: 0 })); };
  return html`<button ref=${button} type="button" class=${cls("hand-die", { "is-gone": gone })} data-open=${open ? "1" : undefined} aria-label=${words} title=${words}
      onClick=${pressPlay} onPointerEnter=${hover}>
    <span key=${wob.key} class=${cls("ork-die face-5", { "is-playing": glow, "is-wobbling": wob.left > 0 })} aria-hidden="true" onAnimationEnd=${ended}></span>
    <span class="hand-die__word">${glow ? PLAYING : PLAY}</span>
  </button>`;
}
