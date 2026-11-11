// The spreads' part of the mock (goal 170): what the spreads read that the host does not answer yet, the contract proposed
// (docs/mockups/spreads/). `proposed.costs`: the tools' share left today and each goal's cost before it is played, by slug (an estimate,
// `mark` says so in what a person reads); `proposed.order`: the goals already in line, the order the duel sets new ones into. The
// recording has no new goal, so four are laid, each marked as an example, for the sort and the duel to work on.
import { EXAMPLE, latest, nodesOf, reply } from "./kit.js";

const NEW = [
  ["The timer stops at a round's end", "lava", "bug", "tech", "a play test"], ["Coins in the sky", "ice", "balance", "design", "a play test"],
  ["Store page", "dust", "store", "product", "its first page"], ["A glint on every coin", "meadow", "picture", "design", "a play test"],
];

export function lay(data) {
  const map = reply(data, "ideas.map")?.result;
  if (!map) return;
  const top = Math.max(...nodesOf(data).map((n) => parseInt(n.slug, 10) || 0));
  const fresh = NEW.map(([title, element, sign, goal, origin], i) => ({ slug: `${top + 1 + i}-example-${i + 1}`, goal, title: title + EXAMPLE, short: title + EXAMPLE, state: "new", queue: "", agreed: false,
    element, hue: element, flag: null, type: { sign }, route: [], decided: [], origin: origin + EXAMPLE }));
  map.nodes = [...map.nodes, ...fresh];
  const deck = nodesOf(data).filter((n) => ["new", "talk", "spec", "idea"].includes(n.state)).map((n) => n.slug);
  const share = [[12, "claude"], [6, "claude"], [25, "codex"], [4, "claude"]];
  data.proposed = {
    ...data.proposed,
    costs: { mark: EXAMPLE, reset: "04:00", tools: [{ id: "claude", name: "Claude", left: 0.62 }, { id: "codex", name: "Codex", left: 0.18 }],
      goals: Object.fromEntries(deck.slice(0, 4).map((slug, i) => [slug, { pct: share[i][0], tool: share[i][1], ...(share[i][1] === "codex" ? { alt: { tool: "claude", pct: 11 } } : {}) }])) },
    order: { ranked: latest(data, "ready", 3).map((n) => n.slug) },
  };
}
