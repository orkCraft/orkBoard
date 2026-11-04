// The Play die (docs/specs/112-the-bars-marks-and-the-play-die.md §3.2–§3.3, decisions §190.2–§190.3): Play is a die lying in the hand, at its right end, left of the potions — orkUI's `.ork-die` (a cube in CSS 3D since 0.24.0: `DieCube`, its six faces, seen from above, lit from above, the card's greys with
// pips in the muted ink), turned by the lean token — and its word under it, as a potion's share is: *Play*, *Playing* while the preview is open and its build plays. The pane's head has no Play any more. Hovered, it wobbles once (`is-wobbling`: the cube rocks on its edges, put on
// at pointer enter and taken off at the cube's `animationend` named `ork-die-wobble`) and stays lifted; not under reduced motion. Pressed it opens the `play` view over the pane (as the title's button did), and pressed again, while that view is open, it closes it (`aria-label`
// *Play: the project's preview of dev*, *Close the preview* while open). It is a `<button>`; the die inside is `aria-hidden`. On a touch phone upright (frame/upright.js) and in the phone's app there is no Play: no die.
// **Asleep** (docs/specs/113-a-project-with-no-preview-or-no-gate.md §3, decisions §191.1): a project with no preview (the snapshot's `preview` is "": no checks.toml `preview`, no index.html, no dev script) has a die that sleeps: grey and still
// (`is-asleep`: no wobble, no lift, no glow), its word still *Play*, its `title` *Nothing to play yet* (and ': say how the project opens' after it for a screen reader). Pressed, it opens the play view as always, which says *Nothing here yet* and how, and throws nothing.
// **The up face** (docs/specs/118-the-dies-up-face.md, decisions §196): the die says by its up face what pressing Play would show, from the snapshot's `play_face` (the computer's alone): the cross (`face-no`) while the last start of dev's head failed,
// the spark (`face-new`) when dev's head is a commit the person has not tried in Play yet, else the play arrow (`face-play`, orkUI 0.28.0, decisions §200.1); asleep it is the five, whatever the snapshot says. Its `title` and `aria-label` then say it (*Play: it did not start last time*, *Play: dev has changed since you last
// played*), after *Close the preview* and *Nothing to play yet*. **The pips** (decisions §200.5): when the snapshot's `new_n` counts goals landed in dev since the last play, the up face is that many pips in the ink (`face-1` … `face-6`, six for six or more; `is-news` inks them,
// mana.css) in place of the spark, and the `title` says it (*Play: 3 new goals in dev since you last played*); a `new_n` of 0 (only the person's own commits are new) keeps the spark. At rest an awake die shows the play arrow (the pips' muted ink; the ink and the glow while it plays), a sleeping one the five. When the face changes after the die was first drawn with a snapshot (not on the first one), the cube rolls onto it: `is-landing` is put on the die until the cube's `animationend` named `ork-die-land` (the faces'
// shades end theirs as `ork-die-land-<side>`, ignored); not under reduced motion, not while the die is out on the pane or asleep. A wobble and a landing never run together (both are the cube's `animation`): a landing is skipped while a wobble runs, and a wobble (hover, a warm start) puts an
// unfinished landing out.
// **The die in a goal's rune** (spec 128 F.3, decisions §206.8): with a goal done or at work picked, the die wears its rune's colour (`data-elem`: mana.css gives the pips and the edge orkUI's element token), its `title` and `aria-label` say *Play: <goal>* (the rest of
// the words keep their order: *Close the preview* while it is open, *Nothing to play yet* asleep), and pressed it plays dev with that goal in it (`ideas.play {idea}`).
// **The front face** (docs/specs/139-the-die-the-door-and-the-bug.md A.1–A.3, decisions §246.1–§246.3, orkUI 0.29.0): the die is no longer one button. The whole die is the Play press (`hand-die__play`), and the front face is a second `<button>` (`hand-die__stop`, *Stop all: stop every run
// of this project's orks*) laid over its projected box (`lay`: measured, split at the middle between the up face's bottom and the front's top; laid again on a resize, on a draw and after a wobble, a landing or a turn). The die wears `front-stop`, and `is-orks-running` while `isWorking` says a task runs
// (table/door.js `useOrks`): the mark is muted else, the danger's only then. Pressed it asks the host to stop everything (`halt`, door.js); then its word says *Stopped* (muted, `aria-disabled`) until work starts. Under the die its two words: *Play* · *Stop all* (*Playing*, *Stopped*),
// *Stop all* in the danger colour only while running. A sleeping die sleeps on its up face alone: Stop all stays pressable. **Resume** (docs/specs/139-the-die-the-door-and-the-bug.md B.3, decisions §246.3): while the snapshot says `stopped` (the host keeps it, table/door.js) the front face wears `front-resume` and `is-orks-stopped` (orkUI's circular arrow in the ink), its button says *Resume: the orks go back to work*, the word under the die *Stopped*, and pressed it sends `resume`. On each change between stop and resume the die turns: `is-turning` is put on and, at the cube's `animationend` named `ork-die-turn`, taken off and the front mark swapped; under reduced motion there is no turn and the mark swaps at once (a halt from an older host, which does not send `stopped`, keeps *Stopped* muted and nothing to press).
// The seam with the play view (arena/play.js): three signals and the die's rectangle. `thrown`: the die is out on the pane (it flew from here and rolls), so this one is hidden (kept in its place: `visibility`) until the frame rises or the failure
// takes its place; `playing`: the view is open and its build plays (the pips glow, the word says *Playing*); `warmed`: the view opened on a build already playing, so the die wobbles twice. `dieRect()` is where the throw starts.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { town } from "../link.js";
import { closeOver, openOver, over, picked, tab } from "../frame/state.js";
import { leaving } from "../shell/store.js";
import { litKey } from "../table/card.js";
import { mapName, partiesAll } from "../table/data.js";
import { nodeOf, playable } from "../table/goalmap.js";
import { halt, resume, useOrks } from "../table/door.js";

