// The first step of New party on the phone (docs/specs/91-the-owners-list.md §7, decisions §107.5): presets to start the party from, each a 44 px button (`aria-pressed` on the one pressed) with its leader's
// head, its name and one line — **By stage of the project** (Ideation, Concept, Build, Release, LiveOps, fitted to what the project is: *For a mobile app: the Orkmaster knows what this project is*),
// **By craft** (Tech, Design, Data, Marketing, Product, Art and sound: two to a row) and **Your own party** (the Taskmaster alone: *Start from the Taskmaster and add who you need*) — and, under them,
// the person's saved parties when there are some (*Your parties*). A press fills the seats under it (shell-party-seats.js); nothing is saved until Save party. The desktop's twin is js/shell/partypresets.js.
import { h, head, icon } from "./util.js";
import { raceOf } from "./shell-who.js";
import { GROUPS, agentOf } from "./shell-party-model.js";

/** *3 parties in 2 projects · 2 met*: said only once a party of the person's has been used. */
const usedWords = (p) => (p.goals ? `${p.goals} ${p.goals === 1 ? "party" : "parties"} in ${p.projects} ${p.projects === 1 ? "project" : "projects"} · ${p.met} met` : "");

/** `core`: the board's frame; `act`: {pick(preset), own(party)}. Returns {el, draw(), lit(id), picked(partyId), load()}: `load` asks the host for the person's saved parties. */
export function makePresets(core, act) {
  const el = h("nav", { class: "presets", "aria-label": "Presets" });
  let lit = "", partyId = "", owns = [], asking = "";
  const data = () => core.st.partyPresets || { kind: null, presets: [] };

  const card = (p, compact) => {
    const lead = agentOf(core, p.leader);
    return h("button", { class: `craft-tile preset-tile${compact ? " is-compact" : ""}`, type: "button", "data-preset": p.id, "data-craft": p.id, "data-stage": p.stage || null, "aria-pressed": String(!partyId && lit === p.id),
      title: p.line, onclick: () => act.pick(p) },
    head(lead ? raceOf(lead) : "peon", lead?.tier || "elder"), h("span", { class: "preset-text" }, h("b", {}, p.name), compact ? null : h("small", { class: "muted" }, p.line)));
  };

  async function load() {
    const got = await core.call("ideas.parties");
    if (got) { owns = got.parties || []; draw(); }
  }
  const ownRow = () => {
    if (!owns.length) return null;
    const drop = async (p) => {
      const got = await core.call("ideas.party_drop", { id: p.id });
      asking = "";
      if (got) load(); else draw();
    };
    return h("section", { class: "own-parties", "aria-label": "Your parties" }, h("h4", {}, "Your parties"),
      h("div", { class: "own-chips" }, ...owns.map((p) => h("div", { class: `own-chip${partyId === p.id ? " is-on" : ""}`, "data-party": p.id },
        h("button", { class: "own-pick", type: "button", "aria-pressed": String(partyId === p.id), "aria-label": `Pick your party “${p.name}”`, onclick: () => act.own(p) },
          h("span", { class: "own-heads" }, ...[p.leader, ...p.team].map((id) => agentOf(core, id)).filter((a) => a?.craft).map((a) => head(raceOf(a), a.tier || "warrior", { small: true }))),
          h("b", {}, p.name), usedWords(p) ? h("small", { class: "muted" }, usedWords(p)) : null),
        h("button", { class: "own-close", type: "button", "aria-label": `Remove your party “${p.name}”`, onclick: () => { asking = p.id; draw(); } }, icon("close")),
        asking === p.id ? h("p", { class: "own-ask", role: "alert" }, `Remove your party “${p.name}”? Parties that use it keep their agents.`,
          h("button", { class: "ork-btn danger", type: "button", onclick: () => drop(p) }, "Remove it"),
          h("button", { class: "ork-btn", type: "button", onclick: () => { asking = ""; draw(); } }, "Keep it")) : null))));
  };

  function draw() {
    const { kind, presets } = data();
    el.replaceChildren(...GROUPS.map(([group, words]) => {
      const mine = presets.filter((p) => p.group === group);
      if (!mine.length) return null;
      return h("section", { class: `preset-group is-${group}`, "aria-label": words },
        h("h4", {}, words),
        group === "stage" && kind?.words ? h("p", { class: "muted presets__kind" }, `For ${kind.words}: the Orkmaster knows what this project is`) : null,
        h("div", { class: `preset-cards${group === "craft" ? " is-grid" : ""}` }, ...mine.map((p) => card(p, group === "craft"))),
        group === "own" ? ownRow() : null);
    }).filter(Boolean));
  }

  return { el, draw, load, lit: (id) => { lit = id; draw(); }, picked: (id) => { partyId = id; draw(); } };
}
