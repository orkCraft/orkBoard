// What the table reads (docs/specs/98-the-table-and-the-hand.md §3, §5): pure functions over the page's own stores — `ideas.map`
// (the parties and their goals, the code's goals and ideas), `ideas.agents` and `ideas.roles` (the seats), the snapshot's limits —
// and the words the table says. No template here. The table draws a party's name, never "goal" or "track" (CLAUDE.md, Wording).
import { mapData, agents, roles } from "../shell/store.js";
import { goalList } from "../board/store.js";
import { goalsOf, nodesOf, atWork, openTasks, partyOf, roleOf, RANK } from "../arena/arenawords.js";
import { ORKMASTER } from "../frame/state.js";
import { ORKUI } from "../orkui.js";
import { TARGETS } from "../board/target.js";
import { command, toast } from "../link.js";

export const GENERAL = "general";                       // the system's party: it has no tab of its own
export const WHOLE = "The whole project";
export const LIVE = ["running", "testing", "picking", "failed"];       // a task a column's card shows: at work, asking, or failed
const SIZE_WORD = { lean: "Lean", standard: "Standard", full: "Full" };
const SIZE_TARGET = { lean: "thrift", standard: "balance", full: "quality" };

/** The project's parties in the Board's order, General left out. */
export const partiesNow = () => goalsOf(mapData.value, goalList().map((x) => x.slug)).filter((g) => g.slug !== GENERAL);

export const nameOf = (g) => g?.short || g?.title || "";
export const nodesFor = (g) => nodesOf(mapData.value, g.slug);

/** The tab that is open: the person's (state.js `tab`), else the Orkmaster's when that party is gone. */
export const openTabOf = (tab, parties) => (tab !== ORKMASTER && parties.some((g) => g.slug === tab) ? tab : ORKMASTER);

/** *through the Orkmaster* / *through Tech*. */
export const throughWords = (tab, parties) => `through ${tab === ORKMASTER ? "the Orkmaster" : nameOf(parties.find((g) => g.slug === tab)) || tab}`;

/** What is looked at: the picked goal's name, else the whole project. */
export function lookedAt(picked) {
  if (!picked) return WHOLE;
  const n = (mapData.value?.nodes || []).find((x) => x.slug === picked);
  return n?.short || n?.title || WHOLE;
}

/** The title of the pane: *The whole project · through the Orkmaster*. */
export const paneTitle = (picked, tab, parties) => `${lookedAt(picked)} · ${throughWords(tab, parties)}`;

/** The name of the map a tab shows, where a thing opened over it says it came from (*← System · server/lobby.ts*). */
export function mapName(tab, parties) {
  if (tab === ORKMASTER) return "Board";
  const g = parties.find((x) => x.slug === tab);
  return g && leadsSystem(g) ? "System" : nameOf(g) || tab;
}

/** Tech's map is the System: the party the Architect leads (systemmap.js `leadsSystem`). */
export const leadsSystem = (g) => (g?.leader?.slug || "") === "architect";

/** The parties a picked goal's route passes (`ideas.map` nodes' `route` steps), for the dot on their tabs: its own party always. */
export function routeParties(picked) {
  const n = picked && (mapData.value?.nodes || []).find((x) => x.slug === picked);
  if (!n) return new Set();
  const out = new Set([n.goal]);
  for (const s of n.route || []) { if (s.party) out.add(s.party); if (s.from) out.add(s.from); }
  return out;
}

/** The tasks of a party that the Board shows as its column's cards: at work, asking or failed, the one nearest its member first. [{n, t}] */
export function cardsOf(g, only = "") {
  const out = [];
  nodesFor(g).filter((n) => atWork(n) && (!only || n.slug === only)).forEach((n, i) => openTasks(n).forEach((t, j) => {
    if (LIVE.includes(t.state)) out.push({ n, t, at: i * 1000 + j });
  }));
  return out.sort((a, b) => (RANK[a.t.state] ?? 9) - (RANK[b.t.state] ?? 9) || a.at - b.at);
}

/** The goals the Orkmaster does itself: read or being routed (`reading`, `planning`), in the Board's order. [{n, g}] */
export function ownOf(parties, only = "") {
  const out = [];
  for (const g of parties) for (const n of nodesFor(g)) if ((n.state === "reading" || n.state === "planning") && (!only || n.slug === only)) out.push({ n, g });
  return out;
}

/** What the Orkmaster does with a goal, in a word. */
export const doingWords = (n) => (n.state === "reading" ? "Reading" : "Routing");

/** A card's foot caption for a task. */
export function footWords(t) {
  return { running: "Doing", testing: "Testing", picking: "Asks you to pick", failed: t.band === "check" ? "Check failed" : "Failed" }[t.state] || t.state;
}

// -- a party's seats ---------------------------------------------------------------------------------------------------------------

/** The seats of a party in three groups, *Leads* | *Does* | *Checks* (at most seven in all): [{band, word, seats: [member]}]. */
export function groupsOf(g) {
  const { lead, members } = partyOf(g, nodesFor(g));
  const take = (band) => members.filter((m) => m.band === band);
  const groups = [["lead", "Leads", lead ? [lead] : []], ["build", "Does", take("build")], ["check", "Checks", take("check")]];
  let left = 7;
  return groups.map(([band, word, seats]) => { const kept = seats.slice(0, Math.max(0, left)); left -= kept.length; return { band, word, seats: kept }; }).filter((x) => x.seats.length);
}

/** The AI tool a seat runs on: the seat's own, the party's, else the role's (the Main tool). {id, name} */
export function toolOf(g, m) {
  const role = roleOf(agents.value, m.slug), id = g.tools?.[m.slug] || g.tool || role?.harness?.id || "claude";
  return { id, name: role?.harness && role.harness.id === id ? role.harness.name : id.charAt(0).toUpperCase() + id.slice(1) };
}

/** The ink mark of a tool (orkUI marks/): known tools only. */
export const MARKED = ["claude", "codex", "agy", "cursor", "hermes", "pi"];
export const markSrc = (id, x2 = false) => `${ORKUI}/marks/harness-${id}-ink${x2 ? "@2x" : ""}.png`;

/** A party's size in one word, and what it works as. */
export const sizeWord = (g) => SIZE_WORD[g.size] || "";
export function sizeTip(g) {
  const [, word, line] = TARGETS.find(([id]) => id === SIZE_TARGET[g.size]) || [];
  return word ? `${sizeWord(g)}: works as ${word}, ${line}` : sizeWord(g);
}

/** The library's line for a seat (what the role does), else its task kinds, else what a leader does. */
export function doesWords(m, lead) {
  if (lead) return "plans the party's goals";
  const lib = (roles.value?.library || []).find((a) => a.id === m.slug);
  const role = roleOf(agents.value, m.slug);
  return lib?.line || (role?.kinds || []).join(", ") || (m.band === "check" ? "checks before it lands" : "does the work");
}

/** A task as the host tells it (`ideas.task`): it carries its own `error` (its failure), so a refusal is the answer that has only that. `quiet`: no toast. */
export async function readTask(slug, task, quiet = false) {
  try {
    const got = await command("ideas.task", { slug, task }, true);
    if (got?.error && !got.id) { if (!quiet) toast(got.error, "error"); return null; }
    return got || {};
  } catch (e) { if (!quiet && !e.refused) toast(e.message, "error"); return null; }
}
