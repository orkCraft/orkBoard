// The hand names the goal under the pointer (docs/specs/165 I, decisions §280.1): a signal `reachGoal` (a goal's slug, "" for none) set from a hand card's `data-goal` after the pointer rests about 150 ms on it (a mouse or a pen, never touch: a touch
// press lifts the card as it always did and sets nothing) and at once when the keyboard focuses it; cleared when the pointer leaves the hand, when focus leaves it and on Esc. It sends no command: the map's reach (table/reach.js) is read from what the page kept.
import { signal } from "@preact/signals";

export const REST_MS = 150;                       // how long the pointer rests on a card before its reach lights
export const reachGoal = signal("");              // the slug of the goal whose reach the open map shows, "" for none

const CARD = ".hand-card[data-goal]";
let timer = 0, installed = false;

const goalOf = (el) => (el instanceof Element ? el.closest(CARD)?.dataset.goal || "" : "");
const inHand = (el) => el instanceof Element && !!el.closest(".hand");
const stop = () => { if (timer) { clearTimeout(timer); timer = 0; } };
const set = (slug) => { stop(); if (reachGoal.value !== slug) reachGoal.value = slug; };

/** Installed once (a second call changes nothing): listeners on the document, so the cards the hand redraws are heard without being found again. */
export function installReachHover() {
  if (installed || typeof document === "undefined") return;
  installed = true;
  document.addEventListener("pointerover", (e) => {
    if (e.pointerType === "touch") return;
    const slug = goalOf(e.target);
    if (!slug) { if (inHand(e.target)) set(""); return; }
    stop();
    if (slug !== reachGoal.value) timer = setTimeout(() => { timer = 0; set(slug); }, REST_MS);
  });
  document.addEventListener("pointerout", (e) => {
    if (e.pointerType === "touch" || !inHand(e.target) || inHand(e.relatedTarget)) return;
    set("");
  });
  document.addEventListener("focusin", (e) => { const slug = goalOf(e.target); if (slug) set(slug); });
  document.addEventListener("focusout", (e) => { if (inHand(e.target) && !inHand(e.relatedTarget)) set(""); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") set(""); });
}
