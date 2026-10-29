// The box of picking (docs/specs/102-the-other-maps-and-picking-on-them.md §6, decisions §152): only while a map is in picking, a drag from the map's empty place draws a dashed box in the ink and takes the cards it
// covers (Shift adds to the marks). On a touch screen a drag is the scroll and stays so: a long press on the empty place, then a drag, draws the box. A press on a card is picking.js's. Pure reads of the page's
// elements: a card is an element with `data-pick-map` and `data-pick-id` (picking.js); the box is drawn by the host from the rectangle `setRect` is given.
import { useEffect, useRef } from "preact/hooks";

const SLOP = 4;                                            // a mouse drag begins past this many pixels
const HOLD_MS = 450;                                       // a finger held still this long on an empty place begins a box
const MOVED = 10;                                          // a finger that moves this far before then is scrolling
const INTERACTIVE = "[data-pick-id], button, a, input, textarea, select, [role=button], [role=tab], [role=menuitem]";

let quiet = 0;                                             // a box just ended: the click that may follow it is not a press
/** Whether a click now is the end of a box (a press on a card then is not a press). */
export const gestureEnded = () => performance.now() < quiet;

/** The element a card is drawn by: `Pickable`'s wrapper has none of its own (`display: contents`), its card is its first child. */
export const cardEl = (w) => (w.classList.contains("pick") ? w.firstElementChild || w : w);

/** The cards a map draws now (all of them, seen or not): `{el, map, id, name, group, groupName}`. */
export function cardsIn(host) {
  return [...host.querySelectorAll("[data-pick-id]")].map((el) => ({ el, map: el.dataset.pickMap, id: el.dataset.pickId, name: el.dataset.pickName || el.dataset.pickId,
    group: el.dataset.pickGroup || "", groupName: el.dataset.pickGroupName || "" }));
}

/** The part of a card that can be seen (clipped by every scrolling or hiding ancestor), or null. */
function seen(el) {
  const r = el.getBoundingClientRect();
  let l = r.left, t = r.top, rt = r.right, b = r.bottom;
  for (let p = el.parentElement; p && p !== document.documentElement; p = p.parentElement) {
    const s = getComputedStyle(p);
    if (s.display === "contents" || !/auto|scroll|hidden|clip/.test(`${s.overflowX} ${s.overflowY}`)) continue;
    const q = p.getBoundingClientRect();
    l = Math.max(l, q.left); t = Math.max(t, q.top); rt = Math.min(rt, q.right); b = Math.min(b, q.bottom);
  }
  return rt > l && b > t ? { l, t, r: rt, b } : null;
}

/** Whether a press at `e` is on the map's empty place: no card, no control, and not the scrollbar of a scrolling area. */
function empty(e, host) {
  const t = e.target;
  if (!(t instanceof Element) || !host.contains(t) || t.closest(INTERACTIVE)) return false;
  if (t.scrollHeight > t.clientHeight || t.scrollWidth > t.clientWidth) {
    const r = t.getBoundingClientRect();
    if (e.clientX - r.left >= t.clientWidth || e.clientY - r.top >= t.clientHeight) return false;
  }
  return true;
}

