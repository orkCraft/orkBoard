// How the hand's cards answer the hand (docs/specs/98-the-table-and-the-hand.md §6.1, decisions §149.1; docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.9–§6.10, decisions §198.9): orkUI draws every motion (`.ork-leans`, `.ork-deal`,
// `.ork-play`, `.ork-fan`, `.ork-crumble`, `.ork-gives`, `.ork-turn`: its tokens, its keyframes, nothing under reduced motion); the page only says when and from where. A card leans toward the pointer (`lean`), a card that
// comes is handed from where it was played (`useHanded`: the goal's card on the table, else the leader's tab, else on a phone the goal in the middle or the crown; `fromWhere`), a card that is
// answered is played back there (stopcard.js, `between`), a card that goes crumbles where it lay (`useGone`). At rest and under reduced motion nothing moves: the hooks add no class then.
import { h } from "preact";
import { signal } from "@preact/signals";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { ORKMASTER } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";

export const reduced = () => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

export const DEAL_MS = 650, CRUMBLE_MS = 700;     // a dealt card's travel, the shards' fall (orkUI's play time and the six shards' gaps)

/** The pointer's place on a card, -1 to 1 each way, for orkUI's lean (`--ork-lean-x`, `--ork-lean-y`); set on the card itself. */
export function lean(e) {
  const el = e.currentTarget, r = el.getBoundingClientRect();
  if (!r.width || !r.height) return;
  el.style.setProperty("--ork-lean-x", String(Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width) * 2 - 1)).toFixed(2)));
  el.style.setProperty("--ork-lean-y", String(Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height) * 2 - 1)).toFixed(2)));
}
export function level(e) {
  e.currentTarget.style.removeProperty("--ork-lean-x");
  e.currentTarget.style.removeProperty("--ork-lean-y");
}
/** The handlers that give a card its lean. */
export const leans = { onPointerMove: lean, onPointerLeave: level };

// -- where a card comes from and goes back to (spec 120 §6.9–§6.10) ---------------------------------------------------------------------------------

/** A token of orkUI (`--ork-motion-play`), read where the page's animations (not its sheets) need it; `fallback` when the page has none. */
export const token = (name, fallback) => {
  try { return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback; } catch { return fallback; }
};
export const tokenMs = (name, fallback) => parseFloat(token(name, `${fallback}ms`)) || fallback;
export const spring = () => token("--ork-motion-spring", "cubic-bezier(.34,1.56,.64,1)");
export const ease = () => token("--ork-motion-ease", "ease-out");               // no overshoot: what grows to the window's edge must not spill past it

/** The box of `el` when it is in view, else null (a box with no size, or out of the window, is no place to fly from). */
export function boxIn(el) {
  const r = el?.isConnected ? el.getBoundingClientRect() : null;
  return r && r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth ? r : null;
}

/** Where a card played by `who` comes from, the first in view of: the task's own card on the table when it has one (`[data-goal][data-task]`: the card of the task that asks or failed, its place (`.ork-card-place`) when it was thrown to the hand, its edge
 *  in the fan), the goal's own card or stack on the table (`[data-goal]` of the table: its back at the Orkmaster for Talk's questions, the front card of a stack in its party's lane);
 *  the leader's tab (`[data-tab]`; the Orkmaster's for what the Orkmaster plays); on a phone, which has no lanes, the goal picked in the middle when it is the card's goal, else the crown. `who`: `{goal, party, ork, task}`.
 *  Returns `{el, at: "goal" | "tab" | "crown"}`, null for a card of no goal and no party (it is dealt from under its place, as it was). */
export function fromWhere({ goal = "", party = "", ork = false, task = "" } = {}) {
  const find = (sel) => [...document.querySelectorAll(sel)].find((el) => boxIn(el)) || null, name = goal ? CSS.escape(goal) : "";
  if (uprightNow.value) {
    const mid = goal ? find(`.up-look[data-goal="${name}"]`) : null, crown = mid ? null : find(".up-crown");
    return mid ? { el: mid, at: "goal" } : crown ? { el: crown, at: "crown" } : null;
  }
  const own = goal && task ? find(`.frame-table [data-goal="${name}"][data-task="${CSS.escape(String(task))}"]`) : null;                  // the asking (or failed) task's own card first
  if (own) return { el: own, at: "goal" };
  const card = goal ? find(`.frame-table .table-card[data-goal="${name}"]`) : null;       // its own card
  if (card) return { el: card, at: "goal" };
  const slug = ork ? ORKMASTER : party, tab = slug ? find(`.frame-table .table-tab[data-tab="${CSS.escape(slug)}"], .frame-column .col-head__tab[data-tab="${CSS.escape(slug)}"]`) : null;
  return tab ? { el: tab, at: "tab" } : null;
}

