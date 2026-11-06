// A card that turns face up on its way (docs/specs/147-one-card-four-corners.md parts D.2 and E, decisions §251.3, §251.7, §70): a back lifts where it lies, turns to its face (orkUI's `.ork-turn`, put `is-up` on after a beat) and stands where the card
// lands; or, the other way, a card turns face down, its rune lights in the middle of its back and it flies small into the Orkmaster's fan (`layFly`, fieldturn.js). A copy over everything (`.table-flyer`), the real card is hidden by the caller until it lands,
// taken away when it has landed. The page measures (it passes the boxes and the times); this draws the copy and plays the one Web Animations flight. No import of the hand's motion.js (it imports this): the times and the curve come in from the caller.

export const flights = { now: 0, done: 0 };                  // how many turn flights fly now, how many have landed (what a test reads)

const clean = (el) => {
  for (const a of ["id", "aria-label", "title", "aria-pressed", "aria-expanded", "aria-haspopup"]) el.removeAttribute(a);
  for (const n of [el, ...el.querySelectorAll("*")]) {                    // a copy is never found as the card it copies: no id and no data-* (data-goal, data-kind, data-key …) on it or inside it
    n.removeAttribute("id");
    for (const a of n.getAttributeNames()) if (a.startsWith("data-")) n.removeAttribute(a);
  }
  el.classList.remove("ork-leans", "ork-picked", "is-lifted", "ork-deal", "is-dim");
  el.setAttribute("aria-hidden", "true");
  el.tabIndex = -1;
  el.inert = true;
};

/** A back as the Orkmaster's hand draws one: orkUI's back with its small seal and the rune of `from` (an element that holds a rune: the card it stands for) in the middle. `asks`: the ring is the alert's. */
export function backOf(from, { asks = false, lit = true } = {}) {
  const back = document.createElement("div");
  back.className = `ork-turn__back ork-card-back small table-turned__back${asks ? " is-asking" : ""}`;   // orkUI 0.30.0: the back draws its ring of runes itself
  const seal = document.createElement("span");
  seal.className = "col-fan__seal table-turned__seal";
  const rune = from?.querySelector?.(".ork-elem")?.cloneNode(true);
  if (rune) { rune.classList.remove("is-glowing"); rune.classList.toggle("table-turned__rune", true); if (!lit) rune.style.opacity = "0.25"; seal.appendChild(rune); }
  back.appendChild(seal);
  return back;
}

/** The copy of a card that turns: an `.ork-turn` at the box `to` (where the card lands), its back the goal's (`backOf`), its face a copy of `face`. It begins at `from` (the box of the back as it lies; `sideways`: on its side, as the deck's backs lie) and
 *  is put on its face a beat into the flight. Returns `{finished, cancel}`: `finished` settles when it has landed (and the copy is gone), `cancel` takes it away at once. `ms`: the whole flight; `lift`: px the back rises first. */
export function turnFly({ from, to, face, rune = face, sideways = false, asks = false, ms = 900, easing = "ease-out", lift = 6, kind = "" }) {
  const g = document.createElement("div"), f = face.cloneNode(true);
  g.className = "ork-turn table-flyer table-turned";
  g.dataset.fly = kind;
  g.setAttribute("aria-hidden", "true");
  g.inert = true;
  g.style.cssText = `position:fixed;left:${to.left}px;top:${to.top}px;width:${to.width}px;height:${to.height}px;margin:0;z-index:90;pointer-events:none;transform-origin:50% 50%;`;
  clean(f);
  f.classList.add("ork-turn__face");
  f.style.cssText = "position:absolute;inset:0;width:100%;height:100%;margin:0;";
  g.append(backOf(rune, { asks }), f);
  document.body.appendChild(g);
  flights.now++;
  const dx = from.left + from.width / 2 - (to.left + to.width / 2), dy = from.top + from.height / 2 - (to.top + to.height / 2);
  const s = (sideways ? from.height : from.width) / to.width, turn = sideways ? "rotate(90deg)" : "rotate(0deg)", at = (y) => `translate(${dx}px, ${dy + y}px) ${turn} scale(${s})`;
  let over = false;
  const end = () => { if (over) return; over = true; clearTimeout(t); g.remove(); flights.now--; flights.done++; };
  const t = setTimeout(() => { void g.offsetWidth; g.classList.add("is-up"); }, ms * 0.18);                    // lifted, then turned to its face on its way
  const a = g.animate([{ transform: at(0) }, { transform: at(-lift), offset: 0.18 }, { transform: "none" }], { duration: ms, easing, fill: "forwards" });
  const finished = a.finished.then(end, end);
  return { finished, cancel: () => { a.cancel(); end(); } };
}

/** A card of a goal folded into a strip: a copy of `card` at its box that flies to the strip `to` and shrinks into it, fading as it lands. Settles when it is gone. `kind` names the flight for a test. */
export function foldInto(card, from, to, { ms = 600, easing = "ease-out", kind = "fold" } = {}) {
  const g = card.cloneNode(true);
  clean(g);
  g.classList.add("table-flyer", "table-folded");
  g.dataset.fly = kind;
  g.style.cssText = `position:fixed;left:${from.left}px;top:${from.top}px;width:${from.width}px;height:${from.height}px;margin:0;z-index:90;pointer-events:none;transform-origin:0 0;`;
  document.body.appendChild(g);
  flights.now++;
  const dx = to.left - from.left, dy = to.top - from.top, sx = to.width / from.width, sy = Math.max(to.height / from.height, 0.05);
  const end = () => { g.remove(); flights.now--; flights.done++; };
  return g.animate([{ transform: "none", opacity: 1 }, { transform: `translateY(-8px) rotate(2deg)`, opacity: 1, offset: 0.2 },
    { transform: `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`, opacity: 1, offset: 0.7 }, { transform: `translate(${dx}px, ${dy}px) scale(${sx}, ${sy})`, opacity: 0 }],
  { duration: ms, easing, fill: "forwards" }).finished.then(end, end);
}
