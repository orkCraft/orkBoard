// What the table reads (docs/specs/98-the-table-and-the-hand.md §3, §5): pure functions over the page's own stores — `ideas.map`
// (the parties and their goals, the code's goals and ideas), `ideas.agents` and `ideas.roles` (the seats), the snapshot's limits —
// and the words the table says. No template here. The table draws a party's name, never "goal" or "track" (CLAUDE.md, Wording).
import { signal } from "@preact/signals";
import { mapData, agents, roles, gateData } from "../shell/store.js";
import { board, goalList, hhmm } from "../board/store.js";
import { goalsOf, nodesOf, atWork, openTasks, partyOf, roleOf } from "../arena/arenawords.js";
import { ORKMASTER } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { ORKUI } from "../orkui.js";
import { TARGETS } from "../board/target.js";
import { command, toast } from "../link.js";
import { pctShort, rated } from "../spend.js";
import { setPostWorld } from "./post.js";

export const GENERAL = "general";                       // the system's party: it has no tab of its own
export const WHOLE = "The whole project";
export const LIVE = ["running", "testing", "picking", "failed"];       // a task a column's card shows: at work, asking, or failed
const SIZE_WORD = { lean: "Lean", standard: "Standard", full: "Full" };
const SIZE_TARGET = { lean: "thrift", standard: "balance", full: "quality" };

// -- the parties, and the road's two out of the tabs at the wide width (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4.1, decisions §188.1) --------------------------

const WIDE = typeof matchMedia === "function" ? matchMedia("(min-width: 760px)") : null;
/** Whether the window is at the wide width (760 px and up), where Release and Live wait in the portal ring's corners; the narrow width keeps them as tabs. */
export const wide = signal(WIDE ? WIDE.matches : true);
WIDE?.addEventListener?.("change", () => { wide.value = WIDE.matches; });

/** Whether the Orkmaster's column is pinned at the window's left (spec 128 B.1): the wide width, and not a phone held on its side or upright. Under it the Orkmaster's tab and first lane stay as the phone has them. */
export const columnOn = () => wide.value && !uprightNow.value;

/** Every party of the project in the Board's order, General left out: what everything that looks a party up by its slug needs (a map's name, a question's party, the open tab). */
export const partiesAll = () => goalsOf(mapData.value, goalList().map((x) => x.slug)).filter((g) => g.slug !== GENERAL);
setPostWorld({ parties: partiesAll, nodes: () => mapData.value?.nodes || [], orkmaster: () => mapData.value?.project?.orkmaster || null });      // table/post.js asks the Board through these and imports none of it

const LIVE_CRAFTS = ["run", "liveops"];
/** Whether a decided goal's wait runs (spec 120 §3.5: the leaders agreed, not held, not yet ended): it goes on by itself, so its decision asks nothing of the person (decisions §240). */
export const waitRuns = (n) => n?.state === "decided" && !!n.back?.ripe && !n.back.ripe.held && !n.back.ripe.by;

/** The project has no gate: dev and main are one branch, or main does not exist (the gate's own answer, `ideas.gate`'s `same`; docs/specs/113-a-project-with-no-preview-or-no-gate.md §4, decisions §191.2). Unknown before the first answer: a gate. */
export const noGate = () => gateData.value?.same === true;

/** The road's two parties: Release (the party whose craft is `release`, before main) and Live (the first whose craft is `run` or `liveops`, past it); null for one the project does not have. At the wide width they are the row's last two tabs
 *  (Live, then Release: spec 156 D.2, decisions §261.7), in a project with no gate too. */
export function roadParties(all = partiesAll()) {
  return { release: all.find((g) => g.party_craft === "release") || null, live: all.find((g) => LIVE_CRAFTS.includes(g.party_craft)) || null };
}
/** The slugs of the road's parties. */
export const roadSlugs = (all = partiesAll()) => new Set(Object.values(roadParties(all)).filter(Boolean).map((g) => g.slug));

/** Whether a party is Release's (its lane is the discard, outside the Board's lanes at the wide width), or Live's (the last of the Board's lanes, after the tabs' end). */
export const isRelease = (g) => !!g && g.party_craft === "release";
export const isLive = (g) => !!g && LIVE_CRAFTS.includes(g.party_craft) && roadParties().live?.slug === g.slug;

/** The parties of the Board's lanes and of the tabs: every party in the Board's order (Release waits: it has no tab nor lane, decisions §283.29, which changes §273.2), but at the wide width Live after the others (its tab and its lane stand after the tabs' end). The discard is no party's lane: it is the window's right column (table/lane.js). */
export function partiesNow() {
  const all = partiesAll().filter((g) => !isRelease(g));            // a Release seated keeps its page and has no tab nor lane (decisions §283.29)
  if (!wide.value) return all;
  const { live } = roadParties(all), rest = all.filter((g) => g !== live);
  return live ? [...rest, live] : rest;
}