export const thrown = signal(false);          // the die is out on the pane: this one is hidden
export const playing = signal(false);         // the play view is open and its build plays
export const warmed = signal(0);              // counts the views opened on a build already playing: the die wobbles twice

export const PLAY = "Play", PLAYING = "Playing", PLAY_WORDS = "Play: the project's preview of dev", CLOSE_WORDS = "Close the preview";
export const ASLEEP = "Nothing to play yet", ASLEEP_WORDS = `${ASLEEP}: say how the project opens`;
export const FAILED_WORDS = "Play: it did not start last time", NEW_WORDS = "Play: dev has changed since you last played";
export const PIPS_MAX = 6;
export const STOP = "Stop all", STOPPED = "Stopped", STOP_WORDS = "Stop all: stop every run of this project's orks", RESUME_WORDS = "Resume: the orks go back to work";
/** *Play: 3 new goals in dev since you last played*, *Play: 1 new goal in dev …*. */
export const newGoalsWords = (n) => `Play: ${n} new ${n === 1 ? "goal" : "goals"} in dev since you last played`;

/** What orkUI's die holds (0.24.0): its cube and the cube's six faces; the die's classes (its face, its state) say which face is up and how it moves. */
export const DieCube = () => html`<span class="ork-die__cube"><i class="ork-die__face is-up"></i><i class="ork-die__face is-front"></i><i class="ork-die__face is-right"></i><i class="ork-die__face is-back"></i><i class="ork-die__face is-left"></i><i class="ork-die__face is-down"></i></span>`;

/** The project has no preview to play (the snapshot's `preview` is ""; undefined, before the first snapshot, is not): the die sleeps. */
export const asleepNow = () => town.value?.preview === "";

let rectOf = () => null;
/** Where the throw starts: the hand's die as a rectangle (null when it is not drawn). */
export const dieRect = () => rectOf();

