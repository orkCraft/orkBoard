// New party opens on the Orkmaster's proposals (docs/specs/75-parties-fitted-to-the-project.md §5.1–§5.2, decisions §90): the Orkmaster reads what the project is (`ideas.map` `project.kind`, no model)
// and `ideas.proposals` gives the parties that kind needs, each in three sizes — **Lean · Standard · Full** — with its heads, its agents and its price a goal. A card: its name, its line, its why and the
// size switch (Standard picked); **Make it** saves that party (`ideas.goal_save` with the leader, the team, `size` and the proposal's id — the host logs `proposal_taken` by it —, as a tile's party saves) and the heads gather into its deck (spec 63). An empty folder
// asks one line first, *What is this project for?*, and **Read it** draws the proposals of what the line says. **More: the library** opens today's tiles and seats. A host that does not send `project.kind`
// has no proposals: New party is today's (goalwizard.js). The words are spec 75 §0's; this file draws and sends, the host reads.
// Under the size switch each card has **Its AI tool** (toolpick.js, spec 81 §4): the Main tool picked, a list that drops down; a tool with no tiers of its own says *runs its own model* where the price was, and the pick is
// sent as `tool` with **Make it**. The size gives the party its team and its seats' tiers (the heads wear them).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command, toast } from "../link.js";
import { track } from "../board/store.js";
import { Head, Switch } from "../orkui.js";
import { pctRange } from "../spend.js";
import { gatherWaits } from "../arena/arenastate.js";
import { reducedMotion } from "../arena/motion.js";
import { act, mapData, showGoal } from "./store.js";
import { Modal, closeDialog, openDialog } from "./modals.js";
import { TARGETS } from "../board/target.js";
import { presetsOf } from "./party.js";
import { ToolPick, runsOwn, useTools } from "./toolpick.js";

export const SIZES = [["lean", "Lean"], ["standard", "Standard"], ["full", "Full"]];
export const SIZE_WORD = Object.fromEntries(SIZES);
/** What a size works as, the Target's words (board/target.js `TARGETS`): Lean works as Thrift, Standard as Balance, Full as Quality. */
export const SIZE_TARGET = { lean: "thrift", standard: "balance", full: "quality" };

/** The host sends the Orkmaster's reading of the project (spec 75 §4.3): only then New party opens on proposals. */
export const proposalsOn = () => !!mapData.value?.project?.kind;

/** *Works as Balance: the default…*: what a size does to the party's goals, in the Target's words. */
export function WorksAs({ size }) {
  const [, word, line] = TARGETS.find(([id]) => id === SIZE_TARGET[size]) || TARGETS[1];
  return html`<small class="shell-size__works ok-tone-muted">Works as ${word}: ${line}</small>`;
}

export const agentsWords = (n) => (n === 1 ? "one agent" : `${n} agents`);

/** *≈$0.40–1.20 a goal*; on the subscription its share of the window, *≈3–8 % of 5h a goal*. */
export function priceWords(price) {
  if (!price) return "";
  const { low, high } = price, pct = pctRange(low, high);
  if (pct) return `≈${pct} a goal`;
  if (low < 1) return `≈$${low.toFixed(2)}–${high.toFixed(2)} a goal`;
  const a = Math.round(low), b = Math.round(high);
  return a === b ? `≈$${a} a goal` : `≈$${a}–${b} a goal`;
}

/** `ideas.proposals` ({about?}): its answer, or null (an older host, a refusal — said once by `command`). */
export async function askProposals(about = "") {
  try {
    const got = await command("ideas.proposals", about ? { about } : {});
    return got && !got.error && Array.isArray(got.proposals) ? got : null;
  } catch { return null; }
}

/** A party is saved (New party's Make it, the library's Save party): the heads gather into its deck once it is shown, the dialog closes, the party is shown (or the goal asked for). */
export function savedParty(got, heads, then) {
  for (const note of got.notes || []) toast(note);       // an agent of the project's own that the party carries stays as it was
  if (heads.length) gatherWaits(got.slug, heads);        // the heads gather into the party's deck once it is shown (arena/goaltabs.js)
  closeDialog();
  track.value = got.slug;
  if (then === "idea") openDialog("idea", { goal: got.slug });
  else showGoal(got.slug);
}

/** The heads of a card as drawn now: [{race, tier, box}], the leader's first (six at most). */
function cardHeads(card, heads) {
  const imgs = [...(card?.querySelectorAll(".shell-prop__heads .ork-race__head") || [])].map((x) => x.getBoundingClientRect());
  return heads.slice(0, 6).map((h, i) => imgs[i] && { race: h.race, tier: h.tier, box: { left: imgs[i].left, top: imgs[i].top, width: imgs[i].width, height: imgs[i].height } }).filter(Boolean);
}

/** The size's heads, its agents, its price (*runs its own model* for a tool with no tiers: the price is its own). */
function SizeLine({ z, own = false }) {
  return html`<span class="shell-prop__heads">${(z.heads || []).map((h, i) => html`<${Head} key=${i} race=${h.race} tier=${h.tier} />`)}</span>
    <span class="shell-prop__agents">${agentsWords(z.agents)}</span><span class="shell-prop__price">${own ? "runs its own model" : priceWords(z.price)}</span>`;
}

