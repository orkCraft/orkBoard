// The first open as four cards (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md G, decisions §254.8; mockup docs/mockups/table-edge/ section 7): while the project is not laid (realm/first_open.py `step` is not `laid`) and has no
// parties of its own, the wide frame is **the room, dark**: no table, no hand, no edge, **the Orkmaster in its middle** (48 x 44), its bubble *I'm the Orkmaster. Four cards, and we start.*, **holding the backs** (orkUI's one back, `.ork-card-back`, fanned) of the steps
// not done: the AI tools (a tool already in the hand: no card), the project, the table, the hand. **The Orkmaster throws them one at a time** (the first after a beat, or at once when the fan is pressed; each next when the card before it is answered), and each
// **flies to its place, and the place appears as it lands** (one motion, table/flight.js's way, the Web Animations API on a copy; under reduced motion no flight: the place appears):
//   1. **the potions' place**, the edge's foot: the tools' adding card (hand/addtool.js) lifted there, a ready tool one press *Use <tool>*; the first potion fills.
//   2. **the portal's place**, the edge's top: the ring appears, asleep; the project's card (hand/setupcards.js) and, once a folder is open, **its release branch** (`first_open.branch`: read from git, `main` by default; a press lists the local branches; the one
//      picked is kept as the project's main, the one the portal sends into and the gate reads). GitHub: later (§254.12).
//   3. **the table**: the kind's card and **the parties as empty chairs at its far side** (orkUI's `.ork-chair.is-empty`, `ideas.party_presets` of the project's kind and stage); a chair pressed seats its leader, its size and seats said under its head (§232's
//      line); **Start** saves the seated parties (`ideas.goal_save`), throws the last back to the hand and lays the table (`ideas.project_ask`, §232.1; table/laying.js plays the laying).
//   4. **the hand**: the + card's card opens (hand/pluscard.js `Field`) **with its corners lit one at a time as each fills** (`FirstGoal`); no tour.
// A project with parties of its own is laid at once; the second project holds no tools' card. The narrow page and the phone keep the first open of spec 130 (the cards in the hand).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { command, town } from "../link.js";
import { Chair, Chev, Head, Icon } from "../orkui.js";
import { ask } from "../board/store.js";
import { refreshShell } from "../shell/store.js";
import { currentProject } from "../shell/projects.js";
import { closeOver, lift, lifted, openOver, over } from "./state.js";
import { faceOf } from "./kinds.js";

import { Menu } from "../table/menu.js";
import { openReport } from "../hand/logsbtn.js";
import { columnOn } from "../table/data.js";
import { laidNow, layLine, laying } from "../table/laying.js";
import { Mana } from "../hand/mana.js";
import { AddTool } from "../hand/addtool.js";
import { ADD_TOOL, fieldOpen, liftKey } from "../hand/state.js";
import { reading, setupNow, SetupCard } from "../hand/setupcards.js";
import { reduced, spring, tokenMs } from "../hand/motion.js";
import { SIZES, headOf, seatsOf } from "../table/partyseats2.js";
import { openParties } from "../table/parties.js";

export const SLOTS = ["potions", "ring", "table", "hand"];
export const HELLO = "I'm the Orkmaster. Four cards, and we start.";
const COUNT = ["No cards", "One card", "Two cards", "Three cards", "Four cards"];
const BEAT_MS = 1400;                                            // the room as it opens, before the Orkmaster throws its first card
const STAGES = ["idea", "being_made", "live"];

export const starting = signal(false);                           // Start was pressed: the room stays until the table is laid (the parties made already lay it, realm/first_open.py `laid`)
export const firstGoal = signal(false);                          // the first goal's card is open from the room: its corners are lit one at a time (`FirstGoal`)

/** The room is drawn: the wide frame (the edge's width, not a phone), a host with a first open (`tools` in its snapshot), the table not laid yet, or being laid by the room's Start. */
export const roomOn = () => columnOn() && !!town.value?.tools && (!laidNow() || starting.value);

