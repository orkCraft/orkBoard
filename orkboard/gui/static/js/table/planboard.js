// The Orkmaster's tab with a goal picked (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.1, decisions §206.4): the Board shows **that goal's plan alone**, its tasks in their leaders' lanes (the party a task is the work of: the snapshot's task
// `party`, else the goal's own), every other goal's out of sight; **planned ones faint, done ones grey, the one at work glowing** (the task card's own flame), and **arrows** from each task to the tasks that wait for it (planarrows.js). The tasks lie in
// each lane in the order the plan runs them (the wave they wait in, then as written). A goal with no plan yet says *Its tasks are dealt to the leaders when it is agreed* in the lanes' place. Only with the column pinned (the wide width): the narrow
// width keeps the Board as it is. Nothing here changes a task: a press lifts it (card.js), as on the Board.
import { useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { isLive, nameOf, partiesNow, wide } from "./data.js";
import { TaskCard } from "./card.js";
import { PlanArrows } from "./planarrows.js";

export const NONE_YET = "Its tasks are dealt to the leaders when it is agreed";

/** How far a task of the plan is: *done* (merged), *work* (started and not merged, or asking), else *planned* (it waits for its turn). */
export const planPhase = (t) => (t.state === "merged" ? "done" : ["running", "testing", "review", "picking", "failed"].includes(t.state) ? "work" : "planned");

/** The lane a task stands in: its party's when that party has one (Release and Live have none at the wide width), else the goal's own, else the first. */
function laneOf(n, t, lanes) {
  const has = (slug) => lanes.some((g) => g.slug === slug);
  return has(t.party) ? t.party : has(n.goal) ? n.goal : lanes[0]?.slug || "";
}

/** The goal `n`'s plan over the lanes. */
export function PlanBoard({ n }) {
  const host = useRef(), lanes = partiesNow(), tasks = (n.tasks || []).filter((t) => t.state !== "dropped");
  const order = [...tasks].map((t, i) => ({ t, i })).sort((a, b) => (a.t.wave || 1) - (b.t.wave || 1) || a.i - b.i).map(({ t }) => t);
  const mine = (g) => order.filter((t) => laneOf(n, t, lanes) === g.slug);
  return html`<div class="table-board table-board--plan" ref=${host} data-picked=${n.slug} data-plan=${n.slug} data-tokens="false">
    ${lanes.map((g) => html`<div key=${g.slug} class="table-lane" data-party=${g.slug} data-live=${wide.value && isLive(g) ? "1" : undefined} role="group" aria-label=${nameOf(g)}>
      ${mine(g).map((t) => html`<div key=${t.id} class=${cls("plan-slot", `is-${planPhase(t)}`)} data-plan-task=${t.id} data-phase=${planPhase(t)}><${TaskCard} n=${n} t=${t} /></div>`)}
      ${tasks.length > 0 && mine(g).length === 0 && html`<p class="table-board__none plan-none" data-none=${g.slug}>Nothing for ${nameOf(g)}</p>`}
    </div>`)}
    <div class="table-lane table-lane--free"></div>
    ${tasks.length === 0 && html`<p class="table-board__none plan-wait" data-state=${n.state}>${NONE_YET}</p>`}
    ${tasks.length > 0 && html`<${PlanArrows} host=${host} tasks=${order} />`}
  </div>`;
}
