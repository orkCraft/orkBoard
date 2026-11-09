// The preview (docs/specs/168 A2, decisions §283.4): a small card hovered or focused is shown at 144 x 202 beside it, after about 300 ms, one at a time; Esc puts it away, and focus never moves (it cannot be pressed or focused).
// A face-up card shows itself again, bigger (its rune and kind at the corners, its name, its picture); a back shows its goal's name and the line of its state. It floats over the table (`position: fixed`, preview.css), to the card's right and, where
// that has no room, to its left, so it changes no box's size. It is drawn into a box of its own on the page's body (`render`), so no column's clip or turn holds it. The words stay in the card's `aria-label`: the preview is for the eyes.
import { h, render } from "preact";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { CornerTop } from "./corners.js";

export const DELAY = 300, W = 144, H = 202, GAP = 8;

/** What is shown now: `{mode: "back" | "face", at: {left, top}, ...the card's words or parts}`, or null. */
export const shown = signal(null);

let timer = 0, anchor = null, watch = 0, hidden = null, host = null;

function hide() { clearTimeout(timer); clearInterval(watch); timer = 0; watch = 0; anchor = null; if (shown.value) shown.value = null; }

/** Where the preview lies for a card at `r` (its box on screen): to its right, else its left, the top kept inside the window. */
export function placeOf(r, vw = innerWidth, vh = innerHeight) {
  const left = r.right + GAP + W <= vw ? r.right + GAP : Math.max(GAP, r.left - GAP - W);
  return { left, top: Math.max(GAP, Math.min(r.top + (r.bottom - r.top) / 2 - H / 2, vh - H - GAP)) };
}

function ensureHost() {
  if (host?.isConnected) return;
  host = document.createElement("div");
  host.className = "pv-host";
  document.body.appendChild(host);
  render(h(Preview, {}), host);
}

function arm(el, spec) {
  if (el === hidden) return;                                                  // put away with Esc: it stays away until the pointer or the focus leaves
  if (anchor === el && (shown.value || timer)) return;
  hide();
  anchor = el;
  timer = setTimeout(() => {
    timer = 0;
    if (!el.isConnected) { hide(); return; }
    ensureHost();
    shown.value = { ...spec(), at: placeOf(el.getBoundingClientRect()) };
    watch = setInterval(() => { if (!el.isConnected || !(el.matches(":hover") || el === document.activeElement)) hide(); }, 150);
  }, DELAY);
}

function leave(el) {
  if (hidden === el && !el.matches(":hover") && el !== document.activeElement) hidden = null;
  if (anchor === el) hide();
}

/** The attributes of a card (`props`) with the preview's four handlers wrapped around its own; `spec()` gives what to show: `{mode: "back", name, line}` or `{mode: "face", name, element, hue, kind (a sign's name), signal, picture (a URL), node (an element), time (words: *4 min left*, *took 18 min*: the time leaves the corner, decisions §283.17), much (words: the spend)}`. */
export function withPreview(props, spec) {
  const call = (k, e) => { try { props[k]?.(e); } catch (err) { console.error(err); } };
  return { ...props,
    onPointerEnter: (e) => { call("onPointerEnter", e); if (e.pointerType !== "touch") arm(e.currentTarget, spec); },
    onPointerLeave: (e) => { call("onPointerLeave", e); leave(e.currentTarget); },
    onFocus: (e) => { call("onFocus", e); arm(e.currentTarget, spec); },
    onBlur: (e) => { call("onBlur", e); leave(e.currentTarget); } };
}

/** What a back shows: its goal's `name` and the `line` of its state (the card keeps the same words in its `aria-label`), with the goal `n`'s rune. */
export const backSpec = (name, line, n = {}) => () => ({ mode: "back", name, line, element: n.element || "", hue: n.hue || n.element || "" });

if (typeof document !== "undefined") {
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || !(shown.value || timer)) return;
    hidden = anchor;
    hide();
  }, true);
  document.addEventListener("pointerdown", () => { if (shown.value || timer) hide(); }, true);
}

/** The preview: one box on the body, filled while `shown` is. */
export function Preview() {
  const s = shown.value;
  if (!s) return null;
  const style = `left:${s.at.left}px;top:${s.at.top}px`;
  if (s.mode === "back") {
    return html`<div class="ork-card pv pv--back" style=${style} data-preview="back" aria-hidden="true">
      <span class="pv-rune"><${Elem} name=${s.element || ""} hue=${s.hue || ""} dim=${!s.element} /></span>
      <span class="pv-nm">${s.name}</span>${s.line && html`<span class="pv-line">${s.line}</span>`}</div>`;
  }
  return html`<div class=${cls("ork-card pv pv--face", { [`el-${s.hue}`]: !!s.hue, [`is-${s.signal}`]: !!s.signal })} style=${style} data-preview="face" aria-hidden="true">
    <${CornerTop} rune=${{ name: s.element, hue: s.hue, dim: !s.element }} kind=${s.kind} signal=${s.signal} />
    <span class="pv-nm">${s.name}</span>
    <span class="pv-pic">${s.node ? s.node : s.picture ? html`<img class="sm-pic__img" src=${s.picture} alt="" />` : s.kind && html`<${Sign} name=${s.kind} big=${true} />`}</span>
    ${(s.time || s.much) && html`<span class="pv-time" data-preview-time=${s.time || undefined}>${s.time && html`<span class="pv-time__t">${s.time}</span>`}${s.much && html`<span class="pv-time__m">${s.much}</span>`}</span>`}</div>`;
}
