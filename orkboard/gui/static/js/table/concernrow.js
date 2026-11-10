// A party's concerns in its header (docs/specs/168 E1, which replaces D4's 28 x 39 stand-in, decisions §283.16.2, §283.21): a small card, 56 x 78, for each open concern of the leader, **face down** with the goal's rune on its seal, or a **+** for a concern on no goal.
// A concern in the hand (an alert) wears the alert's ring; a note none; one laid **Later** lies face down, out of the hand, until the leader's next look finds it again. The card is the hand's card and the scheme's mark (concernlit.js): hovered or focused it lights both,
// and pressed it lifts the hand's card, which plays it with its three ways (hand/concernplay.js), else it shows the concern on the scheme (a note or a card laid Later has no card in the hand). Hovered, its preview says the part and what is wrong (preview.js).
// The record is the snapshot's (`goals[].concerns.list`, realm/concerns.py `cards`), so the header, the hand and the scheme read one list. Nothing here sends a command.
import { html, cls } from "../html.js";
import { Elem, Icon } from "../orkui.js";
import { lift } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { wide } from "./data.js";
import { liftKey } from "../hand/state.js";
import { isLit } from "./concernlit.js";
import { cardEl } from "./pickbox.js";
import { backSpec, withPreview } from "./preview.js";

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

/** The goal a concern is on, when its row says one (`goal`, a slug): its node, else null. */
const goalOf = (c) => (c.goal ? (mapData.value?.nodes || []).find((n) => n.slug === c.goal) || null : null);

/** One concern as a small face-down card: the goal's rune, or a + for a concern on no goal. */
export function ConcernCard({ g, c }) {
  const key = concernKey(g.slug, c.id), goal = goalOf(c), words = cardWords(c), el = goal?.element || "";
  const press = () => { if (c.in_hand && wide.value) lift(liftKey(key)); else showOnScheme(c); };
  const props = withPreview({ class: cls("ork-card sb-back hd-concern", { "is-lit": isLit(g.slug, c.id) }), "data-concern-id": `${g.slug}/${c.id}`, "data-face": "down", "data-level": c.level, "data-later": c.later ? "1" : undefined, "data-in-hand": c.in_hand ? "1" : "0",
    "aria-label": words }, backSpec(c.name, `${c.later ? "Later · " : ""}${c.what}`, goal || {}));
  return html`<button type="button" ...${props} onClick=${press}><span class="ork-card-back small" aria-hidden="true"><span class="ork-card-back__seal">${goal ? html`<${Elem} name=${el} hue=${goal.hue || el} dim=${!el} />` : html`<${Icon} name="plus" />`}</span></span></button>`;
}

/** The party's concerns as small cards; nothing for a party with none open. `g`: the party's row of the snapshot. */
export function ConcernCards({ g, limit = 4 }) {
  const list = g?.concerns?.list || [];
  if (!list.length) return null;
  return html`<span class="cn-cards" role="group" aria-label="Concerns" data-party=${g.slug}>${list.slice(0, limit).map((c) => html`<${ConcernCard} key=${c.id} g=${g} c=${c} />`)}</span>`;
}
