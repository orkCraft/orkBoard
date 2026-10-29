// System fitted to the pane (docs/specs/107-what-the-owners-day-said.md §6, decisions §182.6): the architecture is drawn at its natural size, then scaled to the scroller's width (`transform: scale`,
// origin top left, the wrapper `.arch-fit` taking the scaled size): `fit = min(1, width / natural)`, never under 0.5, where it stays and scrolls sideways. *Fit* and *100 %* in the System's corner
// (the choice kept per project in `localStorage`, read and written inside try/catch); a drag on the empty ground pans (a touch screen scrolls by itself).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { town } from "../link.js";

export const MIN_FIT = 0.5;                              // never smaller: past it, the System scrolls sideways
export const FIT = "Fit", ACTUAL = "100 %";
const KEPT = "orkboard.system.fit.";
const PAN_PX = 4;                                        // a press moves this far before it is a pan
const NOT_GROUND = "button, a, input, select, textarea, [data-part], .sys-stk, .arch-link, .arch-lib, .arch-way";

const read = (project) => { try { return localStorage.getItem(KEPT + project) === "full" ? "full" : "fit"; } catch { return "fit"; } };
const write = (project, mode) => { try { localStorage.setItem(KEPT + project, mode); } catch { /* this run only */ } };

/** The scale that fits `natural` into `avail`: 1 when it fits already, else the ratio floored to a thousandth (so the scaled box never passes the edge), never under `MIN_FIT`. */
export const scaleFor = (natural, avail) => (natural > 0 && avail > 0 && natural > avail ? Math.max(MIN_FIT, Math.floor((avail / natural) * 1000) / 1000) : 1);

/** The System's scale and its choice. `scroller` holds the scaled `host` (`.arch`); `redraw` is called with the scale when it changed or the box did (the arrows are measured in the unscaled box). */
export function useFit(scroller, host, redraw, deps) {
  const project = town.value?.projects?.current || "";
  const [mode, setModeState] = useState(() => read(project));
  const [view, setView] = useState({ f: 1, w: 0, h: 0 });
  const now = useRef({ mode, f: 1 });
  now.current.mode = mode;
  const setMode = (m) => { write(project, m); setModeState(m); };
  const measure = () => {
    const arch = host.current, box = scroller.current;
    if (!arch || !box) return;
    const w = arch.offsetWidth, h = arch.offsetHeight, f = now.current.mode === "fit" ? scaleFor(w, box.clientWidth) : 1;
    now.current.f = f;
    setView((was) => (was.f === f && was.w === w && was.h === h ? was : { f, w, h }));
  };
  useEffect(() => { setModeState(read(project)); }, [project]);
  useLayoutEffect(measure, [mode, ...deps]);
  useLayoutEffect(() => redraw(view.f), [view.f, view.w, view.h]);
  useEffect(() => {
    if (typeof ResizeObserver !== "function" || !host.current || !scroller.current) return undefined;
    const ro = new ResizeObserver(() => { measure(); redraw(now.current.f); });
    ro.observe(host.current);
    ro.observe(scroller.current);
    return () => ro.disconnect();
  }, deps);
  return { mode, setMode, f: view.f, w: view.w, h: view.h, scale: () => now.current.f };
}

/** *Fit* and *100 %*, in the System's corner. */
export function FitButtons({ mode, setMode }) {
  return html`<div class="arch-zoom" role="group" aria-label="Size">
    <button type="button" class="ork-btn quiet arch-zoom__btn" data-fit="fit" aria-pressed=${String(mode === "fit")} title="Fit the System to the pane's width" onClick=${() => setMode("fit")}>${FIT}</button>
    <button type="button" class="ork-btn quiet arch-zoom__btn" data-fit="full" aria-pressed=${String(mode === "full")} title="Show the System at its own size" onClick=${() => setMode("full")}>${ACTUAL}</button>
  </div>`;
}

/** A drag from the empty ground pans the scroller (the mouse; a touch screen scrolls by itself, and picking has the drag for its box). */
export function usePan(scroller, deps = []) {
  useEffect(() => {
    const el = scroller.current;
    if (!el) return undefined;
    let drag = null;
    const down = (e) => {
      if (e.button !== 0 || e.pointerType === "touch" || e.target.closest(NOT_GROUND) || el.closest("[data-picking]")) return;
      drag = { x: e.clientX, y: e.clientY, left: el.scrollLeft, top: el.scrollTop, on: false, id: e.pointerId };
    };
    const move = (e) => {
      if (!drag || e.pointerId !== drag.id) return;
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!drag.on && Math.hypot(dx, dy) < PAN_PX) return;
      if (!drag.on) { drag.on = true; el.dataset.panning = "1"; try { el.setPointerCapture(e.pointerId); } catch { /* the drag goes on without it */ } }
      el.scrollLeft = drag.left - dx;
      el.scrollTop = drag.top - dy;
    };
    const up = () => { drag = null; delete el.dataset.panning; };
    el.addEventListener("pointerdown", down);
    el.addEventListener("pointermove", move);
    el.addEventListener("pointerup", up);
    el.addEventListener("pointercancel", up);
    return () => { el.removeEventListener("pointerdown", down); el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); el.removeEventListener("pointercancel", up); };
  }, deps);
}
