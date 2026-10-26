// A seat's AI tool (docs/specs/91-the-owners-list.md §6, §7, decisions §107.4): the button on a seat's row shows the tool's mark and name — *Party's tool · Claude Code* by default — and opens a list under
// it. Its first row is *The party's tool (<name>)*; then the group **Can do what <role> needs** (the ready tools whose `makes` covers the role's `needs`; all the ready ones for a role that needs nothing)
// and **Cannot make pictures** / **Cannot make sound** (or **Cannot run yet**), each tool with its mark, its name, what it makes and which model its tier runs, *experimental* in the alert colour, and
// the reason it cannot in words (*draws no pictures*, *not installed*, *not signed in*). A tool that cannot do the need may still be picked — the person decides; only a tool that is not installed
// is shown and not taken. No tool makes sound today: the first group then says so plainly, and every tool is listed under *Cannot make sound*, pickable. The tier comes from the party's size.
// A tool not signed in, picked, opens its sign-in (spec 45) and stays picked.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { ORKUI } from "../orkui.js";
import { Chev } from "../orkui.js";
import { Pop } from "./partypop.js";
import { signIn } from "./signin.js";
import { toolCaption, toolGroups } from "./partymodel.js";
import { toolRow } from "./toolpick.js";

const MARKED = ["claude", "codex", "agy", "cursor", "hermes", "pi"];

/** A tool's mark (orkUI's marks/), nothing for a tool it draws none for. */
export const Mark = ({ id }) => MARKED.includes(id) ? html`<img class="ork-mark" src=${`${ORKUI}/marks/harness-${id}.png`} srcset=${`${ORKUI}/marks/harness-${id}@2x.png 2x`} alt="" draggable="false" />` : null;

function Row({ t, picked, onPick }) {
  const off = !t.installed && !picked;
  return html`<button type="button" class=${cls("shell-pop__row", { "is-off": off })} data-tool=${t.id} aria-pressed=${String(picked)} disabled=${off} onClick=${() => onPick(t.id)}>
    <${Mark} id=${t.id} /><span class="shell-pop__text"><b>${t.name}${t.experimental && html` <span class="shell-pop__alert" data-experimental>experimental</span>`}</b>
      <small class="ok-tone-muted">${t.caption}${t.reason ? html` · <span class="shell-pop__why" data-why>${t.reason}</span>` : ""}</small></span></button>`;
}

/** **Its AI tool** on a seat. `tools`: `ideas.tools` (null: not drawn); `partyTool`: the party's ("" the Main tool); `value`: the seat's ("" the party's); `role`: the library entry (name, needs); `tier`: the seat's. */
export function SeatTool({ tools, partyTool = "", role, tier, value = "", onPick }) {
  const [open, setOpen] = useState(false);
  if (!tools) return null;
  const party = toolRow(tools, partyTool), shown = value ? tools.tools.find((t) => t.id === value) : null, mark = shown || party;
  const groups = toolGroups(tools, role), say = (t) => ({ ...t, caption: toolCaption(t, tier) });
  const pick = (id) => {
    setOpen(false);
    onPick(id);
    const t = tools.tools.find((x) => x.id === id);
    if (t && t.installed && !t.signed_in) signIn(id);               // its sign-in opens; the tool stays picked
  };
  return html`<div class="shell-seat__tool">
    <button type="button" class="ork-btn shell-seat__toolbtn" data-seat-tool=${role?.id} data-tool=${value} aria-haspopup="true" aria-expanded=${String(open)}
      aria-label=${`Its AI tool for ${role?.name}: ${shown ? shown.name : `Party's tool · ${party?.name || "Claude Code"}`}`} onClick=${() => setOpen(!open)}>
      <${Mark} id=${mark?.id} /><span>${shown ? shown.name : `Party's tool · ${party?.name || "Claude Code"}`}</span><${Chev} /></button>
    ${open && html`<${Pop} label=${`Its AI tool for ${role?.name}`} onClose=${() => setOpen(false)} cls="shell-pop--tools">
      <button type="button" class="shell-pop__row" data-tool="" aria-pressed=${String(!value)} onClick=${() => pick("")}>
        <${Mark} id=${party?.id} /><span class="shell-pop__text"><b>The party's tool (${party?.name || "Claude Code"})</b></span></button>
      <section aria-label=${groups.canTitle} data-group="can"><h4 class="ok-font-label">${groups.canTitle}</h4>
        ${groups.none && html`<p class="ok-tone-muted shell-pop__none" data-none>${groups.none}</p>`}
        ${groups.can.map((t) => html`<${Row} key=${t.id} t=${say(t)} picked=${value === t.id} onPick=${pick} />`)}</section>
      ${groups.cannot.length > 0 && html`<section aria-label=${groups.cannotTitle} data-group="cannot"><h4 class="ok-font-label">${groups.cannotTitle}</h4>
        ${groups.cannot.map((t) => html`<${Row} key=${t.id} t=${say(t)} picked=${value === t.id} onPick=${pick} />`)}</section>`}
      <p class="ok-tone-muted shell-pop__foot">The tier comes from the party's size. Each tool runs its own model for it.</p>
    <//>`}</div>`;
}