/** The parties of the tabs: the lanes' (spec 161 D: Release stands among them in the route's order). */
export const tabsNow = partiesNow;

/** How many of the lanes stand before the tabs' end (`--lanes`): all but Live's at the wide width, where Live's lane follows the end. */
export const lanesBeforeEnd = () => partiesNow().length - (wide.value && roadParties().live ? 1 : 0);

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

/** The name of the table a tab shows, where a thing opened over it says it came from (*← Tech's table · server/lobby.ts*). */
const MAP_NAMES = { tech: "Tech's table", design: "Design's table", product: "Product's table", "game-design": "Game design's table", art: "Art's table", release: "Release's table", marketing: "Marketing's table" };   // spec 150 C.2: a tab shows its party's table
export function mapName(tab, parties) {
  if (tab === ORKMASTER) return "Board";
  const g = parties.find((x) => x.slug === tab);
  return g && leadsSystem(g) ? "Tech's table" : MAP_NAMES[g?.party_craft] || (g ? `${nameOf(g)}'s table` : tab);
}

/** Tech's map is the System: the party the Architect leads (systemmap.js `leadsSystem`). */
export const leadsSystem = (g) => (g?.leader?.slug || "") === "architect";

/** The parties a picked goal's route passes, for the dot on their tabs: its own party always; the parties of its route as the Board has it (`ideas.map` nodes' `route` steps, once its work is planned) and as the rows
 *  that wait for the person say it (the `route` row's steps, the `talk` row's stances, a `fork`'s sides: `ideas.board` `needs_you`). */
export function routeParties(picked) {
  const n = picked && (mapData.value?.nodes || []).find((x) => x.slug === picked);
  if (!n) return new Set();
  const out = new Set([n.goal]);
  for (const s of n.route || []) { if (s.party) out.add(s.party); if (s.from) out.add(s.from); }
  for (const r of board.value?.needs_you || []) {
    if (r.idea !== picked) continue;
    for (const x of [...(r.route || []), ...(r.stances || []), ...(r.sides || [])]) if (x && x.party) out.add(x.party);
  }
  return out;
}

/** The parties a picked goal is on, for the tabs that are not grey (spec 156 B.5, decisions §261.3): those of its route as the Board has it (`routeParties`), without its own party's default when it is not routed yet (every leader is grey then:
 *  the Orkmaster's alone). null for a goal the snapshot does not have. */
export function onRoute(picked) {
  const n = picked && (mapData.value?.nodes || []).find((x) => x.slug === picked);
  if (!n) return null;
  const all = routeParties(picked), routed = (n.route || []).some((s) => s.party || s.from) || (board.value?.needs_you || []).some((r) => r.idea === picked && [...(r.route || []), ...(r.stances || []), ...(r.sides || [])].some((x) => x?.party));
  const out = new Set(!routed && !PHASE_OF[n.state] ? [] : all);
  for (const slug of roadSlugs()) out.add(slug);                      // Release's and Live's tabs look at the whole project: they are never grey
  return out;
}

// -- a goal's phases (docs/specs/95-the-window-as-decided.md §3.6, §5.2; decisions §126.4, §147.2) -----------------------------------------------------

/** The phases as the person reads them, in order; the engine's states are its own (`realm/ideas.py` STATES). */
export const PHASES = [["talk", "Talk"], ["spec", "Spec"], ["work", "Work"], ["done", "Done"]];
const PHASE_OF = { routed: "talk", talk: "talk", decided: "spec", sections: "spec", ready: "work", planning: "work", accepting: "work", plan: "work", working: "work", failed: "work", done: "done" };

/** The phase a goal is in (`talk`, `spec`, `work`, `done`); "" for one with none (not routed yet, or a pitch). */
export const phaseOf = (picked) => PHASE_OF[(mapData.value?.nodes || []).find((x) => x.slug === picked)?.state] || "";

// -- the Board's cards (docs/specs/101-the-cards-the-cascade-and-the-hand-under-the-lanes.md §2, §3; decisions §167.1, §167.4) -------------------------------------------------

/** The stages a card says on the Board: its small sign and its word. The first lane's are the Orkmaster's (reading, routing, joining); a party's are its tasks'. */
export const STAGES = {
  planning: { word: "Planning", sign: "page" }, doing: { word: "Doing", sign: "sword" }, checking: { word: "Checking", sign: "shield" },
  review: { word: "To look at", sign: "page" }, done: { word: "Done", sign: "check" },          // a task waiting for the person's look, and one merged: never *Planning* (spec 143 F.1, decisions §250.7)
  reading: { word: "Reading", sign: "page" }, routing: { word: "Routing", sign: "page" }, joining: { word: "Joining", sign: "page" },
  routed: { word: "Routed", sign: "page" }, talking: { word: "Talking", sign: "page" }, decided: { word: "Decided", sign: "page" },
};

