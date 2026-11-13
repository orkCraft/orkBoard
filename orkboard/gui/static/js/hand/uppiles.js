// The crown's piles on the phone (docs/specs/147-one-card-four-corners.md part F.1, decisions §251.3–§251.4; the look: docs/mockups/card-ratio/ section 5): the Orkmaster's column as part B draws it, in the menu's sheet over its leaders — **In analysis** the Orkmaster's hand (the fan of small backs,
// the goal being read lifted), **To review** the squared deck of backs on their side (13 px under the screen's edge), **At work** standing cards (every one behind the front showing its foot) —, each pile's words beside it (*reading: …*, *next in 2 min: …*), not under it, so the sheet is not tall. The cards are
// the column's (table/piles.js `Pile`, fan.js): this file only says which goals each pile holds and what a press does (it is passed in: the menu picks the goal and closes). A screen of its own: the sheet may scroll (decisions §251.4). Layout only (upmenu.css).
import { html } from "../html.js";
import { mapData } from "../shell/store.js";
import { waitsWords } from "../table/holdwords.js";
import { askedWords } from "../table/passing.js";
import { PILES_OLD, Pile, nextWords, pilesOfOld, underOf } from "../table/piles.js";

/** The piles of the project's goals, as the column draws them; nothing when no goal lies in any of them. `onPress(n)`: a card pressed. */
export function Piles({ onPress }) {
  const piles = pilesOfOld(mapData.value?.nodes || []);
  if (!PILES_OLD.some(([id]) => piles[id].length)) return null;
  const behind = piles.analysis.find(({ n }) => askedWords(n.slug));
  const under = { analysis: underOf(piles.analysis) || waitsWords(piles.analysis.map((x) => x.n)), review: nextWords(piles.review), work: "" };
  return html`<section class="up-piles" aria-label="The Orkmaster's piles" data-piles="1">
    ${PILES_OLD.map(([id, title]) => html`<${Pile} key=${id} id=${id} title=${title} items=${piles[id]} under=${under[id]} asked=${id === "analysis" && behind ? askedWords(behind.n.slug) : ""} onPress=${(n) => onPress(n)} />`)}
  </section>`;
}
