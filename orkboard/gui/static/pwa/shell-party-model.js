// What New party on the phone knows about a party's seats, without drawing any (docs/specs/91-the-owners-list.md §7, decisions §107.5): the presets (`ideas.party_presets`: the stages of the project's
// kind, the crafts, the person's own; an older host's `ideas.roles` presets when it has none), the team a size gives a recipe and the tiers it gives its seats (the same rule as
// realm/party_recipes.py `sized` and `tiers_for`, so a seat's head changes at once, before anything is saved), and the AI tools a seat may run on, grouped by what its role needs
// (realm/library.py `needs`, `ideas.tools` `makes`): the ones that can do it, and the ones that cannot with the reason in words. The desktop's twin is js/shell/partymodel.js.
import { CRAFT_WORDS, TIER_WORDS } from "./shell-who.js";

export const TASKMASTER = "taskmaster";
export const GROUPS = [["stage", "By stage of the project"], ["craft", "By craft"], ["own", "Your own party"]];
const STAGES = ["ideation", "concept", "build", "release", "liveops"];
const CRAFTS = ["engineering", "design", "data", "marketing", "product", "art"];
const SIZE_IDS = ["lean", "standard", "full"];
export const OWN_LINE = "Start from the Taskmaster and add who you need";

export const library = (core) => core.st.roles?.library || [];
export const agentOf = (core, id) => library(core).find((a) => a.id === id);
export const bandOf = (core, id) => agentOf(core, id)?.band || "build";
/** The seats of a leader's party (`ideas.roles` `stages`): a seat a stage. A pitch leader (Ideation) keeps its views and the Skeptic as they are. */
export function seatsOf(core, leader, team = []) {
  const stage = core.st.roles?.stages?.[leader] || core.st.roles?.stages?.default, seats = stage?.seats || core.st.roles?.seats || { lead: 1, build: 1, check: 1 };
  if (!agentOf(core, leader)?.pitch) return seats;
  return { lead: 1, build: Math.max(1, team.filter((s) => bandOf(core, s) === "build").length), check: Math.max(1, team.filter((s) => bandOf(core, s) === "check").length) };
}

/** The word of a leader's stage in a band (`ideas.roles` `stages`): *Concept*, *Build*, *Playtest* with a Game designer; *Planning*, *Implementation*, *Checking* otherwise. */
export const stageWord = (core, leader, band) => (core.st.roles?.stages?.[leader] || core.st.roles?.stages?.default || {})[band] || { lead: "Planning", build: "Implementation", check: "Checking" }[band];

/** The builders and checkers of a team, in its order: the candidates a size seats from. */
export const recOf = (core, team) => ({ build: team.filter((s) => bandOf(core, s) === "build"), check: team.filter((s) => bandOf(core, s) === "check") });

/** The team a size gives a recipe's candidates (`rec`: {build, check}, the most needed first): Lean the leader alone, Standard the first builder, Full the first builder and the first checker (a seat a
 *  stage: `seats`); no size ("") the whole party. */
export function sizedTeam(rec, size, seats = { build: 1, check: 1 }) {
  const build = (rec.build || []).slice(0, seats.build), check = (rec.check || []).slice(0, seats.check);
  return size === "lean" ? [] : size === "standard" ? build : [...build, ...check];
}

/** `{agent: tier}` a size gives a party's seats (realm/party_recipes.py `tiers_for`): Lean every seat Seasoned; Standard the leader Veteran and the first builder Seasoned; Full the leader and the
 *  checkers Veteran, the builders Seasoned. The Taskmaster is no seat. No size: none (the library's tiers stand). */
export function tiersFor(core, leader, team, size) {
  if (!SIZE_IDS.includes(size)) return {};
  const lead = leader && leader !== TASKMASTER ? [leader] : [], build = team.filter((s) => bandOf(core, s) === "build"), check = team.filter((s) => bandOf(core, s) === "check");
  const put = (ids, tier) => ids.map((s) => [s, tier]);
  if (size === "lean") return Object.fromEntries(put([...lead, ...team], "warrior"));
  if (size === "standard") return Object.fromEntries([...put(lead, "elder"), ...put(build.slice(0, 1), "warrior")]);
  return Object.fromEntries([...put(lead, "elder"), ...put(build, "warrior"), ...put(check, "elder")]);
}

/** The tier a seat wears: the size's, else the library's. */
export const tierOf = (core, id, tiers) => tiers[id] || agentOf(core, id)?.tier || "warrior";

/** The size's line under the switch (spec 81 §0): *One agent, Seasoned* · *3 agents: the leader Veteran, the rest Seasoned* · *4 agents, Seasoned and up*. */
export function sizeWords(size, agents) {
  const n = agents === 1 ? "One agent" : `${agents} agents`;
  return size === "lean" ? `${n}, Seasoned` : size === "standard" ? `${n}: the leader Veteran, the rest Seasoned` : size === "full" ? `${n}, Seasoned and up` : "";
}

