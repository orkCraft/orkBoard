// The turns of the card-field (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.1–§6.2, docs/specs/128 A, decisions §198.8, §206.1): the + card is a card's back; pressed, it turns over where it lies and grows into the card of the text (`placeField` lays the field with its left edge on the card's and its foot under the window's edge; `growFrom`: a turn of 180° in two halves, the card's back and then the field, and the growth from the card's box through both, the
// travel from its place, about 360 ms); Esc or a press away turns it back into the + card where it lay (`turnBack`: its text and rune kept by the field's own state); **Send** turns it to its back and carries the back to its place in the Orkmaster's lane
// (`sendBack`). **The turn in place is orkUI's** (`.ork-turn`, 0.28.0: the card of the words turns to its back where the field lay); the turns that are also a growth and a travel from a place (the field out of the + card, the field back into it) and the flights stay Web Animations, as orkUI has no flight whose end points are not known before the cards are drawn, in orkUI's tokens (read where it needs them: motion.js `tokenMs`, `spring`), and nothing under reduced motion. What flies is a copy over
// everything (`.hand-ghost`: the real card is gone or hidden meanwhile and takes the pointer only when the copy lands), never what the person presses.
// **The focus in the press** (`focusInPress`): on iOS a keyboard rises only for a focus given inside the press itself, and the field is drawn after it; so the press focuses a field of its own (drawn nowhere), and the real field takes the focus from it, the keyboard
// staying up (`releaseProxy`).
import { render } from "preact";
import { html } from "../html.js";
import { boxIn, ease, reduced, spring, token, tokenMs } from "./motion.js";
import { Elem } from "../orkui.js";
import { BackBody } from "../table/backbody.js";

let proxy = null;

/** Inside a press on the + card: a field of its own takes the focus (and the phone's keyboard rises); it is taken away when the real one has the focus, or after a second. */
export function focusInPress() {
  if (typeof document === "undefined") return;
  try {
    releaseProxy();
    proxy = document.createElement("textarea");
    proxy.className = "hand-field__proxy";
    proxy.setAttribute("aria-hidden", "true");
    proxy.tabIndex = -1;
    document.body.appendChild(proxy);
    proxy.focus({ preventScroll: true });
    const mine = proxy;
    setTimeout(() => { if (proxy === mine) releaseProxy(); }, 1000);
  } catch { proxy = null; }
}
export function releaseProxy() {
  proxy?.remove();
  proxy = null;
}

const FROM = (a, b, turn) => `translate(${a.left - b.left}px, ${a.top - b.top}px) scale(${a.width / b.width}, ${a.height / b.height})${turn ? ` perspective(60em) rotateY(${turn})` : ""}`;

/** A copy of `el` at the box `b`, over the page, taking no press. */
function copyOf(el, b, extra = "") {
  const g = el.cloneNode(true);
  g.classList.remove("hand-plus", "ork-leans", "is-choosing", "is-large");
  g.classList.add("hand-ghost");
  for (const a of ["aria-label", "title", "aria-haspopup", "aria-expanded", "id", "ref"]) g.removeAttribute(a);
  g.setAttribute("aria-hidden", "true");
  g.tabIndex = -1;
  g.inert = true;
  place(g, b, extra);
  return g;
}
function place(g, b, extra = "") {
  g.style.cssText = `position:fixed;left:${b.left}px;top:${b.top}px;width:${b.width}px;height:${b.height}px;margin:0;z-index:90;pointer-events:none;transform-origin:0 0;${extra}`;
}

const GROW = 2.8, SHOWN = 330, NARROW = "(max-width: 759.98px)";   // the field is about 2.8 times the + card's width; so much of it shows above the window's edge (spec 128 A.1)

/** Where the field lies (wide width, `.hand-field` not in the pane's middle): its left edge on the + card's (its layout box, not the turned box), its width 2.8 times the card's; hand.css puts its top `SHOWN` px above the window's foot, so its foot goes under the edge.
 *  The phone's width keeps the field as wide as the screen (hand.css); a + card out of view leaves the field where hand.css lays it. */
export function placeField(el) {
  if (!el) return;
  const plus = document.querySelector(".hand .hand-plus"), box = boxIn(plus);
  if (!box || (typeof matchMedia === "function" && matchMedia(NARROW).matches)) { el.style.removeProperty("--hf-left"); el.style.removeProperty("--hf-w"); return; }
  const w = Math.min(plus.offsetWidth * GROW, innerWidth - 16), left = Math.max(8, Math.min(box.left + box.width / 2 - plus.offsetWidth / 2, innerWidth - w - 8));
  el.style.setProperty("--hf-left", `${left}px`);
  el.style.setProperty("--hf-w", `${w}px`);
}

/** A turn about the vertical line through the middle of a box `w` wide (the box grows from its corner, so the turn's own pivot is moved to its middle). */
const TURN = (w, deg) => `translateX(${w / 2}px) perspective(60em) rotateY(${deg}) translateX(${-w / 2}px)`;

/** The field has just been drawn: the + card turns over and grows into it, from where it lies. A copy of the + card (the card's back) turns away over the first half while the field, edge-on until then, turns in over the second: a half turn and a half turn, 180° in all,
 *  and the growth from the + card's box to the field's runs through both (`translate` and `scale`, which leave the turn its own `transform`). Nothing under reduced motion. */
