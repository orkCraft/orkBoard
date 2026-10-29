// The pane (docs/specs/98-the-table-and-the-hand.md §3.2–§3.6, decisions §110, §142): its title — *<what is looked at> · through <whom>* (*The whole project · through the Orkmaster*), or, with a thing opened over it, **←** and
// where it came from (*← System · server/lobby.ts*) —, **▶ Play** and, on the Orkmaster's tab, its **…** (the projects, Settings, Files; under 760 px also the AI tools' limits); under it the tab's map — the Board for the
// Orkmaster, a party's header and, for Tech, its System — or the one thing opened over it (`Over`, which draws whatever kind `frame/kinds.js` knows, the table's and the hand's). A card lifted where it lies is drawn over
// the map (card.js `Lifted`).
import { useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { town } from "../link.js";
import { ORKMASTER, closeOver, lifted, openOver, over, picked } from "../frame/state.js";
import { KINDS, faceOf } from "../frame/kinds.js";
import { mapData, leaving } from "../shell/store.js";
import { PHASES, leadsSystem, mapName, paneTitle, phaseOf } from "./data.js";
import { BoardMap } from "./boardmap.js";
import { mapOf } from "./maps.js";
import "./mapparts.js";                                     // the parties' maps (spec 102)
import { PickHost, PickStrip } from "./picking.js";         // picking on a party's map (spec 102 §6)
import { Header } from "./header.js";
import { SystemPane, PartBack, LinkBack } from "./syspane.js";
import { Lifted, OwnBack, TaskBack, litKey, mineKey } from "./card.js";
import { LimitChip } from "./tabs.js";
import { Menu } from "./menu.js";
import { isForm } from "./over.js";
import { openParties } from "./parties.js";
import { DiscardEnd } from "./discard.js";                // the discard at the last column's foot (spec 104 C)
import { Notice } from "./notice.js";                    // the Orkmaster's line when the work moved to another tool (spec 105 D)

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

/** The picked goal's phases in the pane's title, *Talk · Spec · Work · Done*: the current one marked, the ones gone by lit; *Talk* and *Spec* are pages (the stances, the sections), opened by a press once the goal is at them or past them
 *  (decisions §126.4). Work and Done are marks alone: their pane is the Board's. `from`: where the pane was (the page opened says it came from there). */
function Phases({ goal, from }) {
  const now = phaseOf(goal), at = PHASES.findIndex(([id]) => id === now), shown = over.value?.kind;
  if (at < 0) return null;
  return html`<nav class="table-phases" aria-label="The goal's phases" data-phase=${now}>${PHASES.map(([id, word], i) => {
    const state = i < at ? "past" : i === at ? "now" : "next", page = id === "talk" || id === "spec";
    const cls_ = cls("table-phase", { "is-past": state === "past", "is-now": state === "now", "is-open": shown === id });
    const said = `${word}${state === "now" ? ", now" : state === "past" ? ", done" : ""}`;
    return page && state !== "next"
      ? html`<button type="button" key=${id} class=${cls("ork-btn quiet", cls_)} data-phase=${id} aria-current=${state === "now" ? "step" : undefined} aria-pressed=${String(shown === id)} aria-label=${said}
          title=${`${word}: open it`} onClick=${() => { if (shown !== id) openOver(id, { idea: goal }, over.peek()?.from || from, word); }}>${word}</button>`
      : html`<span key=${id} class=${cls_} data-phase=${id} aria-current=${state === "now" ? "step" : undefined} aria-label=${said}>${word}</span>`;
  })}</nav>`;
}

/** The pane's title: *The whole project · through Tech*, or ← and *System · server/lobby.ts*. */
function Title({ parties, tab, narrow }) {
  const o = over.value, where = o?.from?.title || "", code = o && (o.kind === "file" || (o.kind === "diff" && o.props?.path));
  const play = () => { if (o?.kind !== "play") openOver("play", {}, o?.from || { title: mapName(tab, parties), key: "" }, "Play"); };
  const limits = town.value?.limits || [], from = { title: mapName(tab, parties), key: "" };
  const items = [["Switch project", () => openOver("projects", {}, from, "Projects"), false, "list-box"], ["Settings", () => openOver("settings", {}, from, "Settings"), false, "sliders"],
    ["Files", () => openOver("files", {}, from, "Files"), false, "folder"]];
  return html`<header class="ork-head table-title">
    ${o && html`<button type="button" class="ork-btn quiet table-title__back" aria-label="Back" title="Back" onClick=${back}><${Icon} name="arrow-left" /></button>`}
    <span class="table-title__pt" data-title>${o ? html`${where && html`${where} · `}<span class=${code ? "table-pathcase" : undefined}>${o.title}</span>` : paneTitle(picked.value, tab, parties)}</span>
    ${picked.value && html`<${Phases} goal=${picked.value} from=${from} />`}
    <span class="table-grow"></span>
    <button type="button" class="ork-btn table-play" aria-label="Play" title="Play: the project's preview of dev" onClick=${play}><${Icon} name="play" /><span class="table-play__w">Play</span></button>
    ${!o && tab === ORKMASTER && html`<${Menu} label="The Orkmaster's menu" items=${items}
      top=${narrow && limits.length > 0 ? html`<div class="table-menu__limits"><span class="ork-label">Limits</span><div class="table-menu__chips">${limits.map((l) => html`<${LimitChip} key=${l.provider} l=${l} from=${from} />`)}</div></div>` : null} />`}
  </header>`;
}

export function Pane({ parties, tab, narrow }) {
  const body = useRef(), o = over.value, g = parties.find((x) => x.slug === tab);
  const key = lifted.value, shown = mineKey(key) && !o ? backOf(key, parties, tab) : null;
  const from = { title: mapName(tab, parties), key: "" };
  return html`<section class="table-pane ork-table" id="table-pane" role="tabpanel" aria-labelledby=${`tab-${tab}`}>
    <${Title} parties=${parties} tab=${tab} narrow=${narrow} />
    ${!o && html`<${Notice} />`}
    <div class="table-body" ref=${body} data-end=${o && o.kind !== "discard" ? "over" : o || tab !== ORKMASTER ? "side" : "board"}>
      ${o ? html`<${Over} />` : tab === ORKMASTER ? html`<${PickStrip} tab=${tab} /><${BoardMap} parties=${parties} narrow=${narrow} />
          ${!parties.length && html`<div class="table-empty"><p>No parties yet</p>
            <p class="table-over__muted">Make a party, then write it a goal in plain words. Its orks do the work; you look at it before it goes in.</p>
            <p><button type="button" class="ork-btn primary" onClick=${() => openParties({ first: true }, from)}>Choose the parties</button></p></div>`}`
        : g ? html`<${Header} key=${g.slug} g=${g} from=${from} /><${PickStrip} tab=${tab} /><${PickHost} key=${g.slug} g=${g}>${leadsSystem(g) ? html`<${SystemPane} key=${g.slug} g=${g} />` : mapOf(g) ? html`<${mapOf(g)} key=${g.slug} g=${g} narrow=${narrow} />` : null}<//>` : null}
      ${shown && html`<${Lifted} host=${body} name=${shown[0]} narrow=${narrow}>${shown[1]}</${Lifted}>`}
      <${DiscardEnd} />
    </div>
  </section>`;
}

