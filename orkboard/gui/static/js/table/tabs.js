// The tabs, the leaders' side of the table (docs/specs/123-the-leaders-at-the-table.md §7, decisions §201.6–§201.8; before it docs/specs/98-the-table-and-the-hand.md §3.1, docs/specs/95-the-window-as-decided.md §2, decisions §167.6): the project's first — the crowned
// head and the project's name (*Party game*), then **▾** (*Switch project*, spec 107 §8.2) —, then a tab a party in the Board's order, its leader's head and the party's name, and under the name its **sword and shield**: the marks of the AI tools its Does and
// its Checks run on (tabmarks.js, docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.4, decisions §189; the title and the label say them: *Tech · Does on Claude · Checks on Codex*; the project's tab shows the main tool on both). Every head is `mid`
// (36 x 33) and wears the face its leader's state gives it (moods.js; it stands still: the old step of a head at work is the *focused* face now, `data-working` stays); each stands on a chair's back at the wide width (orkUI's `chair`, none under 760 px).
// The open tab has no fill and no bar: its head is `big` (48 x 44) and 3 px lower, over the table's rim, its name in the ink and the leader's own name under it (*the Orkmaster* on the project's), the others' names muted. The open head is a **button of its own** in the
// tab's cell, not inside the tab's button (a button holds no button), over the head's place: it opens the leader's bubble (ask.js; `data-ask-head`; the desktop only, as the bubble is), and beside it the leader's marks, each a button stepping through the marked parts of its map
// (concerns.js `stepMarked`): orkUI's alert sign in the alert's tone for an alert, a muted dot for a note; while the leader looks, `title` says so. The other tabs keep their alert sign. A tab's width is its column's (decisions §143): only its height grows.
// At the end: **New party**, the empty chair (chairs.js, where *+ Party* was), **Stop all**, a door (door.js, where the planks were) and, last, the bug under the glass (*Save the logs*, hand/logsbtn.js: decisions §190.6); the AI tools' limits are the hand's mana (hand/mana.js, spec 104 B).
// The dark edges (table.css): the row and the hand on orkUI's room, a rim under the tabs and over the hand, no line between the tabs. Under 760 px the tabs are a row of heads (the open one at 36 with its marks), the chair and the door small, and the limits are in the Orkmaster's **…**
// as chips (pane.js) and in the hand as small potions. The tabs, the Board's lanes and the hand read the frame's one `--cols`, so a tab stands over its lane. A party's tab carries a dot when the picked goal's route has it.
// At the wide width Release's and Live's are not in the row (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4.1, decisions §188.1): they wait in the portal ring's corners (road.js, portal.js) and open their view in the pane from there; `parties` is the tabs' (data.js `partiesNow`).
// The open tab is the person's: nothing here switches it. A name is also said on a long press (nothing only on hover: spec 94 §1.1).
import { useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Chair, Head, Icon, Sign } from "../orkui.js";
import { toast } from "../link.js";
import { ORKMASTER, openTab, openOver, picked } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { levelOf, windowOf } from "../arena/limits.js";
import { nameOf, routeParties, MARKED, markSrc, mapName } from "./data.js";
import { hasAlert, lookOf, stepMarked, theLeader } from "./concerns.js";
import { Marks, marksOf, marksWords, projectMarks } from "./tabmarks.js";
import { AskBubble, askOpen, closeAsk, desk, openAsk } from "./ask.js";
import { EmptyChair, useOffer } from "./chairs.js";
import { StopDoor } from "./door.js";
import { isWorking, moodOf } from "./moods.js";
import { LogsButton } from "../hand/logsbtn.js";                // the bug under the glass, the last of the row (decisions §190.6)

export { isWorking };                                            // the tabs' word for it was here first (road.js)

const LONG_MS = 500;
const CROWN = { race: "peon", tier: "crown" };                   // the Orkmaster's head

/** A long press of a finger says the tab's name (a touch has no hover to say it). */
function usePressName(name) {
  const timer = useRef(0);
  return {
    onPointerDown: (e) => { if (e.pointerType === "touch") timer.current = setTimeout(() => toast(name, "information", "", 2), LONG_MS); },
    onPointerUp: () => clearTimeout(timer.current), onPointerLeave: () => clearTimeout(timer.current), onPointerCancel: () => clearTimeout(timer.current),
  };
}