export function growFrom(el) {
  const plus = document.querySelector(".hand .hand-plus"), a = boxIn(plus), b = el?.getBoundingClientRect();
  if (!el || !a || !b?.width || reduced()) return;
  const time = tokenMs("--ork-motion-play", 400) * 0.9, half = time / 2, origin = { transformOrigin: "0 0" };       // the field grows to the gutters on a phone: a spring's overshoot would spill past the window
  const move = (f, t) => [{ translate: `${f.x}px ${f.y}px`, scale: `${f.kx} ${f.ky}`, ...origin }, { translate: `${t.x}px ${t.y}px`, scale: `${t.kx} ${t.ky}`, ...origin }];
  el.animate(move({ x: a.left - b.left, y: a.top - b.top, kx: a.width / b.width, ky: a.height / b.height }, { x: 0, y: 0, kx: 1, ky: 1 }), { duration: time, easing: ease() });
  el.animate([{ transform: TURN(b.width, "-90deg"), ...origin }, { transform: TURN(b.width, "0deg"), ...origin }], { duration: half, delay: half, fill: "backwards", easing: "ease-out" });
  const g = copyOf(plus, a);                                                          // the back, plus-sized, grown by the same steps to the field's box
  document.body.appendChild(g);
  const done = () => g.remove();
  g.animate(move({ x: 0, y: 0, kx: 1, ky: 1 }, { x: b.left - a.left, y: b.top - a.top, kx: b.width / a.width, ky: b.height / a.height }), { duration: time, easing: ease() }).finished.then(done, done);
  g.animate([{ transform: TURN(a.width, "0deg"), ...origin }, { transform: TURN(a.width, "90deg"), ...origin }], { duration: half, easing: "ease-in", fill: "forwards" }).finished.then(done, done);
}

/** Esc or a press away: the field was taken off the page at once; a copy of the + card turns back from the field's box into the + card where it lay (the real one is hidden meanwhile). */
export function turnBack(box) {
  const plus = document.querySelector(".hand .hand-plus"), b = boxIn(plus);
  if (!plus || !b || !box?.width || reduced()) return;
  const g = copyOf(plus, b);
  document.body.appendChild(g);
  plus.style.visibility = "hidden";
  const done = () => { g.remove(); plus.style.visibility = ""; };
  g.animate([{ transform: FROM(box, b, "-90deg"), opacity: 0.6 }, { transform: "none", opacity: 1 }], { duration: tokenMs("--ork-motion-play", 400) * 0.8, easing: spring() }).finished.then(done, done);
}

/** The card's width on the table (frame.css `--card-w`). */
const cardWidth = () => parseFloat(token("--card-w", "") || getComputedStyle(document.querySelector(".frame-table") || document.body).getPropertyValue("--card-w")) || 144;

/** Sent: the card turns to its back where the field lay, and the back, shrinking, travels to its place in the Orkmaster's lane (the goal's own card there, `[data-goal]`); the real card is hidden until the copy lands. With no place in view (a phone has no lanes) the back
 *  turns and is taken away. `box`: the field's box; `goal`: `{slug, element, name}`. */
export async function sendBack(box, goal) {
  if (reduced() || !box?.width) return;
  const w = cardWidth(), h = w * 7 / 5, g = document.createElement("div"), at = { left: box.left + box.width / 2 - w / 2, top: box.top + box.height / 2 - h / 2, width: w, height: h };
  g.className = "ork-turn hand-ghost is-up";
  g.setAttribute("aria-hidden", "true");
  const big = Math.max(box.width / w, 0.5), play = tokenMs("--ork-motion-play", 400);
  place(g, at, `transform-origin:50% 50%;transform:scale(${big});`);
  render(html`<div class="ork-turn__back ork-card table-card--back"><${BackBody} element=${goal.element} name=${goal.name} /></div>
    <div class="ork-turn__face ork-card hand-ghost__face"><${Elem} name=${goal.element} big=${true} dim=${!goal.element} /><span class="hand-ghost__words">${goal.name}</span></div>`, g);
  document.body.appendChild(g);
  try {
    void g.offsetWidth;                                                                  // the card of the words lies face up first; taking `is-up` off is orkUI's turn, played once
    g.classList.remove("is-up");
    await new Promise((r) => { const t = setTimeout(r, play + 60); g.addEventListener("transitionend", (e) => { if (e.propertyName === "transform") { clearTimeout(t); r(); } }, { once: true }); });
    let target = null;
    for (let tries = 0; tries < 20 && !target; tries++) {                                // the Board answers in a moment: the goal's card is drawn in the lane
      target = [...document.querySelectorAll(`.frame-table .table-card[data-goal="${CSS.escape(goal.slug)}"]`)].find((el) => boxIn(el)) || null;
      if (!target) await new Promise((r) => setTimeout(r, 100));
    }
    const to = target?.getBoundingClientRect();
    if (!to) { await g.animate([{ opacity: 1 }, { opacity: 0 }], { duration: play * 0.5, fill: "forwards" }).finished; return; }
    target.style.visibility = "hidden";
    const v = { x: to.left + to.width / 2 - (at.left + w / 2), y: to.top + to.height / 2 - (at.top + h / 2) };
    try { await g.animate([{ transform: `scale(${big})` }, { transform: `translate(${v.x}px, ${v.y}px) scale(${to.width / w})` }], { duration: play * 1.4, easing: spring(), fill: "forwards" }).finished; }
    finally { target.style.visibility = ""; }
  } catch { /* a page that went away meanwhile: the copy goes with it */ } finally { g.remove(); }
}
