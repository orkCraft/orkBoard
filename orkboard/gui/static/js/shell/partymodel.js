// What New party and Edit the party know about a party's seats, without drawing any (docs/specs/91-the-owners-list.md §7, decisions §107.5): the presets (`ideas.party_presets`: the stages of
// the project's kind, the crafts, the person's own; an older host's `ideas.roles` presets when it has none), the team a size gives a recipe and the tiers it gives its seats (the same rule as
// realm/party_recipes.py `sized` and `tiers_for`, so a seat's head changes at once, before anything is saved), and the AI tools a seat may run on, grouped by what its role needs
// (realm/library.py `needs`, `ideas.tools` `makes`): the ones that can do it, and the ones that cannot with the reason in words.
import { useEffect, useMemo, useState } from "preact/hooks";
import { command } from "../link.js";
import { TIER_WORDS } from "../orkui.js";
import { mapData } from "./store.js";
import { TASKMASTER, agentOf, pitchParty, presetsOf, seatsFor } from "./party.js";

const SIZE_IDS = ["lean", "standard", "full"];
/** The presets' groups in the order the dialog shows them, with their words. */
export const GROUPS = [["stage", "By stage of the project"], ["craft", "By craft"], ["own", "Your own party"]];
const STAGES = ["ideation", "concept", "build", "release", "liveops"];
const CRAFTS = ["engineering", "design", "data", "marketing", "product", "art"];
const OWN_LINE = "Start from the Taskmaster and add who you need";

const bandOf = (id) => agentOf(id)?.band || "build";

/** The team a size gives a recipe's candidates (`rec`: {build, check}, the most needed first): Lean the leader alone, Standard the first builder, Full the first builder and the first checker (a seat a
 *  stage: `seats`); no size ("") the whole party. The builders come first, then the checkers (realm/party_recipes.py `sized`). */
export function sizedTeam(rec, size, seats = { build: 1, check: 1 }) {
  const build = (rec.build || []).slice(0, seats.build), check = (rec.check || []).slice(0, seats.check);
  return size === "lean" ? [] : size === "standard" ? build : [...build, ...check];
}

/** `{agent: tier}` a size gives a party's seats (realm/party_recipes.py `tiers_for`): Lean every seat Seasoned; Standard the leader Veteran and the first builder Seasoned; Full the leader and the
 *  checkers Veteran, the builders Seasoned. The Taskmaster is no seat. No size: none (the library's tiers stand). */
export function tiersFor(leader, team, size) {
  if (!SIZE_IDS.includes(size)) return {};
  const lead = leader && leader !== TASKMASTER ? [leader] : [], build = team.filter((s) => bandOf(s) === "build"), check = team.filter((s) => bandOf(s) === "check");
  const put = (ids, tier) => ids.map((s) => [s, tier]);
  if (size === "lean") return Object.fromEntries(put([...lead, ...team], "warrior"));
  if (size === "standard") return Object.fromEntries([...put(lead, "elder"), ...put(build.slice(0, 1), "warrior")]);
  return Object.fromEntries([...put(lead, "elder"), ...put(build, "warrior"), ...put(check, "elder")]);
}

/** The tier a seat wears: the size's, else the library's. */
export const tierOf = (id, tiers) => tiers[id] || agentOf(id)?.tier || "warrior";

/** The candidates of a party's seats as they stand: its builders and its checkers, in the team's order. */
export const recOf = (team) => ({ build: team.filter((s) => bandOf(s) === "build"), check: team.filter((s) => bandOf(s) === "check") });

/** The size's line under the switch (spec 81 §0): *one agent, Seasoned* · *3 agents: the leader Veteran, the rest Seasoned* · *4 agents, Seasoned and up*. */
export function sizeWords(size, agents) {
  const n = agents === 1 ? "One agent" : `${agents} agents`;
  return size === "lean" ? `${n}, Seasoned` : size === "standard" ? `${n}: the leader Veteran, the rest Seasoned` : size === "full" ? `${n}, Seasoned and up` : "";
}

/** The presets of an older host, from `ideas.roles`: the stages Ideation and Release, the crafts, the Taskmaster alone (the library's mixed Game, Mobile app and Website are the stages' now). */
function fromRoles() {
  const rows = presetsOf().map((p) => ({ id: p.id, name: p.name, line: p.line, craft: p.craft, recipe: "", whole: p.id === "ideation", leader: p.lead, build: p.build, check: p.check }));       // a host that sends no presets: the five crafts' parties
  const out = [];
  for (const p of rows) {
    const group = p.id === "mixed" ? "own" : STAGES.includes(p.id) ? "stage" : CRAFTS.includes(p.id) ? "craft" : "";
    if (group) out.push({ ...p, group, stage: group === "stage" ? p.id : "", ...(group === "own" ? { name: "Your own party", line: OWN_LINE } : {}) });
  }
  const at = (g) => (p) => (g === "stage" ? STAGES : CRAFTS).indexOf(p.id);
  return [...out.filter((p) => p.group === "stage").sort((a, b) => at("stage")(a) - at("stage")(b)), ...out.filter((p) => p.group === "craft").sort((a, b) => at("craft")(a) - at("craft")(b)),
    ...out.filter((p) => p.group === "own")];
}

/** The presets of this project (`ideas.party_presets`): `{kind, presets}`, null while asked; a host without the command gives its `ideas.roles` presets (no kind). A preset has `id`, `name`, `line`,
 *  `group` (stage · craft · own), `recipe`, `whole`, `leader`, `build`, `check`. */
export function usePresets() {
  const [got, setGot] = useState(undefined);
  useEffect(() => {
    let live = true;
    command("ideas.party_presets", {}, true).then((a) => { if (live) setGot(a && Array.isArray(a.presets) && !a.error ? a : null); }).catch(() => { if (live) setGot(null); });
    return () => { live = false; };
  }, []);
  const kind = mapData.value?.project?.kind || null;
  return useMemo(() => (got === undefined ? null : got ? { kind: got.kind || kind, presets: got.presets } : { kind, presets: fromRoles() }), [got]);
}

/** The seats a leader's party has in a band, with the pitch party's fixed ones as they stand. */
export const seatsOf = (leader, team) => {
  const seats = seatsFor(leader);
  return pitchParty(leader) ? { lead: 1, build: Math.max(1, team.filter((s) => bandOf(s) === "build").length), check: Math.max(1, team.filter((s) => bandOf(s) === "check").length) } : seats;
};

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
 *  with its `reason`, titled *Cannot make pictures* (the first need it lacks) or, for a seat that needs nothing, *Cannot run yet*. `none`: the sentence for an empty `can` (a seat that needs sound:
 *  no tool makes it). */
export function toolGroups(tools, role) {
  const needs = role?.needs || [], rows = tools?.tools || [];
  const can = rows.filter((t) => t.ready && !reasonOf(t, needs)), cannot = rows.filter((t) => !can.includes(t)).map((t) => ({ ...t, reason: reasonOf(t, needs) }));
  const need = needs[0];
  const none = can.length ? "" : need === "sound" ? "No AI tool here makes sound: this seat writes it as code or a brief" : need ? `No AI tool ready here can ${MAKE_WORDS[need] || `make ${need}`}` : "";
  return { can, cannot, none, canTitle: `Can do what ${role?.name || "this seat"} needs`, cannotTitle: need ? `Cannot ${MAKE_WORDS[need] || `make ${need}`}` : "Cannot run yet" };
}