/** How many goals landed in dev since the last play (the snapshot's `new_n`): 0 with the face not `new`, asleep, or no count. */
export function newCount() {
  const n = Math.floor(Number(town.value?.new_n));
  return !asleepNow() && town.value?.play_face === "new" && Number.isFinite(n) && n > 0 ? n : 0;
}

/** The die's up face, from the snapshot's `play_face` ("failed" the cross, "new" the spark, else the play arrow at rest) and `new_n` (a `new` face with goals landed is `1` … `6`: the pips in place of the spark); asleep it is the five, grey: the arrow never promises a Play that cannot start. */
export const faceNow = () => (asleepNow() ? "5" : newCount() ? String(Math.min(PIPS_MAX, newCount())) : { failed: "no", new: "new" }[town.value?.play_face] || "play");

const reduced = () => { try { return !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches; } catch { return false; } };

/** The goal picked when the die wears its rune (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.3, decisions §206.8): a goal done or at work; null for none. */
export const runeGoal = () => { const n = nodeOf(picked.value); return playable(n) ? n : null; };
/** *Play: Lobby music*: the die's words while a goal done or at work is picked. */
export const goalPlayWords = (n) => `Play: ${n.short || n.title}`;

/** Opens the play view over the pane, or closes it when it is the one open. With a goal done or at work picked (`goal`, its node) the view plays dev with that goal in it: `ideas.play {idea}`, as the night's card plays a goal (hand/nightcard.js `playIt`). */
export function pressPlay(goal = null) {
  const o = over.peek();
  if (o?.kind === "play") {
    leaving(() => { const key = closeOver(); if (key) litKey.value = key; });
    return;
  }
  openOver("play", goal ? { idea: goal.slug } : {}, o?.from || { title: mapName(tab.peek(), partiesAll()), key: "" }, "Play");
}

/** Lays the two presses over the die: the Play press over the whole die, the Stop all press over the front face's projected box (a transformed face's `getBoundingClientRect` is its projection), from the middle between the up face's bottom and the front's top (the mockup's `lay`).
 *  Not while the cube moves (a wobble, a landing, a turn): the next `animationend` lays them again. */
function lay(box) {
  const die = box?.querySelector(".ork-die"), stop = box?.querySelector(".hand-die__stop");
  if (!die || !stop || die.matches(".is-wobbling, .is-landing, .is-turning")) return;
  const b = box.getBoundingClientRect(), up = die.querySelector(".is-up").getBoundingClientRect(), fr = die.querySelector(".is-front").getBoundingClientRect();
  if (!fr.width) return;
  const cut = Math.round((up.bottom + fr.top) / 2);
  Object.assign(stop.style, { left: `${fr.left - b.left}px`, top: `${cut - b.top}px`, width: `${fr.width}px`, height: `${Math.max(0, fr.bottom - cut)}px` });
}