/** A place opened from the Orkmaster's menu (Settings, Files) lies over the room as it lies over the pane (frame/place.js), its title and ← at its top; closed, the room is as it was. */
function RoomOver() {
  const o = over.value, Face = o && faceOf(o.kind);
  useEffect(() => {                                              // Esc goes back to the room, as it goes back to the map over the pane
    if (!o) return undefined;
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented && !e.target?.closest?.("[data-pop], .hand-pick")) { e.preventDefault(); closeOver(); } };
    addEventListener("keydown", esc);
    return () => removeEventListener("keydown", esc);
  }, [o?.kind]);
  if (!o) return null;
  return html`<section class="fo-over ork-table" aria-label=${o.title || o.kind}>
    <header class="ork-head table-title"><button type="button" class="ork-btn quiet table-title__back" aria-label="Back" title="Back" onClick=${closeOver}><${Icon} name="arrow-left" /></button>
      <span class="table-title__pt" data-title>${o.title}</span></header>
    <div class="table-over" data-kind=${o.kind}>${Face ? html`<${Face} key=${o.kind} props=${o.props || {}} close=${closeOver} />` : null}</div>
  </section>`;
}

/** The Orkmaster's menu in the room's corner: what the pane's title holds when the table is laid (table/pane.js). */
function RoomMenu() {
  const from = { title: "", key: "" };
  const items = [["Settings", () => openOver("settings", {}, from, "Settings"), false, "sliders"], ...(currentProject.value ? [["Files", () => openOver("files", {}, from, "Files"), false, "folder"]] : []),
    ["Report a problem…", () => openReport(), false, "sign:bug"]];
  return html`<div class="fo-menu"><${Menu} label="The Orkmaster's menu" items=${items} /></div>`;
}

/** The slot a step belongs to: the tools the potions', the project and its git the portal's, the kind and the parties the table's; `laid` the hand's. */
export const slotOf = (step) => (step === "tools" ? 0 : step === "project" || step === "git" ? 1 : step === "kind" || step === "parties" ? 2 : 3);

/** One card flies from the Orkmaster's fan to its place: a copy of a back, over everything, the place's box its end. Resolves when it has landed (at once under reduced motion, or with no box to fly to). */
async function fly(from, to) {
  if (!from || !to || !to.width || reduced() || document.hidden || typeof Element.prototype.animate !== "function") return;
  const g = document.createElement("span");
  g.className = "ork-card-back small fo-flyer";
  g.setAttribute("aria-hidden", "true");
  g.style.cssText = `position:fixed;left:${from.left}px;top:${from.top}px;width:${from.width}px;height:${from.height}px;margin:0;z-index:90;pointer-events:none;transform-origin:0 0;`;
  document.body.appendChild(g);
  try {
    const dx = to.left + to.width / 2 - (from.left + from.width / 2), dy = to.top + to.height / 2 - (from.top + from.height / 2);
    await g.animate([{ transform: "none" }, { transform: `translate(${dx * 0.3}px, ${dy * 0.3 - 40}px) rotate(-8deg)`, offset: 0.4 }, { transform: `translate(${dx}px, ${dy}px) rotate(4deg) scale(0.9)`, opacity: 0.4 }],
      { duration: tokenMs("--ork-motion-play", 400) * 1.3, easing: spring(), fill: "forwards" }).finished;
  } catch { /* the flight was cut: the place appears all the same */ } finally { g.remove(); }
}

/** The fan's top back: where a card thrown starts. */
const fanBox = (root) => (root?.querySelector(".fo-fan > .ork-card-back:last-child") || root?.querySelector(".fo-om"))?.getBoundingClientRect() || null;
const placeBox = (root, slot) => root?.querySelector(`[data-place="${slot}"]`)?.getBoundingClientRect() || null;

/** The ring as the portal draws it asleep (table/portal.js, orkUI's `.ork-portal-ring`): the room has no gate to read yet, so it is drawn, not pressed. */
const RingAsleep = () => html`<div class="portal-host is-ring is-asleep fo-ring" data-portal="asleep"><span class="ork-portal-ring" aria-hidden="true"><span class="ork-portal-ring__seal"></span></span></div>`;

