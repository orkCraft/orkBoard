// A leader's mat (decisions §297): an M that is a change in its leader's framework or a spread of it. What it opens is fixed by the
// post's kind, a closed list: a change in a framework (`p.table`: {party, framework, card}, the contract proposed) → that table, laid
// at the part it is about; a change → *What changed*; a concern, a question or views that differ → *Who says what*. A word with none
// of these is no mat: it opens as an L of words. On the table a mat shows its spread's shape and one line, never a picture of it.
import { html } from "../html.js";
import { whoOf } from "../table/post.js";
import { viewsOf } from "./feed.js";
import { openSpread } from "./spreads/open.js";
import { FRAMEWORKS, laid, laidAt, tables } from "./tables/state.js";

const names = (list) => (list.length < 2 ? list.join("") : `${list.slice(0, -1).join(", ")} and ${list[list.length - 1]}`);

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
  const views = p.goal ? viewsOf(p.goal) : [];
  if (p.goal && (p.kind === "concern" || p.asks || views.length > 1))
    return { kind: "dispute", shape: "dispute", line: "Who says what", who: names(views.map((v) => whoOf(v.leader).name)) || whoOf(p.leader).name,
      open: (from) => openSpread({ kind: "dispute", slug: p.goal, from, said: views.some((v) => v.p === p) ? null : p }) };      // a voice of the spread already says its words
  return null;
}

/** A spread's shape on a mat: two cards side by side (before and after), a fan (the voices), a grid (a table). */
export const Shape = ({ shape }) => html`<span class="cards-mat__shape" data-shape=${shape} aria-hidden="true">${
  Array.from({ length: shape === "diff" ? 2 : shape === "dispute" ? 3 : 4 }, (_, i) => html`<i key=${i}></i>`)}</span>`;

/** The mat's foot on an M: its shape and its line. */
export const MatFoot = ({ mat }) => html`<span class="cards-mat" data-mat=${mat.kind}><${Shape} shape=${mat.shape} /><span>${mat.line}</span></span>`;

/** What a mat says to a reader of the screen: its line, and who speaks in it. */
export const matSays = (mat) => `${mat.line}${mat.who ? `: ${mat.who}` : ""}`;