/** Draws and ends the box on `host`'s map while `on`: `setRect({x, y, w, h})` while it is drawn (null when it is gone), `onTake(cards, shift)` when it ends over cards. */
export function usePickGestures(host, on, setRect, onTake) {
  const last = useRef();
  last.current = onTake;
  useEffect(() => {
    const el = host.current;
    if (!el || !on) { setRect(null); return undefined; }
    const bounds = () => el.closest(".table-body")?.getBoundingClientRect() || { left: 0, top: 0, right: innerWidth, bottom: innerHeight };
    const box = (a, x, y) => {
      const f = bounds(), x1 = Math.min(Math.max(x, f.left), f.right), y1 = Math.min(Math.max(y, f.top), f.bottom), x0 = Math.min(Math.max(a.x, f.left), f.right), y0 = Math.min(Math.max(a.y, f.top), f.bottom);
      return { x: Math.min(x0, x1), y: Math.min(y0, y1), w: Math.abs(x1 - x0), h: Math.abs(y1 - y0) };
    };
    const end = (r, shift) => {                                                           // the cards the box covers (the part of each that can be seen)
      setRect(null);
      quiet = performance.now() + 60;
      const taken = cardsIn(el).filter((c) => {
        const s = seen(cardEl(c.el));
        return s && s.l < r.x + r.w && s.r > r.x && s.t < r.y + r.h && s.b > r.y;
      });
      last.current(taken, shift);
    };

    let from = null, drawn = null, shift = false;                                          // the mouse (and a pen)
    const move = (e) => {
      if (!drawn && Math.hypot(e.clientX - from.x, e.clientY - from.y) < SLOP) return;
      drawn = box(from, e.clientX, e.clientY);
      setRect(drawn);
    };
    const up = (e) => {
      stop();
      if (drawn) end(drawn, shift || e.shiftKey);
    };
    const stop = () => { document.removeEventListener("pointermove", move); document.removeEventListener("pointerup", up); document.removeEventListener("pointercancel", cancel); };
    const cancel = () => { stop(); drawn = null; setRect(null); };
    const down = (e) => {
      if (e.pointerType === "touch" || e.button !== 0 || !empty(e, el)) return;
      e.preventDefault();                                                                  // no text selected, the field keeps its focus
      from = { x: e.clientX, y: e.clientY };
      drawn = null;
      shift = e.shiftKey;
      document.addEventListener("pointermove", move);
      document.addEventListener("pointerup", up);
      document.addEventListener("pointercancel", cancel);
    };

    let finger = null, held = 0, boxing = null, longAt = 0;                                // a finger
    const hold = () => { held = 0; boxing = box(finger, finger.x, finger.y); longAt = Date.now(); setRect(boxing); };
    const touchStart = (e) => {
      if (e.touches.length !== 1 || !empty(e, el)) return;
      const t = e.touches[0];
      finger = { x: t.clientX, y: t.clientY };
      boxing = null;
      clearTimeout(held);
      held = setTimeout(hold, HOLD_MS);
    };
    const touchMove = (e) => {
      if (!finger) return;
      const t = e.touches[0];
      if (boxing) {
        if (e.cancelable) e.preventDefault();                                              // the drag is the box now, not the scroll
        boxing = box(finger, t.clientX, t.clientY);
        setRect(boxing);
      } else if (held && Math.hypot(t.clientX - finger.x, t.clientY - finger.y) > MOVED) { clearTimeout(held); held = 0; }
    };
    const touchEnd = (e) => {
      clearTimeout(held);
      held = 0;
      if (boxing) end(boxing, false);
      if (boxing && e.cancelable) e.preventDefault();
      boxing = null;
      finger = null;
    };
    const touchCancel = () => { clearTimeout(held); held = 0; if (boxing) setRect(null); boxing = null; finger = null; };
    const menu = (e) => { if (boxing || Date.now() - longAt < 1000) e.preventDefault(); };   // the long press is not the browser's menu

    el.addEventListener("pointerdown", down);
    el.addEventListener("touchstart", touchStart, { passive: true });
    el.addEventListener("touchmove", touchMove, { passive: false });
    el.addEventListener("touchend", touchEnd);
    el.addEventListener("touchcancel", touchCancel);
    el.addEventListener("contextmenu", menu);
    return () => {
      stop();
      clearTimeout(held);
      el.removeEventListener("pointerdown", down);
      el.removeEventListener("touchstart", touchStart);
      el.removeEventListener("touchmove", touchMove);
      el.removeEventListener("touchend", touchEnd);
      el.removeEventListener("touchcancel", touchCancel);
      el.removeEventListener("contextmenu", menu);
      setRect(null);
    };
  }, [on]);
}
