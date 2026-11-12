// A leader's mat (decisions §297): an M that is a change in its leader's framework or a spread of it. What it opens is fixed by the
// post's kind, a closed list: a change in a framework (`p.table`: {party, framework, card}, the contract proposed) → that table, laid
// at the part it is about; a change → *What changed*. A word with none
// of these is no mat: it opens as an L of words. On the table a mat shows its layout's slots behind its words and one line (slots.js), never a picture of it.
import { html } from "../html.js";
import { Slots, layoutOf } from "./slots.js";
import { openSpread } from "./spreads/open.js";
import { FRAMEWORKS, laid, laidAt, laidFrom, tables } from "./tables/state.js";

/** The name of a part of a leader's framework, read from its table (a module, a job), or its id. */
function partName(t) {
  const data = tables.value?.[t.party]?.[t.framework];
  const all = JSON.stringify(data || {}), at = all.indexOf(`"id":"${t.card}"`);
  if (at < 0) return t.card;
  const m = all.slice(at).match(/"title":"([^"]*)"/);
  return m ? m[1] : t.card;
}

/** The mat of a post: {kind, layout, line, open(from)}, or null when the post is a word only. */
export function matOf(p) {
  if (!p) return null;
  if (p.table?.party && FRAMEWORKS[p.table.framework])
    return { kind: "table", layout: layoutOf("table", p.table.framework), line: `${FRAMEWORKS[p.table.framework]}: ${partName(p.table)}`,
      open: (from) => { laidAt.value = { ...p.table, p, from }; laidFrom.value = from || null; laid.value = p.table.party; } };
  if (p.kind === "change") return { kind: "diff", layout: layoutOf("diff"), line: "What changed", open: (from) => openSpread({ kind: "diff", p, from }) };
  return null;
}

/** The mat's foot on an M: its one line; the layout's slots lie behind the M's words (slots.js), no shape beside it. */
export const MatFoot = ({ mat }) => html`<${Slots} layout=${mat.layout} /><span class="cards-mat" data-mat=${mat.kind}><span>${mat.line}</span></span>`;

/** What a mat says to a reader of the screen: its line, and who speaks in it. */
export const matSays = (mat) => `${mat.line}`;
