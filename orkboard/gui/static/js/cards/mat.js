// A leader's mat (decisions §297): an M that is a change in its leader's framework or a spread of it. What it opens is fixed by the
// post's kind, a closed list: a change in a framework (`p.table`: {party, framework, card}, the contract proposed) → that table, laid
// at the part it is about; a change → *What changed*. A word with none
// of these is no mat: it opens as an L of words. On the table a mat shows its spread's shape and one line, never a picture of it.
import { html } from "../html.js";
import { openSpread } from "./spreads/open.js";
import { FRAMEWORKS, laid, laidAt, tables } from "./tables/state.js";

/** The name of a part of a leader's framework, read from its table (a module, a job), or its id. */
function partName(t) {
  const data = tables.value?.[t.party]?.[t.framework];
  const all = JSON.stringify(data || {}), at = all.indexOf(`"id":"${t.card}"`);
  if (at < 0) return t.card;
  const m = all.slice(at).match(/"title":"([^"]*)"/);
  return m ? m[1] : t.card;
}

/** The mat of a post: {kind, shape, line, open(from)}, or null when the post is a word only. */
export function matOf(p) {
  if (!p) return null;
  if (p.table?.party && FRAMEWORKS[p.table.framework])
    return { kind: "table", shape: "table", line: `${FRAMEWORKS[p.table.framework]}: ${partName(p.table)}`,
      open: () => { laidAt.value = { ...p.table, p }; laid.value = p.table.party; } };
  if (p.kind === "change") return { kind: "diff", shape: "diff", line: "What changed", open: (from) => openSpread({ kind: "diff", p, from }) };
  return null;
}

/** A spread's shape on a mat: two cards side by side (`diff`: before and after, or two weighed), a fan (`dispute`: the voices, the costs, the deal), a grid (`table`: a table, the new goals sorted). */
export const Shape = ({ shape }) => html`<span class="cards-mat__shape" data-shape=${shape} aria-hidden="true">${
  Array.from({ length: shape === "diff" ? 2 : shape === "dispute" ? 3 : 4 }, (_, i) => html`<i key=${i}></i>`)}</span>`;

/** The mat's foot on an M: its shape and its line. */
export const MatFoot = ({ mat }) => html`<span class="cards-mat" data-mat=${mat.kind}><${Shape} shape=${mat.shape} /><span>${mat.line}</span></span>`;

/** What a mat says to a reader of the screen: its line, and who speaks in it. */
export const matSays = (mat) => `${mat.line}`;
