// A card's four corners (docs/specs/147-one-card-four-corners.md part A, decisions §251.2): top left the rune (which goal), top right the kind (what card), bottom left who (whose work), bottom right how much (one figure by the card's state).
// Two rows, 20 px tall, `space-between` (corners.css): the sign is 14 px and the head 16 on every card, so they read as an index. The signal colours (the alert: it waits for you; the danger: it failed; the success: done) are in the kind's corner only.
// `muchOf` is pure: its cost before it is agreed, its time left at work (else the time it has worked, as the card said before), the time it took when done, *asks you* while it waits for the person; nothing known draws nothing.
import { html, cls } from "../html.js";
import { Elem, Head, Sign, headWords } from "../orkui.js";
import { workedWords } from "./worktime.js";

// the words, as realm/lexicon.py says them (corner_*; tests/test_corners_browser.py keeps them so)
export const ASKS = "asks you", LEFT = "left", TOOK = "took", WORKED = "worked", IN_MAIN = "in main since";

/** *4 min left*, *2 h left*: the time a task at work has left (`secs`). */
export function leftWords(secs) {
  const s = Math.max(0, Math.round(secs));
  return `${s < 3600 ? Math.max(1, Math.ceil(s / 60)) + " min" : Math.round(s / 3600) + " h"} ${LEFT}`;
}

/** *took 18 min*, *took 2 h*: the time it took. */
export function tookWords(secs) {
  const s = Math.max(0, Math.round(secs));
  return `${TOOK} ${s < 60 ? s + " s" : s < 3600 ? Math.round(s / 60) + " min" : Math.round(s / 3600) + " h"}`;
}

/** The seconds from one ISO time of the host to another, NaN when either is not usable. */
export const secondsBetween = (from, to) => (Date.parse(to || "") - Date.parse(from || "")) / 1000;

const known = (x) => typeof x === "number" && Number.isFinite(x) && x >= 0;

/** The one figure of the bottom right corner, `{ kind: "ask" | "time" | "gem", text }`, or null when nothing is known.
 *  `asks`: it waits for the person; `done` with `took` (seconds): the time it took; `left` (seconds) or, with none, `worked` (seconds) at work; `cost` (words) before it is agreed or spent. */
export function muchOf({ asks = false, done = false, took = NaN, left = NaN, worked = NaN, cost = "" } = {}) {
  if (asks) return { kind: "ask", text: ASKS };
  if (done && known(took) && took > 0) return { kind: "time", text: tookWords(took) };
  if (!done && known(left)) return { kind: "time", text: leftWords(left) };
  if (!done && known(worked)) return { kind: "time", text: `${WORKED} ${workedWords(worked)}` };
  if (cost) return { kind: "gem", text: cost };
  return null;
}

/** The top row: the goal's rune at the left (`rune`: Elem's props), the kind's sign at the right (`kind`: a sign's name) in the `signal`'s colour (`alert`, `danger`, `success`, else the muted ink). */
export function CornerTop({ rune = null, kind = "", signal = "", name = "", word = "", large = false, slot = "", kindSlot = "", kindClass = "", runeNode = null, kindNode = null }) {
  return html`<span class=${cls("corner corner--top", large && "corner--large")}>
    <span class="corner__rune">${runeNode ? runeNode : slot ? html`<span class="corner__slot" data-slot="rune">${slot}</span>` : rune && html`<${Elem} ...${rune} />`}${name && html`<span class="corner__name" title=${name}>${name}</span>`}</span>
    <span class=${cls("corner__kind", signal && `is-${signal}`)}>${kindNode ? kindNode : kindSlot ? html`<span class="corner__slot" data-slot="kind">${kindSlot}</span>` : html`${word && html`<span class=${cls("corner__word", kindClass)}>${word}</span>`}${kind && !kind.startsWith("tool:") && html`<${Sign} name=${kind} />`}`}</span>
  </span>`;
}

/** The bottom row (a gem whose `much.share` is false is a price in dollars, not a share of a window: spec 147 C): who at the left (`who`: `{ heads: [head…], word }`, one to three heads at 16 px and an optional word), how much at the right (`much`: `muchOf`'s; `ask`: it waits for you, the figure is then *asks you* in the alert). */
export function CornerFoot({ who = null, much = null, ask = false, large = false, whoSlot = "", muchSlot = "", whoNode = null, muchNode = null }) {
  const figure = ask ? { kind: "ask", text: ASKS } : much, heads = (who?.heads || []).filter(Boolean).slice(0, 3);
  return html`<span class=${cls("corner corner--foot", large && "corner--large")}>
    ${whoNode ? whoNode : whoSlot ? html`<span class="corner__slot" data-slot="who">${whoSlot}</span>` : html`<span class="corner__who" title=${heads.map(headWords).join(", ") || undefined}>${heads.map((h, i) => html`<${Head} key=${i} race=${h.race} tier=${h.tier} />`)}${who?.word && html`<span class="corner__word">${who.word}</span>`}</span>`}
    ${muchNode ? muchNode : muchSlot ? html`<span class="corner__slot" data-slot="much">${muchSlot}</span>` : figure && (figure.kind === "gem"
      ? html`<span class="corner__much"><span class=${figure.share === false ? "ork-gem" : "ork-gem share"} data-cost=${figure.text}>${figure.text}</span></span>`
      : html`<span class=${cls("corner__much", figure.kind === "ask" && "is-ask")} data-much=${figure.kind}>${figure.text}</span>`)}
  </span>`;
}