/** The head of who plays a card, at its origin (spec 120 §6.9): the leader's tab head (the Orkmaster's for what the Orkmaster plays); on the phone the crown's. `where`: `fromWhere`'s. */
export function headAt(where, { party = "", ork = false } = {}) {
  if (!where?.el) return null;
  const head = (root) => root?.querySelector?.(".ork-race__head") || null;
  if (where.at === "crown" || uprightNow.value) return head(document.querySelector(".up-crown"));
  const slug = ork ? ORKMASTER : party;
  const tab = slug ? [...document.querySelectorAll(`.frame-table .table-tab[data-tab="${CSS.escape(slug)}"], .frame-column .col-head__tab[data-tab="${CSS.escape(slug)}"]`)].find((el) => boxIn(el)) : null;
  return tab ? head(tab) || head(tab.closest(".table-tabcell")) : null;            // the open tab's head stands beside its button, in its cell (spec 123 §7.2)
}

/** One beat on a head: orkUI's `.ork-gives` is put on and taken off at its `animationend` named `ork-give` (nothing plays under reduced motion; orkUI's rule says so too, and the class is not put on). */
export function give(head) {
  if (!head || reduced()) return;
  head.classList.remove("ork-gives");
  void head.offsetWidth;                                                              // a second give while the first plays begins again
  const off = (e) => { if (e.animationName !== "ork-give") return; head.classList.remove("ork-gives"); head.removeEventListener("animationend", off); };
  head.addEventListener("animationend", off);
  head.classList.add("ork-gives");
}

/** The vector from the middle of the box `a` to the middle of `b`, in px. */
export const between = (a, b) => ({ x: Math.round(b.left + b.width / 2 - (a.left + a.width / 2)), y: Math.round(b.top + b.height / 2 - (a.top + a.height / 2)) });

/** The cards that came to the hand and say who handed them: `{key: {name}}`, kept while the page lives (a card says *From <Leader>* for good: spec 120 §6.9). */
const handed = new Map();
export const handedName = (key) => handed.get(key)?.name || "";
/** The polite line a screen reader hears when a card lands: *<Leader> hands you <what>*, said once. */
export const said = signal("");

const FLY_MAX = 3;                               // at most three cards fly at once; the others are dealt from under their place
const HOLD_MS = 5000;                            // a pointer that never comes up does not keep the cards from coming
let down = 0;                                    // when a pointer went down in the hand (0: none): no card is dealt then, they wait for it to come up (the no lost tap of spec 50 §6.9)
const waiting = new Set();
if (typeof document !== "undefined") {
  document.addEventListener("pointerdown", (e) => { if (e.target.closest?.(".hand")) down = Date.now(); }, true);
  const up = () => { if (!down) return; setTimeout(() => { down = 0; for (const f of [...waiting]) f(); }, 0); };
  window.addEventListener("pointerup", up, true);
  window.addEventListener("pointercancel", up, true);
}
const pointerDown = () => down > 0 && Date.now() - down < HOLD_MS;

/** The cards that came since the last draw (not the first draw; none for a hidden page or under reduced motion: the card is there, saying *From <Leader>*). `items`: `[{key, goal, party, ork, name, words}]` (`name`: who hands it, `words`:
 *  what it is, for the line a screen reader hears). Returns `{key: {i, el?, hold?}}` for the ones dealt: `i` its place in the deal (a deal gap apart: orkUI's `--ork-deal-i`), `el` the box it comes from (the first three that have one; the others
 *  are dealt from under their place), `hold` while a pointer is down in the hand. Read while drawing, so a card is dealt in the very frame it is first drawn. */
export function useHanded(items) {
  const seen = useRef(null), live = useRef({}), [, tick] = useState(0), now = new Set(items.map((x) => x.key));
  if (seen.current === null) seen.current = now;
  else {
    const all = items.filter((x) => !seen.current.has(x.key)), came = all.filter((x) => x.top), line = () => came.map((c) => `${c.name} hands you ${c.words}`).join(". ");
    seen.current = now;
    for (const c of all) handed.set(c.key, { name: c.name });
    if (came.length && !reduced() && !document.hidden) {
      const hold = pointerDown(), keys = came.map((c) => c.key);
      let flying = 0, begun = false;
      came.forEach((c, i) => {
        const where = flying < FLY_MAX ? fromWhere(c) : null;
        if (where) flying++;
        live.current[c.key] = { i, ...(where ? { el: where.el, head: headAt(where, c) } : {}), ...(hold ? { hold: true } : {}) };
      });
      const begin = (drawing = false) => {                                    // the deal begins (while this very draw, or when the pointer is up)
        if (begun) return;
        begun = true;
        waiting.delete(begin);
        if (!drawing) {
          for (const k of keys) if (live.current[k]) live.current[k] = { ...live.current[k], hold: false };
          tick((n) => n + 1);
        }
        setTimeout(() => { for (const k of keys) delete live.current[k]; tick((n) => n + 1); said.value = line(); }, DEAL_MS + came.length * 40);
      };
      if (hold) { waiting.add(begin); setTimeout(begin, HOLD_MS); } else begin(true);
    } else if (came.length) setTimeout(() => { said.value = line(); }, 0);
  }
  return { ...live.current };
}

