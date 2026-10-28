// A seat's popover (docs/specs/98-the-table-and-the-hand.md §3.4, docs/specs/95-the-window-as-decided.md §2.5; decisions §110.7): a head pressed in a party's header says its role, what it does, its AI tool, its tier and
// what it costs, **Set** (a new AI tool for the seat, *From the next task*) with **Undo**, **Take off the seat**, and the role's text (**Open**, over the pane). At the narrow width it is a sheet at the foot of the pane.
// Esc or a press away closes it and the focus goes back to the head. A change is the party's: `ideas.goal_save` (its `tools`, its `team`), as Edit the party sends it.
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { command, toast } from "../link.js";
import { Head, Icon, RACE_WORDS, TIER_WORDS } from "../orkui.js";
import { agents } from "../shell/store.js";
import { roleOf, statsOf } from "../arena/arenawords.js";
import { ToolPick, useTools } from "../shell/toolpick.js";
import { openOver } from "../frame/state.js";
import { doesWords, groupsOf, nameOf, toolOf } from "./data.js";

/** *Standard ork · does the work*: the seat's tier and race. */
const tierWords = (m) => `${TIER_WORDS[m.head?.tier] || ""} ${RACE_WORDS[m.head?.race] || ""}`.replace(/\s+/g, " ").trim();

export function SeatPop({ g, slug, from, onClose }) {
  const m = groupsOf(g).flatMap((x) => x.seats).find((s) => s.slug === slug);
  const tools = useTools(), box = useRef();
  const lead = m?.band === "lead", now = m ? toolOf(g, m) : { id: "", name: "" };
  const [want, setWant] = useState(null), [was, setWas] = useState(null), [busy, setBusy] = useState(false);
  useLayoutEffect(() => {                                                        // the focus goes in, and back to the head on the way out
    const head = document.activeElement;
    box.current?.querySelector("button, select")?.focus();
    const away = (e) => { if (box.current && !box.current.contains(e.target) && !e.target.closest?.(".table-seat")) onClose(); };
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
