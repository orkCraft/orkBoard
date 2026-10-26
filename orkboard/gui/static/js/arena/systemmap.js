// The Tech lens's System (docs/specs/89-the-tech-lens-system.md §6, decisions §104.0, §104.2, §104.8): a party the Architect leads has two tabs over its table, System and Board (arena.js); System
// lays the project's parts out on the table as the field's cards — a column for each area, the area's name over it as a member's name is over its column (a 2 px rule as wide as the column), a part a card
// (5:7, 128 x 180: its folder's name, *n files*, *Uses k · Used by m*, the element of the goal that changed it top left until it is seen), the rest of a long column a stack ×n — from `ideas.system`
// (realm/project_map.py: read from the code and git, no model). The places are the host's: a part keeps its column and row, a gone one its place until *Rearrange* (in the tab's corner) lays them out anew.
// What changed since the device's last look (`localStorage` `orkboard.system.look.<project>`: dev's head as shown and the time, written when the tab is left or the page) is played once when the tab is
// opened: the map stands as it was, then each goal in the order it landed — its new parts dealt, its changed ones sealed with its element, its gone ones crumble (spec 74's moments: steps, ≤ 0.42 s each,
// the whole at most 3 s, a press ends it, none under reduced motion or while the page is hidden, none for a goal that landed while the tab was open). Over the table *Since your last look at <time>* and the
// goals with their elements: a press on one dims the others' marks. Hovering a card draws its uses as the field's arrows (arrows.js `across`; a use new since the last look in its goal's element), never all
// of them at once; a card pressed opens its part in the window's right column (`ideas.system_part`, spec 90 §2): its files, *Uses*, *Used by*, and its changes since the last look with their goals and *What it made*; a goal
// there opens the goal. *Reading the project…* while the host reads it (the first snapshot of a project takes a moment).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Chev, Elem } from "../orkui.js";
import { command, town } from "../link.js";
import { closePreview, mapData, preview, show, showIdea } from "../shell/store.js";
import { reducedMotion } from "./motion.js";
import { ArrowLines, across, fine } from "./arrows.js";

// -- the words (spec 89 §0) ---------------------------------------------------------------------------------------------------------------------------------------------------
export const TABS = [["system", "System"], ["board", "Board"]];
export const READING = "Reading the project…";
export const NOTHING_CHANGED = "Nothing changed since your last look";
export const NOTHING = "Nothing here yet";
export const COULD_NOT = "The project could not be read";
export const BY_YOU = "By you";
export const REARRANGE = "Rearrange";
export const KIND_WORDS = { new: "New", changed: "Changed", gone: "Gone" };
export const sinceWords = (time) => `Since your last look at ${time}`;
export const changedBy = (title) => `Changed by ${title}`;
export const filesWords = (n) => `${n} ${n === 1 ? "file" : "files"}`;
export const usesWords = (k, m) => `Uses ${k} · Used by ${m}`;

/** A party has the System when the Architect leads it (spec 89 §5–§6.1). */
export const leadsSystem = (g) => (g?.leader?.slug || "") === "architect";

// -- the moments (spec 74 §0) ---------------------------------------------------------------------------------------------------------------------------------------------------
const START_MS = 300;                                    // the map stands as it was, then the first goal plays
const STEP_MS = 420;                                     // a goal's moment: a deal (0.3 s, 20 ms apart, six at most), a seal or a crumble (0.42 s)
const SLOT_MS = 520;                                     // from one goal to the next, shortened so the whole is at most WHOLE_MS
const WHOLE_MS = 2800;                                   // the whole at most 3 s (spec 89 §6.3), with room for a late frame
const APART_MS = 20, DEALT = 6;
const DONE = 1e9;                                        // the reveal's step once it is played (or when nothing plays)
const motion = () => !reducedMotion() && typeof document !== "undefined" && !document.hidden;

