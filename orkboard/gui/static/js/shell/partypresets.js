// The left half of New party and Edit the party (docs/specs/91-the-owners-list.md §7, decisions §107.5): presets to start the party from, each a button (`aria-pressed` on the one pressed) with its leader's
// head, its name in the pixel face and one line — **By stage of the project** (Ideation, Concept, Build, Release, LiveOps, fitted to what the project is: *For a mobile app: the Orkmaster knows what this
// project is*), **By craft** (Tech, Design, Data, Marketing, Product, Art and sound: two to a row) and **Your own party** (the Taskmaster alone: *Start from the Taskmaster and add who you need*) —,
// then the person's saved parties when there are some; a card says under its line what the Orkmaster's deal says of it (*You have one*). A press fills the seats on the right (partydraft.js); nothing is saved until Save party.
import { html } from "../html.js";
import { Head } from "../orkui.js";
import { dealEntry, whyWords } from "../arena/projectwords.js";
import { mapData } from "./store.js";
import { OwnParties, agentOf, raceOfAgent } from "./party.js";
import { GROUPS } from "./partymodel.js";

const Card = ({ p, lit, onPick, compact = false }) => {
  const lead = agentOf(p.leader), race = lead ? raceOfAgent(lead) : "peon", tier = lead?.tier || "elder";
  const e = dealEntry(mapData.value?.project?.deal, p.id), why = whyWords(e);         // what the Orkmaster's deal says of it (spec 70 §3.2): *You have one*, *3 flags wait and no party releases them*
  return html`<button type="button" class=${`shell-craft-tile shell-preset${compact ? " is-compact" : ""}`} data-craft=${p.id} data-stage=${p.stage || undefined} aria-pressed=${String(lit === p.id)}
    title=${p.line} onClick=${() => onPick(p)}><${Head} race=${race} tier=${tier} /><span class="shell-craft-tile__text"><b>${p.name}</b><small class="ok-tone-muted">${p.line}</small>
      ${why && !compact && html`<small class="shell-craft-tile__why ok-tone-muted" data-why=${e.why}>${why}</small>`}</span></button>`;
};

/** `presets`: [{id, name, line, group, stage, leader, build, check, …}] (partymodel.js `usePresets`); `lit`: the id pressed; `kind`: what the project is ({words}); `own`: {parties, pick, reload, picked}. */
export function Presets({ presets, kind, lit, onPick, own }) {
  const mine = (g) => presets.filter((p) => p.group === g && p.id !== "team");          // the Team preset is Operations' (spec 98 §1): not drawn here
  return html`<nav class="shell-presets" aria-label="Presets">${GROUPS.map(([group, words]) => mine(group).length > 0 && html`<section key=${group} class=${`shell-presets__group is-${group}`} aria-label=${words}>
    <h3 class="ok-font-label">${words}</h3>
    ${group === "stage" && kind?.words && html`<p class="shell-presets__kind ok-tone-muted">For ${kind.words}: the Orkmaster knows what this project is</p>`}
    <div class=${`shell-presets__cards${group === "craft" ? " is-grid" : ""}`}>${mine(group).map((p) => html`<${Card} key=${p.id} p=${p} lit=${lit} onPick=${onPick} compact=${group === "craft"} />`)}</div>
    ${group === "own" && own && html`<${OwnParties} parties=${own.parties} onPick=${own.pick} reload=${own.reload} picked=${own.picked} />`}</section>`)}</nav>`;
}
