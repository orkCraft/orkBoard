// A card's turns, a battle and the dropped pile on the mock (goal 170, decisions §298.6–§298.8). The host does not answer them yet: the contract proposed.
//   `proposed.turns`:   [{ goal: <slug>, kind: "rated" | "spec_rated" | "battle", at }], the cards the hand gets at their turns.
//   `proposed.battles`: { <slug>: { against: [{ kind: "goal" | "decision", ref, title, state?, undo: { pct, tool, what } }] } }, a new card against old ones.
//   `proposed.dropped`: [<slug>…], the goals dropped, the discard's third pile; `proposed.dropped_goals`: { <slug>: <node> } for those the Board no longer lists.
// A decision's verdicts lie in `proposed.verdicts` under its ref (*§240*), as a goal's under its slug. Every text a person reads is marked as an example.
import { EXAMPLE, latest, nodesOf } from "./kit.js";

const hash = (s) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
const OK = ["Nothing imports the other way round", "The change has its test", "It serves the job", "Readable at 390 px", "Only orkUI's tokens", "The owner asked for it"];

/** A verdict for a goal or decision the verdicts' part did not lay: `leaders` each with one to three approvals, a question for the first when `ask`. */
function verdictOf(key, leaders, ask = false) {
  return leaders.map((leader, i) => {
    const h = hash(key + leader), checks = Array.from({ length: 1 + (h % 3) }, (_, k) => ({ kind: "ok", text: OK[(h + k) % OK.length] + EXAMPLE }));
    if (ask && i === 0) checks.push({ kind: "q", text: "Is its order its own?" + EXAMPLE });
    return { leader, checks };
  });
}

export function lay(data) {
  const verdicts = data.proposed?.verdicts;
  if (!verdicts) return;
  const nodes = nodesOf(data), now = Date.now(), ago = (min) => new Date(now - min * 60000).toISOString();
  const talk = nodes.filter((n) => n.state === "talk"), fresh = nodes.find((n) => n.state === "new" && n.slug.includes("-example-"));
  const rated = talk.find((n) => n.goal === "tech") || talk[0], fight = talk.find((n) => n !== rated) || talk[0];
  // the rated goal's Tech has a risk that blocks: its start waits until Tech lifts it
  if (rated) {
    const own = verdicts[rated.slug] || (verdicts[rated.slug] = []), tech = own.find((v) => v.leader === "tech") || (own.push({ leader: "tech", checks: [] }), own[own.length - 1]);
    if (!tech.checks.some((c) => c.kind === "b")) tech.checks.push({ kind: "b", text: "Two feeds share one reader: a phone's own order breaks" + EXAMPLE, fix: "a phone keeps its order apart, one reader below" + EXAMPLE });
  }
  const turns = [];
  if (rated) turns.push({ goal: rated.slug, kind: "rated", at: ago(9) });
  if (fresh) turns.push({ goal: fresh.slug, kind: "spec_rated", at: ago(21) });
  // a battle: the goal in talk against a decision (a card of its own, its § its number) and a goal done
  const old = latest(data, "done", 5)[4], battles = {};
  if (fight) {
    verdicts["§240"] = verdictOf("§240", ["product", "tech", "design"]);
    if (old) verdicts[old.slug] = verdictOf(old.slug, ["product", "tech", "design"], true);
    battles[fight.slug] = { against: [
      { kind: "decision", ref: "§240", title: "The hand is the person's move only", state: "decided", undo: { pct: 20, tool: "Claude", what: "2 modules, 6 tests change" + EXAMPLE } },
      ...(old ? [{ kind: "goal", ref: old.slug, title: old.short || old.title, state: "done", undo: { pct: 12, tool: "Claude", what: "1 module, 3 tests change" + EXAMPLE } }] : []),
    ] };
    turns.push({ goal: fight.slug, kind: "battle", at: ago(34) });
  }
  // the dropped pile: two goals the Board no longer lists, their last tokens kept
  const lost = [["Coins fall from the left", "ice", "design"], ["A second timer for bugs", "lava", "tech"]].map(([title, element, goal], i) => ({
    slug: `${900 + i}-dropped-example-${i + 1}`, goal, title: title + EXAMPLE, short: title + EXAMPLE, state: "new", element, hue: element, type: { sign: i ? "bug" : "balance" }, route: [], decided: [] }));
  for (const n of lost) verdicts[n.slug] = verdictOf(n.slug, [n.goal, "product"], true);
  data.proposed = { ...data.proposed, turns, battles, dropped: lost.map((n) => n.slug), dropped_goals: Object.fromEntries(lost.map((n) => [n.slug, n])) };
}
