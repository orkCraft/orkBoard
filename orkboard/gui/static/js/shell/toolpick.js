// A party's AI tool, picked from a list that drops down (docs/specs/81-a-party-its-tool-and-size.md §4.1, decisions §98): orkUI's `.ork-select` around a native `<select>`, *Main tool (Claude Code)*
// first and picked, then the tools in groups — **Ready**, **Not signed in**, **Not installed** (shown, never picked: disabled) — as `ideas.tools` gives them (the host reads what Settings' tool rows read; it runs nothing).
// A tool with no tiers says it *runs its own model*. A row not signed in, picked, opens its sign-in (the flow of spec 45, `signin.js`) and stays picked: the party's work waits for it. A host without `ideas.tools`
// (an older one) has no list: `useTools` gives null and the field is not drawn.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command, town } from "../link.js";
import { signIn } from "./signin.js";

/** The three groups, in the order the host sorts them: [id, word, whether a tool is in it]. */
export const TOOL_GROUPS = [["ready", "Ready", (t) => t.ready], ["signed", "Not signed in", (t) => t.installed && !t.signed_in], ["missing", "Not installed", (t) => !t.installed]];

/** `ideas.tools`: `{main, tools}`, or null while it is asked or when the host has none. Asked again whenever a sign-in begins or ends. */
export function useTools() {
  const [got, setGot] = useState(null);
  const sig = JSON.stringify((town.value?.sign_in || []).map((e) => [e.harness, e.state]));
  useEffect(() => {
    let live = true;
    command("ideas.tools", {}, true).then((a) => { if (live && a && Array.isArray(a.tools)) setGot(a); }).catch(() => {});
    return () => { live = false; };
  }, [sig]);
  return got;
}

/** The tool a party runs on: its own, else the Main tool (a row of `ideas.tools`); undefined when the list is not known. */
export const toolRow = (tools, id) => tools?.tools.find((t) => t.id === (id || tools.main));

/** Whether the tool the party would run on has no tiers of its own: it runs its own model, so a size's tiers and its price do not apply. */
export const runsOwn = (tools, id) => toolRow(tools, id)?.tiers === false;

const word = (t) => `${t.name}${t.tiers ? "" : " · runs its own model"}`;

/** **Its AI tool**. `value`: the party's tool ("" the Main tool); `onChange(id)`. `id`: the select's id (one on a page). */
export function ToolPick({ tools, value = "", onChange, id = "party-tool", label = "Its AI tool" }) {
  if (!tools) return null;
  const main = toolRow(tools, "");
  const picked = tools.tools.find((t) => t.id === value);
  const pick = (v) => {
    onChange(v);
    const t = tools.tools.find((x) => x.id === v);
    if (t && t.installed && !t.signed_in) signIn(v);               // its sign-in opens; the tool stays picked
  };
  const shown = value && picked ? picked : null;
  return html`<div class="shell-field shell-tool" role="group" aria-label=${label} data-tool=${value}>
    <label class="ok-font-label" for=${id}>${label}</label>
    <div class="ork-select"><select id=${id} class="ork-field" value=${value} onChange=${(e) => pick(e.target.value)}>
      <option value="" selected=${!value}>${`Main tool (${main?.name || "Claude Code"})${main && !main.tiers ? " · runs its own model" : ""}`}</option>
      ${TOOL_GROUPS.map(([gid, name, has]) => {
        const rows = tools.tools.filter(has);
        return rows.length ? html`<optgroup key=${gid} label=${name} data-group=${gid}>${rows.map((t) => html`<option key=${t.id} value=${t.id} selected=${t.id === value}
          disabled=${gid === "missing" && t.id !== value}>${word(t)}</option>`)}</optgroup>` : null;
      })}
    </select></div>
    ${shown && !shown.signed_in && shown.installed && html`<small class="shell-tool__hint ok-tone-muted">Not signed in: its sign-in opens, and the party's work waits for it.</small>`}
  </div>`;
}
