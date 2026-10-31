// A party's sword and shield on its tab (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.4, decisions §189): under the tab's name a second line, orkUI's `sword` and the mark of the AI tool the party's **Does** run
// on, then its `shield` and the mark of the tool its **Checks** run on (`marks/harness-<id>-ink.png`, 14 px, in ink; the open tab's in colour). A column whose roles run on more than one tool shows the most used with a small dot; a **Lean** party
// (no separate check) shows the shield faint with no mark. The map serves what is needed on the party's node (`does_tool`, `checks_tool`, `does_mixed`, `checks_mixed`, `lean`: gui/ideas_map.py `marks_of`); the project's tab shows the machine's
// main tool on both (`town.mana.main`). Words on hover and for a screen reader: *Does on Claude · Checks on Codex* (*no separate check* for Lean). Not pressable (it lies inside the tab's button): the tools are changed in the party's editor.
// A tool with no mark of its own shows its initial. A potion hovered or focused marks its tool's marks on the tabs (`markedTool`, hand/mana.js): a 1 px ink outline. The narrow width's tabs are heads only: no second line (table.css).
// Whether a side follows the default (docs/specs/114-the-mana-in-two-windows.md §3.5, decisions §192.4; the node's `does_default`, `checks_default`: gui/ideas_map.py): a side that does is drawn **in a small frame** (1 px of ink, orkUI's notch,
// the default potion's frame) and shows the tool now (`town.mana.now`, else the Main tool), changing when the work moves on; a side set to a tool on purpose is a **bare mark**, dim with orkUI's `moon` beside it while that tool is dry (a
// window of it at 0: hand/windows.js). A potion that is the default's, hovered or focused, outlines the framed marks too (`markedDefault`). The words: *Does on the default (now Claude Code)*, *Does on Claude Code, set for this party*,
// *Does waits for Claude Code until Thu 09:00*, the same for Checks. A host that does not say (no `does_default`) draws bare marks and the words of before.
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { town } from "../link.js";
import { markedDefault, markedTool } from "../hand/state.js";
import { windowsOf } from "../hand/windows.js";
import { untilWords } from "../arena/arenawords.js";
import { MARKED, markSrc } from "./data.js";

/** A tool's name as the potions say it (the limits' own), else its id with a capital. */
export function toolName(id) {
  const l = (town.value?.limits || []).find((x) => x.provider === id);
  return l?.name || (id ? id.charAt(0).toUpperCase() + id.slice(1) : "");
}

/** The tool the work goes to when a side follows the default: the tool now (`town.mana.now`), else the machine's Main tool; `fallback` while the snapshot says neither. */
const defaultTool = (fallback = "") => town.value?.mana?.now || town.value?.mana?.main || fallback;

/** The marks of a party's tab, from its map node: `{does, checks, doesMixed, checksMixed, lean, doesMode, checksMode}`; null while the node has none (a host that does not say). A side's mode is `"default"` (it follows the default: its tool is the one
 *  now), `"set"` (a tool set on purpose) or `""` (the host does not say: drawn bare, in the words of before). */
export function marksOf(g) {
  if (!g?.does_tool) return null;
  const mode = (flag, tool) => (!tool ? "" : flag === true ? "default" : flag === false ? "set" : "");
  const doesMode = mode(g.does_default, g.does_tool), checksMode = mode(g.checks_default, g.checks_tool);
  return { does: doesMode === "default" ? defaultTool(g.does_tool) : g.does_tool, checks: checksMode === "default" ? defaultTool(g.checks_tool) : g.checks_tool || "", doesMixed: !!g.does_mixed, checksMixed: !!g.checks_mixed, lean: !!g.lean, doesMode, checksMode };
}

/** When a tool is dry, the time it is back (*Thu 09:00*, "" when the reader does not say) and null while it has room (or its limits are not read): the set mark of a dry tool is dim with the moon. */
export function dryUntil(id) {
  const l = (town.value?.limits || []).find((x) => x.provider === id), w = l ? windowsOf(l) : null;
  return w?.dry ? untilWords(w.back) || "" : null;
}

/** The project's tab: the machine's main tool on both, null while the snapshot does not say. */
export function projectMarks() {
  const main = town.value?.mana?.main || "";
  return main ? { does: main, checks: main, doesMixed: false, checksMixed: false, lean: false } : null;
}

/** One side in words: *Does on the default (now Claude Code)*, *Does on Claude Code, set for this party*, *Does waits for Claude Code until Thu 09:00*; with no mode (the host does not say) *Does on Claude Code*. A column that mixes tools says *and others*. */
export function sideWords(verb, tool, mode, mixed) {
  const name = toolName(tool), others = mixed ? " and others" : "";
  if (mode === "default") return `${verb} on the default (now ${name})`;
  const dry = mode === "set" ? dryUntil(tool) : null;
  if (dry !== null) return `${verb} waits for ${name}${others}${dry ? ` until ${dry}` : ""}`;
  return `${verb} on ${name}${others}${mode === "set" ? ", set for this party" : ""}`;
}

/** *Does on the default (now Claude Code) · Checks on Codex, set for this party*; *Does on Claude · no separate check* for a Lean party; a column that mixes tools says *and others*. */
export function marksWords(m) {
  if (!m) return "";
  return `${sideWords("Does", m.does, m.doesMode, m.doesMixed)} · ${m.lean ? "no separate check" : sideWords("Checks", m.checks, m.checksMode, m.checksMixed)}`;
}

/** One tool's mark: its ink mark (its colour on the open tab), its initial with none; outlined while its potion is hovered or focused (and, for a side that follows the default, while the default's potion is). `mode`: the side's
 *  (see `marksOf`): `"default"` draws it in a small frame, a `"set"` tool that is dry dim with the moon beside it. */
export function Mark({ id, on, mode = "" }) {
  const dry = mode === "set" ? dryUntil(id) !== null : false, marked = markedTool.value === id || (mode === "default" && markedDefault.value);
  const one = !MARKED.includes(id)
    ? html`<span class=${cls("table-tab__initial", { "is-marked": marked })} data-tool=${id} aria-hidden="true">${toolName(id).charAt(0).toUpperCase()}</span>`
    : html`<img class=${cls("ork-mark table-tab__mark", { "is-marked": marked })} data-tool=${id} src=${markSrc(id, false, on)} srcset=${`${markSrc(id, true, on)} 2x`} alt="" draggable="false" />`;
  if (mode === "default") return html`<span class="table-tab__follow" data-mode="default">${one}</span>`;
  return dry ? html`<span class="table-tab__dry" data-mode="dry">${one}<${Sign} name="moon" /></span>` : one;
}

/** The second line of a tab: the sword and its tool's mark, the shield and its tool's mark (faint with none for a Lean party). `on`: the open tab, whose marks are in colour. */
export function Marks({ m, on = false }) {
  if (!m) return null;
  return html`<span class="table-tab__marks" aria-hidden="true">
    <${Sign} name="sword" /><${Mark} id=${m.does} on=${on} mode=${m.doesMode} />${m.doesMixed && html`<i class="table-tab__more"></i>`}
    <i class="table-tab__gap"></i>
    ${m.lean ? html`<span class="table-tab__off"><${Sign} name="shield" /></span>` : html`<${Sign} name="shield" /><${Mark} id=${m.checks} on=${on} mode=${m.checksMode} />${m.checksMixed && html`<i class="table-tab__more"></i>`}`}
  </span>`;
}
