// The phone's menu of the leaders (docs/specs/117-the-phone-a-menu-of-the-leaders.md §4, docs/mockups/phone/sidebar.html A2, decisions §195.1): the Board turned on its side, a way to look, never a place where something waits. **The crown** (the Orkmaster's crowned
// head, 44 px, at the top row's left) opens a sheet from the left, 312 px (at most 80% of the width), over orkUI's scrim; the scrim's press, Esc, the phone's back (one history entry while it is open) and any pick close it, the focus goes into it and back to the
// crown. Never an edge swipe: the left edge is the system's back. At its head: the project's name with a chevron (*Switch project*, over the pane), *Settings* and *Stop all* (the tabs' own halt: no confirm, as on the desktop). Under it the Orkmaster's goals — those
// in Talk and in Spec in the Board's order, then those in line with the moon beside the name of one that waits for the reset — then each party, Release too, its leader's head, its name, its sword and shield as the tabs draw them (table/tabmarks.js) and its goals at
// work under it, each its element, its type's sign, its short name and its phase (Work, or Checks while the front task is checking). **No count, no alert, no *waits for you* anywhere here**: what waits is the hand's. A press on a goal picks it (entries.js `pickGoal`:
// the entry of the goal on the screen when it has one), on a party picks the party (`pickParty`: `tab` its slug, `picked` emptied); the menu closes. The picked row has the ink's bar at its left and the panel's fill. Layout only (upmenu.css).
import { useEffect, useRef } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { command } from "../link.js";
import { openOver } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { mapData } from "../shell/store.js";
import { PHASES, laneOf, lineNow, nameOf, partiesAll, phaseOf, stageOf, typeSignOf } from "../table/data.js";
import { Marks, marksOf, marksWords } from "../table/tabmarks.js";
import { orkHeadOf } from "./context.js";
import { pickGoal, pickParty } from "./entries.js";
import { PhoneRows } from "./upphone.js";

export const menuOpen = signal(false);                           // the sheet is open
export const MENU = "The leaders and their goals";               // the crown's words
const phaseWord = (id) => (PHASES.find(([p]) => p === id) || [])[1] || "";

/** The Orkmaster's goals: those in Talk and in Spec in the Board's order (not those in line, done or at work in a party), then those in line (`lineNow`). Each `{slug, name, element, sign, phase, moon}`. */
export function talkedOf(map = mapData.value) {
  const working = new Set(partiesAll().flatMap((g) => laneOf(g).map(({ n }) => n.slug)));
  const talk = (map?.nodes || []).filter((n) => ["talk", "spec"].includes(phaseOf(n.slug)) && !["deck", "discard", "history"].includes(n.place) && !working.has(n.slug))
    .map((n) => ({ slug: n.slug, name: nameOf(n), element: n.element || "", sign: typeSignOf(n), phase: phaseWord(phaseOf(n.slug)), moon: false }));
  const line = lineNow(map).map((g) => ({ slug: g.slug, name: g.title, element: g.element, sign: g.type?.sign || "", phase: "In line", moon: g.reset }));
  return [...talk, ...line];
}

/** A party's goals at work, the Board's order of a lane: `{slug, name, element, sign, phase}`; *Checks* while a goal's front task is a check. */
export function workOf(g) {
  return laneOf(g).map(({ n, tasks }) => ({ slug: n.slug, name: nameOf(n), element: n.element || "", sign: typeSignOf(n), phase: stageOf(tasks[0]) === "checking" ? "Checks" : phaseWord("work"), moon: false }));
}

/** One goal as a row: its element, its type's sign, its short name, the moon of one that waits for the reset, its phase at the right. */
export function GoalRow({ r, on, onPress }) {
  return html`<button type="button" class=${cls("up-grow", { "is-on": on })} data-goal=${r.slug} aria-current=${on ? "true" : undefined} aria-label=${`${r.name}: ${r.moon ? "in line, waits for the reset" : r.phase}`} onClick=${onPress}>
    <${Elem} name=${r.element} dim=${!r.element} />${r.sign ? html`<${Sign} name=${r.sign} />` : html`<span class="up-grow__none" aria-hidden="true"></span>`}<span class="up-grow__name">${r.name}</span>
    ${r.moon && html`<${Sign} name="moon" />`}<span class="up-grow__phase">${r.phase}</span>
  </button>`;
}

