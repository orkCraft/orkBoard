// Where a goal lies in the Orkmaster's column (docs/specs/168-the-window-played-as-a-card-games-table.md B1, decisions §283.11–§283.12; before: decisions §224, §247.2, §251.3): the piles are the goal's stages —
// **Ideas** (the Orkmaster reads and routes it, Talk, an agreed decision's wait), **Specs** (its sections being written, the plan, the look's wait), **Implementation** (at work) — and a goal lies where what happens to it next:
// held or put off to a later hour *before Talk* at the end of Ideas' fan with a pause or a moon on its back; held *after its spec*, or waiting for the night's build, at the foot of Implementation's cascade; held *at work* in the cascade with a pause.
// A failure stays in its stage's pile (the danger's ring). The pile ids keep their names in the code (`analysis` = Ideas, `review` = Specs, `work` = Implementation). Pure: a node in, its place out.
import { board } from "../board/store.js";

export const READING = "reading", WRITING = "writing", AT_WORK = "at work", NEXT_IN = "next in", NEXT_AT = "next at";          // the words under a pile's title (realm/lexicon.py column_*)

export const IDEAS = ["raw", "reading", "asks", "routed", "talk", "decided"];                  // the idea, Talk and the decision: Ideas (an agreed decision's wait too: `decided`)
export const SPECS = ["sketch", "sections", "planning", "ready", "plan"];                      // the sections being written, the plan, the spec made and its wait: Specs
const WORKING = ["working", "failed"];
const PAST_WAITING = ["running", "testing", "picking", "review", "failed"];                   // a task past waiting: its goal is at work
export const ACTIVE = ["reading", "planning", "talk", "sketch", "sections"];                  // the Orkmaster or its leaders are on it: its ring runs
export const DECK_SHOWN = 5, WORK_SHOWN = 6, DECK_STEP = 3;                                   // the cards drawn of the deck (the front and four behind) and of Implementation (the front and five behind); the rest wait their turn, never counted

export const PILES = [["analysis", "Ideas"], ["review", "Specs"], ["work", "Implementation"]];

/** A spec being written now (sections, its sketch, the Orkmaster's own draft that no decision has confirmed): its card's ring fills as it is written, not as a wait runs down. */
export const writing = (n) => n.state === "sketch" || n.state === "sections" || (n.state === "planning" && !n.agreed);
export const failed = (n) => n.state === "failed" || (n.tasks || []).some((t) => t.state === "failed");
const heldFor = (n) => n.held_for === "hold";
const laterAt = (n) => !n.held_for && Date.parse(n.held_until || "") > Date.now();

/** Where a goal lies in the column: `{pile, off, mark}`; `pile` "analysis" | "review" | "work", `off` "" | "held" | "night" (put off: at the cascade's foot after the ones at work), `mark` "" | "hold" | "later" (a pause, or a moon, on its card: before Talk at the fan's end,
 *  at work in the cascade). null for a goal the column does not hold (done, a pitch, one folded away). */
export function kindOf(n) {
  const s = n.state, ripe = n.back?.ripe || null, hold = heldFor(n), later = laterAt(n);
  if (s === "done" || n.folded) return null;
  if (s === "decided") return ripe?.held ? { pile: "work", off: "held", mark: "" } : { pile: "analysis", off: "", mark: hold ? "hold" : "" };      // the decision worded waits for the person's word; held (put off until the person starts it): the cascade's foot
  if (n.start_at === "night" || n.waits?.kind === "night") return { pile: "work", off: "night", mark: "" };                                           // waiting for the night's build
  if (WORKING.includes(s) || (n.tasks || []).some((t) => PAST_WAITING.includes(t.state))) return { pile: "work", off: "", mark: hold || later ? "hold" : "" };
  if (SPECS.includes(s)) return hold || ripe?.held ? { pile: "work", off: "held", mark: "" } : { pile: "review", off: "", mark: "" };              // held after its spec: the cascade's foot, as put off
  if (IDEAS.includes(s)) return { pile: "analysis", off: "", mark: hold ? "hold" : later ? "later" : "" };
  return null;
}

/** The clock time a spec made starts by itself at (spec 144 B.2; the look's wait, `look_until` in the future): *13:40*, with the weekday when it is not today's; "" for a card with no look running. Never a countdown. */
export function lookAt(n) {
  if (!(Number(n?.look_until) > Date.now() / 1000)) return "";
  const d = new Date(Number(n.look_until) * 1000), hm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return d.toDateString() === new Date().toDateString() ? hm : `${d.toLocaleDateString("en-GB", { weekday: "short" })} ${hm}`;
}

export const night = () => String(board.value?.night || "01:00-07:00").split("-")[0];
export const clock = (left_s) => { const d = new Date(Date.now() + Math.max(0, Number(left_s) || 0) * 1000); return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; };

/** The three piles in their order: `{analysis, review, work}`, each a list of `{n, off, mark}`. Ideas: the goal being worked on first, the others in the Orkmaster's order, the ones held or put off to a later hour last; Specs: the sections being written first, then by the time left of the wait
 *  (the one that starts first in front); Implementation: the ones at work, then held after their spec, then the night's. */
export function pilesOf(nodes) {
  const out = { analysis: [], review: [], work: [] };
  (nodes || []).forEach((n) => { const k = kindOf(n); if (k) out[k.pile].push({ n, off: k.off, mark: k.mark }); });
  const at = (x) => (ACTIVE.includes(x.n.state) ? 0 : 1);
  out.analysis = out.analysis.map((x, i) => ({ ...x, i })).sort((a, b) => Number(!!a.mark) - Number(!!b.mark) || at(a) - at(b) || a.i - b.i);
  const left = (x) => (lookAt(x.n) ? Number(x.n.look_until) - Date.now() / 1000 : Number.isFinite(Number(x.n.back?.ripe?.left_s)) && !x.n.back?.ripe?.by ? Number(x.n.back.ripe.left_s) : Infinity);
  out.review = out.review.map((x, i) => ({ ...x, i })).sort((a, b) => Number(writing(b.n)) - Number(writing(a.n)) || left(a) - left(b) || a.i - b.i);
  const rank = { "": 0, held: 1, night: 2 };
  out.work = out.work.map((x, i) => ({ ...x, i })).sort((a, b) => rank[a.off] - rank[b.off] || a.i - b.i);
  return out;
}
