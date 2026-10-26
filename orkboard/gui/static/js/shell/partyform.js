// New party and Edit the party are one dialog in two halves (docs/specs/91-the-owners-list.md §7, decisions §107.5): **left**, the presets (partypresets.js); **right**, the name and *What it is for*, the size
// switch with the party's AI tool, and the team by seats in the bands *Leads*, *Does*, *Checks* (partyseats.js) — the seats and their tiers change at once with a preset or a size (partydraft.js) —,
// what the party costs a goal and what it can take, the checks on every goal, the priority. `usePartyForm` holds all of it for either dialog (goalwizard.js, goaldialog.js); `PartyBody` draws it.
// What the dialog sends is the dialog's to say: the party's leader, team, size and AI tool, and `tools` for the seats whose tool is not the party's (`seatTools`). The host gives the tiers of the size.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";
import { mapData, roles } from "./store.js";
import { ReleasesFrom, useReleasesFrom } from "./release.js";
import { SizeBar } from "./partysize.js";
import { proposalsOn, askProposals } from "./proposals.js";
import { useTools, runsOwn } from "./toolpick.js";
import { Presets } from "./partypresets.js";
import { Bands } from "./partyseats.js";
import { usePartyDraft } from "./partydraft.js";
import { recOf, sizedTeam, usePresets, seatsOf } from "./partymodel.js";
import { TASKMASTER, PriceLine, CanTake, ChecksBlock, agentOf, overfull, pitchParty, useOwnParties, usePartyPrice } from "./party.js";

export const FOR_HINT = "goes first when the window is short";
export const PRIORITIES = [["high", "High"], ["normal", "Normal"], ["low", "Low"]];
const bandOf = (id) => agentOf(id)?.band || "build";

/** A proposal of the Orkmaster's deal as a preset (it is not one of the list's): its leader and its seats at Full, builders and checkers apart. */
function fromProposal(p) {
  const full = p.sizes?.full || p.sizes?.standard || {}, team = full.team || [];
  return { id: p.id, name: p.name, line: p.line, group: "stage", stage: "", recipe: p.id, whole: false, leader: full.leader, build: team.filter((s) => bandOf(s) === "build"), check: team.filter((s) => bandOf(s) === "check") };
}

/** A party of the library that the list does not hold (the mixed Game, Mobile app and Website, which a deal's card may still ask for) as a preset: its seats as the library has them. */
const fromLibrary = (id) => {
  const p = (roles.value?.presets || []).find((x) => x.id === id);
  return p ? { id: p.id, name: p.name, line: p.line, group: "craft", stage: "", craft: p.craft, recipe: "", whole: false, leader: p.lead, build: p.build, check: p.check } : null;
};

/** The seats an existing party could have: its own, and the rest of its recipe's (`ideas.party_sizes`'s Full), so a size picked in Edit the party can seat them again. */
function useFullRec(slug, team, set) {
  useEffect(() => {
    if (!slug) return undefined;
    let live = true;
    command("ideas.party_sizes", { slug }, true).then((a) => {
      const full = a?.sizes?.full?.team;
      if (!live || !Array.isArray(full)) return;
      set((was) => { const mine = recOf(was.team), more = recOf(full), rec = { build: [...new Set([...mine.build, ...more.build])], check: [...new Set([...mine.check, ...more.check])] }; return { rec, pool: rec }; });
    }).catch(() => {});
    return () => { live = false; };
  }, [slug]);
}