/** A leader's name as a sentence takes it after *the*: *Architect*, *Orkmaster*. */
const roleWord = (name) => String(name || "Taskmaster").replace(/^the\s+/i, "");

/** A head on its chair: the chair's back under it at the wide width (`chair`), the head over the back's rail; the open leader's `big` and 3 px lower, over the table's rim. `children` stand in the head's place (the open head's button). */
function Sit({ head, mood, size, chair, on, extra, children }) {
  return html`<span class=${cls("table-seatbox", { "has-chair": chair, "is-big": size === "big", "is-on": on })}>
    ${chair && html`<${Chair} big=${size === "big"} />`}
    <span class="table-seatbox__sit">${children || (head && html`<${Head} race=${head.race} tier=${head.tier} size=${size} mood=${mood} />`)}</span>
    ${extra}
  </span>`;
}

/** The open leader's marks beside its head: orkUI's alert sign (alert tone) for an alert, a muted dot for a note, each a button that steps through the marked parts of the map (alerts first). */
function LookMarks({ slug, who }) {
  const { alerts, notes } = lookOf(slug);
  if (!alerts && !notes) return null;
  const said = (n, one, many) => `${who}: ${n} ${n === 1 ? one : many}, step through ${n === 1 ? "it" : "them"}`;
  return html`<span class="table-marks">
    ${alerts > 0 && html`<button type="button" class="table-mark is-alert" data-level="alert" aria-label=${said(alerts, "alert", "alerts")} title=${said(alerts, "alert", "alerts")} onClick=${() => stepMarked(slug, "alert")}><${Sign} name="alert" /></button>`}
    ${notes > 0 && html`<button type="button" class="table-mark is-note" data-level="note" aria-label=${said(notes, "note", "notes")} title=${said(notes, "note", "notes")} onClick=${() => stepMarked(slug, "note")}></button>`}
  </span>`;
}