/** *Release branch* on the project's card: the branch read from git (`main` by default); a press lists the local branches, the one picked is kept (`first_open.branch`). Nothing with no git yet. */
export function ReleaseBranch({ path }) {
  const [got, setGot] = useState(null), [open, setOpen] = useState(false), [why, setWhy] = useState("");
  useEffect(() => {
    let live = true;
    command("first_open.branch", {}, true).then((r) => { if (live && r && !r.error) setGot(r); }).catch(() => {});
    return () => { live = false; };
  }, [path]);
  if (!got?.branch) return null;
  const pick = async (branch) => {
    setOpen(false);
    if (branch === got.branch) return;
    const r = await command("first_open.branch", { branch }, true).catch((e) => ({ error: e.message }));
    if (r?.error) setWhy(r.error); else { setWhy(""); setGot(r); }
  };
  const keys = (e) => { if (e.key === "Escape" && open) { e.preventDefault(); e.stopPropagation(); setOpen(false); } };
  return html`<div class="fo-branch" onKeyDown=${keys}>
    <span class="fo-branch__row"><span class="ork-label">Release branch</span>
      <button type="button" class="ork-chip fo-branch__btn" data-release-branch=${got.branch} aria-haspopup="true" aria-expanded=${String(open)} aria-label=${`Release branch: ${got.branch}, change it`} onClick=${() => setOpen(!open)}>${got.branch}<${Chev} /></button></span>
    ${open && html`<div class="hand-pick fo-branch__list" role="menu" aria-label="The local branches">${got.branches.map((b) => html`<button type="button" key=${b} role="menuitemradio" class=${cls("hand-pick__item", { "is-checked": b === got.branch })}
        aria-checked=${String(b === got.branch)} data-branch=${b} onClick=${() => pick(b)}><span class="hand-pick__word">${b}</span></button>`)}</div>`}
    <span class="cap fo-muted">The branch the portal sends into. GitHub: later.</span>
    ${why && html`<p class="cap is-danger" role="alert">${why}</p>`}
  </div>`;
}

/** The project's card once its folder is open: its name and path, its release branch, **Go on**. */
function ProjectOpen({ onGo }) {
  const p = currentProject.value;
  return html`<article class="ork-card hand-card--big hand-tool fo-card fo-at-ring" role="dialog" aria-label="The project" data-setup="ring">
    <div class="hand-tool__top"><span class="ork-label">The project</span></div>
    <div class="fo-q"><p class="body">${p?.name || ""}</p><${Head} race="peon" tier="crown" size="mid" /></div>
    <p class="cap fo-muted">${p?.path || ""}</p>
    <${ReleaseBranch} path=${p?.path || ""} />
    <span class="fo-row"><button type="button" class="ork-btn primary" data-ring-go="1" autofocus onClick=${onGo}>Go on</button></span>
  </article>`;
}

/** The parties the table offers: `ideas.party_presets` of the stage's group, at the project's stage, Release (locked, always Lean) left out; asked once the kind is answered (`on`: asked before, the host would write General's pages into the
 *  folder the kind is read from), again for another project. */
function usePresets(key, on) {
  const [got, setGot] = useState(null);
  useEffect(() => {
    if (!on) { setGot(null); return undefined; }
    let live = true;
    Promise.all([command("ideas.stage", {}, true).catch(() => null), command("ideas.party_presets", {}, true).catch(() => null)]).then(([st, pr]) => {
      if (!live) return;
      const at = STAGES.indexOf(st?.stage || "idea");
      setGot((pr?.presets || []).filter((p) => p && p.group === "stage" && !p.locked && STAGES.indexOf(p.stage) <= Math.max(0, at)));
    });
    return () => { live = false; };
  }, [key, on]);
  return got;
}

/** What a seated party's chair says under its head (§232's line): its size, who does and who checks. */
export function seatLine(p) {
  const size = p.size || "standard", v = { p, squad: p.squad || [], tiers: {} }, word = (SIZES.find(([id]) => id === size) || [size, size])[1];
  if (size === "lean") return `${word} · 1 does · the leader accepts`;
  const does = seatsOf(v, "build", size).on.length, checks = seatsOf(v, "check", size).on.length;
  return `${word} · ${does} ${does === 1 ? "does" : "do"} · ${checks ? `${checks} ${checks === 1 ? "checks" : "check"}` : "the leader accepts"}`;
}

/** The parties as chairs at the table's far side: empty until pressed, then its leader sits on it. */
function Chairs({ presets, seated, onSeat, busy }) {
  if (!presets) return null;
  return html`<ul class="fo-chairs" aria-label="The parties">${presets.map((p) => {
    const on = seated.includes(p.id), head = headOf({ p, tiers: {} }, p.leader, p.size || "standard", true);
    return html`<li key=${p.id}><button type="button" class=${cls("fo-chair", { "is-seated": on })} data-chair=${p.id} aria-pressed=${String(on)} disabled=${busy}
        aria-label=${on ? `${p.name}: seated, ${seatLine(p)}. Press to stand its leader up` : `${p.name}: an empty chair. Press to seat its leader`} onClick=${() => onSeat(p.id)}>
      ${on ? html`<${Head} race=${head.race} tier=${head.tier} /><${Chair} />` : html`<${Chair} empty=${true} />`}
      <span class="fo-chair__name">${p.name}</span>${on && html`<span class="cap fo-chair__line">${seatLine(p)}</span>`}
    </button></li>`;
  })}</ul>`;
}

