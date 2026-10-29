// The top card's context (docs/specs/103-the-phones-app-a-native-frame.md §1.2, decisions §174.1, §178.5): upright on a touch phone, over the one stack, what the table would say of the card in hand — whose it is (its leader's head and
// party), which goal (its element, its type's sign, its short name; a project question says the project's name instead, *Go on paid?* the Orkmaster and the project), why it is asked (the question's `why`, in the body face, no line
// when it has none), what the leader recommends (*Recommended: <pick>*) and that work waits on it (*<member> waits for your answer*, *The work waits for your answer*). Never a count. At most a quarter of the screen's height, its own
// scroll past that. A press on it opens the goal's way over the pane (§142: the page of the phase it is in), and ← comes back to the same card. Nothing here answers anything: the answers are on the card.
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { askedOf, paidWords } from "../arena/arenawords.js";
import { openOver } from "../frame/state.js";
import { phaseOf } from "../table/data.js";
import { currentProject } from "../shell/projects.js";
import { mapData } from "../shell/store.js";
import { goalOfStop } from "./data.js";

const WAITS = "The work waits for your answer";

/** The Orkmaster's crowned head, as the map names it (the hand's `orkHead` for a stop with none of its own). */
const orkHeadOf = () => {
  const o = mapData.value?.project?.orkmaster || null;
  return { race: o?.race || "peon", tier: o?.tier || "crown" };
};

/** The leader's pick of a card, in the words of its choice; "" with none. */
export function pickOf(s) {
  if (s.card) return s.card.choices?.[s.card.pick] ?? "";
  if (s.kind === "asks" || s.kind === "goal") {
    const q = askedOf(s.row, s.node)[0];
    return q && q.pick != null ? q.choices?.[q.pick] || "" : "";
  }
  return "";
}

/** The question's why, as its leader wrote it; the Orkmaster's *Go on paid?* says its first sentence. */
export function whyOf(s) {
  if (s.card?.why) return s.card.why;
  if (s.kind === "paid") return (paidWords(s.row).match(/^[^.]*\.(?=\s|$)/) || [""])[0];
  if (s.why) return s.why;
  if (s.kind === "asks" || s.kind === "goal") return askedOf(s.row, s.node)[0]?.why || "";
  return "";
}

/** Who waits, in words, or "" when the work does not wait for the card (a question the leader asked for later): *Grunt waits for your answer*; the work of every party (a tool to sign in, going on paid) *The work waits for your answer*. */
export function waitsOf(s) {
  const blocks = s.row?.blocks === true || s.card?.blocks === true || s.kind === "failed";
  if (!blocks) return "";
  if (s.kind === "paid" || s.kind === "sign_in") return WAITS;
  const member = s.task?.by?.name || s.row?.todo?.by?.name || askedOf(s.row, s.node)[0]?.by?.name || s.party?.lead || "";
  return member && member !== "Taskmaster" ? `${member} waits for your answer` : WAITS;
}

/** What the context says of `s`, as data: `{head, who, goal: {name, element, sign} | null, project, why, pick, waits, idea}`. */
export function contextOf(s) {
  const party = s.party || {}, ork = s.kind === "paid" || s.kind === "sign_in" || !party.name, project = currentProject.value?.name || "", node = s.node || null;
  const goal = node ? { name: node.short || node.title || s.title || "", element: node.element || "", sign: node.type?.sign || "" } : null;
  return { head: ork ? orkHeadOf() : party.head || null, who: ork ? (project ? `Orkmaster · ${project}` : "Orkmaster") : party.name, goal, project: !goal && !ork ? project : "",
    why: whyOf(s), pick: pickOf(s), waits: waitsOf(s), idea: goalOfStop(s) };
}

/** The page of the goal's way it is in (§142): Talk until it is decided, else its Spec. */
const pageOf = (idea) => (phaseOf(idea) === "talk" ? "talk" : "spec");

/** The context of the card on top of the stack. */
export function Context({ s }) {
  const c = contextOf(s), open = c.idea && !c.idea.startsWith("party:") ? () => {
    const word = pageOf(c.idea) === "talk" ? "Talk" : "Spec";
    openOver(pageOf(c.idea), { idea: c.idea }, { title: "", key: "" }, word);      // no upright Board to name: the title says the page
  } : null;
  const inner = html`<span class="up-ctx__who ork-race">${c.head && html`<${Head} race=${c.head.race} tier=${c.head.tier} />`}<span class="ork-race__word">${c.who}</span></span>
    ${c.goal && html`<span class="up-ctx__goal"><${Elem} name=${c.goal.element} dim=${!c.goal.element} />${c.goal.sign && html`<${Sign} name=${c.goal.sign} />`}<span class="up-ctx__name">${c.goal.name}</span></span>`}
    ${c.project && html`<span class="up-ctx__goal"><span class="up-ctx__name">${c.project}</span></span>`}
    ${c.why && html`<span class="up-ctx__why">${c.why}</span>`}
    ${c.pick && html`<span class="up-ctx__rec">Recommended: ${c.pick}</span>`}
    ${c.waits && html`<span class="up-ctx__wait"><${Sign} name="alert" />${c.waits}</span>`}`;
  const label = [c.who, c.goal?.name || c.project].filter(Boolean).join(", ");
  return open
    ? html`<button type="button" class=${cls("up-ctx", "is-goal")} data-kind=${s.kind} aria-label=${`${label}: open the goal`} title="Open the goal" onClick=${open}>${inner}</button>`
    : html`<div class="up-ctx" data-kind=${s.kind} role="group" aria-label=${label}>${inner}</div>`;
}
