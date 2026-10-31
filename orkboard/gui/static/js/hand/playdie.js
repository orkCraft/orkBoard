// The Play die (docs/specs/112-the-bars-marks-and-the-play-die.md §3.2–§3.3, decisions §190.2–§190.3): Play is a die lying in the hand, at its right end, left of the potions — orkUI's `.ork-die` (a cube in CSS 3D since 0.24.0: `DieCube`, its six faces, seen from above, lit from above, the card's greys with
// pips in the muted ink), turned by the lean token — and its word under it, as a potion's share is: *Play*, *Playing* while the preview is open and its build plays. The pane's head has no Play any more. Hovered, it wobbles once (`is-wobbling`: the cube rocks on its edges, put on
// at pointer enter and taken off at the cube's `animationend` named `ork-die-wobble`) and stays lifted; not under reduced motion. Pressed it opens the `play` view over the pane (as the title's button did), and pressed again, while that view is open, it closes it (`aria-label`
// *Play: the project's preview of dev*, *Close the preview* while open). It is a `<button>`; the die inside is `aria-hidden`. On a touch phone upright (frame/upright.js) and in the phone's app there is no Play: no die.
// **Asleep** (docs/specs/113-a-project-with-no-preview-or-no-gate.md §3, decisions §191.1): a project with no preview (the snapshot's `preview` is "": no checks.toml `preview`, no index.html, no dev script) has a die that sleeps: grey and still
// (`is-asleep`: no wobble, no lift, no glow), its word still *Play*, its `title` *Nothing to play yet* (and ': say how the project opens' after it for a screen reader). Pressed, it opens the play view as always, which says *Nothing here yet* and how, and throws nothing.
// **The up face** (docs/specs/118-the-dies-up-face.md, decisions §196): the die says by its up face what pressing Play would show, from the snapshot's `play_face` (the computer's alone): the cross (`face-no`) while the last start of dev's head failed,
// the spark (`face-new`) when dev's head is a commit the person has not tried in Play yet, else today's five; asleep it is the five, whatever the snapshot says. Its `title` and `aria-label` then say it (*Play: it did not start last time*, *Play: dev has changed since you last
// played*), after *Close the preview* and *Nothing to play yet*. When the face changes after the die was first drawn with a snapshot (not on the first one), the cube rolls onto it: `is-landing` is put on the die until the cube's `animationend` named `ork-die-land` (the faces'
// shades end theirs as `ork-die-land-<side>`, ignored); not under reduced motion, not while the die is out on the pane or asleep. A wobble and a landing never run together (both are the cube's `animation`): a landing is skipped while a wobble runs, and a wobble (hover, a warm start) puts an
// unfinished landing out.
// The seam with the play view (arena/play.js): three signals and the die's rectangle. `thrown`: the die is out on the pane (it flew from here and rolls), so this one is hidden (kept in its place: `visibility`) until the frame rises or the failure
// takes its place; `playing`: the view is open and its build plays (the pips glow, the word says *Playing*); `warmed`: the view opened on a build already playing, so the die wobbles twice. `dieRect()` is where the throw starts.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { town } from "../link.js";
import { closeOver, openOver, over, tab } from "../frame/state.js";
import { leaving } from "../shell/store.js";
import { litKey } from "../table/card.js";
import { mapName, partiesAll } from "../table/data.js";

export const thrown = signal(false);          // the die is out on the pane: this one is hidden
export const playing = signal(false);         // the play view is open and its build plays
export const warmed = signal(0);              // counts the views opened on a build already playing: the die wobbles twice

export const PLAY = "Play", PLAYING = "Playing", PLAY_WORDS = "Play: the project's preview of dev", CLOSE_WORDS = "Close the preview";
export const ASLEEP = "Nothing to play yet", ASLEEP_WORDS = `${ASLEEP}: say how the project opens`;
export const FAILED_WORDS = "Play: it did not start last time", NEW_WORDS = "Play: dev has changed since you last played";

/** What orkUI's die holds (0.24.0): its cube and the cube's six faces; the die's classes (its face, its state) say which face is up and how it moves. */
export const DieCube = () => html`<span class="ork-die__cube"><i class="ork-die__face is-up"></i><i class="ork-die__face is-front"></i><i class="ork-die__face is-right"></i><i class="ork-die__face is-back"></i><i class="ork-die__face is-left"></i><i class="ork-die__face is-down"></i></span>`;

/** The project has no preview to play (the snapshot's `preview` is ""; undefined, before the first snapshot, is not): the die sleeps. */
export const asleepNow = () => town.value?.preview === "";

let rectOf = () => null;
/** Where the throw starts: the hand's die as a rectangle (null when it is not drawn). */
export const dieRect = () => rectOf();

/** The die's up face, from the snapshot's `play_face` ("failed" the cross, "new" the spark, else the five); asleep it is the five. */
export const faceNow = () => (asleepNow() ? "5" : { failed: "no", new: "new" }[town.value?.play_face] || "5");

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
  const [wob, setWob] = useState({ key: 0, left: 0 }), [land, setLand] = useState(false), button = useRef(null);
  const asleep = asleepNow(), open = over.value?.kind === "play", glow = open && playing.value && !asleep, gone = thrown.value, face = faceNow(), known = !!town.value;
  const said = face === "no" ? FAILED_WORDS : face === "new" ? NEW_WORDS : PLAY_WORDS, words = open ? CLOSE_WORDS : said;
  useEffect(() => {
    rectOf = () => button.current?.querySelector(".ork-die")?.getBoundingClientRect() || null;
    return () => { rectOf = () => null; };
  }, []);
  const was = useRef(null);                                                           // the face before, null until a snapshot is known: the first one rolls nothing
  useLayoutEffect(() => {                                                             // before the paint: the new face is never seen standing for a frame before it rolls in
    const before = was.current;
    was.current = known ? face : null;
    if (before && before !== face && !reduced() && !gone && !asleep && wob.left === 0) setLand(true);
  }, [face, known]);
  const seen = useRef(warmed.peek());
  useEffect(() => { if (warmed.value !== seen.current) { seen.current = warmed.value; if (!reduced()) { setLand(false); setWob((w) => ({ key: w.key + 1, left: 2 })); } } }, [warmed.value]);
  const hover = () => { if (!reduced() && !asleep) { setLand(false); setWob((w) => (w.left ? w : { key: w.key + 1, left: 1 })); } };
  const ended = (e) => {
    if (e.animationName === "ork-die-wobble") setWob((w) => (w.left > 1 ? { key: w.key + 1, left: w.left - 1 } : { key: w.key, left: 0 }));
    else if (e.animationName === "ork-die-land") setLand(false);
  };
  return html`<button ref=${button} type="button" class=${cls("hand-die", { "is-gone": gone, "is-asleep": asleep })} data-open=${open ? "1" : undefined} aria-label=${asleep && !open ? ASLEEP_WORDS : words} title=${asleep && !open ? ASLEEP : words}
      onClick=${pressPlay} onPointerEnter=${hover}>
    <span key=${wob.key} class=${cls(`ork-die face-${face}`, { "is-playing": glow, "is-wobbling": wob.left > 0 && !asleep, "is-landing": land && wob.left === 0 && !asleep })} aria-hidden="true" onAnimationEnd=${ended}><${DieCube} /></span>
    <span class="hand-die__word">${glow ? PLAYING : PLAY}</span>
  </button>`;
}
