// What the loop map draws besides its rings (docs/specs/107-what-the-owners-day-said.md §14; decisions §182): the words of the spans and the feelings, the rings' places, **what the loop says** (one alert line a finding), **the economy**
// (each currency: what gives it, it, what takes it) and **the feeling** (a stepped line of the intensities of one loop's steps, each point its feeling's word). Written for loopmap.js; the sheet is maps.css.
import { html, cls } from "../html.js";
import { Chev, Sign } from "../orkui.js";
import { MapCard, keyOf } from "./mapkit.js";
import { lift } from "../frame/state.js";

export const MAP = "game-design";

/** The spans from the inside out, each its time (the leader is told the same, core/idea_loop.py). */
export const SPANS = [["core", "seconds"], ["session", "minutes"], ["meta", "days and weeks"]];
export const TIME = Object.fromEntries(SPANS);
export const cap = (w) => (w ? w[0].toUpperCase() + w.slice(1) : "");

/** MDA's eight, each with what it feels like (the back says it under the feeling). */
export const FEELS = [["sensation", "pleasure of the senses"], ["fantasy", "make-believe"], ["narrative", "a story unfolding"], ["challenge", "an obstacle to master"],
  ["fellowship", "being with others"], ["discovery", "uncharted ground"], ["expression", "making it one's own"], ["submission", "a pastime, no strain"]];
export const FEEL_HINT = Object.fromEntries(FEELS);
export const INTENSITIES = [[1, "calm"], [2, "easy"], [3, "steady"], [4, "tense"], [5, "peak"]];
export const KIND_WORDS = { soft: "soft", hard: "hard", energy: "energy", progress: "progress", social: "social", time: "time" };

/** A step's intensity as pips, 1 to 5 (orkUI's: drawn, never typed). */
export const Pips = ({ n }) => html`<span class="ork-pips mp-pips" role="img" aria-label=${`intensity ${n} of 5`}>${[1, 2, 3, 4, 5].map((i) => html`<i key=${i} class=${i <= n ? "d" : ""}></i>`)}</span>`;

export const RING_MIN = 640;                                             // under it the loops lie as lists
const HEIGHTS = { 1: 420, 2: 560, 3: 720 }, MARGIN = 62;

/** The rings' places in `w` px: the loops from the core out, each an ellipse with its steps' centres clockwise round it from just right of its top (half a step from it, so that the top keeps the ring's tag), and the
 *  chevron between each two (at the mid-angle, pointing along the loop). The core ring of a game with more loops has its tag in its middle, any other at its top. The card's width follows the room between the rings. */
export function layout(loops, w) {
  const n = loops.length, h = HEIGHTS[n] || HEIGHTS[1], cx = w / 2, cy = h / 2;
  const rxMax = Math.max(120, w / 2 - MARGIN), ryMax = h / 2 - 40;
  const rx0 = n === 1 ? rxMax : Math.max(120, rxMax * 0.4), ry0 = n === 1 ? ryMax : Math.max(96, ryMax * 0.48);
  const cw = n === 1 ? 116 : Math.round(Math.max(80, Math.min(104, ((rxMax - rx0) / (n - 1)) * 0.85)));
  const rings = loops.map((lp, i) => {
    const t = n === 1 ? 0 : i / (n - 1), rx = rx0 + (rxMax - rx0) * t, ry = ry0 + (ryMax - ry0) * t, k = lp.steps.length;
    const at = (a) => [cx + rx * Math.cos(a), cy + ry * Math.sin(a)];
    const places = lp.steps.map((_, j) => {
      const a = -Math.PI / 2 + ((j + 0.5) / k) * 2 * Math.PI, m = a + Math.PI / k, [x, y] = at(a), [mx, my] = at(m);
      const dx = -rx * Math.sin(m), dy = ry * Math.cos(m);
      return { x, y, mx, my, dir: Math.abs(dx) >= Math.abs(dy) ? (dx > 0 ? "right" : "left") : dy > 0 ? "down" : "up" };
    });
    return { rx, ry, places, tag: n > 1 && i === 0 ? { x: cx, y: cy, mid: true } : { x: cx, y: cy - ry, mid: false } };
  });
  return { h, cx, cy, cw, rings };
}

/** The path (in px, from the ring's top, clockwise) the pixel dot steps round. */
export const orbitOf = (cx, cy, rx, ry) => `path('M ${cx} ${cy - ry} A ${rx} ${ry} 0 1 1 ${cx} ${cy + ry} A ${rx} ${ry} 0 1 1 ${cx} ${cy - ry}')`;

/** **What the loop says**: one alert line a finding (`ideas.loop`'s `findings`, by code); nothing when it has nothing to say. */
export function Says({ lines }) {
  if (!lines?.length) return null;
  return html`<ul class="mp-says" aria-label="What the loop says">${lines.map((t) => html`<li key=${t} class="mp-says__line" data-tone="alert"><${Sign} name="alert" /><span>${t}</span></li>`)}</ul>`;
}

const names = (steps) => steps.map((s) => s.name);

/** **Why a player comes back**: the hooks, D1, D7 and D30, a line each. */
const Hooks = ({ hooks }) => (hooks?.length ? html`<div class="mp-hooks"><span class="ork-label">Why a player comes back</span>
  <ul class="mp-hooks__list">${hooks.map((h) => html`<li key=${h.when}><b class="mp-hooks__when">${h.when}</b><span>${h.line}</span></li>`)}</ul></div>` : null);

