// The phone's hand, its row (docs/specs/117-the-phone-a-menu-of-the-leaders.md §3.2, docs/mockups/phone/sidebar.html, decisions §195.4): one card an entry (entries.js `entriesOf`: a goal's cards one entry, a card of no goal one, a goal ready for
// main one), each showing its upper part — its element, its name (three lines at most: stopcard.js `upName`), its window with the action's sign and its asker's head small in the corner (the alert's colour when it asks or failed) —, in a row that
// scrolls sideways under the + card, which lies at the row's right end, fixed (a press opens the field: updeck.js `DeckField`). The picked entry is raised and wears the ink's frame; a press picks it (entries.js `pickEntry`). No count, and no
// edge for the rest of a goal's cards. With no entry the row is the + card alone. Layout only (upright.css); every colour, face and corner is orkUI's.
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { gateData } from "../shell/store.js";
import { Mark, headOf, labelOf, upName } from "./stopcard.js";
import { pickEntry } from "./entries.js";
import { PlusCard } from "./pluscard.js";

const ASKS = ["asks", "goal", "pick", "collide"];

/** What an entry's card says of itself: `{name, label, element, asker, sign, ask, fail}`; `sign` is the window's (a ready goal's is the check), `ask`/`fail` put the card in the alert's colour. */
function faceOf(e) {
  if (e.kind === "ready") {
    const name = `${e.name} is ready for ${gateData.value?.main || "main"}`;
    return { name, label: name, element: e.element, asker: e.head, sign: null, ask: false, fail: false };
  }
  const s = e.stops[0];
  return { name: upName(s), label: labelOf(s), element: s.node?.element || "", asker: headOf(s), sign: s, ask: ASKS.includes(s.kind), fail: s.kind === "failed" };
}

/** One entry as a card of the row. */
function Entry({ e, on, onPick }) {
  const f = faceOf(e);
  return html`<button type="button" class=${cls("ork-card up-card", { asks: f.ask, fails: f.fail, "is-picked": on })} data-key=${e.key} data-kind=${e.kind} aria-label=${f.label} aria-pressed=${String(on)} onClick=${onPick}>
    <span class="up-card__head"><${Elem} name=${f.element} dim=${!f.element} /><span class="up-card__name">${f.name}</span></span>
    <span class="up-card__window">${f.sign ? html`<${Mark} s=${f.sign} big=${true} />` : html`<span class="hand-mark is-ok"><${Sign} name="check" big=${true} /></span>`}
      ${f.asker && html`<span class="up-card__asker"><${Head} race=${f.asker.race} tier=${f.asker.tier} /></span>`}</span>
  </button>`;
}

/** The row: the entries' cards, the picked one (`cur`) raised and kept in view, the + card at the end. */
export function Row({ entries, cur, plus }) {
  const cards = useRef();
  useEffect(() => {                                              // the picked card is kept inside the row's clear part (the + card lies over its right end)
    const row = cards.current, el = row?.querySelector('[aria-pressed="true"]');
    if (!row || !el) return;
    const r = row.getBoundingClientRect(), c = el.getBoundingClientRect(), plusW = row.parentElement.querySelector(".up-plus")?.offsetWidth || 0, gutter = 12;
    if (c.left < r.left + gutter) row.scrollLeft -= r.left + gutter - c.left;
    else if (c.right > r.right - plusW - gutter) row.scrollLeft += c.right - (r.right - plusW - gutter);
  }, [cur?.key, entries.length]);
  return html`<div class="up-row" role="group" aria-label="Cards in the hand">
    <div class="up-cards" ref=${cards}>${entries.map((e) => html`<${Entry} key=${e.key} e=${e} on=${cur?.key === e.key} onPick=${() => pickEntry(e)} />`)}</div>
    <div class="up-plus"><${PlusCard} onPress=${plus} /></div>
  </div>`;
}