/** The parties' card on the table, after the kind: the line, **Start**; *Sizes and AI tools…* opens the Orkmaster's large card of the parties over the room (table/parties.js, §232.6), for a party's size, its seats and its tool before Start. */
function StartCard({ n, busy, onStart }) {
  return html`<article class="ork-card hand-card--big hand-tool fo-card fo-at-table" role="dialog" aria-label="The parties" data-setup="parties">
    <div class="hand-tool__top"><span class="ork-label">The parties</span></div>
    <div class="fo-q"><p class="body">${n ? "Start lays the table with them." : "Who shall work on it? Press a chair to seat its leader."}</p><${Head} race="peon" tier="crown" size="mid" /></div>
    <span class="fo-row"><button type="button" class="ork-btn primary" data-act="start" disabled=${busy || !n} onClick=${onStart}>Start</button>
      <button type="button" class="ork-btn quiet" data-act="parties" disabled=${busy} onClick=${() => openParties({ first: true }, { title: "", key: "" })}>Sizes and AI tools…</button></span>
  </article>`;
}

/** The room. Mounted by the frame (frame.js) in place of the table, the hand and the edge while `roomOn()`. */
export function Room() {
  const root = useRef(), s = setupNow.value, step = s?.step || "";
  const st = useRef(null), [, tick] = useState(0), redraw = () => tick((n) => n + 1);
  const [armed, setArmed] = useState(reduced()), [confirmed, setConfirmed] = useState(false), [seated, setSeated] = useState([]), [busy, setBusy] = useState(false);
  if (st.current === null && s) {                                // what the room holds is set by the first answer: the steps done already are places from the start, their cards not held
    const start = slotOf(step);
    st.current = { start, thrown: new Set(SLOTS.map((_, i) => i).filter((i) => i < start)), landed: new Set(SLOTS.map((_, i) => i).filter((i) => i < start)), flying: false, sawRing: false };
  }
  const r = st.current, raw = slotOf(step);
  if (r && raw === 1 && r.landed.has(1)) r.sawRing = true;
  const hold = !!r && r.sawRing && !confirmed && raw === 2, slot = hold ? 1 : raw;          // a folder opened from the card: its release branch is said before the table comes
  const presets = usePresets(currentProject.value?.path || "", step === "parties");
  useEffect(() => { if (armed) return undefined; const t = setTimeout(() => setArmed(true), BEAT_MS); return () => clearTimeout(t); }, []);
  const land = (i) => { r.landed.add(i); r.flying = false; redraw(); };
  const throwTo = async (i) => {
    r.thrown.add(i);
    r.flying = true;
    redraw();
    await fly(fanBox(root.current), placeBox(root.current, SLOTS[i]));
    land(i);
  };
  useEffect(() => {                                              // the Orkmaster throws the next card when its step has come and nothing flies
    if (!r || !armed || r.flying) return;
    const next = [0, 1, 2].find((i) => i >= r.start && !r.thrown.has(i));
    if (next !== undefined && next <= slot) throwTo(next);
  });
  const tools = r?.landed.has(0) && step === "tools";
  const toolKey = liftKey(ADD_TOOL), liftedOnce = useRef(false);
  useEffect(() => { if (tools && !liftedOnce.current) { liftedOnce.current = true; lift(toolKey); } }, [tools]);      // the tools' card lands lifted, as the adding card is lifted from the empty slot
  const seat = (id) => setSeated((was) => (was.includes(id) ? was.filter((x) => x !== id) : [...was, id]));
  const start = async () => {
    setBusy(true);
    starting.value = true;
    try {
      for (const p of (presets || []).filter((x) => seated.includes(x.id))) {
        if (!(await ask("ideas.goal_save", { title: p.name, about: p.line, leader: p.leader, team: p.squad || [], every: [], size: p.size, preset: p.id }))) return;
      }
      await throwTo(3);                                          // the last back to the hand: it lands where the hand will lie
      await refreshShell();
      if (await ask("ideas.project_ask", {})) firstGoal.value = true;          // the + card's card opens once the table is laid (`FirstGoal`)
    } finally { starting.value = false; setBusy(false); }
  };
  if (!r) return html`<div ref=${root} class="fo-stage"><div class="fo-om"><${Head} race="peon" tier="crown" size="big" /></div></div>`;
  const held = SLOTS.map((_, i) => i).filter((i) => i >= r.start && !r.thrown.has(i)), out = r.thrown.size > r.start;
  const line = !out ? (r.start === 0 ? HELLO : `I'm the Orkmaster. ${COUNT[held.length]}, and we start.`) : reading.value ? `Reading ${reading.value}` : hold ? `${currentProject.value?.name || "The project"} is open. Its release branch is the one the portal sends into.` : s?.line || "";
  const at = (i) => r.landed.has(i);
  const card = r.flying || over.value ? null                    // a place open over the room (the parties' large card, Settings) stands for the card under it
    : slot === 0 && at(0) ? null
    : slot === 1 && at(1) ? (hold ? html`<${ProjectOpen} onGo=${() => setConfirmed(true)} />` : html`<${SetupCard} at="ring" />`)
    : slot === 2 && at(2) ? (step === "kind" ? html`<${SetupCard} at="table" />` : html`<${StartCard} n=${seated.length} busy=${busy} onStart=${start} />`)
    : null;
  return html`<div ref=${root} class=${cls("fo-stage", { "is-out": out })} data-backs=${held.length} data-slot=${SLOTS[slot]}>
    <div class=${cls("fo-table ork-table", { "is-landed": at(2) })} data-place="table" aria-hidden=${at(2) ? undefined : "true"}>
      ${at(2) && html`<${Chairs} presets=${presets} seated=${seated} onSeat=${seat} busy=${busy || step !== "parties"} />`}
    </div>
    <aside class=${cls("fo-edge", { "is-landed": at(0) || at(1) })} aria-label="The table's edge">
      <div class=${cls("fo-place", { "is-landed": at(1) })} data-place="ring">${at(1) && html`<${RingAsleep} />`}</div>
      <div class=${cls("fo-place fo-place--potions", { "is-landed": at(0) })} data-place="potions">${at(0) && html`<${Mana} lifted=${null} />`}</div>
    </aside>
    <div class=${cls("fo-place fo-place--hand", { "is-landed": at(3) })} data-place="hand" aria-hidden="true"></div>
    <div class="fo-om">
      <div class="fo-bubble fo-room-bubble" role="status" aria-live="polite" data-step=${out ? step : "hello"}><span class="ork-label">Orkmaster</span><p class=${reading.value ? "ork-think" : undefined}>${line}</p></div>
      <${Head} race="peon" tier="crown" size="big" />
      ${held.length > 0 && html`<button type="button" class="fo-fan" data-fan=${held.length} aria-label=${`The Orkmaster holds ${COUNT[held.length].toLowerCase()}: throw the next`} disabled=${armed || r.flying}
          onClick=${() => setArmed(true)}>${held.map((i) => html`<span key=${i} class="ork-card-back small" data-back=${SLOTS[i]}></span>`)}</button>`}
    </div>
    <${RoomMenu} />
    <${RoomOver} />
    <footer class="hand fo-hand" aria-label="The Orkmaster's cards">
      ${card}
      ${lifted.value === toolKey && html`<${AddTool} />`}
    </footer>
  </div>`;
}

