// The turns of the card-field (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.1–§6.2, decisions §198.8): the + card is a card's back; pressed, it turns over and grows into the card of the text (`growFrom`: one motion, the turn, the growth and the
// travel from its place, about 360 ms); Esc or a press away turns it back into the + card where it lay (`turnBack`: its text and rune kept by the field's own state); **Send** turns it to its back and carries the back to its place in the Orkmaster's lane
// (`sendBack`). orkUI has no turn yet (`.ork-turn`, spec 120 G): the page animates with the Web Animations API, in orkUI's tokens (read where it needs them: motion.js `tokenMs`, `spring`), and nothing under reduced motion. What flies is a copy over
// everything (`.hand-ghost`: the real card is gone or hidden meanwhile and takes the pointer only when the copy lands), never what the person presses.
// **The focus in the press** (`focusInPress`): on iOS a keyboard rises only for a focus given inside the press itself, and the field is drawn after it; so the press focuses a field of its own (drawn nowhere), and the real field takes the focus from it, the keyboard
// staying up (`releaseProxy`).
import { render } from "preact";
import { html } from "../html.js";
import { boxIn, reduced, spring, token, tokenMs } from "./motion.js";
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

/** The field has just been drawn: it grows out of the + card, turning over (a turn, a growth and a travel at once; the + card lies under it). */
export function growFrom(el) {
  const plus = document.querySelector(".hand .hand-plus"), a = boxIn(plus), b = el?.getBoundingClientRect();
  if (!el || !a || !b?.width || reduced()) return;
  el.animate([{ transformOrigin: "0 0", transform: FROM(a, b, "90deg"), opacity: 0.4 }, { transformOrigin: "0 0", transform: "none", opacity: 1 }],
    { duration: tokenMs("--ork-motion-play", 400) * 0.9, easing: spring() });
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
  g.className = "ork-card table-card table-card--back hand-ghost";
  g.setAttribute("aria-hidden", "true");
  place(g, at, "transform-origin:50% 50%;");
  render(html`<${BackBody} element=${goal.element} name=${goal.name} />`, g);
  document.body.appendChild(g);
  const big = Math.max(box.width / w, 0.5), play = tokenMs("--ork-motion-play", 400);
  try {
    await g.animate([{ transform: `perspective(60em) rotateY(90deg) scale(${big})` }, { transform: `perspective(60em) rotateY(0deg) scale(${big})` }], { duration: play * 0.5, easing: spring(), fill: "forwards" }).finished;
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
