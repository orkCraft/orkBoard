// A party's concerns in its header (docs/specs/168 D4, decisions §283.21; E1 gathers the header's groups): a small card for each open concern of the leader, at the right of the row, 28 x 39 (a 56 x 78 card at half), the row never taller for them.
// A concern in the hand (an alert) lies face up with the alert's ring; a note face up in the muted ink; one laid **Later** face down, out of the hand, until the leader's next look finds it again. The card is the hand's card and the scheme's
// mark (concernlit.js): hovered or focused it lights both, and pressed it lifts the hand's card, else it shows the concern on the scheme (a note or a card laid Later has no card in the hand). The record is the snapshot's (`goals[].concerns.list`,
// realm/concerns.py `cards`), so the header, the hand and the scheme read one list. Nothing here sends a command.
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { lift } from "../frame/state.js";
import { wide } from "./data.js";
import { liftKey } from "../hand/state.js";
import { isLit } from "./concernlit.js";
import { cardEl } from "./pickbox.js";

if (typeof document !== "undefined") {
  const href = new URL("./concernrow.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const concernKey = (party, id) => `concern/${party}/${id}`;

/** What a concern's card says in words: *Alert on Cart: No way back*, *Later: …* for one laid face down. */
export const cardWords = (c) => `${c.later ? "Later" : c.level === "alert" ? "Alert" : "Note"} on ${c.name}: ${c.what}`;

/** The concern's mark on the scheme, shown (scrolled into view and its card pressed, as a step through the marks does). */
function showOnScheme(c) {
  const w = [...document.querySelectorAll(".table-body [data-pick-id]")].find((x) => x.dataset.pickId === c.on);
  const el = w ? cardEl(w) : null;
  if (!el) return;
  el.scrollIntoView?.({ block: "center", inline: "center" });
  if (!el.matches(".is-lifted, [aria-pressed=true]")) el.click();
}

/** The party's concerns as small cards in its header; nothing for a party with none open. `g`: the party's row of the snapshot. */
export function ConcernCards({ g }) {
  const list = g?.concerns?.list || [];
  if (!list.length) return null;
  return html`<span class="cn-cards" role="group" aria-label="Concerns" data-party=${g.slug}>${list.map((c) => {
    const key = concernKey(g.slug, c.id), face = c.later ? "down" : "up", words = cardWords(c);
    const press = () => { if (c.in_hand && wide.value) lift(liftKey(key)); else showOnScheme(c); };
    return html`<button type="button" key=${c.id} class=${cls("cn-card", { "is-lit": isLit(g.slug, c.id) })} data-concern-id=${`${g.slug}/${c.id}`} data-face=${face} data-level=${c.level} data-in-hand=${c.in_hand ? "1" : "0"}
      aria-label=${words} title=${words} onClick=${press}>
      ${c.later ? html`<span class="ork-card-back small cn-card__back" aria-hidden="true"></span>`
        : html`<span class=${cls("ork-card sm cn-card__face", { "is-alert": c.level === "alert" })} aria-hidden="true"><span class="sm-pic">${c.level === "alert" ? html`<${Sign} name="alert" big=${true} />` : html`<i class="cn-dot"></i>`}</span></span>`}
    </button>`;
  })}</span>`;
}