/** The first goal's card, opened from the room: its corners light one at a time, the first not filled yet (the rune, the kind, who), then **Now**; it ends when the card closes. Mounted by the frame once the table is laid. */
export function FirstGoal() {
  const on = firstGoal.value && !laying.value;
  useLayoutEffect(() => {
    if (!on) return undefined;
    if (!document.querySelector(".hand-field")) fieldOpen.value = true;          // the laying has played (table/laying.js): the + card grows into its card
    let seen = false;
    const mark = () => {
      const field = document.querySelector(".hand-field");
      if (!field) { if (seen) firstGoal.value = false; return; }
      seen = true;
      if (layLine.peek()) layLine.value = "";                     // the card is open: the laid table's line has nothing left to say (no tour)
      const corners = ["rune", "type", "to"].map((id) => field.querySelector(`[data-corner="${id}"]`)).filter(Boolean);
      const next = corners.find((c) => c.getAttribute("data-set") !== "1") || field.querySelector('[data-go="now"]');
      for (const el of field.querySelectorAll("[data-first-lit]")) if (el !== next) el.removeAttribute("data-first-lit");
      if (next && !next.hasAttribute("data-first-lit")) next.setAttribute("data-first-lit", "1");
    };
    const watch = new MutationObserver(mark);
    watch.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-set"] });
    mark();
    return () => { watch.disconnect(); for (const el of document.querySelectorAll("[data-first-lit]")) el.removeAttribute("data-first-lit"); };
  }, [on]);
  return null;
}
