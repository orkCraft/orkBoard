// The frame every spread shares is `../matframe.js`'s (goal 171 H): the mat on the felt, the Orkmaster's head with a line and what it
// says, the field in the middle, the hand's strip under it (a note, the acts, the seal). Esc and *Close* put it away, the focus goes back to what
// opened it (open.js). The pieces drawn in a field: a card (`SpCard`), a card face down (`SpBack`), a check's mark (`Chk`).
import { html, cls } from "../../html.js";
import { HeadOf, whoOf } from "../../table/post.js";
import { Index } from "../card.js";
import { named, signOf } from "../kind.js";
import { closeSpread, spread } from "./open.js";
import { Said } from "../said.js";
import { MatFrame } from "../matframe.js";

/** `kind`: the spread (its `data-spread`); `title`, `line`, `say`: its head; `note`: the hand's words; `acts`: the hand's buttons; `seal`: a `Seal` for a move that cannot be undone;
 *  `phase`: the goal's, along its foot (the gate, the battle); children: the field. It lies in `../matframe.js`'s frame. */
export function SpreadFrame({ kind, title, line = "", say = "", note = "", acts = null, hand = null, seal = null, phase = "", children }) {
  return html`<${MatFrame} kind=${kind} title=${title} line=${line} say=${say} note=${note} acts=${acts} hand=${hand} seal=${seal} phase=${phase} onClose=${closeSpread}
    extra=${spread.value?.said && html`<${Said} p=${spread.value.said} />`}>${children}</${MatFrame}>`;
}

/** A key as the mockup shows it: `<kbd>`. */
export const Key = ({ k }) => html`<kbd class="sp-kb">${k}</kbd>`;

/** A check's mark on a card's corner: green with a check; red with a cross when `no`. */
export const Chk = ({ no = false }) => html`<span class=${cls("sp-chk", { "is-no": no })} aria-hidden="true">${no ? "✕" : "✓"}</span>`;

/** A card face up in a spread: its party's colour (`party`), the goal's rune and sign (`n`), its name, a line, and more under them (children).
 *  `kind`: goal, decision or part (its sign at the top right and its name, decisions §300.4); `size`: xl, lg, md or sm; `tilt`: its turn in degrees; `mark`: "ok" or "no" puts a check on it. */
export function SpCard({ party, n = null, kind = "goal", name, line = "", size = "lg", tilt = 0, mark = "", muted = false, portal = false, label = "", onPress = null, picked = false, children }) {
  const w = whoOf(party || "orkmaster"), Tag = onPress ? "button" : "div", face = { ...n, sign: signOf(kind, n?.sign) };
  return html`<${Tag} type=${onPress ? "button" : undefined} onClick=${onPress || undefined} aria-pressed=${onPress && picked !== null ? String(!!picked) : undefined}
    class=${cls("ork-card cards-s sp-card", { [`is-${size}`]: true, "is-muted": muted, "is-portal": portal, "is-pick": !!onPress, "is-picked": picked })} data-race=${w.race || "orkmaster"} data-cardkind=${kind} style=${tilt ? `--rot:${tilt}deg` : ""} aria-label=${named(label || `${name}${line ? `: ${line}` : ""}`, kind)}>
    <${Index} n=${face} rune=${size !== "sm"} />${mark && html`<${Chk} no=${mark === "no"} />`}
    ${(size === "xl" || size === "lg") && html`<span class="sp-pic"><${HeadOf} w=${w} size=${size === "xl" ? "big" : "mid"} /></span>`}
    <b class="sp-card__name">${name}</b>${line && html`<small class="sp-card__line">${line}</small>`}${children}</${Tag}>`;
}

/** A pile's thickness, never a number: up to six backs, each a little higher than the one under it (`n` the cards in it; nothing when none). */
export function Thick({ n, label }) {
  if (n < 1) return null;
  return html`<span class="sp-col sp-deckl"><span class="sp-thick" aria-hidden="true">${Array.from({ length: Math.min(n, 6) }, (_, i) => html`<span key=${i} style=${`--dx:${i * 2}px;--dy:${-i * 2}px`}></span>`)}</span>
    <span class="sp-cap">${label}</span></span>`;
}

/** What a goal's card shows of its Board node: its rune, hue and sign. */
export const faceOf = (n) => ({ element: n?.element, hue: n?.hue, sign: n?.type?.sign || "" });

/** A card face down (orkUI's back): what is not needed yet. A button when `onPress` is given (it turns the card). */
export function SpBack({ tilt = 0, size = "md", name = "", onPress = null }) {
  const style = tilt ? `--rot:${tilt}deg` : "";
  return onPress ? html`<button type="button" class=${cls("sp-back", `is-${size}`)} style=${style} aria-label=${`${name}, face down. Press to turn it.`} onClick=${onPress}></button>`
    : html`<span class=${cls("sp-back", `is-${size}`)} style=${style} aria-hidden="true"></span>`;
}
