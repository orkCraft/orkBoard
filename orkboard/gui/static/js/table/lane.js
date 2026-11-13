// The discard column: the window's right column, **beside the table** and not in it (docs/specs/161-the-tables-look-and-the-rooms-things.md D, decisions §273; before it Release's lane under its tab, docs/specs/156-one-pick-and-the-release-column.md D.3–D.6, decisions §261.7–§261.10; before it the table's edge, spec 150 D). Its head is a row for what never changes the table (`.release-lane__head`, spec 168 A4, decisions §285): the potions in a row at its left (hand/potionrow.js), the lamp's chain at its right edge with *Stop all* under it, over the label. At 760 px and up, on every tab, as wide as a lane
// (`--col-w`) and flush with the window's right edge: its label *Discard* (the Orkmaster's tab), *<party>'s discard* (a party's, Live's and Release's), **through the open tab's eyes** — on a party's tab the goals whose route held that party (`routeParties`), on the
// Orkmaster's, Live's and Release's the project's —, its cards whole at the hand's size, **top to bottom**: the goal ready for main (with the portal's ring round the top one, ring.js, only while one is ready, checked or going in), the goals done and not yet seen
// (newest first; the moon of a night's goal as before). **The past is not here**: it lies in the history book (hand/book.js, table/history.js; spec 168 G3, decisions §283.28). **Each card is picked** (part B, frame/state.js `pick`); a goal done and not seen is told to the host as seen when it is picked (`ideas.seen`) and then lies
// with its version in the past. To main is the picked ready card's act on the table (tomain.js). The lane scrolls with the table (only the table scrolls: §254.2). A project with no Release party seated has the column all the same (Release is a craft as any, decisions §274.1) with the word *Discard* on every tab; with no gate
// (`noGate`) there is no portal and no goal ready for main. **Two piles** (spec 168 F2, decisions §283.27: table/plates.js): under the *main* plate the upper one, in dev and waiting for main; under the *dev* plate the lower one, done on its own branch and waiting for dev, drawn only while *Lands in dev by itself* is off. A form over the pane leaves the lane drawn (decisions §283.5). Layout only: lane.css, discard.css (the card's anatomy is the hand's).
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { act } from "../shell/store.js";
import { TESTING, mergeGate, testing } from "../arena/gate.js";
import { ORKMASTER, pick, picked, tab } from "../frame/state.js";
import { readyOf, readyWords } from "../hand/data.js";
import { nightMoons } from "../hand/nightcard.js";
import { shownDone, useNightDeal } from "./discard.js";
import { columnOn, isLive, isRelease, nameOf, noGate, openTabOf, partiesAll, roadParties, routeParties } from "./data.js";
import { laidNow } from "./laying.js";
import { lowerHeld } from "./plates.js";            // the two piles and the plates over them (spec 168 F2)
import { discardLabel } from "./chroniclewords.js";
import { choose, chosenSlug, close } from "./portal.js";
import { PotionRow } from "../hand/potionrow.js";
import { StopAll } from "./stopall.js";
import { PresenceChain } from "./presence.js";
import { CardsPiles } from "../cards/discard.js";                                  // the table of cards' look (goal 170): the piles as S cards

/** Whether the lane is drawn: the table is laid. A form over the pane leaves it, nothing changes size by what is open (decisions §283.5). */
export const laneShown = () => laidNow();

/** The party whose eyes the lane looks through: a leader's slug on its own tab, "" on the Orkmaster's, Live's and Release's (the project's). */
const eyesOf = (g) => (g && !isRelease(g) && !isLive(g) ? g.slug : "");

export function ReleaseLane({ tab, parties }) {
  const g = parties.find((x) => x.slug === tab) || null, party = eyesOf(g), scroll = useRef(), moons = nightMoons();
  useNightDeal();                                                                                   // the night's goals are dealt into the pile one by one (discard.js `shownDone`)
  const headless = !roadParties().release, label = headless || tab === ORKMASTER || !g ? discardLabel() : discardLabel(nameOf(g));
  const held = (slug) => !party || routeParties(slug).has(party);                                    // a goal is a party's when its route held it
  const ready = noGate() ? null : readyOf(), goals = (ready?.goals || []).filter((x) => held(x.slug)), top = goals[0] || null, own = !!ready && !ready.goals.length && !party && ready.commits > 0;
  const inReady = new Set(goals.map((x) => x.slug)), done = shownDone().filter((x) => held(x.slug) && !inReady.has(x.slug)), now = picked.value, lowerGoals = lowerHeld(held);
  const upper = !noGate() && !!(top || goals.length || own || done.length);                                                          // the upper pile (in dev, waiting for main) has its plate; the lower pile (done on its branch, waiting for dev) lies under it with its own
  useEffect(() => {                                                                                 // the ready card picked is the goal chosen for the portal (its plan and its checks); any other pick, or none, drops the choice
    if (now && inReady.has(now)) choose(now);
    else if (chosenSlug()) close();
  }, [now, [...inReady].join(",")]);
  const press = (slug) => {                                                                          // a card pressed is picked (again: put away); a goal not yet seen is told so
    const again = picked.peek() === slug;
    pick(slug);
    if (!again && shownDone().some((x) => x.slug === slug)) act("ideas.seen", { idea: slug });
  };
  const merge = (e) => mergeGate(e);
  const ownNode = own && html`<p class="release-lane__own cap">${readyWords(ready)}: commits that belong to no goal.<button type="button" class="ork-btn" data-to-main disabled=${testing.value} onClick=${merge}>To ${ready.main}</button>${testing.value && html` <span role="status" data-testing>${TESTING}</span>`}</p>`;
  return html`<aside class=${cls("release-lane", { "is-headless": headless })} aria-label=${label} data-lane="release" data-through=${party || undefined}>
    <div class="release-lane__head" data-room-things="discard"><${PotionRow} /><div class="release-lane__side"><${PresenceChain} half=${true} /><${StopAll} /></div></div>
    <span class="release-lane__label">${label}</span>
    <div class="release-lane__scroll" ref=${scroll}>
      <${CardsPiles} p=${{ upper, goals, ready, own: ownNode, done, lowerGoals, now, press, moons }} />
    </div>
  </aside>`;
}

/** The column at the window's right (frame.js): the discard beside the table on the open tab, or nothing under 760 px, before the table is laid. */
export function DiscardColumn() {
  const parties = partiesAll();
  return columnOn() && laneShown() ? html`<${ReleaseLane} tab=${openTabOf(tab.value, parties)} parties=${parties} />` : null;
}
