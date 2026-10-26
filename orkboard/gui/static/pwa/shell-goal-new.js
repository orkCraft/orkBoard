// The team of a party on the phone as the Add to the party sheet changes it (docs/specs/41-phone-round-3.md §6, spec 50 §0, §6.7, spec 59 §2): `makeParty` is the team and the checks alone — the party
// folded to one line (Leads · Builds · Checks) with Change, its checks folded to one line —; the team is three folds, one open at a time, each closed by Done: Leads (one seat: a pick folds it and
// opens Builds), Builds, Checks, each a seat a stage (spec 87 §5). A task goes to the one of the party who does its kind of work (Grunt fills in); a checker's check adds its line to the spec's Done when
// and its task to the plan (realm/idea_checks.py). A goal's own screen changes its team with the same two (shell-goal.js). Under the price, *It can take:* the goal types the seats would be offered
// (spec 63 §2). Ideation (spec 65 §1) is the library's like any: its six agents are offered to no other party, and its seats are not changed (no Change; its price is a pitch's, it takes no goal type).
// **New party** is shell-party-new.js (docs/specs/91-the-owners-list.md §7): presets, then the team by seats with a size and each seat's AI tool.
import { h, head, icon } from "./util.js";
import { makePrice } from "./shell-party-price.js";
import { RACE_WORDS, TIER_WORDS, raceOf } from "./shell-who.js";
import { say } from "./shell-words.js";

const BANDS = [["lead", "Leads", "reads and plans each goal"], ["build", "Builds", "do the work"],
  ["check", "Checks", "hold each goal to their check"]];
const TASKMASTER = "taskmaster";
const library = (core) => core.st.roles?.library || [];     // the agents that come with Orkline (ideas.roles: realm/library.py)
const DEFAULT_SEATS = { lead: 1, build: 1, check: 1 };     // a seat a stage (spec 87 §5)
/** The seats of a leader's party (spec 59 §2.3: `ideas.roles` `stages`), the default's for an older host or a leader the host does not name. */
const stagesOf = (core, leader) => core.st.roles?.stages?.[leader] || core.st.roles?.stages?.default || { lead: "Planning", build: "Implementation", check: "Checking", seats: core.st.roles?.seats || DEFAULT_SEATS };
const seatsOf = (core, leader) => stagesOf(core, leader).seats || DEFAULT_SEATS;
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
/** Ideation is always its four views and the skeptic (spec 65 §1, realm/goal_team.py `IDEATION_WHOLE`): its seats are not changed, and its agents sit in no other party. */
export const IDEATION_WHOLE = "Ideation reads every pitch from all four sides: its views and the skeptic stay.";
/** A head of the sheet that stands for an agent: the gather finds where the sheet shows it by this. */
const tag = (img, id) => { img.dataset.agent = id; return img; };

/** A goal's team and its checks: {team, checks, set({leader, team, every}), get() → {leader, team, every}, preset(craft)}. `team` is the line
 *  with Change and the three folds; `checks` the checks' line with Change and its list. */
