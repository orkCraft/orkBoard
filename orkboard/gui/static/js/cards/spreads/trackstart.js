// *Start the work* on a goal's mat when its spec is all written (goal 171 stage K; decisions §298.7, the person's answer on the seal): it begins paid work that cannot be undone, so it lies on the mat's seal
// (cards/matframe.js `Seal`), never as a one-press way: dim with its why until the host's `ideas.start` can be answered, its cost said before the press as far as the host gives it (the goal's plan estimate),
// else *cost not known yet* as the cost mat says it. Pressed it sends `ideas.start {slug, from: "mat", sealed: true}`; the host refuses in plain words what is not ready (no plan yet), and the mat stays.
// A goal waits for its start when `ideas.turns` names it `spec` (hand/turnstops.js). No *Change the spec*: no host command changes a spec in its turn.
import { html } from "../../html.js";
import { costOf } from "../../hand/cost.js";
import { settle, turns } from "../../hand/turnstops.js";
import { Seal } from "../matframe.js";
import { playMove } from "../played.js";
import { closeSpread } from "./open.js";

/** Whether the host says this goal's spec is all written and waits for its start. */
export const specWaits = (slug) => (turns.value?.turns || []).some((t) => t.goal === slug && t.kind === "spec");

/** What starting costs, said before the press: the plan's estimate as a card says it, else *cost not known yet*. */
export const startCost = (n) => costOf({ kind: "plan", node: n })?.words || "cost not known yet";

/** The seal for a goal whose spec waits; null otherwise. */
export function startSeal(slug, n, title) {
  if (!specWaits(slug)) return null;
  const go = () => playMove("ideas.start", { slug }, { from: "mat", goal: slug, sealed: true, said: `Started: ${title}. The work has begun.`, done: () => { settle(slug, "*"); closeSpread(); } });
  return html`<${Seal} word="Start the work" why=${`It cannot be undone · ${startCost(n)}`} lit=${true} kind="start" onPress=${go} />`;
}
