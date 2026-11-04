// A change's way down, said in one line (docs/specs/132-four-levels-the-way-down-and-findings.md C.2; decisions §234.2, §237.7): every row of a change the hand shows carries `level` (decision, spec, work) and `pulls`
// (realm/way_down.py: `{sections: [{idea, party}], tasks: [{idea, id}], checks, estimate: {usd_low, usd_high}}`). The lifted card says it as one line, its level's sign first and the sign's title *Changes the decision*
// (never a word on the card): *About 4% of Claude's week: 2 sections, 3 tasks* (the share is the gems', cost.js); what each section and task is, under **More**. A change that pulls nothing says the price of the change itself,
// or that nothing below it is redone. The line stands where the plain cost line (cost.js `Spend`) stood: stopcard.js draws one or the other. Cards that make their own lines of it (the quality card's, D) call `LevelSign`
// and `pullsLines` themselves.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Sign } from "../orkui.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { nameOf, partiesAll } from "../table/data.js";
import { pullsWords, spendWords } from "./costline.js";

/** The levels, heaviest first: their word (the pane's mark) and the sign's title; the sign is orkUI's. */
export const LEVELS = {
  decision: { word: "Decision", sign: "compass", title: "Changes the decision" },
  spec: { word: "Spec", sign: "page", title: "Changes the spec" },
  work: { word: "Work", sign: "work", title: "Changes the work" },
  quality: { word: "Quality", sign: "balance", title: "Changes what the goal did against what was promised" },
};

/** The kinds of row whose card says its ways down itself, a line for each finding (the quality card and a finding of no goal: hand/qualitycard.js). */
export const OWN_LINES = new Set(["quality", "finding"]);

/** The levels that hold something open of a goal (C.3: `levels` on its row of `ideas.board`), heaviest first; none for a goal the Board does not list. The pane's marks read it (spec 132 B, kept for a trial). */
export const levelsOf = (slug) => { const got = (board.value?.ideas || []).find((i) => i.slug === slug)?.levels; return Array.isArray(got) ? Object.keys(LEVELS).filter((l) => got.includes(l)) : []; };

/** The level's sign, its title saying what it changes; nothing for a level that is not one. */
export function LevelSign({ level }) {
  const l = LEVELS[level];
  return l ? html`<span class="hand-wayline__sign" data-level=${level}><${Sign} name=${l.sign} label=${l.title} /></span>` : null;
}

const goalTitle = (slug) => { const n = (mapData.value?.nodes || []).find((x) => x.slug === slug); return n?.short || n?.title || slug; };
const partyName = (slug) => nameOf(partiesAll().find((g) => g.slug === slug)) || slug;
const taskTitle = (t) => { const n = (mapData.value?.nodes || []).find((x) => x.slug === t.idea), k = (n?.tasks || []).find((x) => x.id === t.id); return k?.short || k?.title || (typeof t.id === "string" ? t.id : ""); };

/** What each pulled thing is, as lines: *<goal> · <party>* a section, *<goal> · <task>* a task, *<n> checks again*. */
export function pullsLines(p) {
  const lines = [];
  for (const s of p?.sections || []) lines.push({ key: `s:${s.idea}:${s.party}`, kind: "section", text: `${goalTitle(s.idea)} · ${partyName(s.party)}` });
  for (const t of p?.tasks || []) lines.push({ key: `t:${t.idea}:${t.id}`, kind: "task", text: `${goalTitle(t.idea)} · ${taskTitle(t)}` });
  const checks = Number(p?.checks) || 0;
  if (checks) lines.push({ key: "checks", kind: "check", text: `${checks} ${checks === 1 ? "check" : "checks"} again` });
  return lines;
}

/** *About 4% of Claude's week: 2 sections, 3 tasks*, from a row's `pulls`; the card's own price (`own`, costline.js's words) when nothing is pulled; *Nothing below it is redone* with neither. */
export function wayWords(pulls, own = "") {
  const sum = pullsWords(pulls), price = spendWords(pulls?.estimate?.usd_low, pulls?.estimate?.usd_high) || own;
  const head = price ? price.charAt(0).toUpperCase() + price.slice(1) : "";
  return head && sum ? `${head}: ${sum}` : head || (sum ? sum.charAt(0).toUpperCase() + sum.slice(1) : "Nothing below it is redone");
}

/** The one line of a change on its lifted card: its level's sign, the words, **More** when something is pulled. `row` carries `level` and `pulls`; `own`: what the change itself costs, in the gems' words; `signless`: the card draws the level's sign beside it already; `extra`: `[label, text]` lines that go under More first (a finding's *What shows it*). */
export function WayLine({ row, own = "", extra = [], signless = false }) {
  const [more, setMore] = useState(false), lines = [...extra.filter(([, t]) => t).map(([label, t]) => ({ key: `x:${label}`, kind: "extra", text: `${label}: ${t}` })), ...pullsLines(row?.pulls)];
  return html`<div class="hand-wayline" data-level=${row?.level} data-part="way">
    <p class="hand-wayline__line cap">${!signless && html`<${LevelSign} level=${row?.level} />`}<span class="hand-wayline__words">${wayWords(row?.pulls, own)}</span>
      ${lines.length > 0 && html`<button type="button" class="ork-btn quiet hand-wayline__more" aria-expanded=${more} onClick=${() => setMore(!more)}>${more ? "Less" : "More"}</button>`}</p>
    ${more && lines.length > 0 && html`<ul class="hand-wayline__list" aria-label="What it pulls">${lines.map((l) => html`<li key=${l.key} class="cap" data-kind=${l.kind}>${l.text}</li>`)}</ul>`}
  </div>`;
}