export function makeParty(core, opts = {}) {
  let leader = TASKMASTER, team = [], every = [];          // team: the builders and checkers
  let owns = [], partyId = "", asking = "";                // your parties (spec 43 §6); `partyId`: the one whose seats these are, until a seat changes
  let editing = false, fold = "", checking = false;
  let presetId = "";                                       // the library's party the seats are, until a seat changes
  const teamEl = h("div", { class: "party" });
  const checksEl = h("div", { class: "party-checks" });
  const pr = makePrice(core, { current: () => ({ ...current(), ...(craftNow() ? { craft: craftNow() } : {}) }), redraw: () => draw() });       // what the party costs and can take (shell-party-price.js)

  const agent = (id) => library(core).find((a) => a.id === id) || (core.st.roles?.roles || []).find((r) => r.slug === id && { id: r.slug, name: r.name });
  const nameOf = (id) => agent(id)?.name || agent(id)?.id || id;
  /** The band an agent sits in: the library says; an agent of the person's own builds. */
  const bandOf = (id) => library(core).find((a) => a.id === id)?.band || "build";
  const inBand = (band) => (band === "lead" ? [leader] : team.filter((id) => bandOf(id) === band));
  const names = (band) => inBand(band).map(nameOf).join(", ") || "none";
  const draw = () => { drawTeam(); drawChecks(); opts.onChange?.(); };
  /** The party is Ideation: its leader judges pitches (the library's `pitch`). */
  const ideation = () => agent(leader)?.pitch === true;
  const seats = (band) => seatsOf(core, leader)[band];
  /** The refusal for a stage that has fewer seats with this leader than the party has members (spec 59 §6.2): "" when the party fits. */
  const overWords = () => {
    const band = ideation() ? null : ["build", "check"].find((b) => inBand(b).length > seats(b));       // (Ideation is its views and the Skeptic whole)
    return band ? `${stagesOf(core, leader)[band]} has ${seats(band)} ${seats(band) === 1 ? "seat" : "seats"} with ${nameOf(leader)}: take one out first.` : "";
  };
  async function loadOwns() {
    const got = await core.call("ideas.parties");
    if (got) { owns = got.parties || []; draw(); }
  }
  /** *3 parties in 2 projects · 2 met*: said only once a party has been used. */
  const usedWords = (p) => (p.goals ? `${p.goals} ${p.goals === 1 ? "party" : "parties"} in ${p.projects} ${p.projects === 1 ? "project" : "projects"} · ${p.met} met` : "");
  /** **Your parties**, above the team when there is one: a chip each with its members' small heads, its name and where it was used. A tap fills the seats
   *  (and the craft in New goal); its `close` mark removes it after asking. */
  function ownRow() {
    if (!owns.length) return null;
    const drop = async (p) => {
      const got = await core.call("ideas.party_drop", { id: p.id });
      asking = "";
      if (got) loadOwns(); else draw();
    };
    return h("section", { class: "own-parties", "aria-label": "Your parties" }, h("h3", {}, "Your parties"),
      h("div", { class: "own-chips" }, ...owns.map((p) => h("div", { class: `own-chip${partyId === p.id ? " is-on" : ""}`, "data-party": p.id },
        h("button", { class: "own-pick", type: "button", "aria-pressed": String(partyId === p.id), "aria-label": `Pick your party “${p.name}”`, onclick: () => pickOwn(p) },
          h("span", { class: "own-heads" }, ...[p.leader, ...p.team].map(agent).filter((a) => a?.craft).map((a) => tag(head(raceOf(a), a.tier || "warrior", { small: true }), a.id || a.slug))),
          h("b", {}, p.name), usedWords(p) ? h("small", { class: "muted" }, usedWords(p)) : null),
        h("button", { class: "own-close", type: "button", "aria-label": `Remove your party “${p.name}”`, onclick: () => { asking = p.id; draw(); } }, icon("close")),
        asking === p.id ? h("p", { class: "own-ask", role: "alert" }, `Remove your party “${p.name}”? Parties that use it keep their agents.`,
          h("button", { class: "ork-btn danger", type: "button", onclick: () => drop(p) }, "Remove it"),
          h("button", { class: "ork-btn", type: "button", onclick: () => { asking = ""; draw(); } }, "Keep it")) : null))));
  }
  function pickOwn(p) {
    leader = p.leader || TASKMASTER;
    team = [...p.team];
    every = [...p.every];
    partyId = p.id; presetId = "";
    if (p.craft && opts.onCraft) opts.onCraft(p.craft);
    draw();
    pr.ask();
  }
  const current = () => ({ leader, team: [...team], every: every.filter((id) => team.includes(id)) });

  /** An agent's row in its fold: a tap takes it in or out (a leader takes the one seat; out, the Taskmaster leads). */
  function seat(a) {
    const id = a.id || a.slug, band = a.band || bandOf(id);
    const on = band === "lead" ? leader === id : team.includes(id);
    const kind = raceOf(a);
    return h("button", { class: "team-row", type: "button", "aria-pressed": String(on), "data-agent": id,
      "aria-label": `${on ? "Take out" : "Take in"}: ${a.name}`, onclick: () => {
        if (band === "lead") { leader = on ? TASKMASTER : id; fold = on ? "lead" : "build"; }      // a pick folds Leads and opens Builds
        else if (on) team = team.filter((x) => x !== id);
        else if (inBand(band).length < seats(band)) team = [...team, id];
        else { core.flash(core.st.roles?.stages ? `${stagesOf(core, leader)[band]} has ${plural(seats(band), "seat")} with ${nameOf(leader)}: take one out first.`
          : `${BANDS.find((b) => b[0] === band)[1]} has ${plural(seats(band), "seat")}: take one out first.`); return; }       // an older host has no stages: today's words
        partyId = ""; presetId = "";                             // a seat changed: the party is then the person's own picking
        draw();
        pr.ask();
      } }, head(kind, a.tier || "warrior"), h("b", {}, a.name, a.check ? h("span", { class: "check-badge" }, "checks") : null),
      h("small", { class: "muted" }, say(`${TIER_WORDS[a.tier] || ""} ${RACE_WORDS[kind]}${a.line ? ` · ${a.line}` : ""}`.trim())),
      h("span", { class: "team-mark", "aria-hidden": "true" }, icon(on ? "check" : "plus")));
  }

  function band([id, words, what]) {
    const n = Math.max(seats(id), inBand(id).length), taken = inBand(id), on = fold === id, word = stagesOf(core, leader)[id];
    const own = (core.st.roles?.roles || []).filter((r) => team.includes(r.slug) && bandOf(r.slug) === id && !library(core).some((a) => a.id === r.slug));
    const list = [...library(core).filter((a) => a.band === id && !a.pitch), ...own.map((r) => ({ ...r, id: r.slug, band: id }))]       // the pitch agents are Ideation's only
      .sort((x, y) => (x.craft === craftNow() ? 0 : 1) - (y.craft === craftNow() ? 0 : 1));        // the goal's craft's first
    const over = taken.length > seats(id);
    return h("section", { class: `party-fold band-${id}${on ? " is-open" : ""}`, "aria-label": words, "data-stage": word },
      h("button", { class: "fold-head", type: "button", "aria-expanded": String(on), onclick: () => { fold = on ? "" : id; draw(); } },
        h("b", {}, words), h("small", { class: "muted" }, taken.length ? names(id) : "none"), h("small", { class: "muted fold-stage" }, id === "lead" ? word : `${word} · ${plural(seats(id), "seat")}`), h("span", { class: "fold-mark", "aria-hidden": "true" }, icon(on ? "close" : "plus"))),
      on ? h("div", { class: "fold-body" },
        h("small", { class: "muted" }, `${taken.length} of ${seats(id)} · ${what}`),
        over ? h("p", { class: "party-over", role: "alert" }, overWords()) : null,
        h("div", { class: "team-seats" }, ...Array.from({ length: n }, (_, i) => {
          const a = agent(taken[i]);
          return h("span", { class: `team-seat${a ? "" : " is-empty"}${id === "lead" ? " is-lead" : ""}${i >= seats(id) ? " is-over" : ""}`, title: a ? nameOf(taken[i]) : "A free seat" },
            a ? tag(head(raceOf(a), a.tier || "warrior"), taken[i]) : "");
        })),
        h("div", { class: "team-list" }, ...list.map(seat)),
        h("button", { class: "ork-btn", type: "button", "data-done": id, onclick: () => { fold = ""; draw(); } }, "Done")) : null);
  }

  function drawTeam() {
    const line = h("p", { class: "party-line" }, h("b", {}, "Leads: "), names("lead"), " · ", h("b", {}, "Builds: "), names("build"), " · ", h("b", {}, "Checks: "), names("check"));
    if (ideation()) editing = false;                              // Ideation's seats stay: no Change
    if (!editing) {
      teamEl.replaceChildren(...[h("h3", {}, "The party"), ownRow(), line, overWords() ? h("p", { class: "party-over", role: "alert" }, overWords()) : null, pr.line(), pr.takes(),
        ideation() ? h("p", { class: "muted party-whole", "data-sec": "ideation" }, IDEATION_WHOLE)
          : h("button", { class: "ork-btn", type: "button", "data-change": "team", onclick: () => { editing = true; fold = "lead"; draw(); } }, "Change")].filter(Boolean));
      pr.fit();
      return;
    }
    if (!fold) { editing = false; drawTeam(); return; }            // every fold closed by Done: back to the line
    teamEl.replaceChildren(...[h("h3", {}, "The party"), ownRow(), ...BANDS.map(band), pr.line(), pr.takes()].filter(Boolean));
    pr.fit();
  }

  /** The craft the party was started from (the goal's craft sorts its agents first); set by the sheet. */
  let craftNow = () => "";

  // -- the party's checks: each checker's, where it applies or on every goal, and what a check adds to a goal, in dollars ----------
  function drawChecks() {
    const checkers = team.map(agent).filter((a) => a?.check);
    const mine = every.filter((id) => team.includes(id));
    const said = !checkers.length ? "No check" : `${checkers.length} ${checkers.length === 1 ? "check" : "checks"}, ${mine.length ? `${mine.length} on every goal` : "where each applies"}`;
    if (ideation()) {                                               // the Skeptic makes the case against every pitch: no check to set
      checksEl.replaceChildren(h("h3", {}, "Checks on every goal"), h("p", { class: "party-line" }, `${names("check")} makes the case against every pitch; ${nameOf(leader)} decides.`));
      return;
    }
    if (!checking || !checkers.length) {
      checksEl.replaceChildren(...[h("h3", {}, "Checks on every goal"), h("p", { class: "party-line" }, checkers.length ? said : "No checker in the party: a goal is done when its own Done when lines are."),
        checkers.length ? h("button", { class: "ork-btn", type: "button", "data-change": "checks", onclick: () => { checking = true; drawChecks(); } }, "Change") : null].filter(Boolean));
      return;
    }
    checksEl.replaceChildren(h("h3", {}, "Checks on every goal"), h("div", { class: "checks-block", role: "group", "aria-label": "Checks" },
      h("p", { class: "muted" }, `How deep each goal is worked: every check adds a line to its Done when and a task to its plan.`),
      ...checkers.map((a) => {
        const box = h("input", { type: "checkbox", "aria-label": `Every goal: ${a.name}`, ...(every.includes(a.id) ? { checked: true } : {}) });
        box.addEventListener("change", () => { every = box.checked ? [...every, a.id] : every.filter((x) => x !== a.id); partyId = ""; presetId = ""; pr.ask(); });
        return h("div", { class: "check-row" }, head(raceOf(a), a.tier, { small: true }),
          h("span", { class: "check-text" }, h("b", {}, a.name), h("small", { class: "muted" }, say(`${a.check.done} · applies ${a.check.applies}`) + pr.adds(a.id))),
          h("label", { class: "check-every" }, box, h("span", {}, "Every goal")));
      }),
      h("button", { class: "ork-btn", type: "button", "data-done": "checks", onclick: () => { checking = false; drawChecks(); } }, "Done")));
  }

  return {
    team: teamEl,
    checks: checksEl,
    /** The party a goal has (or starts with); `craft`: whose agents sort first. */
    set(party, craft = () => "") {
      leader = party.leader || TASKMASTER;
      team = [...(party.team || [])];
      every = [...(party.every || [])];
      editing = false; fold = ""; checking = false; pr.reset(); asking = "";
      partyId = party.party || ""; presetId = "";
      craftNow = craft;
      draw();
      pr.ask(true, false);                               // the picker opens: its answers light nothing
      loadOwns();
    },
    fits: () => !overWords() || !!partyId,        // a saved party of the person's (made before) is saved as it was
    get: () => ({ ...current(), party: partyId, preset: partyId ? "" : presetId }),
    /** The crafts of the party's agents, for a Mixed goal's own craft. */
    crafts: () => [leader, ...team].filter((id) => id !== TASKMASTER).map((id) => agent(id)?.craft).filter(Boolean),
    /** The party's heads as the seats draw them, the leader first: [{id, race, tier}]. */
    heads: () => [leader, ...team].filter((id) => agent(id)).map((id) => ({ id, race: raceOf(agent(id)), tier: agent(id).tier || "warrior" })),
    names,
    draw,
  };
}