export function PlayDie() {
  const [wob, setWob] = useState({ key: 0, left: 0 }), [land, setLand] = useState(false), box = useRef(null);
  const [front, setFront] = useState(false), [turning, setTurning] = useState(false);          // the front mark shown (true: Resume) and the turn between the two
  const asleep = asleepNow(), open = over.value?.kind === "play", glow = open && playing.value && !asleep, gone = thrown.value, face = faceNow(), known = !!town.value, orks = useOrks(), toResume = orks.resumable && orks.stopped;
  const news = newCount(), goal = asleep ? null : runeGoal(), said = goal ? goalPlayWords(goal) : face === "no" ? FAILED_WORDS : news ? newGoalsWords(news) : face === "new" ? NEW_WORDS : PLAY_WORDS, words = open ? CLOSE_WORDS : said;
  useEffect(() => {
    rectOf = () => box.current?.querySelector(".ork-die")?.getBoundingClientRect() || null;
    return () => { rectOf = () => null; };
  }, []);
  useLayoutEffect(() => { lay(box.current); });                                         // after every draw: the die's faces are where the presses go
  useEffect(() => {
    const again = () => lay(box.current);
    addEventListener("resize", again);
    document.fonts?.ready?.then(again);
    return () => removeEventListener("resize", again);
  }, []);
  const was = useRef(null);                                                           // the face before, null until a snapshot is known: the first one rolls nothing
  useLayoutEffect(() => {                                                             // before the paint: the new face is never seen standing for a frame before it rolls in
    const before = was.current;
    was.current = known ? face : null;
    if (before && before !== face && !reduced() && !gone && !asleep && wob.left === 0) setLand(true);
  }, [face, known]);
  const knew = useRef(false);                                                         // a snapshot was seen before: the first one turns nothing
  useLayoutEffect(() => {
    const was = knew.current;
    knew.current = known;
    if (front === toResume) { if (turning) setTurning(false); return; }
    if (!was || reduced() || gone) { setTurning(false); setFront(toResume); return; }
    setLand(false);
    setWob((w) => (w.left ? { key: w.key + 1, left: 0 } : w));                        // a turn, a wobble and a landing never run together
    setTurning(true);
  }, [toResume, known, front]);
  const seen = useRef(warmed.peek());
  useEffect(() => { if (warmed.value !== seen.current) { seen.current = warmed.value; if (!reduced()) { setLand(false); setWob((w) => ({ key: w.key + 1, left: 2 })); } } }, [warmed.value]);
  const hover = () => { if (!reduced() && !asleep && !turning) { setLand(false); setWob((w) => (w.left ? w : { key: w.key + 1, left: 1 })); } };
  const ended = (e) => {
    if (e.animationName === "ork-die-wobble") setWob((w) => (w.left > 1 ? { key: w.key + 1, left: w.left - 1 } : { key: w.key, left: 0 }));
    else if (e.animationName === "ork-die-land") setLand(false);
    else if (e.animationName === "ork-die-turn") { setTurning(false); setFront(toResume); }
    requestAnimationFrame(() => lay(box.current));                                    // the class comes off at the next draw, the presses are laid again after it
  };
  const stopWord = orks.stopped ? STOPPED : STOP, press = () => { if (toResume) resume(); else if (!orks.stopped) halt(); };
  return html`<div class=${cls("hand-die", { "is-gone": gone, "is-asleep": asleep, "is-orks-running": orks.running, "is-orks-stopped": orks.stopped })} data-open=${open ? "1" : undefined} data-elem=${goal?.hue || goal?.element || undefined} data-goal=${goal?.slug || undefined}>
    <span class="hand-die__box" ref=${box}>
      <span key=${wob.key} class=${cls(`ork-die face-${face} ${front ? "front-resume" : "front-stop"}`, { "is-turning": turning && !gone, "is-orks-stopped": front, "is-playing": glow, "is-news": news > 0, "is-wobbling": wob.left > 0 && !asleep, "is-landing": land && wob.left === 0 && !asleep, "is-orks-running": orks.running })} aria-hidden="true" onAnimationEnd=${ended}><${DieCube} /></span>
      <button type="button" class="hand-die__play" aria-label=${asleep && !open ? ASLEEP_WORDS : words} title=${asleep && !open ? ASLEEP : words} onClick=${() => pressPlay(goal)} onPointerEnter=${hover}></button>
      <button type="button" class="hand-die__stop" aria-label=${toResume ? RESUME_WORDS : STOP_WORDS} title=${toResume ? RESUME_WORDS : STOP_WORDS} aria-disabled=${orks.stopped && !toResume ? "true" : undefined} onClick=${press}></button>
    </span>
    <span class="hand-die__words"><span class="hand-die__word" onClick=${() => pressPlay(goal)}>${glow ? PLAYING : PLAY}</span><i class="hand-die__dot" aria-hidden="true">·</i><span class="hand-die__orks" onClick=${press}>${stopWord}</span></span>
  </div>`;
}