/** The presets of an older host, from `ideas.roles`: Ideation and Release for the stages, the crafts, the Taskmaster alone. */
function fromRoles(core) {
  const crafts = ["engineering", "design", "data", "marketing", "product"], parties = core.st.roles?.parties || {};
  const sent = core.st.roles?.presets || crafts.filter((c) => parties[c]).map((c) => ({ id: c, name: CRAFT_WORDS[c], line: "", craft: c, lead: parties[c].lead, build: parties[c].build || [], check: parties[c].check || [] }));       // a host that sends no presets: the five crafts' parties
  const rows = sent.map((p) => ({ id: p.id, name: p.name, line: p.line, craft: p.craft, recipe: "", whole: p.id === "ideation", leader: p.lead, build: p.build, check: p.check }));
  const out = [];
  for (const p of rows) {
    const group = p.id === "mixed" ? "own" : STAGES.includes(p.id) ? "stage" : CRAFTS.includes(p.id) ? "craft" : "";
    if (group) out.push({ ...p, group, stage: group === "stage" ? p.id : "", ...(group === "own" ? { name: "Your own party", line: OWN_LINE } : {}) });
  }
  const order = (list, ids) => list.sort((a, b) => ids.indexOf(a.id) - ids.indexOf(b.id));
  return [...order(out.filter((p) => p.group === "stage"), STAGES), ...order(out.filter((p) => p.group === "craft"), CRAFTS), ...out.filter((p) => p.group === "own")];
}

/** Asks `ideas.party_presets`; keeps `core.st.partyPresets` = {kind, presets}. A host without it gives its `ideas.roles` presets, the kind the Map says. */
export async function loadPresets(core) {
  const got = await core.call("ideas.party_presets", {}, () => {});
  const kind = got?.kind || core.st.map?.project?.kind || null;
  core.st.partyPresets = got && Array.isArray(got.presets) ? { kind, presets: got.presets } : { kind, presets: fromRoles(core) };
  return core.st.partyPresets;
}

/** A party of the library that the list does not hold (a deal's card for the mixed Game, Mobile app or Website) as a preset. */
export function libraryPreset(core, id) {
  const p = (core.st.roles?.presets || []).find((x) => x.id === id);
  return p ? { id: p.id, name: p.name, line: p.line, group: "craft", stage: "", craft: p.craft, recipe: "", whole: false, leader: p.lead, build: p.build, check: p.check } : null;
}

// -- the AI tool of a seat ------------------------------------------------------------------------------------------------------------------------------------

const MAKE_WORDS = { pictures: "make pictures", sound: "make sound" };
const NO_MAKE = { pictures: "draws no pictures", sound: "makes no sound" };

/** What a tool says it makes, in words: *Pictures, code and text*; *Code and text* for a tool that makes only those. */
export const makesWords = (t) => (t.makes?.length ? `${t.makes.map((m, i) => (i ? m : m[0].toUpperCase() + m.slice(1))).join(" and ")}, code and text` : "Code and text");

/** The caption of a tool's row for a seat of this tier: what it makes, and which model the tier runs (a tool with no tiers runs its own). */
export const toolCaption = (t, tier) => `${makesWords(t)} · ${t.tiers ? `its ${TIER_WORDS[tier] || "Seasoned"} model` : "runs its own model"}`;

/** Why a tool cannot do what a seat needs, in words ("" when it can): what it does not make, else that it is not installed or not signed in. */
export function reasonOf(t, needs = []) {
  const lacks = needs.find((n) => !(t.makes || []).includes(n));
  if (lacks) return NO_MAKE[lacks] || `makes no ${lacks}`;
  return !t.installed ? "not installed" : !t.signed_in ? "not signed in" : "";
}

/** The groups of the tools for a seat (`role`: its library entry with `needs`): `can` the ready tools that make what the seat needs (all the ready ones when it needs nothing) and `cannot`, each
 *  with its `reason`, titled *Cannot make pictures* (the first need) or, for a seat that needs nothing, *Cannot run yet*. `none`: the sentence for an empty `can`. */
export function toolGroups(tools, role) {
  const needs = role?.needs || [], rows = tools?.tools || [];
  const can = rows.filter((t) => t.ready && !reasonOf(t, needs)), cannot = rows.filter((t) => !can.includes(t)).map((t) => ({ ...t, reason: reasonOf(t, needs) }));
  const need = needs[0];
  const none = can.length ? "" : need === "sound" ? "No AI tool here makes sound: this seat writes it as code or a brief" : need ? `No AI tool ready here can ${MAKE_WORDS[need] || `make ${need}`}` : "";
  return { can, cannot, none, canTitle: `Can do what ${role?.name || "this seat"} needs`, cannotTitle: need ? `Cannot ${MAKE_WORDS[need] || `make ${need}`}` : "Cannot run yet" };
}