const LOOK = "orkboard.system.look.", TAB = "orkboard.party.tab.";
const read = (k) => { try { return localStorage.getItem(k) || ""; } catch { return ""; } };
const write = (k, v) => { try { localStorage.setItem(k, v); } catch { /* the changes are marked again next time */ } };
const lookOf = (project) => { try { const v = JSON.parse(read(LOOK + project) || "null"); return v && v.commit ? v : null; } catch { return null; } };

/** *14:20* today, *25 Oct, 14:20* another day. */
export function timeWords(iso) {
  const d = new Date(iso || "");
  if (Number.isNaN(d.getTime())) return "";
  const hm = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  return d.toDateString() === new Date().toDateString() ? hm : `${d.toLocaleDateString([], { day: "numeric", month: "short" })}, ${hm}`;
}

/** The tasks landed on the Board: the System is read again when one more lands (a merge moves dev). */
const landedOf = (m) => (m?.nodes || []).reduce((k, n) => k + (n.tasks || []).filter((t) => t.state === "merged").length + (n.state === "done" ? 1 : 0), 0);

/** What changed, grouped by goal in the order the goals landed (the time of each one's last change): [{goal, at, parts: [path]}]; *By you* is goal "". */
export function orderOf(doc) {
  const by = new Map();
  for (const [path, m] of Object.entries(doc?.changed || {})) {
    const k = m.goal || "", o = by.get(k) || { goal: k, at: 0, parts: [] };
    o.parts.push(path);
    o.at = Math.max(o.at, Date.parse(m.at || "") || 0);
    by.set(k, o);
  }
  return [...by.values()].sort((a, b) => a.at - b.at);
}

/** The answer as it is once seen: nothing marked, the gone parts' cards taken off (their places stay until Rearrange). */
const seenOf = (d) => d && { ...d, since: d.commit, changed: {}, uses_changed: [], goals: {}, columns: d.columns.map((c) => ({ ...c, parts: c.parts.filter((p) => !p.gone), stack: c.stack.filter((p) => !p.gone) })) };

/** The System of a party the Architect leads (`on`), read by arena.js for the whole party so its first answer can choose the tab: `{doc, err, look, changed, seen, rearrange}`. `seen()`: the tab is
 *  left — the device's look is dev's head as shown, now, and the answer is as seen. Read again with the same look when a task lands. */
export function useSystem(on, party) {
  const project = town.value?.projects?.current || "";
  const [look, setLook] = useState(() => lookOf(project));
  const [doc, setDoc] = useState(null), [err, setErr] = useState(""), [none, setNone] = useState(false);
  const now = useRef(null), live = useRef(true), landed = landedOf(mapData.value);
  const args = { party, ...(look?.commit ? { since: look.commit } : {}) };
  useEffect(() => () => { live.current = false; }, []);
  useEffect(() => {
    if (!on) return undefined;
    let mine = true;
    command("ideas.system", args, true).then((r) => {
      if (!mine) return;
      if (!r || r.error) { setErr(r?.error || COULD_NOT); return; }
      if (!Array.isArray(r.columns)) { setNone(true); return; }                   // a host from before spec 89: no System, the Board as it was
      now.current = r;
      setErr("");
      setDoc(r);
    }).catch((e) => { if (mine) setErr(e.message || COULD_NOT); });
    return () => { mine = false; };
  }, [on, party, look?.commit, landed]);
  const seen = useRef(null);
  seen.current = () => {
    const c = now.current?.commit;
    if (!c) return;
    const v = { commit: c, at: new Date().toISOString() };
    write(LOOK + project, JSON.stringify(v));
    if (!live.current) return;
    now.current = seenOf(now.current);
    setDoc(now.current);
    setLook(v);
  };
  const rearrange = () => command("ideas.system_rearrange", args, true).then((r) => {
    if (!r || r.error || !Array.isArray(r.columns) || !live.current) return;
    now.current = r;
    setDoc(r);
  }).catch(() => {});
  const changed = !!doc && (Object.keys(doc.changed || {}).length > 0 || (doc.uses_changed || []).length > 0);
  return { doc, err, look, changed, none, seen: () => seen.current(), rearrange };
}

