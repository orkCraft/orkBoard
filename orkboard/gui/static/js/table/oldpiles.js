// The Orkmaster's piles as the phone's menu draws them (docs/specs/147-one-card-four-corners.md B, decisions §251.3): *In analysis*, *To review*, *At work · later*. The wide window's column lies its goals by stage (stages.js, spec 168 B1);
// the phone and the window under 760 px are not changed by it, so the menu's sheet (hand/uppiles.js) keeps this classification and these titles. Pure.
import { ACTIVE, lookAt } from "./stages.js";

const ANALYSIS = ["raw", "reading", "asks", "routed", "talk", "decided", "sketch", "sections"];
const SPEC_MADE = ["ready", "planning", "plan"];
const WORKING = ["working", "failed"];
const PAST_WAITING = ["running", "testing", "picking", "review", "failed"];

export const PILES_OLD = [["analysis", "In analysis"], ["review", "To review"], ["work", "At work · later"]];

/** Where a goal lies in the phone's piles: `{pile, off}` (see the header), null for a goal they do not hold. */
export function kindOfOld(n) {
  const s = n.state, ripe = n.back?.ripe || null;
  if (s === "done" || n.folded) return null;
  if (s === "decided") return ripe?.held ? { pile: "work", off: "held" } : { pile: "analysis", off: "" };
  if (n.start_at === "night" || n.waits?.kind === "night") return { pile: "work", off: "night" };
  if (WORKING.includes(s) || (n.tasks || []).some((t) => PAST_WAITING.includes(t.state))) return { pile: "work", off: "" };
  if (SPEC_MADE.includes(s)) return s === "planning" && !n.agreed ? { pile: "analysis", off: "" } : { pile: "review", off: "" };
  if (ANALYSIS.includes(s)) return { pile: "analysis", off: "" };
  return null;
}

/** The phone's three piles in their order: `{analysis, review, work}`, each a list of `{n, off}`. */
export function pilesOfOld(nodes) {
  const out = { analysis: [], review: [], work: [] };
  (nodes || []).forEach((n) => { const k = kindOfOld(n); if (k) out[k.pile].push({ n, off: k.off }); });
  out.analysis = out.analysis.map((x, i) => ({ ...x, i })).sort((a, b) => Number(ACTIVE.includes(b.n.state)) - Number(ACTIVE.includes(a.n.state)) || a.i - b.i);
  const left = (x) => (lookAt(x.n) ? Number(x.n.look_until) - Date.now() / 1000 : Number.isFinite(Number(x.n.back?.ripe?.left_s)) && !x.n.back?.ripe?.by ? Number(x.n.back.ripe.left_s) : Infinity);
  out.review = out.review.map((x, i) => ({ ...x, i })).sort((a, b) => left(a) - left(b) || a.i - b.i);
  const rank = { "": 0, held: 1, night: 2 };
  out.work = out.work.map((x, i) => ({ ...x, i })).sort((a, b) => rank[a.off] - rank[b.off] || a.i - b.i);
  return out;
}