function Proposal({ p, size, setSize, make, busy, asked, tools, tool, setTool }) {
  const z = p.sizes?.[size] || p.sizes?.standard, root = useRef();
  useEffect(() => { if (asked) root.current?.scrollIntoView?.({ block: "nearest" }); }, [asked]);
  return html`<article ref=${root} class=${cls("shell-prop", { "is-have": p.have, "is-asked": asked })} data-proposal=${p.id} data-size=${size} aria-label=${p.name}>
    <div class="shell-prop__top"><h4 class="shell-prop__name">${p.name}</h4>${p.have && html`<span class="shell-prop__have ok-tone-muted">You have one</span>`}</div>
    <p class="shell-prop__line">${p.line}</p>
    ${p.why && html`<p class="shell-prop__why ok-tone-muted">${p.why}</p>`}
    <${Switch} label="Size" options=${SIZES} value=${size} onPick=${setSize} />
    <${ToolPick} tools=${tools} value=${tool} onChange=${setTool} id=${`tool-${p.id}`} />
    <div class="shell-prop__foot"><${SizeLine} z=${z} own=${runsOwn(tools, tool)} />
      <button type="button" class="ork-btn primary shell-prop__make" disabled=${busy} onClick=${() => make(p, size, root.current, tool)}>Make it</button></div>
  </article>`;
}

/** An empty folder: *What is this project for?* and **Read it**. */
function AskLine({ onRead, busy }) {
  const [about, setAbout] = useState("");
  return html`<form class="shell-props__ask" onSubmit=${(e) => { e.preventDefault(); if (about.trim() && !busy) onRead(about.trim()); }}>
    <label class="shell-field"><span class="ok-font-label">What is this project for?</span>
      <input class="ork-field" autofocus value=${about} aria-label="What is this project for?" maxlength="300" placeholder="a line is enough: a mobile app for…, our team's wiki, my design files"
        onInput=${(e) => setAbout(e.target.value)} /></label>
    <button type="submit" class="ork-btn" disabled=${!about.trim() || busy}>Read it</button>
  </form>`;
}

/** New party, first screen: the Orkmaster's proposals. `pick`: the proposal the Orkmaster's deal was pressed on (lit, brought into view); `onMore`: today's tiles and seats. */
export function Proposals({ then = "", pick = "", onMore }) {
  const [got, setGot] = useState(undefined);              // undefined: being read; null: the host would not say
  const [asked, setAsked] = useState(false);              // a line was read
  const [busy, setBusy] = useState("");
  const [sizes, setSizes] = useState({});
  const [pickedTool, setPickedTool] = useState({});        // each card's AI tool ("" the Main tool)
  const tools = useTools();
  const ork = mapData.value?.project?.orkmaster || { race: "peon", tier: "crown" };
  useEffect(() => { askProposals().then((a) => { setGot(a); if (!a) onMore(); }); }, []);
  const read = async (about) => {
    setBusy("read");
    const a = await askProposals(about);
    setBusy("");
    if (a) { setGot(a); setAsked(true); }
  };
  const make = async (p, size, card, tool = "") => {
    const z = p.sizes[size];
    const heads = then === "idea" || reducedMotion() || document.hidden ? [] : cardHeads(card, z.heads || []);
    setBusy(p.id);
    const saved = await act("ideas.goal_save", { title: p.name, about: p.line, leader: z.leader, team: z.team || [], every: [], priority: "normal", size, proposal: p.id, ...(tool ? { tool } : {}),
      ...(presetsOf().some((x) => x.id === p.id) ? { preset: p.id } : {}) });
    setBusy("");
    if (saved?.slug) savedParty(saved, heads, then);
  };
  const kind = got?.kind;
  return html`<${Modal} title="New party" onClose=${closeDialog} wide=${true} foot=${html`<button type="button" class="ork-btn" onClick=${closeDialog}>Cancel</button>`}>
    <div class="shell-props">
      <header class="shell-props__head"><${Head} race=${ork.race} tier=${ork.tier} size="mid" />
        <div class="shell-props__who"><h3 class="shell-props__title">Orkmaster proposes <span class="ok-tone-muted">for this project</span></h3>
          ${kind && html`<p class="shell-props__kind ok-tone-muted">${[kind.words, ...(kind.signs || [])].filter(Boolean).join(" · ")}</p>`}</div></header>
      ${got === undefined && html`<p class="ok-tone-muted" role="status">Reading the project…</p>`}
      ${got && (got.ask || asked) && html`<${AskLine} onRead=${read} busy=${busy === "read"} />`}
      ${got && asked && got.read === false && html`<p class="shell-props__unread ok-font-status ok-tone-muted" role="status">No model could read the line: these are the proposals for code.</p>`}
      ${got && html`<div class="shell-props__cards" role="group" aria-label="Orkmaster proposes">${got.proposals.map((p) => html`<${Proposal} key=${p.id} p=${p} size=${sizes[p.id] || "standard"}
        setSize=${(s) => setSizes({ ...sizes, [p.id]: s })} make=${make} busy=${!!busy} asked=${p.id === pick}
        tools=${tools} tool=${pickedTool[p.id] || ""} setTool=${(t) => setPickedTool({ ...pickedTool, [p.id]: t })} />`)}</div>`}
      <div class="shell-props__more"><button type="button" class="ork-btn" onClick=${onMore}>More: the library</button></div>
    </div>
  <//>`;
}