/** The stage a task is in: a check (the checker's band, or testing) is *Checking*, one being done or failed *Doing*, one that asks the person's pick or waits to start *Planning*. */
export const stageOf = (t) => (t.state === "review" ? "review" : t.state === "merged" ? "done" : t.band === "check" || t.state === "testing" ? "checking" : t.state === "running" || t.state === "failed" ? "doing" : "planning");

/** Where a task stands in a cascade, the front lowest: a failed check, any failure, *Checking*, *Doing*, *Planning*. */
const FRONT = { review: 1.5, checking: 2, doing: 3, planning: 4, done: 5 };         // *To look at* in front of *Checking*, *Done* last (spec 143 F.1)
const rankOf = (t) => (t.state === "failed" ? (t.band === "check" ? 0 : 1) : FRONT[stageOf(t)]);

/** A goal's tasks that the Board draws, the front one first: by the rule above, the most recent first among equals (a later task of the plan is a more recent one). */
export function cascadeOf(n) {
  return openTasks(n).map((t, i) => ({ t, i })).filter(({ t }) => LIVE.includes(t.state))
    .sort((a, b) => rankOf(a.t) - rankOf(b.t) || b.i - a.i).map(({ t }) => t);
}

/** How urgent a goal is in its lane, the hand's order: a failure, then a question, then the rest. */
const urgencyOf = (n, tasks) => (tasks.some((t) => t.state === "failed") ? 0 : n.asks_you || tasks.some((t) => t.state === "picking") ? 1 : 2);

/** The goals of a party that have tasks at work, in the hand's order (urgency, then their place in the Board): [{n, tasks}], `tasks` front first. */
export function laneOf(g) {
  const out = [];
  nodesFor(g).filter(atWork).forEach((n, i) => { const tasks = cascadeOf(n); if (tasks.length) out.push({ n, tasks, at: urgencyOf(n, tasks) * 1000 + i }); });
  return out.sort((a, b) => a.at - b.at);
}

/** A task's words for a label: *Doing, failed*. */
export const footWords = (t) => `${STAGES[stageOf(t)].word}${t.state === "failed" ? ", failed" : t.state === "picking" ? ", asks you to pick" : ""}`;

/** A task's kind as the sign that says it, by the kind (`kind`) or the label the Board carries (`tag`). Code, the default, says nothing: the goal's type does. */
// A task's kind to a goal type's sign, every one drawn at 14 x 14 in two tones (orkUI 0.16, decisions §170.1): the window shows the big drawing, never a 7 x 7 at four pixels a cell.
const KIND_SIGN = { tests: "flask", docs: "page", text: "tagline", research: "flask", architecture: "restructure", design: "screen", uikit: "screen", a11y: "steps", art: "picture",
  data: "chart", query: "chart", metrics: "chart", datacheck: "chart", experiment: "abtest", seo: "landing", campaign: "horn", community: "post", security: "logo", edit: "tagline",
  gamedesign: "mechanic", level: "level", sound: "tune", music: "tune", playtest: "balance", aso: "store", artdirection: "character", motion: "picture", artcheck: "picture" };
const TAG_KIND = { "Tests": "tests", "Docs": "docs", "Text for people": "text", "Research": "research", "Architecture": "architecture", "Screens and flows": "design", "UI kit": "uikit",
  "Accessibility": "a11y", "Pixel art": "art", "Data pipelines and tables": "data", "Queries": "query", "Metrics": "metrics", "Data check": "datacheck", "Experiments": "experiment",
  "Search (SEO)": "seo", "Launch and campaigns": "campaign", "Community": "community", "Security check": "security", "Editing": "edit", "Game design": "gamedesign", "Levels": "level",
  "Sound": "sound", "Music": "music", "Playtest": "playtest", "Store pages (ASO)": "aso", "Art direction": "artdirection", "Animation": "motion", "Art check": "artcheck" };

// Each race's drawings (orkUI 0.16: *each party's things lean on its race*) and its tool (`.ork-tool`, four variants): a task card shows a drawing of the race
// that does it, by its head (decisions §173): its kind's when that race has it, else the race's tool, its variant by the kind (the same kind, the same variant).
const RACE_OF = { peon: "ork", shaman: "ork", elf: "elf", dryad: "elf", goblin: "goblin", imp: "goblin", gnome: "gnome", fairy: "gnome", knight: "knight", unicorn: "knight",
  skeleton: "undead", lich: "undead" };
