// Concerns on a party's map (docs/specs/108-a-leader-says-no-and-shows-where-it-hurts.md §3, decisions §183.4–§183.5): what a party's leader says is wrong or at risk in one part of its map, with why and what would fix it.
// Painted as picking paints (picking.js): a map draws nothing of it. A card is any element carrying `data-pick-map` and `data-pick-id` (maps.js `Pickable`; System's parts stamped by syspane.js); `sync` finds the cards a record names
// (`concerns[].on` is the card's id) and gives each a mark in a slot of its own — inside the card, or, for a card that is a button (System's part), beside it in the box that holds it, so the mark scales with the System's fit and a
// button holds no button. An alert is orkUI's alert sign in the alert tone with the leader's small head beside it, a note a small dot in the muted ink; several on one card show the highest level and the count only in the label
// (*2 concerns of the Architect*). A mark is decoration over a card (a press falls through to the card, which lifts); made into a goal it becomes a link to the goal in the goal's element's colour.
// `Concerns` draws the strip over the map (the leader's head, *The Architect: 2 alerts, 3 notes*, **Ask again**; a press on the counts steps through the marked cards) and the host that paints; under the strip's line, the row of the
// aspects the leader looks at (docs/specs/109-each-leader-looks-as-a-senior-of-its-craft.md §4: the rubric's `short`, then each aspect an orkUI chip with the small mark of its state, alert, note, hint, clear or none yet; a press on one steps
// through the cards whose open concerns are of it, an aspect with no card is no button; a record with no `rubric`, from an older host, draws no row); `ConcernsBack` is the section a lifted card's back (card.js `Lifted`) gains: each
// concern's what, why and fix and its aspect beside its level (*Alert · Hotspots*), **Make it a goal** and **Not a problem**. The record is the host's (`ideas.concerns`, `ideas.concerns_again`, `ideas.concern_dismiss`, `ideas.concern_goal`);
// a host without the commands draws nothing and throws nothing. Picking wins: while a map is in picking a press is a pick, and the marks take no press.
// The slot is shared with the heat (heat.js, docs/specs/117-each-lens-a-games-shape.md §4.1): `slotOf` makes it (for a card only heat is on too), the mark lives in the slot's own box `.cn-slot__m` (so a render of the mark leaves the heat's squares
// alone), and `sync` keeps a slot while either has something in it. Under the aspects the strip says what the goal shown reaches (reach.js `ReachLine`, §4.4).
import { render } from "preact";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { Head, Sign } from "../orkui.js";
import { command } from "../link.js";
import { pick, tab } from "../frame/state.js";
import { act, mapData } from "../shell/store.js";
import { leadsSystem } from "./data.js";
import { mapOf } from "./maps.js";
import { pickFor } from "./picking.js";
import { cardEl } from "./pickbox.js";
import { ReachLine } from "./reach.js";                      // the strip's line for the goal shown (spec 117 E); reach.js and heat.js read nothing of this module while they load, so the cycle is only in their functions
import { heatNow } from "./heat.js";