/** The party's tab: the one last pressed on this device (System at first); the first answer of the System opens it on System when something changed since the last look, unless a tab was pressed. */
export function usePartyTab(on, party, sys) {
  const key = `${TAB}${town.value?.projects?.current || ""}.${party}`;
  const [tab, setTab] = useState(() => (read(key) === "board" ? "board" : "system"));
  const decided = useRef(false);
  useEffect(() => {
    if (!on || decided.current || !sys.doc) return;
    decided.current = true;
    if (sys.changed) setTab("system");
  }, [on, sys.doc]);
  const press = (id) => { decided.current = true; write(key, id); setTab(id); };
  return [on ? tab : "board", press];
}

/** The two tabs over the party's table (spec 89 §6.1). ← → (Home, End) move between them. */
export function PartyTabs({ tab, setTab, name }) {
  const key = (e) => {
    const at = TABS.findIndex(([id]) => id === tab), step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    const to = e.key === "Home" ? 0 : e.key === "End" ? TABS.length - 1 : step ? (at + step + TABS.length) % TABS.length : -1;
    if (to < 0) return;
    e.preventDefault();
    setTab(TABS[to][0]);
    e.currentTarget.querySelectorAll("[role=tab]")[to]?.focus();
  };
  return html`<div class="ork-tabs sys-tabs" role="tablist" aria-label=${name} onKeyDown=${key}>
    ${TABS.map(([id, word]) => html`<button type="button" key=${id} role="tab" class="ork-tab" id=${`ptab-${id}`} data-tab=${id} aria-selected=${String(id === tab)} aria-controls="ppanel"
      tabindex=${id === tab ? 0 : -1} onClick=${() => setTab(id)}>${word}</button>`)}
  </div>`;
}

// -- the reveal ---------------------------------------------------------------------------------------------------------------------------------------------------------------

/** Plays what changed once, on the first answer the tab shows (`doc`): the step is -1 while the map stands as it was, i while the i-th goal of `order` plays, DONE after (and at once when nothing plays). */
function useReveal(doc, order) {
  const [step, setStep] = useState(DONE), played = useRef(false), timers = useRef([]);
  const end = useRef(null);
  end.current = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    removeEventListener("pointerdown", end.fire, true);
    removeEventListener("keydown", end.fire, true);
    setStep(DONE);
  };
  if (!end.fire) end.fire = () => end.current();
  useLayoutEffect(() => {                                  // before the paint: the first frame is the map as it was
    if (!doc || played.current) return;
    played.current = true;
    if (!order.length || !motion()) return;
    const slot = order.length > 1 ? Math.min(SLOT_MS, (WHOLE_MS - START_MS - STEP_MS) / (order.length - 1)) : SLOT_MS;
    setStep(-1);
    timers.current = order.map((_, i) => setTimeout(() => setStep(i), START_MS + i * slot));
    timers.current.push(setTimeout(() => end.current(), START_MS + (order.length - 1) * slot + STEP_MS));
    addEventListener("pointerdown", end.fire, true);       // a press ends it
    addEventListener("keydown", end.fire, true);
  }, [doc]);
  useEffect(() => () => end.current(), []);
  return step;
}

/** What the reveal shows of a part now: its change `m` (or none), the index of its goal in `order`, the step. */
function phaseOf(m, gi, step) {
  if (!m) return "";
  if (step === DONE || step > gi) return m.kind === "gone" ? "left" : "marked";
  if (step === gi) return { new: "dealt", changed: "sealed", gone: "crumble" }[m.kind] || "marked";
  return m.kind === "new" ? "unborn" : "before";            // the map as it was: a new part not yet there, a gone one still standing, a changed one unmarked
}

// -- a part ------------------------------------------------------------------------------------------------------------------------------------------------------------------

/** A part as the field's card (5:7): the element of the goal that changed it and *New*, *Changed* or *Gone* top left while it is marked, its folder's name (four lines), *n files*, *Uses k · Used by m*.
 *  `many` > 1: the front of a stack (edges behind it, ×n; a press opens it). */
