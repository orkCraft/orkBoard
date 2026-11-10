// A decision's entry, or a goal as it was, read over the pane (docs/specs/134-release-keeps-the-chronicle.md part B, decisions §238.3–§238.4; docs/specs/156-one-pick-and-the-release-column.md D.5, decisions §261.9). The past itself is no longer opened over the
// pane: it lies in the history book (history.js), through the open tab's eyes, and a past goal's card is picked (the table shows it as it was: pastgoal.js). What stays here is the one thing a link needs: **a decision's entry** — its *Changes* and *changed by* as
// links, so its history is walked on (chroniclerows.js `Decision`) — opened from a decision's card in the lane, from a number in the Orkmaster's bubble (asklinks.js) and from the conflict's card (*Open in the past*, hand/conflictcard.js). The pane's ← goes back to the tab's table.
// It decides nothing and writes nothing but the party's last look (pastseen.js); every command it asks reads (`ideas.chronicle*`, gui/ideas_chronicle.py). Not on the phone (§238.6).
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Icon } from "../orkui.js";
import { drawn } from "../frame/kinds.js";
import { openOver, tab } from "../frame/state.js";
import { mapName, partiesAll } from "./data.js";
import { Decision, GoalAsItWas } from "./chroniclerows.js";
import { whose } from "./chronicleparts.js";
import { entryTitle } from "./chroniclewords.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as mapkit.js links its own
  const href = new URL("./chronicle.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** Opens a decision's entry (`{decision}`), or a goal as it was (`{goal}`) over the pane from where it is pressed, through the open tab. */
export function openChronicle(props = {}) {
  openOver("chronicle", props, { title: mapName(tab.value, partiesAll()), key: "" }, entryTitle(whose().name, props));
}

/** The face of kind `chronicle`: a decision's entry or a goal as it was; a press inside walks on and the quiet button above walks back to where it began; the pane's ← leaves for the tab's table. */
export function Chronicle({ props }) {
  const w = whose(), [stack, setStack] = useState([props?.goal ? { goal: props.goal } : { decision: props?.decision || props?.lit }]);
  const view = stack.at(-1);
  const goal = (idea) => setStack((s) => [...s, { goal: idea }]), decision = (number) => setStack((s) => [...s, { decision: number }]);
  return html`<div class="table-over__chronicle" data-view=${view.goal ? "goal" : "decision"} data-party=${w.party || undefined}>
    ${stack.length > 1 && html`<p class="chr-back"><button type="button" class="ork-btn quiet" onClick=${() => setStack((s) => s.slice(0, -1))}><${Icon} name="arrow-left" /> Back</button></p>`}
    ${view.goal ? html`<${GoalAsItWas} key=${view.goal} idea=${view.goal} onDecision=${decision} show=${null} />`
      : html`<${Decision} key=${view.decision} number=${view.decision} onDecision=${decision} onGoal=${goal} show=${null} />`}
  </div>`;
}

drawn("chronicle", Chronicle);
