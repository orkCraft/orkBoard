// The top bar (docs/specs/33-v1-shell.md §6, spec 49 §3.1, spec 52 §3.1, docs/specs/69-parties-in-the-column.md §1, spec 75 §5.5, docs/specs/91-the-owners-list.md §1): the product's name and *Settings* as a word
// on the left; on the right a chip for each AI tool whose limits the snapshot has (its mark, its name, its share left, its window) and *Stop all*. A chip opens, under it, the panel of arena/limits.js with
// today's *Spend* and *Last week* (the week's work). *Agents* and *Files* are not here: the files are in the Orkmaster's *Assets and files*. The project switcher and the parties are the left column's.
// Roles only: warning at 20 % or less left, danger at 5 % or less (docs/design-system.md).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { ORKUI } from "../orkui.js";
import { town, command, say, PRODUCT } from "../link.js";
import { openDialog } from "./modals.js";
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

const MARKED = ["claude", "codex", "agy", "cursor", "hermes", "pi"];
const pct = (left) => `${Math.round(left * 100)} %`;

/** The window a chip names: the tightest row's (*5h*, *week*), "" with none. */
export const windowOf = (l) => [...(l.rows || [])].sort((a, b) => a.left - b.left)[0]?.window || "";

/** One AI tool's chip: its mark, its name, its share left and its window, in the warning colour at 20 % or less, danger at 5 %; a tool whose limits were not read shows its name and a dash.
 *  A press opens (or closes) the panel under the chips. */
function Chip({ l, open, press }) {
  const read = typeof l.left === "number", win = read ? windowOf(l) : "";
  const words = read ? `${l.name} ${pct(l.left)} left${win ? `, ${win}` : ""}` : `${l.name}: limits not read`;
  return html`<button type="button" class=${cls("shell-top__chip", { [`is-${read ? levelOf(l.left) : "unread"}`]: true })} data-provider=${l.provider}
    aria-expanded=${String(open)} aria-controls="shell-limits" aria-label=${words} title=${`${words}. What is left of your AI tools`} onClick=${press}>
    ${MARKED.includes(l.provider) && html`<img class="ork-mark" src=${`${ORKUI}/marks/harness-${l.provider}-ink.png`} srcset=${`${ORKUI}/marks/harness-${l.provider}-ink@2x.png 2x`} alt="" draggable="false" />`}
    <span class="shell-top__chipname">${l.name}</span> <b>${read ? pct(l.left) : "—"}</b>${win && html`<span class="shell-top__chipwin">${win}</span>`}</button>`;
}

/** The chips and, under the one pressed, the panel: every tool's line (limits.js), today's *Spend* (a press opens the week's work) and *Last week*. Esc, a press elsewhere, or the same chip closes it.
 *  With no tool's limits in the snapshot there is one chip, *Spend*, for the same panel. */
function Chips() {
  const [open, setOpen] = useState(""), box = useRef();
  const limits = town.value?.limits || [], hud = town.value?.hud || {}, spend = hud.show_gold ? hud.gold : hud.lumber;
  useEffect(() => {
    if (!open) return undefined;
    const away = (e) => { if (!box.current?.contains(e.target)) setOpen(""); };
    addEventListener("pointerdown", away, true);
    return () => removeEventListener("pointerdown", away, true);
  }, [open]);
  const press = (id) => () => setOpen(open === id ? "" : id);
  const chips = limits.length ? limits.map((l) => html`<${Chip} key=${l.provider} l=${l} open=${open === l.provider} press=${press(l.provider)} />`)
    : html`<button type="button" class="shell-top__chip" aria-expanded=${String(!!open)} aria-controls="shell-limits" aria-label=${`Spend today: ${spend ?? "—"}`} onClick=${press("spend")}>
        <span class="shell-top__chipname">Spend</span> <b>${spend ?? "—"}</b></button>`;
  return html`<div class="shell-top__chips" ref=${box} onKeyDown=${(e) => { if (e.key === "Escape" && open) { e.stopPropagation(); box.current?.querySelector("[aria-expanded=true]")?.focus(); setOpen(""); } }}>
    ${chips}
    ${open && html`<div class="shell-top__limits" id="shell-limits" data-open=${open}>
      ${limits.length > 0 && html`<${Limits} provider=${open} />`}
      <button type="button" class="shell-top__spend" title="What was spent today. This week's work" aria-haspopup="dialog"
        aria-label=${`Spend today: ${spend ?? "—"}. This week's work`} onClick=${() => { setOpen(""); openDialog("this_week"); }}><span class="ok-tone-muted">Spend today</span> <b>${spend ?? "—"}</b></button>
      <${MapFoot} />
    </div>`}
  </div>`;
}

export function TopBar() {
  return html`<header class="shell-top">
    <span class="shell-top__brand">${PRODUCT}</span>
    <button type="button" class="ork-btn quiet shell-top__settings" aria-haspopup="dialog" onClick=${() => openDialog("settings")}>Settings</button>
    <span class="shell-top__spacer"></span>
    <${Chips} />
    <button class="ork-btn danger" title=${say("Stop every ork, script and browser at once")}
      onClick=${() => command("halt").catch(() => {})}>Stop all</button>
  </header>`;
}
