// The pane (docs/specs/98-the-table-and-the-hand.md §3.2–§3.6, decisions §110, §142): its title — *<the picked goal> · through <whom>*, said **only for a goal picked** (decisions §247.5, spec 140 A3: with none picked the open tab already says whose eyes, so the title says nothing and the row keeps its back arrow and its …), or, with a thing opened over it, **←** and
// where it came from (*← System · server/lobby.ts*) — and, on the Orkmaster's tab, its **…** (the projects, Settings, Files, *Report a problem…*; under 760 px also the AI tools' limits). Play is no button of the title any more: it is the die in the hand (hand/playdie.js, spec 112 §3.2–§3.3,
// decisions §190.2), which opens and closes the same `play` view over this pane; under it the tab's map — the Board for the
// Orkmaster, a party's header and, for Tech, its System — or the one thing opened over it (`Over`, which draws whatever kind `frame/kinds.js` knows, the table's and the hand's). A card lifted where it lies is drawn over
// the map (card.js `Lifted`).
import { useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { presenceNow } from "./presence.js";
import { Icon } from "../orkui.js";
import { town } from "../link.js";
import { ORKMASTER, closeInventory, closeOver, inventory, lifted, openOver, over, picked } from "../frame/state.js";
import { KINDS, faceOf } from "../frame/kinds.js";
import { mapData, leaving } from "../shell/store.js";
import { PHASES, isRelease, leadsSystem, mapName, paneTitle, phaseOf } from "./data.js";
import { BoardMap } from "./boardmap.js";
import { mapOf } from "./maps.js";
import "./mapparts.js";                                     // the parties' maps (spec 102)
import { PickHost, PickStrip } from "./picking.js";         // picking on a party's map (spec 102 §6)
import { Heat } from "./heat.js";                         // what code found on a part: its hollow squares on every map (spec 165 H)
import { Concerns } from "./concerns.js";               // the leader's concerns on its map: the marks (spec 108 B, spec 123 C)
import { Header } from "./header.js";
import { SystemPane, PartBack, LinkBack } from "./syspane.js";
import { Earlier, PhaseView, RouteView, phaseKind } from "./phaseview.js";   // a goal picked: the table by its phase (spec 156 C)
import { nodeOf } from "./goalmap.js";
import { Lifted, OwnBack, TaskBack, litKey, mineKey } from "./card.js";
import { LimitChip } from "./tabs.js";
import { uprightNow } from "../frame/upright.js";
import { Stall } from "./stall.js";                          // the inventory: the merchant's stall, drawn instead of the map while it is open (spec 157 D)
import { stall } from "./stallstate.js";
import { Menu } from "./menu.js";
import { isForm } from "./over.js";
import { openParties } from "./parties.js";
import { DiscardEnd } from "./discard.js";                // the discard at the last column's foot (spec 104 C), at the narrow width; at the wide one it is Release's lane beside the pane (table/lane.js, spec 156 D.3)
import { ToMain } from "./tomain.js";                  // the picked ready card's act (spec 156 D.4)
import { ChecksView } from "./checksview.js";          // Release's table shows the checks on the way into main (spec 156 D.4)
import { PastGoal } from "./pastgoal.js";              // a goal of the past picked, as it was (spec 156 D.5)
import { openReport } from "../hand/logsbtn.js";      // the bug's panel opens from the Orkmaster's … (spec 139 A.5)
import { laidNow } from "./laying.js";
import { currentProject } from "../shell/projects.js";
import { setupNow } from "../hand/setupcards.js";
import { Notice } from "./notice.js";                    // the Orkmaster's line when the work moved to another tool (spec 105 D)
import { feltOf } from "./felt.js";                      // the open party's felt (spec 161 E)

/** ← or Esc: the map as it was left, the card the thing came from lit. */
export function back() {
  leaving(() => {                                                    // a file being edited asks first, in its editor
    const key = closeOver();
    if (key) litKey.value = key;
  });
}

/** The back of the lifted card, by its key (card.js): [name, content], or null when what it was is gone. */
function backOf(key, parties, tab) {
  const [, kind, ...rest] = key.split(":"), map = mapName(tab, parties), nodes = mapData.value?.nodes || [];
  if (kind === "task") {
    const [goal, task] = rest.join(":").split("/"), n = nodes.find((x) => x.slug === goal), t = n?.tasks.find((x) => x.id === task);
    return n && t ? [t.title, html`<${TaskBack} n=${n} t=${t} mapName=${map} />`] : null;
  }
  if (kind === "orc") {
    const n = nodes.find((x) => x.slug === rest.join(":"));
    return n ? [n.title, html`<${OwnBack} n=${n} />`] : null;
  }
  if (kind === "part") {
    const party = rest[0], path = rest.slice(1).join(":");
    return [path.split("/").pop() || path, html`<${PartBack} party=${party} path=${path} mapName=${map} />`];
  }
  if (kind === "link") {
    const party = rest[0], link = rest.slice(1).join(":");
    return [link.replace(">", " to "), html`<${LinkBack} party=${party} link=${link} />`];
  }
  return null;
}

/** What is open over the pane, drawn by the face registered for its kind. */
function Over() {
  const o = over.value, Face = faceOf(o.kind);
  return html`<div class=${cls("table-over", { "table-over--form": isForm(o) })} data-kind=${o.kind} data-owner=${KINDS[o.kind] || undefined}>
    ${Face ? html`<${Face} key=${o.kind + JSON.stringify(o.props || {})} props=${o.props || {}} close=${back} />` : html`<p class="ok-tone-muted table-over__wait">Opening…</p>`}
  </div>`;
}

/** The picked goal's phases in the pane's title, *Talk · Spec · Work · Done*: spans, no button (spec 156 C.2, decisions §261.4): the current one `aria-current="step"`, the ones gone by lit. What a phase says lies on the table (phaseview.js). */
function Phases({ goal }) {
  const now = phaseOf(goal), at = PHASES.findIndex(([id]) => id === now);
  if (at < 0) return null;
  return html`<nav class="table-phases" aria-label="The goal's phases" data-phase=${now}>${PHASES.map(([id, word], i) => {
    const state = i < at ? "past" : i === at ? "now" : "next", said = `${word}${state === "now" ? ", now" : state === "past" ? ", done" : ""}`;
    return html`<span key=${id} class=${cls("table-phase", { "is-past": state === "past", "is-now": state === "now" })} data-phase=${id} aria-current=${state === "now" ? "step" : undefined} aria-label=${said}>${word}</span>`;
  })}</nav>`;
}

/** The pane's title: *The whole project · through Tech*, or ← and *System · server/lobby.ts*. */
function Title({ parties, tab, narrow }) {
  const stalled = inventory.value !== null, o = over.value, where = o?.from?.title || "", code = o && (o.kind === "file" || (o.kind === "diff" && o.props?.path));
  const limits = town.value?.limits || [], from = { title: mapName(tab, parties), key: "" };
  const items = [["Settings", () => openOver("settings", {}, from, "Settings"), false, "sliders"], ...(currentProject.value ? [["Files", () => openOver("files", {}, from, "Files"), false, "folder"]] : []),
    ["Report a problem…", () => openReport(), false, "sign:bug"]];     // the bug left the top row (spec 139 A.5, decisions §246.6)   // Switch project is the ▾ after the project's name (tabs.js, spec 107 §8.2)
  return html`<header class=${cls("ork-head table-title", { "is-bare": !o && !picked.value })}>
    ${o && html`<button type="button" class="ork-btn quiet table-title__back" aria-label="Back" title="Back" onClick=${back}><${Icon} name="arrow-left" /></button>`}
    ${!o && stalled && uprightNow.value && html`<button type="button" class="ork-btn quiet table-title__back" data-stall-back aria-label="Close the inventory" title="Close the inventory" onClick=${closeInventory}><${Icon} name="arrow-left" /></button>`}
    <span class="table-title__pt" data-title>${o ? html`${where && html`${where} · `}<span class=${code ? "table-pathcase" : undefined}>${o.title}</span>` : stalled ? html`<span class="stall-title">Inventory</span> how the project is set · <b>${tab === ORKMASTER ? "the whole project" : stall.value?.whose || mapName(tab, parties)}</b>` : picked.value ? paneTitle(picked.value, tab, parties) : ""}</span>
    ${picked.value && !stalled && html`<${Phases} goal=${picked.value} />`}
    <span class="table-grow"></span>
    ${!o && tab === ORKMASTER && html`<${Menu} label="The Orkmaster's menu" items=${items}
      top=${narrow && limits.length > 0 ? html`<div class="table-menu__limits"><span class="ork-label">Limits</span><div class="table-menu__chips">${limits.map((l) => html`<${LimitChip} key=${l.provider} l=${l} from=${from} />`)}</div></div>` : null} />`}
  </header>`;
}

/** A party whose hero is not its craft's default lays the hero's table, even where the craft's own map is the System (spec 157 E): `mapOf` answers the hero's map first. */
const heroLaid = (g) => !!g?.leader?.hero && !g.leader.hero.default;

export function Pane({ parties, tab, narrow, column = false }) {
  const body = useRef(), o = over.value, g = parties.find((x) => x.slug === tab);
  const key = lifted.value, shown = mineKey(key) && !o ? backOf(key, parties, tab) : null;
  const bare = !laidNow(), form = isForm(o), stalled = inventory.value !== null && !o && !bare;      // the inventory open: the stall is the table (spec 157 D.2); a form or an open thing lies over it                // not laid yet: the table is bare (spec 130 C.6); a form covers the whole table, its end included (C.5)
  const from = { title: mapName(tab, parties), key: "" }, picks = nodeOf(picked.value), past = !o && !bare && !!picked.value && !picks && !!mapData.value && !narrow, kind = !o && !bare && picks ? phaseKind(tab === ORKMASTER ? null : g, picks) : "";     // a goal picked: what the table shows by its phase at this tab (phaseview.js)
  return html`<section class=${cls("table-pane ork-table", { "is-out": presenceNow()?.here === false, "ork-leather": stalled })} id="table-pane" data-party=${feltOf(g) || undefined} role="tabpanel" aria-labelledby=${`tab-${tab}`} data-stall=${stalled ? "open" : undefined}>
    <${Title} parties=${parties} tab=${tab} narrow=${narrow} />
    ${!o && !bare && !stalled && html`<${Notice} />`}
    ${!o && !bare && !stalled && html`<${ToMain} />`}
    ${!o && !bare && !stalled && g && isRelease(g) && html`<${ChecksView} />`}
    <div class="table-body" ref=${body} data-end=${form ? "form" : o && o.kind !== "discard" ? "over" : o || tab !== ORKMASTER ? "side" : "board"}>
      ${o ? html`<${Over} />` : stalled ? html`<${Stall} g=${g} />` : past ? html`<${PastGoal} idea=${picked.value} />` : bare ? (setupNow.value?.step === "parties" && html`<div class="table-empty"><p><button type="button" class="ork-btn primary" onClick=${() => openParties({ first: true }, from)}>Choose the parties</button></p></div>`) : tab === ORKMASTER ? html`<${PickStrip} tab=${tab} />${kind === "route" ? html`<${RouteView} n=${picks} />` : html`<${BoardMap} parties=${parties} narrow=${narrow} column=${column} />`}
          ${!parties.length && html`<div class="table-empty"><p>No parties yet</p>
            <p class="table-over__muted">Make a party, then write it a goal in plain words. Its orks do the work; you look at it before it goes in.</p>
            <p><button type="button" class="ork-btn primary" onClick=${() => openParties({ first: true }, from)}>Choose the parties</button></p></div>`}`
        : g && kind ? html`<${Header} key=${g.slug} g=${g} from=${from} /><${PhaseView} g=${g} n=${picks} kind=${kind} />`
        : g ? html`<${Header} key=${g.slug} g=${g} from=${from} /><${PickStrip} tab=${tab} /><${Concerns} key=${g.slug} g=${g}><${Heat} key=${g.slug} g=${g}><${PickHost} key=${g.slug} g=${g}>${leadsSystem(g) && !heroLaid(g) ? html`<${SystemPane} key=${g.slug} g=${g} />` : mapOf(g) ? html`<${mapOf(g)} key=${g.slug} g=${g} narrow=${narrow} />` : null}<//><//><//>` : null}
      ${!o && !bare && !stalled && picks && (tab === ORKMASTER || g) && html`<${Earlier} key=${`${tab}:${picks.slug}`} g=${tab === ORKMASTER ? null : g} n=${picks} />`}
      ${shown && html`<${Lifted} host=${body} name=${shown[0]} narrow=${narrow}>${shown[1]}</${Lifted}>`}
      ${!bare && !form && narrow && html`<${DiscardEnd} />`}
    </div>
  </section>`;
}

