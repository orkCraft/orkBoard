// A seat's popover (docs/specs/98-the-table-and-the-hand.md §3.4, docs/specs/95-the-window-as-decided.md §2.5; decisions §110.7): a head pressed in a party's header says its role, what it does, its AI tool, its tier and
// what it costs, **Set** (a new AI tool for the seat, *From the next task*) with **Undo**, **Take off the seat**, and the role's text (**Open**, over the pane). At the narrow width it is a sheet at the foot of the pane.
// Esc or a press away closes it and the focus goes back to the head. A change is the party's: `ideas.goal_save` (its `tools`, its `team`), as Edit the party sends it.
// **Its level as three heads** (docs/specs/130-the-first-open-is-the-orkmasters.md C.4, decisions §232.6; mockup docs/mockups/setup/ #seat): the seat's race in its three gears (§158: its tier is the gear on its head), each with its word and what a task, a leader's step, costs at it (`ideas.seat_price`); under a leader on Novice a line says the cost in quality plainly. `SeatDraft` is the seat on the parties' card: a head or a mark pressed there, nothing saved until Start or Save; a seat set by hand keeps what was set and the party's size stays picked (spec 81 §2). orkUI first: the three levels' tiles.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { command, toast } from "../link.js";
import { Head, Icon, TIER_WORDS } from "../orkui.js";
import { agents } from "../shell/store.js";
import { roleOf, statsOf } from "../arena/arenawords.js";
import { ToolPick, useTools } from "../shell/toolpick.js";
import { openOver } from "../frame/state.js";
import { doesWords, groupsOf, nameOf, toolOf } from "./data.js";
import { Facts, LEADERS, bandOf, headOf, libOf, nameOf as seatName, raceOf } from "./partyseats2.js";

const TIERS = ["laborer", "warrior", "elder"];
export const NOVICE_LINE = "A leader on Novice reads less of the project before it plans: fine for a small project, weak for a large one.";

/** What the seat costs at each tier (`ideas.seat_price`): `{laborer, warrior, elder}` in dollars, {} while asked. */
function useSeatPrices() {
  const [got, set] = useState({});
  useEffect(() => { let live = true; command("ideas.seat_price", {}, true).then((a) => { if (live && a && !a.error) set(a); }).catch(() => {}); return () => { live = false; }; }, []);
  return got;
}

/** The seat's level, its race in three gears: picked by a press. */
export function Levels({ race, tier, lead, onPick, disabled = false }) {
  const prices = useSeatPrices();
  return html`<div class="pc-field"><span class="ork-label">Its level</span>
    <div class="pc-tiers" role="radiogroup" aria-label="Its level">${TIERS.map((t) => html`<button type="button" key=${t} role="radio" class=${`pc-tier${t === tier ? " is-on" : ""}`} data-tier=${t} aria-checked=${String(t === tier)} disabled=${disabled} onClick=${() => t !== tier && onPick(t)}>
      <${Head} race=${race} tier=${t} size="mid" />${TIER_WORDS[t]}${prices[t] != null && html`<small>≈$${Number(prices[t]).toFixed(2)} ${lead ? "a step" : "a task"}</small>`}</button>`)}</div>
    ${lead && tier === "laborer" && html`<span class="pc-muted" data-novice="1">${NOVICE_LINE}</span>`}</div>`;
}

/** The AI tool of a seat on the card: the leader's is the party's (*Main tool (<name>): follows it*, then the tools in the hand), a member's its own (*As the party (<tool>)*, then the tools in the hand). */
function SeatTool({ lead, value, tools, hand, partyName, onChange }) {
  const main = tools?.tools?.find((t) => t.id === tools.main)?.name || hand?.find((h) => h.main)?.title || "";
  const rows = hand ? hand.map((h) => [h.id, h.title]) : (tools?.tools || []).filter((t) => t.ready).map((t) => [t.id, t.name]);
  return html`<label class="pc-field"><span class="ork-label">${lead ? "The party's AI tool" : "Its AI tool"}</span>
    <span class="ork-select"><select class="ork-field" name="seat-tool" value=${value} onChange=${(e) => onChange(e.target.value)}>
      <option value="" selected=${!value}>${lead ? `Main tool (${main}): follows it` : `As the party (${partyName || main})`}</option>
      ${rows.map(([id, words]) => html`<option key=${id} value=${id} selected=${id === value}>${words}</option>`)}</select></span>
    ${lead && html`<span class="pc-muted">The leader and every member set to As the party run on it.</span>`}</label>`;
}

