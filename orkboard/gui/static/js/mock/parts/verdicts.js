// The verdicts' part of the mock (goal 170, decisions §298.3): what each leader of a goal's route found, `proposed.verdicts`:
// `{ <goal slug>: [{ leader, checks: [{ kind, text, fix? }] }] }`, kind ok (approved), q (a question), r (a risk), b (a risk that blocks), `fix` what
// fixes a risk. The host does not answer it yet; the checks are derived from the feed's posts about a goal (a concern is a risk with a fix, an ask a
// question) and filled with approvals, every text marked as an example. A bug is looked at by Tech alone, a feature by Product, Tech and Design.
import { EXAMPLE, latest, nodesOf, reply } from "./kit.js";

const SHOWN = new Set(["new", "talk", "spec", "idea", "ready", "running", "testing", "picking", "failed", "review"]);       // the goals the table of cards shows as cards
const OK = {
  tech: ["One reader of the feed, realm/board_feed.py", "No module past 600 lines", "The change has its test", "Nothing imports the other way round"],
  design: ["The card keeps its ratio", "Readable at 390 px", "Only orkUI's tokens", "A new face keeps to the frame"],
  product: ["A person reads one story on both", "It serves the job: see what changed since my last look", "Worth its price", "The owner asked for it"],
  release: ["The gate runs its tests", "Nothing reaches main without the person"],
};
const hash = (s) => [...s].reduce((a, c) => (a * 31 + c.charCodeAt(0)) >>> 0, 7);
const say = (t) => t + EXAMPLE;

/** The leaders that look at a goal: a bug Tech alone, else its own party, its route's and Product, Tech and Design, three at most. */
function route(n, parties) {
  if (n.type?.sign === "bug") return ["tech"];
  const own = [n.goal, ...(n.route || []).filter((r) => r.step === "party").map((r) => r.party), "product", "tech", "design"];
  return [...new Set(own)].filter((l) => parties.includes(l) && l !== "release").slice(0, 3);
}

export function lay(data) {
  const map = reply(data, "ideas.map")?.result, feed = reply(data, "ideas.feed")?.result;
  if (!map) return;
  const parties = (map.goals || []).map((g) => g.slug), posts = (feed?.posts || []).flatMap((s) => [s.post, ...(s.more || [])]);
  // one goal at work is a bug (Tech alone, marked as an example), so a card of its kind can be seen
  const work = latest(data, "ready", 12), bug = work[3];
  if (bug && !bug.type) { bug.type = { sign: "bug" }; if (!bug.title.endsWith(EXAMPLE)) { bug.title += EXAMPLE; bug.short = (bug.short || bug.title) + EXAMPLE; } }
  const blockedGoal = work[1]?.slug;
  const verdicts = {};
  for (const n of nodesOf(data).filter((x) => SHOWN.has(x.state))) {
    verdicts[n.slug] = route(n, parties).map((leader) => {
      const h = hash(n.slug + leader), checks = [], said = posts.filter((p) => p.goal === n.slug && p.leader === leader);
      const pool = OK[leader] || OK.tech, ok = 1 + (h % 3);
      for (let i = 0; i < ok; i++) checks.push({ kind: "ok", text: say(pool[(h + i) % pool.length]) });
      for (const p of said) {
        if (p.asks) checks.push({ kind: "q", text: say(p.text.replace(/\s*· example$/, "")) });
        else if (p.kind === "concern") checks.push({ kind: "r", text: say(p.text.replace(/\s*· example$/, "")), fix: say("the leader and the Orkmaster settle it before the start") });
      }
      if (!said.length && h % 4 === 0) checks.push({ kind: "q", text: say(`Does ${n.short || n.title} need its own order?`.replace(EXAMPLE, "")) });
      if (!said.length && h % 5 === 1) checks.push({ kind: "r", text: say("Two faces share one sort"), fix: say("each face keeps its order, one reader below") });
      if (n.slug === blockedGoal && leader === "tech") checks.push({ kind: "b", text: say("A change here breaks the phone's cache name"), fix: say("keep the cache name and bump its version") });
      return { leader, checks };
    });
  }
  data.proposed = { ...data.proposed, verdicts };
}
