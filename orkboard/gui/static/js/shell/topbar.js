// The top bar (docs/specs/33-v1-shell.md §6, spec 49 §3.1, spec 52 §3.1, docs/specs/69-parties-in-the-column.md §1, spec 75 §5.5): Orkline · Agents and Files (the right column's
// panes) · today's Spend and, under it, what is left of the AI tools (docs/specs/90-what-the-first-look-said.md §2.3: arena/limits.js, in a panel a press on the tightest tool's share opens, with
// *Last week*) · Stop all · the gear. The project switcher and the parties are the left column's (arena/partylist.js), not the top bar's.
// Roles only: warning at 20 % or less left, danger at 5 % or less (docs/design-system.md).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Chev, Icon } from "../orkui.js";
import { town, command, say, PRODUCT } from "../link.js";
import { showAgents, showFiles } from "./store.js";
import { openDialog } from "./modals.js";
import { currentProject, projectsOn } from "./projects.js";
import { Limits } from "../arena/limits.js";
import { MapFoot } from "../board/mapfoot.js";

export const WARN = 0.2, DANGER = 0.05;

export const levelOf = (left) => (left <= DANGER ? "danger" : left <= WARN ? "warn" : "ok");

/** "resets at 18:00", or with the day when it is not today. */
export function resetWords(iso, now = new Date()) {
  const d = new Date(iso);
  if (!iso || Number.isNaN(d.getTime())) return "";
  const hm = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  return d.toDateString() === now.toDateString() ? `resets at ${hm}` : `resets ${d.toLocaleDateString([], { weekday: "short" })} ${hm}`;
}

function Gear() {
  return html`<button class="ork-btn" aria-label="Settings" aria-haspopup="dialog" onClick=${() => openDialog("settings")}><${Icon} name="sliders" /></button>`;
}

/** The tool with the least left (its name and share), or null when no tool's limits were read. */
export function tightest(limits) {
  const read = (limits || []).filter((l) => typeof l.left === "number");
  return read.length ? read.reduce((a, b) => (b.left < a.left ? b : a)) : null;
}

/** Under *Spend*: the tightest tool's share left (in the warning colour at 20 % or less, danger at 5 %), a press opens the panel of every tool's line (limits.js) and *Last week*.
 *  Esc, a press elsewhere, or the same press closes it. With no limits in the snapshot, *Last week* alone. */
function Left() {
  const [open, setOpen] = useState(false), box = useRef();
  const limits = town.value?.limits || [], tight = tightest(limits);
  useEffect(() => {
    if (!open) return undefined;
    const away = (e) => { if (!box.current?.contains(e.target)) setOpen(false); };
    addEventListener("pointerdown", away, true);
    return () => removeEventListener("pointerdown", away, true);
  }, [open]);
  if (!limits.length) return html`<${MapFoot} />`;                                   // no tool's limits: Last week alone, beside Spend
  const words = tight ? `${tight.name} ${Math.round(tight.left * 100)} %` : "limits not read";
  return html`<div class="shell-top__left" ref=${box} onKeyDown=${(e) => { if (e.key === "Escape" && open) { e.stopPropagation(); setOpen(false); box.current?.querySelector("button")?.focus(); } }}>
    <button type="button" class=${cls("shell-top__leftbtn", tight && `is-${levelOf(tight.left)}`)} aria-expanded=${String(open)} aria-controls="shell-limits"
      aria-label=${`What is left of your AI tools: ${words}`} title="What is left of your AI tools" onClick=${() => setOpen(!open)}>${words}<${Chev} dir=${open ? "up" : "down"} /></button>
    ${open && html`<div class="shell-top__limits" id="shell-limits"><${Limits} /><${MapFoot} /></div>`}
  </div>`;
}

export function TopBar() {
  const hud = town.value?.hud || {};
  const spend = hud.show_gold ? hud.gold : hud.lumber;
  const shown = !projectsOn.value || !!currentProject.value?.path;      // the window is behind the project: the start screen has no right column
  return html`<header class="shell-top">
    <span class="shell-top__brand">${PRODUCT}</span>
    <span class="shell-top__spacer"></span>
    ${shown && html`<button type="button" class="ork-btn" title="The agents, what each takes and is doing" onClick=${() => showAgents()}>Agents</button>`}
    ${shown && projectsOn.value && html`<button type="button" class="ork-btn" title="The project’s files" onClick=${() => showFiles()}>Files</button>`}
    <div class="shell-top__money">
      <button type="button" class="shell-top__spend" title="What was spent today. This week's work" aria-haspopup="dialog"
        aria-label=${`Spend today: ${spend ?? "—"}. This week's work`} onClick=${() => openDialog("this_week")}><span class="ok-tone-muted">Spend</span> <b>${spend ?? "—"}</b></button>
      <${Left} />
    </div>
    <button class="ork-btn danger" title=${say("Stop every ork, script and browser at once")}
      onClick=${() => command("halt").catch(() => {})}>Stop all</button>
    <${Gear} />
  </header>`;
}