/** A card handed from where it was played (`dealt` is its entry of `useHanded`: `{i, el, head, hold}`): before the first paint the vector from its place to the origin is set (orkUI's `--ork-deal-x/-y`) and orkUI's deal begins; while a pointer is down in the hand it is held back
 *  (`data-handing`, drawn nowhere) and comes when the pointer is up. A card with no origin is dealt from under its place by the card's own class (hand.css). */
export function useFlight(ref, dealt, copy = false) {
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || !dealt) return undefined;
    if (dealt.hold) { el.setAttribute("data-handing", ""); return undefined; }
    el.removeAttribute("data-handing");
    if (!dealt.el) return undefined;
    const origin = boxIn(dealt.el);
    if (origin) give(dealt.head);                                                       // the head of who plays it gives it: one beat at the origin, as the card is let go
    if (copy && origin) return flyCopy(el, origin, dealt.i);
    if (origin) {
      const v = between(el.getBoundingClientRect(), origin);
      el.style.setProperty("--ork-deal-x", `${v.x}px`);
      el.style.setProperty("--ork-deal-y", `${v.y}px`);
    }
    el.classList.add("ork-deal");
    const t = setTimeout(() => el.classList.remove("ork-deal"), DEAL_MS + (dealt.i + 1) * tokenMs("--ork-motion-deal-gap", 40));
    return () => { clearTimeout(t); el.classList.remove("ork-deal"); };                 // the deal is over (the card is not handed any more) or begins again
  }, [dealt?.hold, dealt?.el]);
}

/** A card whose row clips what flies in it (a phone's row scrolls sideways): a copy of it flies over everything from `origin` to its place while the real card is hidden, and takes the pointer when the copy has landed. */
function flyCopy(el, origin, i = 0) {
  const place = el.getBoundingClientRect(), g = el.cloneNode(true), v = between(place, origin);
  for (const a of ["data-key", "aria-label", "id"]) g.removeAttribute(a);
  g.classList.add("hand-ghost", "hand-ghost--handed");
  g.setAttribute("aria-hidden", "true");
  g.inert = true;
  g.style.cssText = `position:fixed;left:${place.left}px;top:${place.top}px;width:${place.width}px;height:${place.height}px;margin:0;z-index:90;pointer-events:none;`;
  document.body.appendChild(g);
  el.style.visibility = "hidden";
  const done = () => { g.remove(); el.style.visibility = ""; };
  const a = g.animate([{ transform: `translate(${v.x}px, ${v.y}px) rotate(-6deg) scale(0.6)`, opacity: 0.6 }, { transform: "none", opacity: 1 }],
    { duration: tokenMs("--ork-motion-play", 400) + 250, easing: spring(), delay: i * tokenMs("--ork-motion-deal-gap", 40), fill: "backwards" });
  a.finished.then(done, done);
  return () => { a.cancel(); done(); };
}

/** `items` with the ones that left kept where they lay for the crumble: `[{item, gone}]`. A card that goes under reduced motion goes at once. */
export function useGone(items, key) {
  const was = useRef(null), [ghosts, setGhosts] = useState([]), id = items.map(key).join("|");
  useEffect(() => {
    const prev = was.current;
    was.current = items.map((item, at) => ({ item, at }));
    if (!prev || reduced()) return undefined;
    const now = new Set(items.map(key)), left = prev.filter(({ item }) => !now.has(key(item)));
    if (!left.length) return undefined;
    setGhosts((g) => [...g, ...left.map(({ item, at }) => ({ item, at, gone: true }))]);
    const t = setTimeout(() => setGhosts((g) => g.filter((x) => !left.some((l) => key(l.item) === key(x.item)))), CRUMBLE_MS);
    return () => clearTimeout(t);
  }, [id]);
  const out = items.map((item) => ({ item, gone: false }));
  for (const g of ghosts) out.splice(Math.min(g.at, out.length), 0, g);
  return out;
}

/** The six shards of a card that goes (orkUI's `.ork-crumble`). */
export const Shards = () => {
  const n = 6;
  return h("span", { class: "ork-crumble", "aria-hidden": "true" }, Array.from({ length: n }, (_, i) => h("i", { key: i })));
};