function Part({ c, m, goal, phase, dim, on, lit, place, deal, many = 0, onPress, onHover }) {
  const marked = phase === "marked" || phase === "sealed" || phase === "dealt" || phase === "crumble";
  const by = m ? (m.goal ? changedBy(goal?.title || m.goal) : BY_YOU) : "", el = goal?.element || "";
  const edges = Math.min(2, many - 1), said = [c.name, filesWords(c.count), usesWords(c.uses.length, c.used_by.length), m && `${KIND_WORDS[m.kind]}, ${by}`,
    many > 1 && `and ${many - 1} more of ${c.area}: a press shows them`].filter(Boolean).join(", ");
  const hover = (by) => () => onHover(c.path, by), leave = () => onHover("", "");
  return html`<div class=${cls("arena-stk sys-stk", { "is-many": many > 1 })} style=${place} data-n=${many > 1 ? many : undefined}>
    ${Array.from({ length: edges }, (_, i) => html`<i key=${i} class="arena-stk__edge" style=${`left:${(i + 1) * 4}px;top:${-(i + 1) * 4}px`}></i>`)}
    <button type="button" class=${cls("arena-task sys-part", { "is-src": lit === "src" || on, "is-after": lit === "use", "is-marked": marked, "is-dim": marked && dim, "has-n": many > 1,
        [`sys-${phase}`]: !!phase && phase !== "marked" && phase !== "before" })}
      data-part=${c.path} data-change=${m?.kind || undefined} data-goal=${m ? m.goal : undefined} style=${phase === "dealt" ? `--delay:${deal * APART_MS}ms` : undefined}
      title=${`${c.path} · ${filesWords(c.count)} · ${usesWords(c.uses.length, c.used_by.length)}${m ? ` · ${KIND_WORDS[m.kind]} · ${by}` : ""}`} aria-label=${said}
      aria-pressed=${many > 1 ? undefined : String(!!on)} aria-expanded=${many > 1 ? "false" : undefined} aria-hidden=${phase === "unborn" || phase === "left" ? "true" : undefined}
      tabindex=${phase === "unborn" || phase === "left" ? -1 : undefined}
      onClick=${() => onPress(c)} onMouseEnter=${hover("pointer")} onMouseLeave=${leave} onFocus=${hover("focus")} onBlur=${leave}>
      <span class="arena-task__top">${marked && m && html`${m.goal ? html`<${Elem} name=${el} dim=${dim || !el} />` : null}<span class="arena-task__phase sys-part__kind">${KIND_WORDS[m.kind]}</span>`}</span>
      <span class="arena-task__name sys-part__name">${c.name}</span>
      <span class="arena-task__count sys-part__files">${filesWords(c.count)}</span>
      <span class="arena-task__foot sys-part__uses"><span>Uses ${c.uses.length} ·</span> <span>Used by ${c.used_by.length}</span></span>
      ${many > 1 && html`<span class="arena-stk__n">×${many}</span>`}
      ${phase === "sealed" && html`<span class="sys-seal" aria-hidden="true"><${Elem} name=${el} dim=${!el} big=${true} /></span>`}
    </button>
  </div>`;
}

/** The cards of a column in their places on the table's grid: a part at its row (a gone part's place stays empty), or, for a column with a stack, one after another; the stack after them (open: all of it). */
function placesOf(col, open) {
  const stacked = col.stack.length > 0;
  const cards = col.parts.map((c, i) => ({ c, slot: stacked ? i : c.row }));
  let next = cards.reduce((k, x) => Math.max(k, x.slot + 1), 0);
  const stack = !stacked ? [] : open ? col.stack.map((c) => ({ c, slot: next++ })) : [{ c: col.stack[0], slot: next++, many: col.stack.length }];
  return { cards: [...cards, ...stack], rows: next };
}

// -- the part beside the table ------------------------------------------------------------------------------------------------------------------------------------------------

