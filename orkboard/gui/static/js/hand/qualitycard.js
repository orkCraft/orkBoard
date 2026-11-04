// A goal's quality card and a finding of no goal's (docs/specs/132-four-levels-the-way-down-and-findings.md D.3; decisions §234.3, §237.1–§237.2, §237.8): what a goal did against what was promised, found where it was found and taken
// up to the level that holds its cause. The row is `{kind: "quality", idea, goal, title, text: "Quality of <goal>", findings: [{id, party, level, what, cause, change, shows, promised, source, on, pulls}], level, pulls}`
// (realm/findings.py `rows`), one a goal, its findings in the order of their level, Decision first; a finding of no goal is a `{kind: "finding", id, party, level, what, …, pulls}` of its own. Both are **never urgent**: they lie in the
// hand after a failure and a question (arenawords.js), push nothing to the phone and show no toast. The face is the hand's card (stopcard.js): the balance's sign, the first finding's leader as its asker, *Quality of <goal>* (or
// *<Party> found: …*) at its foot, the card's price as its gem (the sum of its findings' ways down). Lifted, each finding a block: the finder's head, its level's sign, *<Party> found: <what>*, *The cause is in the code / the spec / the
// decision* and the cause, what would change there, the way down in one line (wayline.js: its cost said before, what shows it and what was promised under **More**), and two answers, **Fix it there** (`ideas.finding_fix {id}`: a fix
// goal for Work and Spec, a proposal into the cascade for Decision) and **Not now** (`ideas.finding_later {id}`: it leaves the hand and stays on the quality record); under the finding's **…**, **Another level…**
// (`ideas.finding_move {id, level}`: its cost said again). With two findings or more, **Fix all there** (`ideas.finding_fix_all {idea}`) answers every finding at once, its cost said first. Nothing here counts what waits.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { toast } from "../link.js";
import { act } from "../shell/store.js";
import { nameOf, partiesAll } from "../table/data.js";
import { changeLine } from "./costline.js";
import { LEVELS, LevelSign, WayLine } from "./wayline.js";
import { way } from "./ways.js";

/** The levels a finding's cause may lie in, as the card says it: *The cause is in the code*. */
export const CAUSE = { decision: "decision", spec: "spec", work: "code" };

const partyOf = (slug) => partiesAll().find((g) => g.slug === slug) || null;
/** *Tech found: …*. */
export const foundWords = (f) => `${nameOf(partyOf(f.party)) || f.party || "The leader"} found: ${f.what}`;
/** The findings a row holds: a quality card's, or the one a finding row is. */
export const findingsOf = (row) => (row?.kind === "finding" ? [row] : row?.findings || []);

/** What was made of a finding, in words, for the toast after *Fix it there*. */
const madeWords = (fix) => (fix?.cascade ? "The change is proposed to the leaders" : "A fix goal is made");

