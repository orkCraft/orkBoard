// A goal of the past, picked, shown as it was (docs/specs/156-one-pick-and-the-release-column.md D.5, decisions §261.9): a card of a version's deck in Release's lane is picked like any card (part B), and the snapshot has no node for a goal that went through the
// portal long ago, so the table draws what the host kept of it (`ideas.chronicle_goal`: its spec as built, its decision, its quality record, *How it works now*: chroniclerows.js `GoalAsItWas`), the same page whatever tab is open. A decision named in it opens its entry over the pane.
import { html } from "../html.js";
import { GoalAsItWas } from "./chroniclerows.js";
import { openChronicle } from "./chronicle.js";

export function PastGoal({ idea }) {
  return html`<div class="table-over__chronicle table-pastgoal" data-past-goal=${idea}><${GoalAsItWas} key=${idea} idea=${idea} onDecision=${(number) => openChronicle({ decision: number })} show=${null} /></div>`;
}
