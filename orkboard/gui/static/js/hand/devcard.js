// A goal and its own branch, as the hand and the discard read it (docs/specs/168 F2, decisions §283.26–§283.27; the host's core/idea_goal_dev.py, realm/goal_branch.py): the Board's row of a goal (`ideas.board`) says `goal_branch`, `waits_for_dev` (done on its branch, not in dev
// yet), `dev_why` (why it waits), `dev_blocked` (something stopped it before dev: a conflict, a red gate, no test that ran) and `dev_kind` ("conflict" · "red" · "no_tests" · "env" · "other"). The discard's lower pile is the goals that wait (table/plates.js, drawn while *Lands in dev by itself*
// is off); **a goal blocked before dev is never silent, whatever the setting**: it is a card in the hand, in the stack of its party's lane (`devStops`), *<Goal> cannot go into dev* with its why at the foot, and the ways *Try again* and, when no test ran, *To dev without the tests*
// (devplay.js). Wide only, as the concern card. Kept apart from the drawing so the hand's data (data.js) does not import it.
import { board } from "../board/store.js";
import { gateData } from "../shell/store.js";
import { ORKMASTER } from "../frame/state.js";

export const TO_DEV = "To dev", TO_DEV_UNTESTED = "To dev without the tests", TRY_AGAIN = "Try again";
export const CANNOT = "cannot go into";                          // the lexicon's `dev_blocked`: *Lobby cannot go into dev*

/** The Board's row of a goal (its branch's words), null for a goal the Board does not list. */
export const devRow = (slug) => (board.value?.ideas || []).find((r) => r.slug === slug) || null;
/** Whether the goal is done on its own branch and waits for dev. */
export const waitsForDev = (slug) => !!devRow(slug)?.waits_for_dev;
/** The project's work branch (where goals land): *dev* by default. */
export const devName = () => gateData.value?.into || board.value?.into || "dev";
/** Whether *Lands in dev by itself* is off (the setting `review`): the lower pile is drawn then, and goals wait on their branch for the person. */
export const lowerOn = () => board.value?.review === true;

/** The hand's stops of the goals blocked before dev, one a goal, under the lane of its party, after the other stops. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `goal(slug)`, `open`). */
export function devStops(map, ctx) {
  const out = [], dev = devName();
  for (const r of board.value?.ideas || []) {
    if (!r.dev_blocked || !r.waits_for_dev) continue;
    const n = (map?.nodes || []).find((x) => x.slug === r.slug), party = n && ctx.party(n.goal), g = n && ctx.goal(n.goal);
    if (!n || !party || !g) continue;
    const title = `${n.short || n.title} ${CANNOT} ${dev}`;
    out.push({ key: `dev/${r.slug}`, kind: "dev_blocked", ref: { idea: r.slug, why: r.dev_why || "", dev_kind: r.dev_kind || "other", dev }, row: { goal: n.goal, idea: r.slug, kind: "dev_blocked", blocks: true }, node: n, task: null,
      label: "Blocked", gem: "", tone: "alert", gemTip: "", head: party.head, small: true, whoTip: "", title, full: title, text: r.dev_why || "", why: r.dev_why || "", g, party, other: ctx.open !== ORKMASTER && ctx.open !== n.goal });
  }
  return out;
}
