// The hand on a phone, its one screen (docs/specs/117-the-phone-a-menu-of-the-leaders.md §3 and §5, docs/specs/103-the-phones-app-a-native-frame.md §1, decisions §174.1, §178, §179, §180, §195, §291.5; the mockups docs/mockups/phone/): from the top, the Orkmaster's line when
// the work moved on (table/notice.js), the top row (uptop.js: the crown, the project, Settings, Stop all, the potions as bottles, the lamp's chain, the discard; it folds to a thin row when the middle is scrolled), the middle — it scrolls — and the hand's row at the foot (uprow.js: the + card at its left, the round button at its right, upround.js). The middle shows what is picked (uplook.js): a goal with its way (upway.js) and,
// when it has a card in the hand, that card with its answers on it (stopcard.js `Lifted` with `inline`, or readycard.js `ReadyCard` for a goal ready for main); the card of no goal; else the project's feed (upfeed.js, goal 169 F), narrowed to a party when one is picked.
// The crown opens the menu of the leaders (upmenu.js). The row is one card an entry (entries.js); a press picks one, a press on the one looked at goes back to the feed, and answering the last card of the entry on the screen picks the next one at once (no motion of
// its own). With the middle on the feed or on a goal that has no card, no card of the row is raised. The field the + card opens lies over the keyboard (updeck.js).
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { ORKMASTER, openTab, picked, tab } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { Notice } from "../table/notice.js";
import { readyOf } from "./data.js";
import { at, entriesOf, looking, pickEntry, placeOf, toFeed } from "./entries.js";
import { fieldOpen } from "./state.js";
import { said } from "./motion.js";
import { DeckField } from "./updeck.js";
import { Look, lookOf } from "./uplook.js";
import { useKeyboard } from "./upkeys.js";
import { Sheet } from "./upmenu.js";
import { Row } from "./uprow.js";
import { Top } from "./uptop.js";
import { feltOf } from "../table/felt.js";
import { presenceNow } from "../table/presence.js";
import { partiesAll } from "../table/data.js";
import { routeOf } from "./upway.js";
import "./turnphone.js";                                   // a card at its turns and a battle open on the phone as a question does (decisions §298.7)

/** The felt the phone's table wears (spec 161 K, decisions §275.3): the party shown, the party of the goal shown (the one at work in its route, else its first, else the goal's own) or of the card's leader; the Orkmaster's wood when none is. */
function feltOfLook(look) {
  if (look.kind === "party") return feltOf(look.g);
  const legs = look.node ? routeOf(look.node) : [], at = legs.find((r) => r.state === "now") || legs[0], stop = look.entry?.stops?.[0];
  const slug = at?.slug || look.node?.goal || stop?.row?.goal || stop?.row?.party || "";
  return (slug && feltOf(partiesAll().find((g) => g.slug === slug))) || "orkmaster";
}

/** The hand on a phone. `root`: the hand's element ref (the keys), `stacks`: data.js `stacksOf`, `plus`: opens the field. */
export function Upright({ root, stacks, plus }) {
  const entries = entriesOf(stacks.flatMap((st) => st.cards), readyOf()?.goals || []), look = lookOf(entries, placeOf(entries)), field = fieldOpen.value, had = useRef(""), keys = useKeyboard();
  const typing = field || look.kind === "feed" || look.kind === "party" ? 0 : keys;      // the keyboard is up and neither the + card's field nor the feed's own is what it is for: the opened card gives up 5 : 7 (spec 147 F.3)
  const project = currentProject.value?.path || "";
  useEffect(() => { if (tab.value !== ORKMASTER) openTab(ORKMASTER); }, [project]);                      // a phone starts on the whole feed: the party the tabs kept on this device is not looked at
  useEffect(() => {
    if (look.kind === "goal" && look.entry) { had.current = look.slug; if (at.value !== look.entry.key) at.value = look.entry.key; }              // the card on the screen is the entry `at` names, so its place is kept when it goes
    else if (look.kind === "goal" && had.current === look.slug && picked.value === look.slug) { had.current = ""; const next = entries[placeOf(entries)]; if (next) pickEntry(next); else toFeed(); }       // its last card was answered: the next entry comes, the feed when none is left
    else { had.current = ""; if (look.kind === "feed" && looking.peek()) looking.value = false; }                     // nothing left to look at: a card that comes later does not take the feed's place
  }, [look.kind, look.slug, look.entry?.key]);
  return html`<footer ref=${root} class=${cls("hand hand-up ork-table", { "is-out": presenceNow()?.here === false })} data-party=${feltOfLook(look)} aria-label="The hand" data-upright="1" data-typing=${typing ? "1" : undefined}>
    <${Notice} />
    <${Top} />
    <${Look} look=${look} entries=${entries} typing=${typing} />
    <${Row} entries=${entries} cur=${look.entry} plus=${plus} />
    <${Sheet} entries=${entries} look=${look} />
    ${field && html`<${DeckField} />`}
    <span class="hand-live" role="status" aria-live="polite">${said.value}</span>
  </footer>`;
}
