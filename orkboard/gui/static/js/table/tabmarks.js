// A party's sword and shield on its tab (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.4, decisions §189): under the tab's name a second line, orkUI's `sword` and the mark of the AI tool the party's **Does** run
// on, then its `shield` and the mark of the tool its **Checks** run on (`marks/harness-<id>-ink.png`, 14 px, in ink; the open tab's in colour). A column whose roles run on more than one tool shows the most used with a small dot; a **Lean** party
// (no separate check) shows the shield faint with no mark. The map serves what is needed on the party's node (`does_tool`, `checks_tool`, `does_mixed`, `checks_mixed`, `lean`: gui/ideas_map.py `marks_of`); the project's tab shows the machine's
// main tool on both (`town.mana.main`). Words on hover and for a screen reader: *Does on Claude · Checks on Codex* (*no separate check* for Lean). Not pressable (it lies inside the tab's button): the tools are changed in the party's editor.
// A tool with no mark of its own shows its initial. A potion hovered or focused marks its tool's marks on the tabs (`markedTool`, hand/mana.js): a 1 px ink outline. The narrow width's tabs are heads only: no second line (table.css).
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { town } from "../link.js";
import { markedTool } from "../hand/state.js";
import { MARKED, markSrc } from "./data.js";

/** A tool's name as the potions say it (the limits' own), else its id with a capital. */
export function toolName(id) {
  const l = (town.value?.limits || []).find((x) => x.provider === id);
  return l?.name || (id ? id.charAt(0).toUpperCase() + id.slice(1) : "");
}

/** The marks of a party's tab, from its map node: `{does, checks, doesMixed, checksMixed, lean}`; null while the node has none (a host that does not say). */
export function marksOf(g) {
  if (!g?.does_tool) return null;
  return { does: g.does_tool, checks: g.checks_tool || "", doesMixed: !!g.does_mixed, checksMixed: !!g.checks_mixed, lean: !!g.lean };
}

/** The project's tab: the machine's main tool on both, null while the snapshot does not say. */
export function projectMarks() {
  const main = town.value?.mana?.main || "";
  return main ? { does: main, checks: main, doesMixed: false, checksMixed: false, lean: false } : null;
}

/** *Does on Claude · Checks on Codex*; *Does on Claude · no separate check* for a Lean party; a column that mixes tools says *and others*. */
export function marksWords(m) {
  if (!m) return "";
  const does = `Does on ${toolName(m.does)}${m.doesMixed ? " and others" : ""}`;
  return `${does} · ${m.lean ? "no separate check" : `Checks on ${toolName(m.checks)}${m.checksMixed ? " and others" : ""}`}`;
}

/** One tool's mark: its ink mark (its colour on the open tab), its initial with none; outlined while its potion is hovered or focused. */
function Mark({ id, on }) {
  const marked = markedTool.value === id;
  if (!MARKED.includes(id)) return html`<span class=${cls("table-tab__initial", { "is-marked": marked })} data-tool=${id} aria-hidden="true">${toolName(id).charAt(0).toUpperCase()}</span>`;
  return html`<img class=${cls("ork-mark table-tab__mark", { "is-marked": marked })} data-tool=${id} src=${markSrc(id, false, on)} srcset=${`${markSrc(id, true, on)} 2x`} alt="" draggable="false" />`;
}

/** The second line of a tab: the sword and its tool's mark, the shield and its tool's mark (faint with none for a Lean party). `on`: the open tab, whose marks are in colour. */
export function Marks({ m, on = false }) {
  if (!m) return null;
  return html`<span class="table-tab__marks" aria-hidden="true">
    <${Sign} name="sword" /><${Mark} id=${m.does} on=${on} />${m.doesMixed && html`<i class="table-tab__more"></i>`}
    <i class="table-tab__gap"></i>
    ${m.lean ? html`<span class="table-tab__off"><${Sign} name="shield" /></span>` : html`<${Sign} name="shield" /><${Mark} id=${m.checks} on=${on} />${m.checksMixed && html`<i class="table-tab__more"></i>`}`}
  </span>`;
}