/** One party as a row: its leader's head, its name, its sword and shield as the tabs draw them. */
function PartyRow({ g, on, onPress }) {
  const marks = marksOf(g), said = marks ? `${nameOf(g)} · ${marksWords(marks)}` : nameOf(g);
  return html`<button type="button" class=${cls("up-prow", { "is-on": on })} data-party=${g.slug} aria-current=${on ? "true" : undefined} aria-label=${said} title=${said} onClick=${onPress}>
    ${g.leader?.head ? html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} />` : html`<span class="up-prow__none" aria-hidden="true"></span>`}<span class="up-prow__name">${nameOf(g)}</span><${Marks} m=${marks} />
  </button>`;
}

/** The crown: the Orkmaster's crowned head, a 44 px button that opens the menu. */
export function Crown() {
  const o = orkHeadOf();
  return html`<button type="button" class="up-crown" aria-label=${MENU} title=${MENU} aria-haspopup="dialog" aria-expanded=${menuOpen.value ? "true" : "false"} onClick=${() => { menuOpen.value = !menuOpen.value; }}>
    <${Head} race=${o.race} tier=${o.tier} /></button>`;
}

/** One history entry while the sheet is open, so the phone's back closes it; `close(then)` leaves through it (the thing a pick opens comes after the back, so the table's own entry never meets this one). */
function useSheet(box) {
  const at = useRef({ pushed: false, then: null, closing: false });
  const gone = () => {
    const s = at.current, then = s.then;
    s.then = null;
    menuOpen.value = false;
    document.querySelector(".up-crown")?.focus();
    then?.();
  };
  useEffect(() => {
    const s = at.current;
    try { history.pushState({ orkboardMenu: 1 }, ""); s.pushed = true; } catch { s.pushed = false; }
    const pop = () => { if (!s.pushed) return; s.pushed = false; gone(); };
    const key = (e) => {
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); return; }
      if (e.key !== "Tab" || !box.current) return;
      const all = [...box.current.querySelectorAll("button")], first = all[0], last = all[all.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    addEventListener("popstate", pop);
    addEventListener("keydown", key, true);
    box.current?.querySelector("button")?.focus();
    return () => {
      removeEventListener("popstate", pop);
      removeEventListener("keydown", key, true);
      if (s.pushed) { s.pushed = false; try { history.back(); } catch { /* no history */ } }          // closed some other way: its entry goes
    };
  }, []);
  const close = (then = null) => {
    const s = at.current;
    if (s.closing) return;
    s.closing = true;
    s.then = then;
    if (s.pushed) { try { history.back(); return; } catch { s.pushed = false; } }
    gone();
  };
  return close;
}

/** The sheet while it is open. */
function Open({ entries, look }) {
  const box = useRef(), close = useSheet(box);
  const project = currentProject.value?.name || "The project", o = orkHeadOf(), from = { title: "", key: "" }, talked = talkedOf(), parties = partiesAll();
  const goalOn = (slug) => look.kind === "goal" && look.slug === slug, partyOn = (slug) => look.kind === "party" && look.g.slug === slug;       // what the middle looks at is what is picked
  return html`<div class="up-scrim" onClick=${() => close()}></div>
    <aside class="up-menu" ref=${box} role="dialog" aria-modal="true" aria-label=${MENU}>
      <div class="up-menu__head">
        <${Head} race=${o.race} tier=${o.tier} />
        <button type="button" class="up-menu__project" aria-label=${`Switch project: ${project}`} title="Switch project" onClick=${() => close(() => openOver("projects", {}, from, "Projects"))}><span>${project}</span><${Icon} name="chevron-down" /></button>
        <button type="button" class="up-menu__ico" aria-label="Settings" title="Settings" onClick=${() => close(() => openOver("settings", {}, from, "Settings"))}><${Icon} name="sliders" /></button>
        <button type="button" class="up-menu__ico is-stop" aria-label="Stop all" title="Stop every ork, script and browser at once" onClick=${() => close(() => command("halt").catch(() => {}))}><${Icon} name="boarded" /></button>
      </div>
      ${talked.length > 0 && html`<section class="up-group" aria-label="Orkmaster · Being talked about"><p class="up-group__label">Orkmaster · Being talked about</p>
        ${talked.map((r) => html`<${GoalRow} key=${r.slug} r=${r} on=${goalOn(r.slug)} onPress=${() => close(() => pickGoal(entries, r.slug))} />`)}</section>`}
      ${parties.map((g) => html`<section key=${g.slug} class="up-group" aria-label=${nameOf(g)}>
        <${PartyRow} g=${g} on=${partyOn(g.slug)} onPress=${() => close(() => pickParty(g.slug))} />
        ${workOf(g).map((r) => html`<${GoalRow} key=${r.slug} r=${r} on=${goalOn(r.slug)} onPress=${() => close(() => pickGoal(entries, r.slug))} />`)}</section>`)}
      <${PhoneRows} />
    </aside>`;
}

/** The sheet. `entries`: the hand's entries (entries.js), so a goal with a card in the hand is picked as that card; `look`: what the middle looks at (uplook.js `lookOf`), whose row is the picked one. */
export const Sheet = ({ entries, look }) => (menuOpen.value ? html`<${Open} entries=${entries} look=${look} />` : null);