/** A list of parts, each a press that shows it. */
const Parts = ({ list, names, onPart }) => html`<ul class="sys-side__list">${list.map((p) => html`<li key=${p}><button type="button" class="sys-side__part" data-part=${p} title=${p} onClick=${() => onPart(p)}>${names[p] || p.split("/").pop() || p}</button></li>`)}</ul>`;

/** What the System shown last read (`{doc, look, party}`): a part opened in the right column names its uses by it and says its changes since the same look. */
const shownSys = signal(null);

/** A part opens in the right column (spec 90 §2, a tab `{kind: "part", path, slug: <its party>}`). */
const openPart = (path, party, name) => show({ kind: "part", path, slug: party, title: name || path.split("/").pop() || path }, { via: "map" });

/** A part pressed (spec 89 §6.5), in the window's right column (spec 90 §2): its files, *Uses*, *Used by*, and its changes since the last look, each with its goal (a press opens the goal) and *What it made*;
 *  a part under *Uses* or *Used by* pressed opens in its place. The tab's × (or Esc) closes it. */
export function PartView({ p: tab }) {
  const path = tab.path, party = tab.slug || "", sys = shownSys.value;
  const doc = sys && sys.party === party ? sys.doc : null, look = doc ? sys.look : null, since = doc?.since || "";
  const names = doc ? Object.fromEntries(doc.columns.flatMap((c) => [...c.parts, ...c.stack]).map((c) => [c.path, c.name])) : {};
  return html`<${PartSide} key=${path} path=${path} party=${party} since=${since} look=${look} names=${names} onPart=${(to) => openPart(to, party, names[to])} />`;
}

function PartSide({ path, party, since, look, names, onPart }) {
  const [p, setP] = useState(null), [err, setErr] = useState("");
  useEffect(() => {
    let live = true;
    setP(null);
    setErr("");
    command("ideas.system_part", { path, party, ...(since ? { since } : {}) }, true).then((r) => {
      if (!live) return;
      if (!r || r.error) setErr(r?.error || COULD_NOT);
      else setP(r);
    }).catch((e) => { if (live) setErr(e.message || COULD_NOT); });
    return () => { live = false; };
  }, [path, since]);
  const name = p?.name || path.split("/").pop() || path, goals = p?.goals || {};
  return html`<section class="sys-side" aria-label=${name} data-path=${path}>
    <div class="sys-side__head"><b class="sys-side__name" title=${path}>${name}</b></div>
    ${err ? html`<p class="arena-cap">${err}</p>` : !p ? html`<p class="arena-cap"><span class="ork-busy"></span></p>` : html`
      <p class="arena-cap sys-side__path">${p.path}${p.kind && html` · <b class="sys-side__kind">${KIND_WORDS[p.kind]}</b>`}</p>
      ${p.changes.length > 0 && html`<section class="sys-side__sec" data-sec="changes"><h3 class="arena-sec">${look?.at ? sinceWords(timeWords(look.at)) : KIND_WORDS[p.kind] || ""}</h3>
        <ul class="sys-side__changes">${p.changes.map((c, i) => html`<li key=${i} class="sys-change">
          ${c.goal ? html`<button type="button" class="sys-change__goal" data-goal=${c.goal} onClick=${() => showIdea(c.goal, { via: "map" })}><${Elem} name=${goals[c.goal]?.element || ""} />${goals[c.goal]?.title || c.goal}</button>`
            : html`<span class="sys-change__goal is-you">${BY_YOU}</span>`}
          ${c.made && html`<span class="sys-change__made"><b>What it made</b> ${c.made}</span>`}</li>`)}</ul></section>`}
      <section class="sys-side__sec" data-sec="files"><h3 class="arena-sec">${filesWords(p.count)}</h3>
        <ul class="sys-side__list sys-side__files">${p.files.map((f) => html`<li key=${f} title=${f}>${f.split("/").pop()}</li>`)}</ul></section>
      <section class="sys-side__sec" data-sec="uses"><h3 class="arena-sec">Uses</h3>${p.uses.length ? html`<${Parts} list=${p.uses} names=${names} onPart=${onPart} />` : html`<p class="arena-cap">—</p>`}</section>
      <section class="sys-side__sec" data-sec="used_by"><h3 class="arena-sec">Used by</h3>${p.used_by.length ? html`<${Parts} list=${p.used_by} names=${names} onPart=${onPart} />` : html`<p class="arena-cap">—</p>`}</section>`}
  </section>`;
}

