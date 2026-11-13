// The Orkmaster's column (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part B, decisions §206.2–§206.3; mockup docs/mockups/goal-card/; as spec 156 B changed it, decisions §261.1, §261.5): pinned at the window's left at the wide width (frame/frame.js), the table's height, the same on every tab, off the table on
// orkUI's room as the hand is. **Its head is the Orkmaster's tab** — the crown and *The Orkmaster*, `role="tab"`, open at first, underlined when open; pressed again, the open tab's head asks (ask.js `data-ask-head`) — and under it the dealer's lane of the table of cards (cards/dealer.js, goal 170 D).
// A press on an empty place of the column puts the pick away (`picked`, frame/state.js: one pick across the window), as Esc and the browser's back do (state.js).
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { ORKMASTER, openOver, openTab, pick, picked, tab } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { openTabOf, partiesAll, partiesNow, mapName } from "./data.js";
import { askOpen, closeAsk, desk, openAsk } from "./ask.js";
import { moodOf } from "./moods.js";
import { SetupBubble } from "../hand/setupcards.js";
import { laidNow } from "./laying.js";
import { Passing } from "./passing.js";
import { CardsColumn } from "../cards/dealer.js";         // the table of cards: the dealer's lane in the column (goal 170 D)
import { ProjectLine, useProjectNow } from "./projectdeal.js";

const CROWN = { race: "peon", tier: "crown" };                   // the Orkmaster's head

/** The Orkmaster's tab: the column's head, its first line the project's name, its second the project's kind and stage (projectdeal.js; spec 161 J). *The Orkmaster* is in its `aria-label` and `title` only. Open at first; pressed again, it asks the Orkmaster (the bubble, ask.js). The project's ▾ beside it (*Switch project*). */
function Top({ parties, all }) {
  const open = openTabOf(tab.value, all) === ORKMASTER, name = currentProject.value?.name || "The project", ask = desk() && all.length > 0;
  const from = { title: mapName(openTabOf(tab.value, all), all), key: "" }, now = useProjectNow(currentProject.value?.path || "");
  const press = () => { if (!open) openTab(ORKMASTER); else if (ask) (askOpen.value === "" ? closeAsk() : openAsk(ORKMASTER)); };
  const keys = (e) => {
    if (e.key !== "ArrowRight" && e.key !== "End") return;
    const first = parties[0]?.slug;
    if (!first) return;
    e.preventDefault();
    openTab(first);
    requestAnimationFrame(() => document.getElementById(`tab-${first}`)?.focus());
  };
  return html`<div class="col-head" role="tablist" aria-label="The Orkmaster" data-race="orkmaster" onKeyDown=${keys}>
    <span class=${cls("ork-pennant small", { "is-open": open })} data-party="orkmaster" aria-hidden="true"></span>
    <button type="button" class=${cls("ork-tab col-head__tab", { "is-open": open })} role="tab" id=${`tab-${ORKMASTER}`} data-tab=${ORKMASTER} data-ask-head=${open && ask ? ORKMASTER : undefined} aria-selected=${String(open)} aria-controls="table-pane"
      aria-haspopup=${ask ? "dialog" : undefined} aria-expanded=${ask && open ? String(askOpen.value === "") : undefined} aria-label=${`The Orkmaster · ${name}`}
      title=${open && ask ? `The Orkmaster: who does what. Press again to ask it (${name})` : `The Orkmaster: who does what (${name})`} onClick=${press}>
      <${Head} race=${CROWN.race} tier=${CROWN.tier} mood=${moodOf(null)} /><span class="col-head__nm" title=${name}>${name}</span>
    </button>
    <${ProjectLine} now=${now} />
    ${currentProject.value && html`<button type="button" class="ork-btn quiet table-switch col-head__switch" aria-label="Switch project" title="Switch project" onClick=${() => openOver("projects", {}, from, "Projects")}><${Icon} name="chevron-down" /></button>`}
  </div>`;
}

export function Column() {
  const root = useRef(), parties = partiesNow(), all = partiesAll(), laid = laidNow();
  useEffect(() => {                                                                                          // a press on an empty place of the column puts the pick away
    const away = (e) => { if (picked.value && e.target.matches?.(".col, .col-scroll")) pick(picked.value); };
    const host = root.current;
    host?.addEventListener("click", away);
    return () => host?.removeEventListener("click", away);
  }, []);
  return html`<div class="col" ref=${root} data-col="1">
    <${Top} parties=${parties} all=${all} />
    <${SetupBubble} />
    ${laid && html`<div class="col-scroll"><${CardsColumn} /></div>`}
    <${Passing} />
  </div>`;
}