/** One finding on the lifted card. `done`: said when it was answered (the card closes with its last). */
function Finding({ f, busy, run }) {
  const [more, setMore] = useState(false), g = partyOf(f.party), head = g?.leader?.head || null, extra = [["What shows it", f.shows], ["What was promised", f.promised]].filter(([, t]) => t);
  const fix = () => run("ideas.finding_fix", { id: f.id }, (got) => toast(madeWords(got.fix)));
  const later = () => run("ideas.finding_later", { id: f.id });
  const move = (level) => run("ideas.finding_move", { id: f.id, level }, () => setMore(false));
  return html`<li class="hand-finding" data-finding=${f.id} data-level=${f.level} data-source=${f.source || undefined}>
    <p class="hand-finding__who">${head && html`<${Head} race=${head.race} tier=${head.tier} />`}<${LevelSign} level=${f.level} /><span class="body hand-finding__what">${foundWords(f)}</span></p>
    <p class="cap hand-finding__cause">The cause is in the ${CAUSE[f.level] || "code"}${f.cause ? `: ${f.cause}` : ""}</p>
    ${f.change && html`<p class="cap hand-finding__change">${f.change}</p>`}
    <${WayLine} row=${{ level: f.level, pulls: f.pulls }} extra=${extra} signless=${true} />
    <div class="hand-answers hand-finding__acts" role="group" aria-label="Answers">
      <button type="button" class="ork-btn primary" data-answer="fix" disabled=${busy} title=${`Fix it at its level: ${changeLine(f.pulls) || "one fix goal"}`} onClick=${fix}>Fix it there</button>
      <button type="button" class="ork-btn quiet" data-answer="later" disabled=${busy} title="It leaves the hand and stays on the goal's quality record" onClick=${later}>Not now</button>
      <button type="button" class="ork-btn quiet hand-finding__dots" aria-expanded=${more} aria-label="More answers" title="More answers" disabled=${busy} onClick=${() => setMore(!more)}><${Icon} name="more-horizontal" /></button>
    </div>
    ${more && html`<div class="hand-finding__levels" role="group" aria-label="Another level…"><span class="ork-label">Another level…</span>
      ${Object.keys(CAUSE).filter((l) => l !== f.level).map((l) => html`<button type="button" key=${l} class="ork-btn" data-level=${l} disabled=${busy} title=${`The cause is in the ${CAUSE[l]}`} onClick=${() => move(l)}>${LEVELS[l].word}</button>`)}</div>`}
  </li>`;
}

/** The lifted card of a quality row or a finding row. */
export function QualityLifted({ s, close }) {
  const row = s.row || {}, list = findingsOf(row), [busy, setBusy] = useState(false);
  const run = async (name, args, then) => {                          // one answer; the Board is read again, the card closes with its last finding
    if (busy) return;
    setBusy(true);
    try {
      const got = await act(name, args);
      if (got) { then?.(got); if (list.length <= 1 || name === "ideas.finding_fix_all") close?.(); }
    } finally { setBusy(false); }
  };
  const all = () => run("ideas.finding_fix_all", { idea: row.idea }, (got) => {
    const left = (got.refused || []).length;
    toast(left ? `${(got.fixed || []).length} fixed there; ${left} could not be: ${got.refused[0].why}` : "Every finding is taken up", left ? "warning" : "information");
  });
  return html`<div class="hand-way hand-quality" data-kind=${row.kind} data-idea=${row.idea || undefined}>
    <ul class="hand-quality__list" aria-label="The findings">${list.map((f) => html`<${Finding} key=${f.id} f=${f} busy=${busy} run=${run} />`)}</ul>
    ${row.kind === "quality" && list.length > 1 && html`<div class="hand-answers hand-way__acts" role="group" aria-label="All the findings">
      <button type="button" class="ork-btn" data-answer="all" disabled=${busy} title=${`Fix every finding at its level: ${changeLine(row.pulls) || "one fix each"}`} onClick=${all}>Fix all there</button></div>`}
  </div>`;
}

/** The first finding's leader is the card's asker: its head. */
const headOf = (s) => partyOf(findingsOf(s.row)[0]?.party)?.leader?.head || null;
/** The card's price: the way down of everything it holds (a gem, and the cost's words under the body). */
const priceOf = (s) => {
  const e = s.row?.pulls?.estimate, low = Number(e?.usd_low), high = Number(e?.usd_high);
  return e && (low || high) ? { low, high } : null;
};

// The face: the balance's sign, the first finding's leader as its asker, *Quality of <goal>* or *<Party> found: …* at its foot, the way down's price as its gem.
way("quality", { sign: "balance", head: headOf, foot: (s) => s.row?.text || `Quality of ${s.row?.title || ""}`, price: priceOf, Lifted: QualityLifted });
way("finding", { sign: "balance", head: headOf, foot: (s) => foundWords(s.row || {}), price: priceOf, Lifted: QualityLifted });
