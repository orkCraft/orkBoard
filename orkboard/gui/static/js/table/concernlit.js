// One concern, three places (docs/specs/168 D4, decisions §283.21): the card in the hand (hand/concerncard.js, key `concern/<party>/<id>`), the small card in the party's header (concernrow.js, `data-concern-id="<party>/<id>"`) and the mark on the scheme
// (concerns.js `Mark`) are one thing: one hovered or focused, or the one lifted, lights the others. `lit` is its id (`<party>/<id>`), "" for none; a face reads `isLit(party, id)`. The hand's card is a button of the hand (stopcard.js) that this
// module does not draw: it marks it `data-lit` from here, as the card is found by its key. Installed once for the whole page; nothing here sends a command.
import { computed, effect, signal } from "@preact/signals";
import { lifted } from "../frame/state.js";

const HAND_KEY = "concern/";
const hovered = signal("");

/** The id (`<party>/<id>`) of the concern a hand card's key or a header card names, "" for none. */
const idOf = (el) => {
  const e = el instanceof Element ? el.closest("[data-concern-id], [data-key^='concern/']") : null;
  return e ? e.dataset.concernId || String(e.dataset.key || "").slice(HAND_KEY.length) : "";
};

/** The concern lit now: the one under the pointer or the focus, else the one lifted in the hand. */
export const lit = computed(() => {
  if (hovered.value) return hovered.value;
  const on = String(lifted.value || "");
  const at = on.indexOf(HAND_KEY);
  return at >= 0 ? on.slice(at + HAND_KEY.length) : "";
});
export const isLit = (party, id) => lit.value === `${party}/${id}`;

let installed = false;
/** Installed once: the pointer and the focus on any of the concern's cards set `hovered`; the hand's cards wear `data-lit` while theirs is lit. */
export function installLit() {
  if (installed || typeof document === "undefined") return;
  installed = true;
  const over = (e) => { if (e.pointerType !== "touch") hovered.value = idOf(e.target); };
  const out = (e) => { if (e.pointerType !== "touch" && idOf(e.target) && idOf(e.relatedTarget) !== idOf(e.target)) hovered.value = idOf(e.relatedTarget); };
  document.addEventListener("pointerover", over);
  document.addEventListener("pointerout", out);
  document.addEventListener("focusin", (e) => { if (idOf(e.target)) hovered.value = idOf(e.target); });
  document.addEventListener("focusout", (e) => { if (idOf(e.target) && idOf(e.relatedTarget) !== idOf(e.target)) hovered.value = idOf(e.relatedTarget); });
  effect(() => {
    const now = lit.value;
    document.querySelectorAll("[data-key^='concern/']").forEach((el) => { if (now && el.dataset.key === `${HAND_KEY}${now}`) el.dataset.lit = "1"; else delete el.dataset.lit; });
  });
}
installLit();