const RACE_SIGNS = { ork: ["feature", "bug", "tidy", "restructure", "compass", "flask", "page"], elf: ["screen", "picture", "logo", "steps", "tune"],
  goblin: ["chart", "balance", "abtest"], gnome: ["horn", "landing", "post", "tagline", "store"], knight: ["mechanic", "level", "character", "target", "abtest"],
  undead: ["release"] };
const RACE_TOOL = { ork: ["drum", "gear", "bolt", "spiral", "tusk"], elf: ["bow", "round", "flat", "drip", "fan"], goblin: ["pick", "gem", "coin", "gear", "mushroom"],
  gnome: ["bell", "waves", "stars", "note", "hearts"], knight: ["map", "cross", "star", "heart", "crown"], undead: ["hourglass", "candle", "bone", "gem", "ring"] };
const variantOf = (word) => [...String(word || "")].reduce((a, c) => a + c.charCodeAt(0), 0) % 4;

/** The drawing in a task card's window: its kind's (else its goal's type's) when the race that does it has that drawing, else that race's tool
 *  (`tool:<tool>-<variant>`); with no head, the kind's; "" with none. */
export function typeSignOf(n, t) {
  const kind = t?.kind || TAG_KIND[t?.tag] || "", sign = KIND_SIGN[kind] || n?.type?.sign || "";
  const race = RACE_OF[String(t?.head?.race || "").split("-")[0]];
  if (!race || !sign || RACE_SIGNS[race].includes(sign)) return sign;
  const [tool, ...variants] = RACE_TOOL[race];
  return `tool:${tool}-${variants[variantOf(kind || sign)]}`;
}

/** The gem on a card that spends: a task being done again (its round past the first) shows what its last run cost, as a share of the limits or at API prices; "" for a card that spends nothing. */
export function gemOf(t) {
  const cost = Number(t?.cost);
  if (!(t?.round > 1) || !Number.isFinite(cost) || cost <= 0) return "";
  return rated() ? pctShort(cost).replace(/\s+%$/, "%") : `$${cost < 1 ? cost.toFixed(2) : Math.round(cost)}`;
}

// -- the goals in line (the first lane's last cascade) --------------------------------------------------------------------------------

/** The goals in line, in the Orkmaster's order (the order of the map's nodes): the nodes whose `place` is `deck`; `reset` when one waits for the window's reset. */
export function lineNow(map = mapData.value) {
  const parties = Object.fromEntries((map?.goals || []).map((g) => [g.slug, g]));
  return (map?.nodes || []).filter((n) => n.place === "deck").map((n) => ({
    slug: n.slug, title: n.short || n.title, full: n.title, element: n.element || "", hue: n.hue || "", party: n.goal, partyName: parties[n.goal]?.short || parties[n.goal]?.title || "", type: n.type || null,
    waits: n.waits_as || "", reset: n.waits_as === "reset", at: n.held_until || n.start_at || "", state: n.state }));
}

/** Why a goal in line waits, in words: the moon's reset and its hour, held, waiting for a goal; "In line" when it simply waits its turn. */
export function waitsWords(g) {
  if (g.reset) return `Waits for the reset${g.at ? `, from ${hhmm(g.at)}` : ""}`;
  return g.waits === "held" ? "Held" : g.waits === "line" ? "Waits for a goal" : "In line";
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

/** A party's squad on its lens (docs/specs/123-the-leaders-at-the-table.md §5): *Does* and *Checks* with their seats, the leader left out (it sits at the table, in the tabs), at most six seats in all: [{band: "build" | "check", word, seats: [member]}]. */
export function squadOf(g) {
  const { members } = partyOf(g, nodesFor(g));
  let left = 6;
  return [["build", "Does"], ["check", "Checks"]].map(([band, word]) => {
    const kept = members.filter((m) => m.band === band).slice(0, Math.max(0, left));
    left -= kept.length;
    return { band, word, seats: kept };
  }).filter((x) => x.seats.length);
}

/** The AI tool a seat runs on: the seat's own, the party's, else the role's (the Main tool). {id, name} */
export function toolOf(g, m) {
  const role = roleOf(agents.value, m.slug), id = g.tools?.[m.slug] || g.tool || role?.harness?.id || "claude";
  return { id, name: role?.harness && role.harness.id === id ? role.harness.name : id.charAt(0).toUpperCase() + id.slice(1) };
}

/** The ink mark of a tool (orkUI marks/): known tools only; `colour`: its own colours (the open tab's, the potions'). */
export const MARKED = ["claude", "codex", "agy", "cursor", "hermes", "pi"];
export const markSrc = (id, x2 = false, colour = false) => `${ORKUI}/marks/harness-${id}${colour ? "" : "-ink"}${x2 ? "@2x" : ""}.png`;

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
