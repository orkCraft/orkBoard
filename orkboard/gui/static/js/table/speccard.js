// A card of Specs (docs/specs/168-the-window-played-as-a-card-games-table.md B2, decisions §283.11, §241.3): orkUI's small back, 56 x 78, lying on its side (78 x 56) in a squared deck, the cards a few px apart and 13 px under the window's left edge (decisions §236, §263.2). Its middle holds the goal's rune in a ring
// (orkUI's `.ork-sigil.is-waiting`, filled in eighths by `share` in the goal's colour): for a spec being written the share of its sections written, for a spec made the share of its wait gone; a goal that waits for the person has the ring full and still in the alert and its frame in the alert; a failure the
// frame in the danger. Hovered or focused it shows its goal's name and state beside it (preview.js); a press picks its goal (column.js). The cards behind the front show their edge. Layout is column.css; this file draws only, `piles.js` says what each card shows.
import { html, cls } from "../html.js";
import { Elem } from "../orkui.js";
import { backSpec, withPreview } from "./preview.js";

export const SPEC_W = 78, SPEC_H = 56;

/** One card of the deck. `say`: its state in words (its label and its preview's line); `share`: the ring (0 to 1, in eighths); `asks`: it waits for the person; `writing`: its spec is being written (its rune glows where `glow`); `look`: the clock time its look ends at; `bad`: a failure;
 *  `own`: its dim and its hatch (piles.js `lit`); `on`: it is the goal picked. */
export function SpecCard({ n, i, say, proposed, share, asks, writing, look, glow, bad, own, on, onPress }) {
  const el = n.element || "", hue = n.hue || el;
  return html`<button type="button" class=${cls("ork-card col-card col-card--down col-card--spec", { "ork-picked": on, asks, fails: bad, "is-dim": own.dim })} ...${withPreview(own.hatch, backSpec(n.title, say, n))} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="review" data-down="1"
    data-changing=${n.changing ? "1" : undefined} data-look=${look || undefined} data-writing=${writing ? "1" : undefined} data-proposed=${proposed ? "1" : undefined} style=${`--i:${i}`} aria-pressed=${String(on)} aria-label=${`${n.title}: ${say}`} onClick=${() => onPress(n, "review", "")}>
    <span class=${cls("ork-card-back small col-spec__back", { "is-ringed": on })} aria-hidden="true"></span>
    <span class=${cls(`ork-sigil table-back-sigil col-sigil col-spec__ring is-waiting${el && !asks ? ` is-${hue}` : ""}`, { "col-stopped": asks })} style=${`--ork-sigil-share:${share}`} data-share=${share} aria-hidden="true"></span>
    <span class="col-spec__rune" aria-hidden="true"><${Elem} name=${el} hue=${hue} dim=${!el} glowing=${!!glow} still=${false} /></span>
    ${proposed && html`<span class="col-spec__proposed" aria-hidden="true">proposed</span>`}
  </button>`;
}
