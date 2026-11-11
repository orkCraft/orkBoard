// The frame every spread shares (docs/mockups/spreads/, desktop): a veil over the window, the Orkmaster's head with a line and what it
// says, the field in the middle, the hand's strip under it (a note, the acts). Esc and *Close* put it away, the focus goes back to what
// opened it (open.js). The pieces drawn in a field: a card (`SpCard`), a card face down (`SpBack`), a check's mark (`Chk`).
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../../html.js";
import { Icon } from "../../orkui.js";
import { HeadOf, whoOf } from "../../table/post.js";
import { Index } from "../card.js";
import { closeSpread } from "./open.js";

/** `kind`: the spread (its `data-spread`); `title`, `line`, `say`: its head; `note`: the hand's words; `acts`: the hand's buttons; children: the field. */
export function SpreadFrame({ kind, title, line = "", say = "", note = "", acts = null, children }) {
  const root = useRef();
  useEffect(() => {
    root.current?.querySelector(".sp-shut")?.focus();
    const key = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeSpread(); } };
    addEventListener("keydown", key, true);
    return () => removeEventListener("keydown", key, true);
  }, []);
  return html`<div ref=${root} class="sp-veil" role="dialog" aria-modal="true" aria-label=${title} data-spread=${kind}>
    <div class="sp">
      <header class="sp-h"><span class="sp-av"><${HeadOf} w=${whoOf("orkmaster")} size="big" /></span>
        <span class="sp-t"><b>${title}</b>${line && html`<small>${line}</small>`}</span>
        ${say && html`<span class="sp-say">${say}</span>`}
        <button type="button" class="ork-btn sp-shut" onClick=${closeSpread}><${Icon} name="close" /><span>Close</span></button></header>
      <div class="sp-field">${children}</div>
      <footer class="sp-hand">${note && html`<p class="sp-note">${note}</p>`}${acts && html`<div class="sp-acts">${acts}</div>`}</footer>
    </div></div>`;
}

/** A key as the mockup shows it: `<kbd>`. */
export const Key = ({ k }) => html`<kbd class="sp-kb">${k}</kbd>`;

/** A check's mark on a card's corner: green with a check; red with a cross when `no`. */
export const Chk = ({ no = false }) => html`<span class=${cls("sp-chk", { "is-no": no })} aria-hidden="true">${no ? "✕" : "✓"}</span>`;

/** A card face up in a spread: its party's colour (`party`), the goal's rune and sign (`n`), its name, a line, and more under them (children).
 *  `size`: xl, lg, md or sm; `tilt`: its turn in degrees; `mark`: "ok" or "no" puts a check on it. */
export function SpCard({ party, n = null, name, line = "", size = "lg", tilt = 0, mark = "", muted = false, portal = false, label = "", children }) {
  const w = whoOf(party || "orkmaster");
  return html`<div class=${cls("ork-card cards-s sp-card", { [`is-${size}`]: true, "is-muted": muted, "is-portal": portal })} data-race=${w.race || "orkmaster"} style=${tilt ? `--rot:${tilt}deg` : ""} aria-label=${label || undefined}>
    ${size !== "sm" && html`<${Index} n=${n} />`}${mark && html`<${Chk} no=${mark === "no"} />`}
    ${(size === "xl" || size === "lg") && html`<span class="sp-pic"><${HeadOf} w=${w} size=${size === "xl" ? "big" : "mid"} /></span>`}
    <b class="sp-card__name">${name}</b>${line && html`<small class="sp-card__line">${line}</small>`}${children}</div>`;
}

/** A card face down (orkUI's back): what is not needed yet. A button when `onPress` is given (it turns the card). */
export function SpBack({ tilt = 0, size = "md", name = "", onPress = null }) {
  const style = tilt ? `--rot:${tilt}deg` : "";
  return onPress ? html`<button type="button" class=${cls("sp-back", `is-${size}`)} style=${style} aria-label=${`${name}, face down. Press to turn it.`} onClick=${onPress}></button>`
    : html`<span class=${cls("sp-back", `is-${size}`)} style=${style} aria-hidden="true"></span>`;
}
