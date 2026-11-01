// What a goal's back is drawn of (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.3–§6.4, decisions §198.8): the seal of summoning (orkUI's `.ork-sigil`, the + card's), **its own rune lit at the seal's top** in its colour (glowing while the leaders talk it over:
// orkUI's `.is-glowing`), **its short name at the back's foot**, no +. While the goal waits to start by itself the seal's ring of runes is the wait: it fills clockwise from the rune in eight steps, its share the page's `--ork-sigil-share` (orkUI's
// `.ork-sigil.is-waiting` will read it; until it is copied, table.css sets orkUI's own `--_arc` from it, spec 120 §6.11). A leaf: the card (backcard.js) and the copy that flies from the field (hand/fieldturn.js) both draw it.
import { html, cls } from "../html.js";
import { Elem } from "../orkui.js";

export const STEPS = 8;                                    // the ring fills in eight steps over the wait (§187.4's rite, slowed)

/** The share of the wait gone, `1 - left/seconds`, in eighths (0 to 1): the ring stands where its step is. */
export function shareOf(ripe) {
  const total = Number(ripe?.seconds) || 0, left = Number(ripe?.left_s);
  if (!(total > 0) || !Number.isFinite(left)) return 0;
  return Math.min(STEPS, Math.max(0, Math.ceil((1 - left / total) * STEPS - 1e-9))) / STEPS;
}

/** *4 min*, *40 s*: the time left of a wait, rounded up (a minute is always shown whole). */
export function leftWords(left_s) {
  const s = Math.max(0, Math.ceil(Number(left_s) || 0));
  return s >= 60 ? `${Math.ceil(s / 60)} min` : `${Math.max(1, s)} s`;
}

/** The back's body: the seal with the goal's rune and the short name. `waiting`: the share of the wait (0 to 1) when the ring is the wait, null otherwise; `glowing`: the leaders are talking it over. */
export function BackBody({ element = "", name = "", glowing = false, waiting = null }) {
  return html`<span class=${cls(`ork-sigil table-back-sigil${element ? ` is-${element}` : ""}`, { "is-waiting": waiting != null })} style=${waiting != null ? `--ork-sigil-share:${waiting}` : undefined} aria-hidden="true"><span class="ork-sigil__seal"><${Elem} name=${element} dim=${!element} glowing=${glowing} /></span></span>
    <span class="table-back-nm">${name}</span>`;
}