/** **The economy**: each currency as *what gives it → it → what takes it*; a side nothing stands on says so, in the alert tone. A currency's press lifts its card (the back is loopmap.js's). Under it, why a player comes back. */
export function Economy({ d }) {
  const cs = d.currencies || [], steps = (d.loops || []).flatMap((lp) => lp.steps);
  const side = (list) => (list.length ? html`<ul class="mp-eco__list">${names(list).map((n, i) => html`<li key=${i}>${n}</li>`)}</ul>` : html`<span class="mp-eco__none">nothing</span>`);
  return html`<section class="mp-eco" aria-label="The economy"><span class="ork-label">The economy</span>
    ${!cs.length && html`<p class="mp-cap">No currency is named yet</p>`}
    ${cs.map((c) => html`<div key=${c.id} class="mp-eco__row" data-currency=${c.id}>
      <div class="mp-eco__side is-in"><span class="mp-cap">Given by</span>${side(steps.filter((s) => s.gives.includes(c.id)))}</div>
      <${Chev} dir="right" />
      <${MapCard} map=${MAP} id=${`cur:${c.id}`} name=${c.name} group="economy" compact=${true} className="mp-cur" foot=${html`<span class="mp-st__meta"><span>${KIND_WORDS[c.kind] || c.kind}</span></span>`} />
      <${Chev} dir="right" />
      <div class="mp-eco__side is-out"><span class="mp-cap">Taken by</span>${side(steps.filter((s) => s.takes.includes(c.id)))}</div>
    </div>`)}
    <${Hooks} hooks=${d.hooks} />
  </section>`;
}

/** The loop **the feeling** is drawn from: the session loop's, else the core's, else the first. */
export const feelingLoop = (loops) => loops.find((l) => l.span === "session") || loops.find((l) => l.span === "core") || loops[0] || null;

const PAD = { l: 44, r: 84, t: 34, b: 34 }, PLOT_H = 100;

/** **The feeling**: a stepped line of the intensities of one loop's steps, one point a step, each labelled with its feeling's word (above the stretch it holds, so that no riser crosses it); a press on a point
 *  lifts its step. */
export function Feeling({ loop, width }) {
  if (!loop) return null;
  const w = Math.max(240, width || 0), n = loop.steps.length, h = PLOT_H + PAD.t + PAD.b, tight = n > 1 && (w - PAD.l - PAD.r) / (n - 1) < 80;      // too close for every word above its line: every other one goes under
  const x = (i) => (n === 1 ? w / 2 : PAD.l + (i * (w - PAD.l - PAD.r)) / (n - 1)), y = (v) => PAD.t + ((5 - v) / 4) * PLOT_H;
  const path = loop.steps.map((s, i) => (i === 0 ? `M ${x(0)} ${y(s.intensity)}` : `H ${x(i)} V ${y(s.intensity)}`)).join(" ") + ` H ${w - 12}`;
  return html`<section class="mp-feel" aria-label="The feeling" data-loop=${loop.span}>
    <span class="ork-label">The feeling · ${loop.name} (${loop.span})</span>
    <svg class="mp-feel__svg" width=${w} height=${h} viewBox=${`0 0 ${w} ${h}`} role="img" aria-label=${`How intense each step of the ${loop.span} loop is, from calm to peak`}>
      ${[1, 2, 3, 4, 5].map((v) => html`<line key=${v} class="mp-feel__grid" x1=${PAD.l - 10} x2=${w - 12} y1=${y(v)} y2=${y(v)} />`)}
      <text class="mp-feel__axis" x="0" y=${y(5) + 4}>peak</text><text class="mp-feel__axis" x="0" y=${y(1) + 4}>calm</text>
      <path class="mp-feel__line" d=${path} />
      ${loop.steps.map((s, i) => html`<g key=${s.id} class="mp-feel__pt" data-step=${s.id} data-feel=${s.feel} data-intensity=${s.intensity} onClick=${() => lift(keyOf(MAP, s.id))}>
        <title>${`${s.name}: ${s.feel || "no feeling said"}, intensity ${s.intensity} of 5`}</title>
        <rect class="mp-feel__dot" x=${x(i) - 4} y=${y(s.intensity) - 4} width="8" height="8" />
        <text class="mp-feel__word" x=${x(i) + 9} y=${y(s.intensity) + (tight && i % 2 ? 20 : -8)}>${s.feel || "—"}</text>
      </g>`)}
    </svg>
  </section>`;
}

/** A step's small card on its ring (or in a list): its name, its feeling's word and its intensity as pips; a press lifts it (loopmap.js draws the back). */
export function StepCard({ s, style, narrow }) {
  return html`<${MapCard} map=${MAP} id=${s.id} name=${s.name} group="loop" compact=${true} className=${cls("mp-st", { "is-narrow": narrow })} style=${style}
    foot=${html`<span class="mp-st__meta"><span>${s.feel || "no feeling said"}</span></span><${Pips} n=${s.intensity} />${narrow && html`<span class="mp-card__foot is-three">${s.line}</span>`}`} />`;
}
