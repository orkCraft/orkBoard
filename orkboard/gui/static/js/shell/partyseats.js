// The right half of New party and Edit the party (docs/specs/91-the-owners-list.md §7, decisions §107.5): the team by seats, in three bands — **Leads** (plans the party's goals), **Does** (does the work),
// **Checks** (checks before it lands), each with *k of n seats*. A seat is a row: its head (race by craft, gear by tier), its role in semibold, *<Tier> <race> · what it does*, a chip when the role needs
// something its AI tool must make (*needs pictures*), **Its AI tool** (a button showing the tool's mark and name, the party's by default: it opens the list of seattool.js) and × (*Remove … from the
// party*). A free seat is a dashed row, *Add a member* · *Add a checker* · *Choose a leader*, that opens a short list of the library's roles for that band (Esc closes it). Ideation's seats stay as
// they are (its views and the Skeptic whole). A seat past the leader's seats (a party made before) is marked and says so.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Icon, RACE_WORDS, TIER_WORDS } from "../orkui.js";
import { roles } from "./store.js";
import { TASKMASTER, IDEATION_STAYS, agentOf, overfull, raceOfAgent, stageWord } from "./party.js";
import { seatsOf, tierOf } from "./partymodel.js";
import { SeatTool } from "./seattool.js";
import { NeedsChip, Pop } from "./partypop.js";

const BANDS = [["lead", "Leads", "plans the party's goals"], ["build", "Does", "does the work"], ["check", "Checks", "checks before it lands"]];
const PITCH = { lead: "decides on each pitch", build: "each reads every pitch, alone", check: "makes the case against" };      // what Ideation's bands do (spec 65 §1)
const ADD = { lead: "Choose a leader", build: "Add a member", check: "Add a checker" };
const SHOWN = 6;                       // the roles a list shows before *More roles*

const library = () => roles.value?.library || [];

/** The words under a role's name: *Seasoned ork · Writes the code a task asks for, with its tests*. */
const caption = (a, tier) => `${TIER_WORDS[tier] || ""} ${RACE_WORDS[raceOfAgent(a)] || ""}${a.line ? ` · ${a.line}` : ""}`.trim();

/** The roles a band's list offers, the most needed first: the preset's candidates, then the leader's craft, then the rest; none already in the party and none of Ideation's. */
function candidates(band, d) {
  const taken = new Set([d.leader, ...d.team]), want = band === "lead" ? [] : d.pool[band] || [], craft = agentOf(d.leader)?.craft;
  const rank = (a) => (want.includes(a.id) ? want.indexOf(a.id) : a.craft === craft ? 100 : 200);
  return library().filter((a) => a.band === band && !a.pitch && !taken.has(a.id)).sort((x, y) => rank(x) - rank(y));
}

/** The list of a free seat: a short list of roles (*More roles* shows the rest); a press puts the role in the seat. */
function AddList({ band, d, onPick, onClose }) {
  const [all, setAll] = useState(false), rows = candidates(band, d), shown = all ? rows : rows.slice(0, SHOWN), box = useRef();
  useEffect(() => { if (all) box.current?.querySelector("button")?.focus(); }, [all]);              // *More roles* is gone: the focus stays in the list
  return html`<${Pop} label=${ADD[band]} onClose=${onClose} cls="shell-pop--roles" boxRef=${box}>
    ${shown.map((a) => html`<button type="button" key=${a.id} class="shell-team-row" data-agent=${a.id} onClick=${() => onPick(a.id)}>
      <${Head} race=${raceOfAgent(a)} tier=${a.tier} /><b>${a.name}${a.check && html`<span class="shell-check-badge">checks</span>`}</b>
      <small class="ok-tone-muted">${caption(a, a.tier)}</small>${(a.needs || []).length > 0 && html`<${NeedsChip} role=${a} />`}</button>`)}
    ${!rows.length && html`<p class="ok-tone-muted shell-pop__none">No other role of the library fits this seat.</p>`}
    ${!all && rows.length > SHOWN && html`<button type="button" class="ork-btn quiet shell-pop__more" onClick=${() => setAll(true)}>More roles (${rows.length - SHOWN})</button>`}
  <//>`;
}

