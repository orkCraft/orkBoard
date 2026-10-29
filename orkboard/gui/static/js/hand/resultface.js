// A result over the pane (`result`, docs/specs/98-the-table-and-the-hand.md §4.3): the goal done that was pressed in the discard, or one task's result a stop of the hand holds at Review.
// Props: `{idea}` is the goal's Result (what its tasks made, what it cost); `{idea, task}` is a task's result as the old drawer drew it (its tests, its changes, its commits and files, the
// answers of Review at its foot). It only reads; the discard sent `ideas.seen` when it was opened.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { ask } from "../board/store.js";
import { mapData, review } from "../shell/store.js";
import { ResultActions, Found, testsWords, changesWords, isRed } from "../shell/review.js";
import { File } from "../shell/diffview.js";
import { LogView, happened } from "../shell/logview.js";
import { spendWords } from "../shell/preview.js";
import { pctShort } from "../spend.js";
import { partyBy } from "./data.js";

const nodeOf = (idea) => (mapData.value?.nodes || []).find((n) => n.slug === idea) || null;

function useRead(idea, task) {
  const [got, set] = useState({ spend: null, diff: null });
  useEffect(() => {
    let live = true;
    Promise.all([ask("ideas.spend", { idea }), task ? ask("ideas.diff", { slug: idea, task }) : null]).then(([spend, diff]) => { if (live) set({ spend, diff }); });
    return () => { live = false; };
  }, [idea, task]);
  return got;
}

/** A task's result: the old drawer's, read from the Map's own copy. */
function TaskResult({ idea, task }) {
  const { spend, diff } = useRead(idea, task), mine = nodeOf(idea)?.results?.find((x) => x.task === task) || null;
  const r = (review.value?.results || []).find((x) => x.idea === idea && x.task === task) || mine, t = r && testsWords(r), shot = r?.shot || mine?.shot || null;
  return html`<div class="hand-result" data-task=${task}>
    ${spend && html`<p class="cap" title="At API prices, not your bill">${spendWords(spend)}</p>`}
    ${r ? html`<h2 class="hand-result__title">${r.title}</h2><dl class="shell-facts">
        <dt>Tests</dt><dd class=${`is-${t.tone}`}>${t.mark && html`<${Sign} name=${t.mark} /> `}${t.text}${t.names.length ? html` <span class="ok-tone-muted">${t.names.join(", ")}</span>` : ""}</dd>
        <dt>Changes</dt><dd>${changesWords(r.diff)}</dd>${r.round > 1 ? html`<dt>Round</dt><dd>${r.round}</dd>` : ""}</dl>
        ${shot?.url && html`<span class="arena-result__shot"><img src=${shot.url} alt=${`What “${r.title}” looks like`} draggable="false" style=${shot.w && shot.h ? `aspect-ratio:${shot.w} / ${shot.h}` : undefined} /></span>`}
        ${r.conflict && html`<p class="ok-tone-error">⚠ ${r.conflict}</p>`}
        <${Found} r=${r} />
        ${isRed(r) && html`<p class="body hand-result__said">${happened({ tests: r.tests, red: true })}</p>`}
        ${isRed(r) && r.tests.tail && html`<${LogView} text=${r.tests.tail} label="What the tests said" />`}`
      : html`<p class="ok-tone-muted">This result is no longer waiting at Review.</p>`}
    ${!diff ? html`<p class="ok-tone-muted">Reading the code…</p>` : html`
      <h3 class="board-sub">Commits</h3>
      <ol class="shell-commits">${diff.commits.map((c) => html`<li key=${c.sha}><code>${c.sha}</code> ${c.subject}</li>`)}</ol>
      <h3 class="board-sub">Files changed (${diff.files.length})</h3>
      ${diff.files.map((f) => html`<${File} key=${f.path} f=${f} />`)}
      ${diff.truncated && html`<p class="ok-tone-muted">Some files are too large to show.</p>`}`}
    ${r && html`<footer class="hand-result__foot"><${ResultActions} r=${r} pinned=${true} /></footer>`}
  </div>`;
}

/** A goal's Result: what it made, task by task, and what it cost. */
function GoalResult({ idea }) {
  const { spend } = useRead(idea, ""), n = nodeOf(idea), party = partyBy()[n?.goal];
  if (!n) return html`<p class="ok-tone-muted">This goal is gone.</p>`;
  const made = (n.tasks || []).filter((t) => t.state === "merged");
  return html`<div class="hand-result" data-idea=${idea}>
    <header class="hand-result__head"><${Elem} name=${n.element || ""} dim=${!n.element} /><h2 class="hand-result__title">${n.title}</h2></header>
    <p class="cap">${party ? `${party.name} · ` : ""}Done${n.updated ? ` · ${String(n.updated).slice(0, 10)}` : ""}</p>
    ${spend && html`<p class="cap" title="At API prices, not your bill">${spendWords(spend)}</p>`}
    <h3 class="board-sub">What it made</h3>
    ${made.length ? html`<ul class="hand-result__made">${made.map((t) => html`<li key=${t.id}><span class="body">${t.made || t.title}</span>
        <span class="cap">${t.by?.name || ""}${pctShort(t.cost) ? ` · ${pctShort(t.cost)}` : ""}</span></li>`)}</ul>`
      : html`<p class="ok-tone-muted">Its tasks left no commit to list.</p>`}
  </div>`;
}

export function ResultFace({ props }) {
  return props?.task ? html`<${TaskResult} idea=${props.idea} task=${props.task} />` : html`<${GoalResult} idea=${props?.idea} />`;
}