/** A seat on the parties' card (spec 130 C.4). `v`: the party as the card has it; `onChange`: the card's own edit, sent at Start or Save. */
export function SeatDraft({ v, slug, tools, hand, onChange, onClose, from }) {
  const box = useRef(), lead = slug === v.p.leader, head = headOf(v, slug, v.size, lead), name = seatName(slug), band = lead ? "lead" : bandOf(v, slug), own = LEADERS[v.p.id];
  const partyTool = v.tool ? (hand?.find((h) => h.id === v.tool)?.title || tools?.tools?.find((t) => t.id === v.tool)?.name || v.tool) : "";
  useLayoutEffect(() => {
    const was = document.activeElement;
    box.current?.querySelector("select, button")?.focus();
    const away = (e) => { if (box.current && !box.current.contains(e.target) && !e.target.closest?.(".pc-hd, .pc-lead")) onClose(); };
    document.addEventListener("pointerdown", away, true);
    return () => { document.removeEventListener("pointerdown", away, true); if (was?.isConnected) was.focus?.(); };
  }, []);
  const setTool = (id) => {
    if (lead) { onChange({ tool: id }); return; }
    const next = { ...v.tools };
    if (id) next[slug] = id; else delete next[slug];
    onChange({ tools: next });
  };
  const off = () => { const tools_ = { ...v.tools }, tiers = { ...v.tiers }; delete tools_[slug]; delete tiers[slug]; onChange({ squad: v.squad.filter((s) => s !== slug), tools: tools_, tiers }); onClose(); };
  return html`<div class="pc-seat" ref=${box} role="dialog" aria-modal="false" aria-label=${`${name}: its seat`} data-seat-card=${slug} data-party=${v.p.id}>
    <div class="pc-seat__who"><${Head} race=${head.race} tier=${head.tier} size="big" />
      <span class="pc-seat__nm"><b>${lead && own ? `${own} · ${name}` : name}</b><span class="pc-muted">${lead ? `${v.p.name}'s leader · how, what changes and why` : `${v.p.name} · ${band === "check" ? "checks" : "does"}: ${libOf(slug)?.line || "the work"}`}</span></span></div>
    <${SeatTool} lead=${lead} value=${lead ? v.tool : v.tools[slug] || ""} tools=${tools} hand=${hand} partyName=${partyTool} onChange=${setTool} />
    <${Levels} race=${raceOf(v, lead)} tier=${head.tier} lead=${lead} onPick=${(t) => onChange({ tiers: { ...v.tiers, [slug]: t } })} />
    ${lead && v.track && html`<${Facts} party=${v.track.slug} />`}
    <div class="pc-seat__acts">${v.track && html`<button type="button" class="ork-btn quiet" onClick=${() => { onClose(); openOver("role", { slug, party: v.track.slug }, from, name); }}>Its role's text</button>`}
      ${!lead && html`<button type="button" class="ork-btn danger" data-off=${slug} title="The party works on without it" onClick=${off}>Take off the seat</button>`}
      <button type="button" class="ork-btn quiet" onClick=${onClose}>Close</button></div>
  </div>`;
}

/** *Novice · does*: the seat's tier and its role, and no word of a race (docs/specs/100-a-goals-way-as-cards.md §0). */
const tierWords = (m) => [TIER_WORDS[m.head?.tier], m.band === "lead" ? "leads" : m.band === "check" ? "checks" : "does"].filter(Boolean).join(" · ");

/** `keep`: a selector of what a press does not close it for (the table's seats; the route card's heads, whose own press toggles it: the pointerdown that closed it first would make the click open it again). */
export function SeatPop({ g, slug, from, onClose, keep = ".table-seat" }) {
  const m = groupsOf(g).flatMap((x) => x.seats).find((s) => s.slug === slug);
  const tools = useTools(), box = useRef();
  const lead = m?.band === "lead", now = m ? toolOf(g, m) : { id: "", name: "" };
  const [want, setWant] = useState(null), [was, setWas] = useState(null), [busy, setBusy] = useState(false);
  useLayoutEffect(() => {                                                        // the focus goes in, and back to the head on the way out
    const head = document.activeElement;
    box.current?.querySelector("button, select")?.focus();
    const away = (e) => { if (box.current && !box.current.contains(e.target) && !e.target.closest?.(keep)) onClose(); };
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); onClose(); } };
    document.addEventListener("pointerdown", away, true);
    window.addEventListener("keydown", esc);
    return () => { document.removeEventListener("pointerdown", away, true); window.removeEventListener("keydown", esc); if (head?.isConnected) head.focus?.(); };
  }, []);
  if (!m) return null;
  const st = statsOf(m, roleOf(agents.value, m.slug), lead);
  const team = (g.team || []).map((x) => x.slug), every = (g.team || []).filter((x) => x.every).map((x) => x.slug);
  const save = async (args, said) => {
    setBusy(true);
    try {
      const got = await command("ideas.goal_save", { slug: g.slug, ...args }, true);
      if (got?.error) toast(got.error, "error");
      else if (said) toast(said);
      return !!got && !got.error;
    } catch (e) { toast(e.message || "That could not be saved", "error"); return false; } finally { setBusy(false); }
  };
  const tools0 = () => ({ ...(g.tools || {}) });
  const set = async () => {                                                      // the seat's AI tool, from its next task
    const before = g.tools?.[m.slug] ?? "", next = { ...tools0() };
    if (want) next[m.slug] = want; else delete next[m.slug];
    if (await save({ tools: next }, `${m.name} runs on ${want ? tools?.tools.find((t) => t.id === want)?.name || want : "the party's tool"} from its next task`)) { setWas(before); setWant(null); }
  };
  const undo = async () => {
    const next = { ...tools0() };
    if (was) next[m.slug] = was; else delete next[m.slug];
    if (await save({ tools: next })) setWas(null);
  };
  const off = async () => {
    if (await save({ team: team.filter((s) => s !== m.slug), every: every.filter((s) => s !== m.slug), ...(g.leader?.slug ? { leader: g.leader.slug } : {}) }, `${m.name} is off the seat`)) onClose();
  };
  const pending = want !== null && want !== (g.tools?.[m.slug] ?? "");
  return html`<div class="ork-frame table-seatpop" role="dialog" aria-modal="false" aria-label=${`${m.name}: its seat`} ref=${box} data-seat=${m.slug}>
    <div class="table-seatpop__top">
      <span class="table-seatpop__who">${m.head && html`<${Head} race=${m.head.race} tier=${m.head.tier} size="mid" />`}
        <span class="table-seatpop__nm"><b>${m.name}</b><span class="table-seatpop__muted">${tierWords(m)}</span></span></span>
      <button type="button" class="ork-btn quiet" aria-label="Close" onClick=${onClose}><${Icon} name="close" /></button>
    </div>
    <dl class="table-facts">
      <dt>Role</dt><dd>${lead ? "Leads" : m.band === "check" ? "Checks" : "Does"} ${nameOf(g)}</dd>
      <dt>What it does</dt><dd>${doesWords(m, lead)}</dd>
      <dt>Its AI tool</dt><dd>${now.name}</dd>
      <dt>Its tier</dt><dd>${st.level}</dd>
      <dt>What it costs</dt><dd><span class="ork-gem" title=${st.priceTip}>${st.price}</span> <span class="table-seatpop__muted">${lead ? "a plan" : "a run"}</span></dd>
    </dl>
    ${m.head && html`<${Levels} race=${m.head.race} tier=${m.head.tier} lead=${lead} disabled=${busy} onPick=${(t) => save({ tiers: { [m.slug]: t } }, `${m.name} is ${TIER_WORDS[t]} from its next task`)} />`}
    ${tools && html`<${ToolPick} tools=${tools} value=${want ?? g.tools?.[m.slug] ?? ""} onChange=${setWant} id=${`seat-tool-${m.slug}`} label="Its AI tool, for the seat" />`}
    <p class="table-seatpop__muted">From the next task</p>
    <div class="table-seatpop__acts">
      <button type="button" class="ork-btn primary" disabled=${!pending || busy} onClick=${set}>Set</button>
      ${was !== null && html`<button type="button" class="ork-btn" disabled=${busy} onClick=${undo}>Undo</button>`}
      ${!lead && html`<button type="button" class="ork-btn danger" disabled=${busy} title="The party works on without it" onClick=${off}>Take off the seat</button>`}
      <button type="button" class="ork-btn" onClick=${() => { onClose(); openOver("role", { slug: m.slug, party: g.slug }, from, m.name); }}>Open</button>
    </div>
  </div>`;
}
