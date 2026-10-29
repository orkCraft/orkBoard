// The tabs (docs/specs/98-the-table-and-the-hand.md §3.1, docs/specs/95-the-window-as-decided.md §2, decisions §167.6): the project's first — its crowned head and the project's name (*Party game*) —, then a tab a party in the Board's order, its leader's
// head and the party's name; at the end **+** (*New party*) and **Stop all**; the AI tools' limits are the hand's mana (hand/mana.js, spec 104 B). Under 760 px the tabs are a row of heads, *Stop all* at the end,
// and the limits are in the Orkmaster's **…** as chips (pane.js) and in the hand as small potions. The tabs, the Board's lanes and the hand read the frame's one `--cols`, so a tab stands over its lane. A party's tab carries a dot when the picked goal's route has it.
// The open tab is the person's: nothing here switches it. A name is also said on a long press (nothing only on hover: spec 94 §1.1).
import { useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { command, toast } from "../link.js";
import { ORKMASTER, openTab, openOver, picked } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { levelOf, windowOf } from "../arena/limits.js";
import { nameOf, routeParties, MARKED, markSrc, mapName } from "./data.js";
import { openParties } from "./parties.js";

const LONG_MS = 500;

/** A long press of a finger says the tab's name (a touch has no hover to say it). */
function usePressName(name) {
  const timer = useRef(0);
  return {
    onPointerDown: (e) => { if (e.pointerType === "touch") timer.current = setTimeout(() => toast(name, "information", "", 2), LONG_MS); },
    onPointerUp: () => clearTimeout(timer.current), onPointerLeave: () => clearTimeout(timer.current), onPointerCancel: () => clearTimeout(timer.current),
  };
}

function Tab({ slug, on, name, head, dot = false, compact, onPick }) {
  const press = usePressName(name);
  return html`<button type="button" class=${cls("ork-tab table-tab", { "is-compact": compact })} role="tab" id=${`tab-${slug}`} data-tab=${slug} aria-selected=${String(on)} tabindex=${on ? 0 : -1}
    aria-label=${name} title=${name} aria-controls="table-pane" onClick=${onPick} ...${press}>
    ${head ? html`<${Head} race=${head.race} tier=${head.tier} />` : null}
    <span class="table-tab__txt"><span class="table-tab__main">${name}</span></span>
    ${dot && html`<i class="table-tab__dot" role="img" aria-label="On the picked goal's route" title="On the picked goal's route"></i>`}
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
      <${Tab} slug=${ORKMASTER} on=${current === ORKMASTER} name=${project} head=${{ race: "peon", tier: "crown" }} compact=${compact} onPick=${() => openTab(ORKMASTER)} />
      ${parties.map((g) => html`<${Tab} key=${g.slug} slug=${g.slug} on=${current === g.slug} name=${nameOf(g)} head=${g.leader?.head} dot=${route.has(g.slug)} compact=${compact} onPick=${() => openTab(g.slug)} />`)}
    </div>
    <div class="table-tabs__end">
      <button type="button" class="ork-btn table-plus" aria-label="New party" title="New party" onClick=${() => openParties({}, from)}><${Icon} name="plus" /></button>
      <button type="button" class="ork-btn danger table-stop" title="Stop every ork, script and browser at once" onClick=${() => command("halt").catch(() => {})}>Stop all</button>
    </div>
  </nav>`;
}

export { LimitChip };