if (typeof document !== "undefined") {
  const href = new URL("./concerns.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const POLL_MS = 2500;                                       // a look under way is asked after this often

// -- the records -----------------------------------------------------------------------------------------------------------------------------------------------------------------

/** Each party's record as the host last gave it (`ideas.concerns`): `{status, error, concerns: [...], dismissed}`; `{off: true}` where the host does not know the command (an older host). */
const records = signal({});
/** The goal a concern was made into in this run (`party/id` → the goal's slug), until the record says it itself. */
const made = signal({});

export const recordOf = (party) => {
  const r = records.value[party];
  return r && !r.off ? r : null;
};
const keep = (party, r) => { records.value = { ...records.peek(), [party]: r }; };

/** Reads (or answers with) a record; a host that does not answer as one is left as it was, and `{off: true}` where there is nothing yet. Returns the record or null. */
export async function read(name, party, more = {}) {
  try {
    const r = await command(name, { party, ...more }, true);
    if (r && Array.isArray(r.concerns)) { keep(party, r); return r; }
  } catch { /* an older host, or none */ }
  if (!records.peek()[party]) keep(party, { off: true });
  return null;
}

/** The goal a concern became (its slug), "" none. */
const goalOf = (party, c) => c.idea || c.goal || made.value[`${party}/${c.id}`] || "";

const levelOf = (list) => (list.some((c) => c.level === "alert") ? "alert" : "note");

/** The concerns on one card of the party's map. */
export const onCard = (party, id) => (recordOf(party)?.concerns || []).filter((c) => c.on === id);

/** *The Architect* (a name as the page names leaders, with its article once). */
export const theLeader = (name) => { const n = String(name || "Taskmaster"); return /^the\s/i.test(n) ? n : `The ${n}`; };
const ofLeader = (name) => theLeader(name).replace(/^The/, "the");

const count = (n, one, many) => `${n} ${n === 1 ? one : many}`;
export const concernWords = (n, name) => `${count(n, "concern", "concerns")} of ${ofLeader(name)}`;

/** The party's leader, as the page names and draws it: `{name, head}`. */
const leaderOf = (g) => ({ name: g?.leader?.name || "Taskmaster", head: g?.leader?.head || null });

// -- the marks -------------------------------------------------------------------------------------------------------------------------------------------------------------------

/** The mark of one card: `list` its concerns, `lead` the party's leader. Made into goals all of them: a link to the first goal, in its element's colour. */
function Mark({ party, list, lead, nodes, mid }) {
  const level = levelOf(list), label = concernWords(list.length, lead.name);
  const slugs = list.map((c) => goalOf(party, c)), all = slugs.every(Boolean), slug = all ? slugs[0] : "";
  const node = slug ? nodes.find((n) => n.slug === slug) : null;
  const face = html`${level === "alert" ? html`<${Sign} name="alert" />` : html`<i class="cn-dot" aria-hidden="true"></i>`}`;
  if (all) {
    const words = `${label}: made into the goal ${node?.title || slug}`;
    return html`<button type="button" id=${mid} class="cn-mark is-made" data-level=${level} data-elem=${node?.element || "dust"} data-nopress="" aria-label=${words} title=${`${words}. Pick the goal`}
      onClick=${(e) => { e.stopPropagation(); pick(slug); }}>${level === "alert" && lead.head && html`<${Head} race=${lead.head.race} tier=${lead.head.tier} />`}${face}</button>`;
  }
  return html`<span id=${mid} class="cn-mark" role="img" data-level=${level} data-count=${list.length} aria-label=${label} title=${`${level === "alert" ? "An alert" : "A note"}: ${label}`}>
    ${level === "alert" && lead.head && html`<${Head} race=${lead.head.race} tier=${lead.head.tier} />`}${face}</span>`;
}

/** The slot of a card: inside it, or, for a button, beside it in the box that holds it. Made, or found, or null. */
export function homeOf(card) {
  const home = card.tagName === "BUTTON" ? card.parentElement : card;
  if (home && getComputedStyle(home).position === "static") home.dataset.cnHost = "";
  return home;
}

/** The slot of a card: the box in its home where a mark and the heat's squares lie (heat.js); made when missing. `id` the card's `data-pick-id`. Null for a card with no home. */
export function slotOf(card, id) {
  const home = homeOf(card);
  if (!home) return null;
  let slot = [...home.children].find((x) => x.classList?.contains("cn-slot") && x.dataset.cnFor === id);
  if (!slot) {
    slot = document.createElement("span");
    slot.className = "cn-slot";
    slot.dataset.cnFor = id;
    home.appendChild(slot);
  }
  return slot;
}

/** The box of a slot that holds the mark (`display: contents`): a render into it leaves the heat's squares beside it alone. */
const boxOf = (slot) => {
  let box = slot.querySelector(":scope > .cn-slot__m");
  if (!box) {
    box = document.createElement("span");
    box.className = "cn-slot__m";
    slot.appendChild(box);
  }
  return box;
};

/** Paints the marks of the party's record on the cards of `host`: a mark in a slot on each card a concern is on, nothing on the others, no slot left behind (one the heat holds stays for it). `nodes`: the Board's goals (a mark made into a goal wears its element). */
export function sync(host, party, lead, nodes) {
  const by = new Map(), marked = new Set(), used = new Set();
  for (const c of recordOf(party)?.concerns || []) by.set(c.on, [...(by.get(c.on) || []), c]);
  for (const w of host.querySelectorAll("[data-pick-id]")) {
    const list = by.get(w.dataset.pickId), card = cardEl(w), home = list && homeOf(card);
    if (!list || !home) continue;
    const slot = slotOf(card, w.dataset.pickId);
    used.add(slot);
    marked.add(card);
    const mid = `cn-${party}-${encodeURIComponent(w.dataset.pickId).replace(/%/g, "_")}`, level = levelOf(list);
    if (card.dataset.concern !== level) card.dataset.concern = level;
    render(html`<${Mark} party=${party} list=${list} lead=${lead} nodes=${nodes} mid=${mid} />`, boxOf(slot));
    if (!card.hasAttribute("aria-describedby") || card.dataset.cnDesc) { card.setAttribute("aria-describedby", mid); card.dataset.cnDesc = "1"; }      // the card says it has concerns, unless it describes itself already
  }
  for (const slot of host.querySelectorAll(".cn-slot")) {
    if (used.has(slot)) continue;
    const box = slot.querySelector(":scope > .cn-slot__m");
    if (box) { render(null, box); box.remove(); }
    if (!slot.querySelector(".cn-heat")) slot.remove();
  }
  for (const el of host.querySelectorAll("[data-concern], [data-cn-desc]")) {
    if (marked.has(el)) continue;
    delete el.dataset.concern;
    if (el.dataset.cnDesc) { el.removeAttribute("aria-describedby"); delete el.dataset.cnDesc; }
  }
}

// -- the strip and the host --------------------------------------------------------------------------------------------------------------------------------------------------

/** The cards marked now, the alerts first (in the order the map draws them). */
const markedCards = () => {
  const all = [...document.querySelectorAll(".table-body [data-concern]")];
  return [...all.filter((el) => el.dataset.concern === "alert"), ...all.filter((el) => el.dataset.concern !== "alert")];
};

/** The cards whose open concerns (not yet made into goals) are of the aspect `id`, the alerts first; `cards` the cards marked now. */
const aspectCards = (party, id, cards) => {
  const on = new Set((recordOf(party)?.concerns || []).filter((c) => c.aspect === id && c.on && !goalOf(party, c)).map((c) => c.on));
  const own = new Set([...document.querySelectorAll(".table-body [data-pick-id]")].filter((w) => on.has(w.dataset.pickId)).map(cardEl));
  return cards.filter((el) => own.has(el));
};

const reduced = () => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/** What an aspect's chip says in words, by its state (`a.n` its open concerns): *Hotspots: 2 concerns*, *a hint from code*, *nothing wrong*, *not looked at yet*. */
export const aspectWords = (a) => `${a.name}: ${a.state === "alert" || a.state === "note" ? count(a.n || 1, "concern", "concerns") : a.state === "hint" ? "a hint from code" : a.state === "clear" ? "nothing wrong" : "not looked at yet"}`;

/** The small mark of an aspect's state: the alert sign in the alert tone, the muted dot, a hollow square (code noticed it), a tick (a look found nothing), nothing (not looked at yet). */
const AspectMark = ({ state }) => (state === "alert" ? html`<${Sign} name="alert" />` : state === "note" ? html`<i class="cn-dot" aria-hidden="true"></i>`
  : state === "hint" ? html`<i class="cn-hint" aria-hidden="true"></i>` : state === "clear" ? html`<${Sign} name="check" />` : null);

/** One aspect of the rubric as an orkUI chip: a button while a card of the map has an open concern of it (a press steps through those cards), else a span that is only its title. `card`: whether one has. */
function Aspect({ a, card, step }) {
  const words = aspectWords(a), title = [a.ask, ...(a.hints || [])].filter(Boolean).join("\n");
  const props = { class: "ork-chip cn-aspect", "data-state": a.state, "data-aspect": a.id, "aria-label": words, title };
  return card ? html`<button type="button" ...${props} onClick=${() => step(a.id)}><${AspectMark} state=${a.state} />${a.name}</button>`
    : html`<span role="img" ...${props}><${AspectMark} state=${a.state} />${a.name}</span>`;
}

/** The strip over the map: the leader's head and its counts (a press steps through the marked cards: each scrolled into view and lifted), **Ask again**. Nothing for a host that does not know concerns. */
function Strip({ g, lead }) {
  const party = g.slug, rec = recordOf(party), rev = mapData.value?.rev, [tick, setTick] = useState(0), [asking, setAsking] = useState(false), at = useRef({ of: "", i: -1 });
  useEffect(() => {                                          // read when the map is opened and when the Board changes; asked again after a while while a look is under way
    let live = true, timer = 0;
    const go = async () => {
      const r = await read("ideas.concerns", party);
      if (live && r?.status === "looking") timer = setTimeout(go, POLL_MS);
    };
    go();
    return () => { live = false; clearTimeout(timer); };
  }, [party, rev, tick]);
  useEffect(() => { at.current = { of: "", i: -1 }; }, [party]);
  if (!rec) return null;
  const name = theLeader(lead.name), list = rec.concerns || [], alerts = list.filter((c) => c.level === "alert").length, notes = list.length - alerts;
  const rubric = rec.rubric && Array.isArray(rec.rubric.aspects) && rec.rubric.aspects.length ? rec.rubric : null;
  const looking = rec.status === "looking", failed = rec.status === "failed";
  const counts = [alerts && count(alerts, "alert", "alerts"), notes && count(notes, "note", "notes")].filter(Boolean).join(", ");
  const again = async () => {
    setAsking(true);
    try { await read("ideas.concerns_again", party); } finally { setAsking(false); }
    setTick((n) => n + 1);
  };
  const step = (only = "") => {
    const cards = only ? aspectCards(party, only, markedCards()) : markedCards();
    if (!cards.length) return;
    if (at.current.of !== only) at.current = { of: only, i: -1 };                              // a press on another aspect (or on the counts) starts that round from its first card
    at.current.i = (at.current.i + 1) % cards.length;
    const el = cards[at.current.i];
    el.scrollIntoView({ block: "center", inline: "center", behavior: reduced() ? "auto" : "smooth" });
    if (!pickFor.value && !el.matches(".is-lifted, [aria-pressed=true]")) el.click();       // picking wins: there a press is a pick, and stepping only shows the card
  };
  const text = looking ? html`${name} is looking at the map…<span class="ork-busy" aria-hidden="true"></span>`
    : failed ? `${name} could not look at the map${rec.error ? `: ${rec.error}` : ""}`
    : list.length ? null : `${name} sees nothing wrong`;
  return html`<div class="cn-strip" role="status" data-concerns=${looking ? "looking" : failed ? "failed" : list.length ? "some" : "none"} data-party=${party}>
    ${lead.head && html`<${Head} race=${lead.head.race} tier=${lead.head.tier} />`}
    ${text ? html`<span class="cn-strip__say">${text}</span>`
      : html`<button type="button" class="ork-btn quiet cn-strip__counts" onClick=${() => step()} title="Step through the marked parts">${name}: ${counts}</button>`}
    ${looking && list.length > 0 && html`<button type="button" class="ork-btn quiet cn-strip__counts" onClick=${() => step()} title="Step through the marked parts">${counts}</button>`}
    <span class="cn-strip__grow"></span>
    <button type="button" class="ork-btn cn-strip__again" disabled=${looking || asking} title=${`${name} looks at the map again`} onClick=${again}>Ask again</button>
    ${rubric && html`<div class="cn-aspects" role="group" aria-label=${`What ${ofLeader(lead.name)} looks at`}>
      ${rubric.short && html`<span class="cn-aspects__short">${rubric.short}</span>`}
      ${rubric.aspects.map((a) => html`<${Aspect} key=${a.id} a=${a} card=${list.some((c) => c.aspect === a.id && c.on && !goalOf(party, c))} step=${step} />`)}
    </div>`}
    <${ReachLine} party=${party} heat=${heatNow.value} />
  </div>`;
}

/** A party's map with its concerns: the strip over it and, around it, a box that paints the marks (no box of its own: `display: contents`). Drawn only for a party that has a map. */
function Inner({ g, children }) {
  const host = useRef(), lead = leaderOf(g), rec = recordOf(g.slug), nodes = mapData.value?.nodes || [];
  const state = useRef();
  state.current = { party: g.slug, lead };
  useEffect(() => {                                          // paint again whenever the map draws a card (marks are ours: they are not watched)
    const el = host.current;
    if (!el) return undefined;
    let queued = false;
    const paint = () => { queued = false; sync(el, state.current.party, state.current.lead, mapData.peek()?.nodes || []); };
    const mine = (n) => n.classList?.contains("cn-slot") || n.classList?.contains("rc-edge");           // the slots, and the edges the reach draws inside a card (reach.js)
    const ours = (m) => !!m.target.closest?.(".cn-slot, .rc-edge") || (m.type === "childList" && m.addedNodes.length + m.removedNodes.length > 0 && [...m.addedNodes, ...m.removedNodes].every(mine));
    const watch = new MutationObserver((list) => {
      if (queued || list.every(ours)) return;
      queued = true;
      queueMicrotask(paint);
    });
    watch.observe(el, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-pick-id"] });
    return () => { watch.disconnect(); };
  }, []);
  useLayoutEffect(() => { if (host.current) sync(host.current, g.slug, lead, nodes); }, [g.slug, rec, lead.name, lead.head?.race, lead.head?.tier, nodes]);
  useEffect(() => () => { if (host.current) for (const box of host.current.querySelectorAll(".cn-slot__m")) render(null, box); }, []);
  return html`<${Strip} g=${g} lead=${lead} />
    <div ref=${host} class="cn-host" style="display:contents" data-concerns-map=${g.slug}>${children}</div>`;
}

/** Whether a party's tab draws a map its leader looks at (Tech's System, or a craft's map). */
export const hasMap = (g) => !!g && (leadsSystem(g) || !!mapOf(g));

/** A party's map with its concerns; a party with no map is left as it is. */
export const Concerns = ({ g, children }) => (hasMap(g) ? html`<${Inner} key=${g.slug} g=${g}>${children}<//>` : children);

// -- the back of a marked card -------------------------------------------------------------------------------------------------------------------------------------------------

function Item({ party, c, lead, title, aspect }) {
  const [busy, setBusy] = useState(false), slug = goalOf(party, c);
  const goal = async () => {
    setBusy(true);
    try {
      const r = await act("ideas.concern_goal", { party, id: c.id });
      if (r?.idea) made.value = { ...made.peek(), [`${party}/${c.id}`]: r.idea };
      await read("ideas.concerns", party);
    } finally { setBusy(false); }
  };
  const dismiss = async () => {
    setBusy(true);
    try {
      const r = await act("ideas.concern_dismiss", { party, id: c.id });
      if (r && Array.isArray(r.concerns)) keep(party, r);
      else await read("ideas.concerns", party);
    } finally { setBusy(false); }
  };
  return html`<div class="cn-item" data-concern-id=${c.id} data-level=${c.level}>
    <p class="cn-item__what">${c.level === "alert" ? html`<${Sign} name="alert" />` : html`<i class="cn-dot" aria-hidden="true"></i>`}<span><span class="ork-label">${c.level === "alert" ? "Alert" : "Note"}${aspect ? ` · ${aspect}` : ""}</span> ${c.what}</span></p>
    ${c.why && html`<p class="cn-item__why"><span class="ork-label">Why</span> ${c.why}</p>`}
    ${c.fix && html`<p class="cn-item__fix"><span class="ork-label">Fix</span> ${c.fix}</p>`}
    <div class="table-back__acts cn-item__acts">${slug
      ? html`<button type="button" class="ork-btn cn-item__goal" data-goal=${slug} onClick=${() => pick(slug)}>${title ? `Goal: ${title}` : "Pick the goal"}</button>`
      : html`<button type="button" class="ork-btn primary cn-item__make" disabled=${busy} onClick=${goal}>Make it a goal</button>
        <button type="button" class="ork-btn cn-item__no" disabled=${busy} onClick=${dismiss}>Not a problem</button>`}</div>
  </div>`;
}

/** What a lifted card's back gains when its party's leader has concerns on it: each with its what, why and fix, **Make it a goal** and **Not a problem**. `el`: the lifted card's element (card.js `elOf`). Nothing for a card that is no part of a map, or has none. */
export function ConcernsBack({ el }) {
  const party = tab.value, w = el?.closest?.("[data-pick-id]"), nodes = mapData.value?.nodes || [];
  const list = w ? onCard(party, w.dataset.pickId) : [], g = (mapData.value?.goals || []).find((x) => x.slug === party);
  if (!list.length) return null;
  const lead = leaderOf(g);
  return html`<div class="table-back__sec cn-back" data-concerns-back="">
    <span class="ork-label">${concernWords(list.length, lead.name)}</span>
    ${list.map((c) => html`<${Item} key=${c.id} party=${party} c=${c} lead=${lead} title=${nodes.find((n) => n.slug === goalOf(party, c))?.title || ""}
      aspect=${(recordOf(party)?.rubric?.aspects || []).find((a) => a.id === c.aspect)?.name || ""} />`)}
  </div>`;
}

/** A party has an alert on its map: the snapshot's count (`mapData` goals[].concerns), read for the tab's **!**. No count is drawn (decisions §145.3). */
export const hasAlert = (g) => (g?.concerns?.alerts || 0) > 0;