// -- the table ---------------------------------------------------------------------------------------------------------------------------------------------------------------

const GX = 12, GY = 8;                                   // half the gutter between two columns (--ork-8) and half the gap between two rows (--ork-6): where a use's line runs

/** The lines of a part's uses, over the table `host`: from it to each part it uses, from each part that uses it to it, between the cards shown; a use new since the last look in its goal's element. */
function usesOf(host, doc, path) {
  const card = doc.columns.flatMap((c) => [...c.parts, ...c.stack]).find((c) => c.path === path);
  if (!host || !card) return [];
  const base = host.getBoundingClientRect();
  const box = (p) => {
    const el = host.querySelector(`.sys-part[data-part="${CSS.escape(p)}"]`);
    if (!el || el.getAttribute("aria-hidden") === "true") return null;
    const r = el.getBoundingClientRect();
    return { x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height };
  };
  const me = box(path);
  if (!me) return [];
  const fresh = new Map((doc.uses_changed || []).filter((u) => u.kind === "new").map((u) => [`${u.from}>${u.to}`, doc.goals?.[u.goal]?.element || ""]));
  const pairs = [...card.uses.filter((u) => u !== path).map((u) => [path, u]), ...card.used_by.filter((u) => u !== path).map((u) => [u, path])];
  const out = [];
  for (const [from, to] of pairs) {
    const a = from === path ? me : box(from), b = to === path ? me : box(to);
    if (!a || !b) continue;
    const key = `${from}>${to}`;
    out.push({ ...across(key, a, b, GX, GY), ...(fresh.has(key) ? { el: fresh.get(key) || "new", kind: "new" } : {}) });
  }
  return out;
}