/** A seat that is taken: the head, the role, its tier and race and what it does, what it needs, its AI tool and ×. `fixed`: Ideation's seats stay. */
function Seat({ id, band, d, api, tools, fixed, leave, over = false }) {
  const a = agentOf(id) || { id, name: id, craft: "engineering", tier: "warrior", line: "" }, tier = tierOf(id, api.tiers), race = raceOfAgent(a);
  const away = id === TASKMASTER ? null : fixed ? null : html`<button type="button" class="ork-btn shell-seat__x" data-act="remove" aria-label=${`Remove ${a.name} from the party`} title=${`Remove ${a.name} from the party`}
    onClick=${() => leave(id)}><${Icon} name="close" /></button>`;
  return html`<div class=${cls("shell-seat", { "is-lead": band === "lead" })} data-seat=${id} data-band=${band}>
    <span class=${`shell-team-seat${over ? " is-over" : ""}`}><${Head} race=${race} tier=${tier} /></span>
    <div class="shell-seat__who"><b>${a.name}</b>${a.check && html`<span class="shell-check-badge">checks</span>`}<small class="ok-tone-muted">${caption(a, tier)}</small></div>
    <${NeedsChip} role=${a} />
    ${id !== TASKMASTER && html`<${SeatTool} tools=${tools} partyTool=${d.tool} role=${a} tier=${tier} value=${d.seatTools[id] || ""} onPick=${(t) => api.seatTool(id, t)} />`}
    ${away}</div>`;
}

/** A free seat: a dashed row that opens the band's list. */
function Free({ band, d, api }) {
  const [open, setOpen] = useState(false);
  return html`<div class="shell-seat-free">
    <button type="button" class="shell-seat is-empty" data-free=${band} aria-haspopup="true" aria-expanded=${String(open)} onClick=${() => setOpen(!open)}>
      <span class="shell-team-seat is-empty"></span><span class="shell-seat__add"><${Icon} name="plus" /> ${ADD[band]}</span></button>
    ${open && html`<${AddList} band=${band} d=${d} onClose=${() => setOpen(false)} onPick=${(id) => { setOpen(false); api.add(band, id); }} />`}</div>`;
}

/** The three bands. `api`: usePartyDraft(); `tools`: ideas.tools (null: no tool button); `canLeave(id)`: "" or why a member cannot leave (it has work open). */
export function Bands({ api, tools, canLeave = () => "" }) {
  const d = api.d, fixed = api.fixed, seats = seatsOf(d.leader, d.team), over = overfull(d.leader, d.team);
  const [note, setNote] = useState("");
  const leave = (id) => { const why = canLeave(id); setNote(why); if (!why) api.remove(id); };
  return html`<div class="shell-bands" role="group" aria-label="The team">${BANDS.map(([band, words, what]) => {
    const mine = band === "lead" ? [d.leader] : d.team.filter((s) => (agentOf(s)?.band || "build") === band);
    const real = band === "lead" ? mine.filter((x) => x !== TASKMASTER) : mine, free = Math.max(0, seats[band] - real.length), past = over.find((x) => x.band === band);
    return html`<section key=${band} class=${`shell-band shell-party-band band-${band}`} aria-label=${words} data-band=${band} data-stage=${stageWord(d.leader, band)}>
      <div class="shell-band-head"><h3>${words}</h3><small class="ok-tone-muted">${fixed ? PITCH[band] : what}</small>
        <small class="shell-band__seats ok-tone-muted" data-seats=${band}>${Math.max(real.length, band === "lead" ? 1 : 0)} of ${seats[band]} seats</small></div>
      ${mine.map((id, i) => html`<${Seat} key=${id} id=${id} band=${band} d=${d} api=${api} tools=${tools} fixed=${fixed} leave=${leave} over=${band !== "lead" && !fixed && i >= seats[band]} />`)}
      ${!fixed && Array.from({ length: band === "lead" ? (d.leader === TASKMASTER ? 1 : 0) : free }, (_, i) => html`<${Free} key=${`free${i}`} band=${band} d=${d} api=${api} />`)}
      ${past && html`<p class="shell-band-over" role="alert">${past.text}</p>`}</section>`;
  })}
    ${fixed && html`<p class="ok-tone-muted shell-band-fixed">${IDEATION_STAYS}</p>`}
    ${note && html`<p class="shell-size__note ok-font-status ok-tone-error" role="alert">${note}</p>`}</div>`;
}