/** One tab in its cell. `g`: the party (null for the project's); the open tab's head is not in its button but beside it, in the cell. */
function Tab({ slug, g = null, on, name, who = "", head, dot = false, working = false, alert = "", switcher = false, marks = null, compact, narrow, onPick, after = null }) {
  const press = usePressName(name), said = marks ? `${name} · ${marksWords(marks)}` : name, mood = moodOf(g), chair = !narrow;
  const size = on && !narrow ? "big" : "mid", key = slug === ORKMASTER ? "" : slug, leader = roleWord(g ? g.leader?.name : "Orkmaster");
  const looking = g ? lookOf(slug).status === "looking" : false, ask = desk() && !!head;
  const button = html`<button type="button" class=${cls("ork-tab table-tab", { "is-compact": compact, "has-switch": switcher, "is-open": on })} role="tab" id=${`tab-${slug}`} data-tab=${slug} data-working=${working ? "" : undefined} aria-selected=${String(on)} tabindex=${on ? 0 : -1}
    aria-label=${said} title=${said} aria-controls="table-pane" onClick=${onPick} ...${press}>
    ${!on && head && html`<${Sit} head=${head} mood=${mood} size=${size} chair=${chair} />`}
    <span class="table-tab__txt"><span class="table-tab__main">${name}</span>${on && who && html`<span class="table-tab__who">${who}</span>`}<${Marks} m=${marks} on=${on} /></span>
    ${dot && html`<i class="table-tab__dot" role="img" aria-label="On the picked goal's route" title="On the picked goal's route"></i>`}
    ${!on && alert && html`<span class="table-tab__alert" role="img" aria-label=${alert} title=${alert}><${Sign} name="alert" /></span>`}
  </button>`;
  return html`<div class=${cls("table-tabcell", { "is-open": on })} role="presentation" data-cell=${slug}>
    ${on && head && html`<${Sit} head=${head} mood=${mood} size=${size} chair=${chair} on=${true} extra=${g ? html`<${LookMarks} slug=${slug} who=${theLeader(g.leader?.name)} />` : null}>${ask
      ? html`<button type="button" class="table-askhead" data-ask-head=${slug} aria-label=${`Ask the ${leader}`} aria-haspopup="dialog" aria-expanded=${String(askOpen.value === key)}
          title=${looking ? `${theLeader(leader)} is looking at the map` : `Ask the ${leader}`} onClick=${() => (askOpen.value === key ? closeAsk() : openAsk(slug))}><${Head} race=${head.race} tier=${head.tier} size=${size} mood=${mood} /></button>`
      : html`<span class="table-askhead is-still" title=${looking ? `${theLeader(leader)} is looking at the map` : undefined}><${Head} race=${head.race} tier=${head.tier} size=${size} mood=${mood} /></span>`}<//>`}
    ${button}
    ${after}
  </div>`;
}

/** One AI tool's chip, in the Orkmaster's **…** at the narrow width (pane.js): its ink mark, its name and its share left; a press opens what used it over the pane. */
function LimitChip({ l, from }) {
  const read = typeof l.left === "number", win = read ? windowOf(l) : "", level = read ? levelOf(l.left) : "unread", words = read ? `${l.name} ${Math.round(l.left * 100)}% left` : `${l.name}: not read`;
  return html`<button type="button" class=${cls("ork-chip table-chip", { [`is-${level}`]: true })} data-provider=${l.provider} title=${`${words}${win ? `, ${win}` : ""}: what has used it`}
    aria-label=${`${words}: what has used it`} onClick=${() => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`)}>
    ${MARKED.includes(l.provider) && html`<img class="ork-mark" src=${markSrc(l.provider)} srcset=${`${markSrc(l.provider, true)} 2x`} alt="" draggable="false" />`}${words}</button>`;
}

export function Tabs({ parties, all = parties, current, narrow, compact }) {
  const project = currentProject.value?.name || "The project", route = routeParties(picked.value), offer = useOffer();
  const from = { title: mapName(current, all), key: "" };
  const slugs = [ORKMASTER, ...parties.map((g) => g.slug)];
  const keys = (e) => {
    if (e.target.getAttribute?.("role") !== "tab") return;           // the head's and the marks' buttons beside a tab take their own keys
    const at = slugs.indexOf(current), to = e.key === "Home" ? 0 : e.key === "End" ? slugs.length - 1 : { ArrowRight: at + 1, ArrowLeft: at - 1 }[e.key];
    if (to === undefined || to < 0 || to >= slugs.length) return;
    e.preventDefault();
    openTab(slugs[to]);
    e.currentTarget.querySelectorAll("[role=tab]")[to]?.focus();
  };
  const switcher = html`<button type="button" class="ork-btn quiet table-switch" aria-label="Switch project" title="Switch project" onClick=${() => openOver("projects", {}, from, "Projects")}><${Icon} name="chevron-down" /></button>`;
  return html`<nav class="table-tabs" aria-label="Parties" data-compact=${String(compact)}>
    <div class="table-tabs__list" role="tablist" aria-label="Parties" onKeyDown=${keys}>
      <${Tab} slug=${ORKMASTER} on=${current === ORKMASTER} name=${project} who="the Orkmaster" head=${CROWN} switcher=${true} marks=${projectMarks()} compact=${compact} narrow=${narrow} onPick=${() => openTab(ORKMASTER)} after=${switcher} />
      ${parties.map((g) => html`<${Tab} key=${g.slug} slug=${g.slug} g=${g} on=${current === g.slug} name=${nameOf(g)} who=${g.leader?.name || ""} head=${g.leader?.head} dot=${route.has(g.slug)} working=${isWorking(g)} marks=${marksOf(g)}
        alert=${hasAlert(g) ? `${theLeader(g.leader?.name)} has an alert on the map` : ""} compact=${compact} narrow=${narrow} onPick=${() => openTab(g.slug)} />`)}
    </div>
    <div class="table-tabs__end">
      ${offer && html`<${EmptyChair} from=${from} narrow=${narrow} />`}
      <span class="table-grow"></span>
      <${StopDoor} narrow=${narrow} />
      <${LogsButton} />
    </div>
  </nav>
  <${AskBubble} tab=${current} parties=${all} />`;
}

export { LimitChip };