/** The System tab: the bar (*Since your last look at <time>*, the goals, *Rearrange*), the table of the parts, the part pressed beside it. `sys`: `useSystem`'s. */
export function SystemMap({ sys, party }) {
  const { doc, err, look } = sys;
  const order = doc ? orderOf(doc) : [], step = useReveal(doc, order);
  const [pick, setPick] = useState(""), [opened, setOpened] = useState(() => new Set());
  const [hover, setHover] = useState({ path: "", by: "" }), [lines, setLines] = useState([]), host = useRef();
  const tab = preview.value, shown = tab?.kind === "part" && tab.slug === party ? tab.path : "";      // the part open in the right column
  useEffect(() => {                                        // the tab is left (or the page): what it showed is seen
    const save = () => sys.seen();
    addEventListener("pagehide", save);
    return () => { removeEventListener("pagehide", save); save(); };
  }, []);
  useEffect(() => { if (doc) shownSys.value = { doc, look, party }; }, [doc, look, party]);
  useLayoutEffect(() => {
    const on = !!hover.path && !!doc && (hover.by === "focus" || fine());
    const next = on ? usesOf(host.current, doc, hover.path) : [];
    setLines((was) => (!was.length && !next.length ? was : next));
  }, [hover.path, hover.by, doc, step]);
  if (err && !doc) return html`<div class="sys" data-state="failed"><p class="arena-cap sys-note">${err}</p></div>`;
  if (!doc) return html`<div class="sys" data-state="reading"><p class="arena-cap sys-note"><span class="ork-busy"></span> ${READING}</p></div>`;
  const goals = doc.goals || {}, gindex = new Map(order.map((o, i) => [o.goal, i]));
  const playing = step !== DONE;
  const lit = new Set(hover.path ? doc.columns.flatMap((c) => [...c.parts, ...c.stack]).filter((c) => c.path === hover.path).flatMap((c) => [...c.uses, ...c.used_by]) : []);
  const deals = new Map();                                 // a goal's new parts in the order they are dealt: the first six 20 ms apart, the rest with the sixth
  for (const o of order) o.parts.filter((p) => doc.changed[p].kind === "new").forEach((p, i) => deals.set(p, Math.min(i, DEALT - 1)));
  const toggle = (k) => setOpened((s) => { const n = new Set(s); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const cols = doc.columns.map((col, ci) => ({ col, ci, ...placesOf(col, opened.has(ci)) }));
  const rows = cols.reduce((k, c) => Math.max(k, c.rows), 0);
  const press = (ci) => (c) => {
    if (cols[ci].col.stack.length && !opened.has(ci) && cols[ci].col.stack[0].path === c.path) { toggle(ci); return; }
    if (shown === c.path) closePreview();                  // pressed again: the right column closes it
    else openPart(c.path, party, c.name);
  };
  const hovered = (path, by) => setHover((h) => (path ? { path, by } : h.path ? { path: "", by: "" } : h));
  const since = doc.since ? (look?.at ? sinceWords(timeWords(look.at)) : sinceWords(doc.since.slice(0, 7))) : "";
  return html`<div class="sys" data-state="shown" data-reveal=${playing ? "playing" : "done"} data-step=${playing ? step : undefined}>
    <div class="sys-bar">
      ${doc.since && (order.length ? html`<span class="sys-since">${since}</span>
        <div class="sys-goals" role="group" aria-label=${since}>${order.map((o) => html`<button type="button" key=${o.goal || "@you"} class="ork-btn quiet sys-goal" data-goal=${o.goal}
          aria-pressed=${String(pick === (o.goal || "@you"))} onClick=${() => setPick(pick === (o.goal || "@you") ? "" : o.goal || "@you")}>
          ${o.goal ? html`<${Elem} name=${goals[o.goal]?.element || ""} />${goals[o.goal]?.title || o.goal}` : BY_YOU}</button>`)}</div>`
        : html`<span class="sys-since is-none">${NOTHING_CHANGED}</span>`)}
      <span class="arena-spacer"></span>
      <button type="button" class="ork-btn sys-rearrange" onClick=${() => sys.rearrange()}>${REARRANGE}</button>
    </div>
    <div class="sys-main">
      ${!doc.columns.length ? html`<div class="assets-none"><p class="assets-none__title">${NOTHING}</p></div>` : html`
      <div class="sys-scroll">
        <div class="sys-table" ref=${host} style=${`--cols:repeat(${cols.length}, 128px)`} data-rows=${rows}>
          ${cols.map(({ col, ci }) => html`<div key=${`h${ci}`} class="sys-area" style=${`grid-column:${ci + 1}`} data-area=${col.name}>
            <span class="arena-member__nm sys-area__nm" title=${col.name}>${col.name}</span>
            ${col.stack.length > 0 && opened.has(ci) && html`<button type="button" class="ork-btn quiet sys-area__fold" aria-expanded="true" onClick=${() => toggle(ci)}><${Chev} dir="up" /> ×${col.stack.length}</button>`}
            <span class="sys-area__rule" aria-hidden="true"></span></div>`)}
          ${cols.flatMap(({ col, ci, cards }) => cards.map(({ c, slot, many }) => {
            const m = doc.changed[c.path], gi = m ? gindex.get(m.goal || "") : -1, phase = phaseOf(m, gi, step);
            return html`<${Part} key=${c.path} c=${{ ...c, area: col.name }} m=${m} goal=${m?.goal ? goals[m.goal] : null} phase=${phase} many=${many || 0} deal=${deals.get(c.path) || 0}
              dim=${!!pick && !!m && pick !== (m.goal || "@you")} on=${shown === c.path} lit=${hover.path === c.path ? "src" : lit.has(c.path) ? "use" : ""}
              place=${`grid-column:${ci + 1};grid-row:${slot + 2}`} onPress=${press(ci)} onHover=${hovered} />`;
          }))}
          <${ArrowLines} lines=${lines} />
        </div>
      </div>`}
    </div>
  </div>`;
}