/** Everything the dialog holds. `edit`: the party being edited (`ideas.board`'s track), else a new party; `first`: the preset asked for by id, `proposal`: the deal's proposal pressed. */
export function usePartyForm({ edit = null, first = "", proposal = "" }) {
  const sized = proposalsOn();
  const shown = edit ? (mapData.value?.goals || []).find((x) => x.slug === edit.slug) : null;       // the Map's party: its size, its members' work
  const [title, setTitle] = useState(edit?.title || "");
  const [about, setAbout] = useState(edit?.about || "");
  const [priority, setPriority] = useState(edit?.priority || "normal");
  const wasTeam = edit?.team || [], wasLeader = edit?.leader?.slug || TASKMASTER;
  const api = usePartyDraft({ leader: wasLeader, team: wasTeam, every: edit?.every || [], size: edit ? shown?.size || "" : sized ? "standard" : "", craft: edit?.craft || "", tool: edit?.tool || "", tools: edit?.tools || {} });
  const d = api.d;
  const tools = useTools();
  const found = usePresets();
  const own = useOwnParties(true);
  const [note, setNote] = useState("");
  const [wanted, setWanted] = useState(proposal ? undefined : null);      // the deal's proposal the list lacks: undefined while asked, null when there is none
  const rf = useReleasesFrom(edit ? { self: edit.slug, saved: shown?.releases_from || [], leads: shown?.leader?.slug === "release-manager", offers: (shown?.types || []).some((t) => t.id === "release") }
    : { leads: d.leader === "release-manager" });
  useFullRec(edit?.slug, wasTeam, api.set);
  const presets = found?.presets || [];
  const press = (p, ifFresh = false) => { api.preset(p, ifFresh); setNote(""); };
  useEffect(() => {                                                      // a proposal of the deal that the list does not hold
    if (!proposal || edit) return;
    askProposals().then((a) => setWanted(a?.proposals?.find((x) => x.id === proposal) || null));
  }, [proposal]);
  const opened = useRef(false);                                          // New party opens on a preset once
  useEffect(() => {                                                      // New party opens on a preset: the one asked for, the proposal's, else the project's Build (a craft's Tech for an older host)
    if (edit || opened.current || !found) return;
    const ask = first || proposal, hit = presets.find((p) => p.id === ask || (proposal && p.recipe === proposal));
    if (!hit && proposal && wanted === undefined) return;               // the proposal is still being asked
    const pick = hit || (ask && fromLibrary(ask)) || (wanted && fromProposal(wanted)) || presets.find((p) => p.stage === "build") || presets.find((p) => p.id === "engineering");
    opened.current = true;
    if (pick) press(pick, true);
  }, [found, wanted]);
  const price = usePartyPrice(!!edit || !!d.lit || d.moved || !!d.partyId, d.leader, d.team, d.every, edit?.craft || d.craft || "", sized ? d.size : "")       // asked once there is a party on the seats;
  const working = (id) => (shown?.party || []).some((m) => m.slug === id && m.band !== "lead" && m.state && m.state !== "free");       // a member with work open never leaves
  const nameOf = (id) => agentOf(id)?.name || id;
  const canLeave = (id) => (edit && working(id) ? `${nameOf(id)} has work open: it cannot leave` : "");
  const pickSize = (size) => {
    const next = sizedTeam(d.rec, size, seatsOf(d.leader, d.team)), busy = d.team.filter((s) => !next.includes(s) && working(s));
    if (busy.length) { setNote(`${busy.map(nameOf).join(", ")} ${busy.length === 1 ? "has" : "have"} work open: ${busy.length === 1 ? "it cannot" : "they cannot"} leave`); return; }
    setNote("");
    api.size(size);
  };
  const fits = edit ? true : overfull(d.leader, d.team).length === 0 || !!d.partyId;       // a leader with fewer seats than the party fills: it is saved once it fits (spec 59 §6.2)
  const main = tools?.main || "claude";
  /** The seats whose AI tool is not the party's: `{agent: tool}`. */
  const seatTools = (from = d.seatTools, party = d.tool, who = [d.leader, ...d.team]) => Object.fromEntries(Object.entries(from).filter(([a, t]) => t && t !== (party || main) && who.includes(a)));
  const own_ = runsOwn(tools, d.tool);
  const suggest = edit ? "" : d.row?.name || "";                                // the pressed preset's name: the name the party is saved under when the person says neither a name nor what it is for
  return { api, d, edit, sized, title, setTitle, suggest, about, setAbout, priority, setPriority, tools, presets, kind: found?.kind || mapData.value?.project?.kind || null, own, press, price, rf, fits,
    note, setNote, pickSize, canLeave, seatTools, shownSize: shown?.size || "", runsOwn: own_, agents: 1 + d.team.length, working, ready: !!(title.trim() || about.trim() || suggest) && fits, loaded: !!found };
}

const PartyTitle = ({ f, autofocus }) => html`<div class="shell-p91__names">
  <label class="shell-field"><span class="ok-font-label">Name</span>
    <input class="ork-field" autofocus=${autofocus === "name"} value=${f.title} aria-label="Name" placeholder=${f.edit ? "The Taskmaster wrote it; correct it here" : f.suggest || "Its name, in a few words"} maxlength="120" onInput=${(e) => f.setTitle(e.target.value)} /></label>
  <label class="shell-field"><span class="ok-font-label">What it is for</span>
    <input class="ork-field" autofocus=${autofocus === "about"} value=${f.about} aria-label="What it is for" placeholder="One line: what this party is for" onInput=${(e) => f.setAbout(e.target.value)} /></label></div>`;

/** The dialog's two halves. `say`: the line under the form (who reads the repository). */
export function PartyBody({ f, say = "" }) {
  const { d, api } = f;
  return html`<div class="shell-p91">
    <${Presets} presets=${f.presets} kind=${f.kind} lit=${d.lit} onPick=${f.press}
      own=${{ parties: f.own[0], reload: f.own[1], picked: d.partyId, pick: (p) => { api.own(p); f.setNote(""); } }} />
    <div class="shell-p91__team">
      <${PartyTitle} f=${f} autofocus=${f.edit ? "about" : "name"} />
      ${f.sized && html`<${SizeBar} size=${d.size} agents=${f.agents} onPick=${f.pickSize} note=${f.note} tools=${f.tools} tool=${d.tool} onTool=${(t) => api.set({ tool: t })} />`}
      <${Bands} api=${api} tools=${f.tools} canLeave=${f.canLeave} />
      ${f.sized && f.runsOwn ? html`<p class="ok-tone-muted shell-tool__own">Runs its own model: its price is its own.</p>` : html`<${PriceLine} price=${f.price} /><${CanTake} price=${f.price} />`}
      <${ReleasesFrom} rf=${f.rf} />
      ${!pitchParty(d.leader) && html`<${ChecksBlock} team=${d.team} every=${d.every} setEvery=${api.setEvery} price=${f.price} />`}
      <div class="shell-field" role="group" aria-label="Priority"><span class="ok-font-label">Priority</span><small class="ok-tone-muted">${FOR_HINT}</small>
        <div class="shell-seg">${PRIORITIES.map(([id, name]) => html`<label key=${id} class=${`shell-seg__one${f.priority === id ? " is-on" : ""}`}>
          <input type="radio" name="priority" class="gui-onb__hide" checked=${f.priority === id} onChange=${() => f.setPriority(id)} />${name}</label>`)}</div></div>
      ${say && html`<p class="ok-font-status ok-tone-muted">${say}</p>`}
    </div></div>`;
}

/** The foot's line: how many agents, and who takes a task. */
export const footLine = (f) => `${f.agents} ${f.agents === 1 ? "agent" : "agents"} · a task goes to the one who does its kind of work, the Grunt fills in`;
