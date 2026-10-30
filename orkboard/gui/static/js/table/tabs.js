// The tabs (docs/specs/98-the-table-and-the-hand.md §3.1, docs/specs/95-the-window-as-decided.md §2, decisions §167.6): the project's first — its crowned head and the project's name (*Party game*), then **▾** (*Switch project*, spec 107 §8.2) —, then a tab a party in the Board's order, its leader's
// head and the party's name (the head steps while one of its tasks runs: `data-working`, spec 107 §8.3), and under the name its **sword and shield**: the marks of the AI tools its Does and its Checks run on (tabmarks.js, docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.4, decisions §189;
// the title and the label say them: *Tech · Does on Claude · Checks on Codex*; the project's tab shows the main tool on both); at the end **+ Party** (*New party*) and **Stop all**; the AI tools' limits are the hand's mana (hand/mana.js, spec 104 B). Under 760 px the tabs are a row of heads, *Stop all* at the end,
// and the limits are in the Orkmaster's **…** as chips (pane.js) and in the hand as small potions. The tabs, the Board's lanes and the hand read the frame's one `--cols`, so a tab stands over its lane. A party's tab carries a dot when the picked goal's route has it.
// The open tab is the person's: nothing here switches it. A name is also said on a long press (nothing only on hover: spec 94 §1.1).
import { useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Icon, Sign } from "../orkui.js";
import { command, toast } from "../link.js";
import { ORKMASTER, openTab, openOver, picked } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { levelOf, windowOf } from "../arena/limits.js";
import { nameOf, routeParties, MARKED, markSrc, mapName, laneOf } from "./data.js";
import { openParties } from "./parties.js";
import { hasAlert, theLeader } from "./concerns.js";
import { Marks, marksOf, marksWords, projectMarks } from "./tabmarks.js";

const LONG_MS = 500;

/** A long press of a finger says the tab's name (a touch has no hover to say it). */
function usePressName(name) {
  const timer = useRef(0);
  return {
    onPointerDown: (e) => { if (e.pointerType === "touch") timer.current = setTimeout(() => toast(name, "information", "", 2), LONG_MS); },
    onPointerUp: () => clearTimeout(timer.current), onPointerLeave: () => clearTimeout(timer.current), onPointerCancel: () => clearTimeout(timer.current),
  };
}

/** A party has an ork at work: one of its goals has a task running or being tested (a task that asks or has failed is not at work). */
export const isWorking = (g) => laneOf(g).some(({ tasks }) => tasks.some((t) => t.state === "running" || t.state === "testing"));

function Tab({ slug, on, name, head, dot = false, working = false, alert = "", switcher = false, marks = null, compact, onPick }) {
  const press = usePressName(name), said = marks ? `${name} · ${marksWords(marks)}` : name;
  return html`<button type="button" class=${cls("ork-tab table-tab", { "is-compact": compact, "has-switch": switcher })} role="tab" id=${`tab-${slug}`} data-tab=${slug} data-working=${working ? "" : undefined} aria-selected=${String(on)} tabindex=${on ? 0 : -1}
    aria-label=${said} title=${said} aria-controls="table-pane" onClick=${onPick} ...${press}>
    ${head ? html`<${Head} race=${head.race} tier=${head.tier} />` : null}
    <span class="table-tab__txt"><span class="table-tab__main">${name}</span><${Marks} m=${marks} on=${on} /></span>
    ${dot && html`<i class="table-tab__dot" role="img" aria-label="On the picked goal's route" title="On the picked goal's route"></i>`}
    ${alert && html`<span class="table-tab__alert" role="img" aria-label=${alert} title=${alert}><${Sign} name="alert" /></span>`}
  </button>`;
}

/** One AI tool's chip, in the Orkmaster's **…** at the narrow width (pane.js): its ink mark, its name and its share left; a press opens what used it over the pane. */
function LimitChip({ l, from }) {
  const read = typeof l.left === "number", win = read ? windowOf(l) : "", level = read ? levelOf(l.left) : "unread";
  const words = read ? `${l.name} ${Math.round(l.left * 100)}% left` : `${l.name}: not read`;
  return html`<button type="button" class=${cls("ork-chip table-chip", { [`is-${level}`]: true })} data-provider=${l.provider} title=${`${words}${win ? `, ${win}` : ""}: what has used it`}
    aria-label=${`${words}: what has used it`} onClick=${() => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`)}>
    ${MARKED.includes(l.provider) && html`<img class="ork-mark" src=${markSrc(l.provider)} srcset=${`${markSrc(l.provider, true)} 2x`} alt="" draggable="false" />`}${words}</button>`;
}

export function Tabs({ parties, current, narrow, compact }) {
  const project = currentProject.value?.name || "The project", route = routeParties(picked.value);
  const from = { title: mapName(current, parties), key: "" };
  const slugs = [ORKMASTER, ...parties.map((g) => g.slug)];
  const keys = (e) => {
    const at = slugs.indexOf(current), to = e.key === "Home" ? 0 : e.key === "End" ? slugs.length - 1 : { ArrowRight: at + 1, ArrowLeft: at - 1 }[e.key];
    if (to === undefined || to < 0 || to >= slugs.length) return;
    e.preventDefault();
    openTab(slugs[to]);
    e.currentTarget.querySelectorAll("[role=tab]")[to]?.focus();
  };
  return html`<nav class="table-tabs" aria-label="Parties" data-compact=${String(compact)}>
    <div class="table-tabs__list" role="tablist" aria-label="Parties" onKeyDown=${keys}>
      <div class="table-tabcell" role="presentation">
        <${Tab} slug=${ORKMASTER} on=${current === ORKMASTER} name=${project} head=${{ race: "peon", tier: "crown" }} switcher=${true} marks=${projectMarks()} compact=${compact} onPick=${() => openTab(ORKMASTER)} />
        <button type="button" class="ork-btn quiet table-switch" aria-label="Switch project" title="Switch project" onClick=${() => openOver("projects", {}, from, "Projects")}><${Icon} name="chevron-down" /></button>
      </div>
      ${parties.map((g) => html`<${Tab} key=${g.slug} slug=${g.slug} on=${current === g.slug} name=${nameOf(g)} head=${g.leader?.head} dot=${route.has(g.slug)} working=${isWorking(g)} marks=${marksOf(g)} alert=${hasAlert(g) ? `${theLeader(g.leader?.name)} has an alert on the map` : ""} compact=${compact} onPick=${() => openTab(g.slug)} />`)}
    </div>
    <div class="table-tabs__end">
      <button type="button" class="ork-btn table-plus" aria-label="New party" title="New party" onClick=${() => openParties({}, from)}><${Icon} name="plus" /><span class="table-plus__w">Party</span></button>
      <button type="button" class="ork-btn danger table-stop" title="Stop every ork, script and browser at once" onClick=${() => command("halt").catch(() => {})}>Stop all</button>
    </div>
  </nav>`;
}

export { LimitChip };
