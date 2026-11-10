// The *Quality* page (docs/specs/132-four-levels-the-way-down-and-findings.md D.4; decisions §234.4, §237.1): a goal's quality record over the pane, `ideas.quality {idea}`: what the goal did against what its spec promised (✓ As
// promised, ≠ Not quite, + More than promised, ✗ Not done, by party; its *Done when* checked), its checks, the lenses' alarms on the parts it touched, the hypothesis it tested, and each finding with its level and what became of it
// (fixed there and by what, put off, moved by the person). A goal picked in the discard opens it from the pane's title (*Done*, table/pane.js): it replaces the result there. The findings put off stay on this page, never in a
// list of their own; a finding not fixed is taken again here, **Fix it there**, with no new call of a leader's. Props: `{idea}`. Registered as the pane's kind `quality` (frame/kinds.js). Nothing here counts what waits.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { board } from "../board/store.js";
import { command, toast } from "../link.js";
import { mapData, act } from "../shell/store.js";
import { Elem, Head } from "../orkui.js";
import { drawn } from "../frame/kinds.js";
import { CAUSE, foundWords } from "../hand/qualitycard.js";
import { LevelSign } from "../hand/wayline.js";
import { VERDICT } from "./goalview.js";
import { nameOf, partiesAll } from "./data.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./quality.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const partyOf = (slug) => partiesAll().find((g) => g.slug === slug) || null;
const partyName = (slug) => nameOf(partyOf(slug)) || slug;
const CHECKED = { ok: "Passed", failed: "Failed", running: "Running", pending: "Waits" };

/** The record, read again when the Board is (`rev`) or after a fix (`again`): undefined while it is read, null when the host has none. */
function useRecord(idea, again) {
  const [rec, setRec] = useState(undefined), rev = board.value?.rev;
  useEffect(() => {
    let live = true;
    command("ideas.quality", { idea }, true).then((a) => { if (live) setRec(a && Array.isArray(a.findings) ? a : null); }).catch(() => { if (live) setRec(null); });
    return () => { live = false; };
  }, [idea, rev, again]);
  return rec;
}

/** What became of a finding, in words. */
export function fateOf(f) {
  const goal = f.fix?.idea ? (mapData.value?.nodes || []).find((n) => n.slug === f.fix.idea) : null;
  if (f.answer === "fix") return `Fixed there${f.fix?.idea ? ` by a fix goal${goal ? `: ${goal.short || goal.title}` : ""}` : f.fix?.cascade ? ", by a proposal to the leaders" : ""}`;
  if (f.answer === "later") return "Not now: put off";
  if (f.status === "sorted") return f.answer === "moved" ? `Moved to the ${CAUSE[f.level] || f.level}; it waits in your hand` : "Waits in your hand";
  return "Not sorted yet";
}

/** The verdict against the spec: each part a line, by party (the record's flat rows; the answer of `ideas.goal_result` when the record kept none). */
function Verdict({ rec }) {
  const flat = rec.verdict?.length ? rec.verdict : (rec.result?.parties || []).flatMap((p) => (p.parts || []).map((w) => ({ party: p.party, id: w.id, kind: w.kind, verdict: w.verdict, line: w.line })));
  const parties = [...new Set(flat.map((r) => r.party))], done = (rec.result?.parties || []).flatMap((p) => (p.done_when || []).map((d) => ({ ...d, party: p.party })));
  if (!flat.length && !done.length) return null;
  return html`<section class="quality-sec" data-part="verdict" aria-label="Against its spec"><h3 class="ork-label">Against its spec</h3>
    ${parties.map((p) => html`<div key=${p} class="quality-party"><span class="quality-party__nm">${partyName(p)}</span><ul class="quality-list">${flat.filter((r) => r.party === p).map((r, i) => html`<li key=${i} class=${cls("quality-line", `is-${r.verdict}`)} data-verdict=${r.verdict}>
      <b class="quality-line__sign" aria-hidden="true">${VERDICT[r.verdict]?.[0] || "·"}</b><span>${r.id}${r.line ? ` — ${r.line}` : ""}</span><span class="cap quality-line__word">${VERDICT[r.verdict]?.[1] || r.verdict}</span></li>`)}</ul></div>`)}
    ${done.length > 0 && html`<div class="quality-party"><span class="quality-party__nm">Done when</span><ul class="quality-list">${done.map((d, i) => html`<li key=${i} class=${cls("quality-line", { "is-ok": d.state === "ok" })} data-state=${d.state || undefined}><b class="quality-line__sign" aria-hidden="true">${d.state === "ok" ? "✓" : "·"}</b><span>${d.text}</span>${d.word && html`<span class="cap quality-line__word">${d.word}</span>`}</li>`)}</ul></div>`}
  </section>`;
}

/** One finding: its level's sign, what the finder found, the cause, what became of it; **Fix it there** while it can still be taken up. */
function Finding({ f, busy, fix }) {
  const head = partyOf(f.party)?.leader?.head;
  return html`<li class="quality-finding" data-finding=${f.id} data-level=${f.level} data-answer=${f.answer || undefined}>
    <p class="quality-finding__who">${head && html`<${Head} race=${head.race} tier=${head.tier} />`}<${LevelSign} level=${f.level} /><span class="body">${foundWords(f)}</span></p>
    ${f.level && html`<p class="cap">The cause is in the ${CAUSE[f.level]}${f.cause ? `: ${f.cause}` : ""}</p>`}
    <p class="cap quality-finding__fate" data-part="fate">${fateOf(f)}</p>
    ${f.status === "sorted" && f.answer !== "fix" && html`<p class="quality-finding__acts"><button type="button" class="ork-btn" data-answer="fix" disabled=${busy} title="Fix it at its level" onClick=${() => fix(f)}>Fix it there</button></p>`}
  </li>`;
}

export function QualityPage({ props }) {
  const idea = props?.idea, [again, setAgain] = useState(0), [busy, setBusy] = useState(false), rec = useRecord(idea, again), node = (mapData.value?.nodes || []).find((n) => n.slug === idea) || null;
  const fix = async (f) => {
    setBusy(true);
    try {
      const got = await act("ideas.finding_fix", { id: f.id });
      if (got) { toast(got.fix?.cascade ? "The change is proposed to the leaders" : "A fix goal is made"); setAgain(again + 1); }
    } finally { setBusy(false); }
  };
  const head = html`<header class="quality-page__head"><${Elem} name=${node?.element || ""} hue=${node?.hue || ""} dim=${!node?.element} /><h2 class="quality-page__title">${node?.title || rec?.title || idea}</h2><span class="ork-label">Quality</span></header>`;
  if (rec === undefined) return html`<article class="quality-page" data-kind="quality" aria-label="Quality">${head}<p class="table-over__muted">Reading the quality record…</p></article>`;
  if (!rec) return html`<article class="quality-page" data-kind="quality" aria-label="Quality">${head}<p class="table-over__muted">The quality record could not be read now.</p></article>`;
  const empty = !rec.verdict?.length && !rec.result?.parties?.length && !rec.checks?.length && !rec.lenses?.length && !rec.hypothesis && !rec.findings?.length;
  return html`<article class="quality-page" data-kind="quality" data-idea=${idea} aria-label="Quality">${head}
    <${Verdict} rec=${rec} />
    ${rec.checks?.length > 0 && html`<section class="quality-sec" data-part="checks" aria-label="Checks"><h3 class="ork-label">Checks</h3><ul class="quality-list">${rec.checks.map((c, i) => html`<li key=${i} class="quality-line" data-state=${c.state || undefined}>
      <span>${c.by || "A check"}</span><span class="cap quality-line__word">${CHECKED[c.state] || c.state}${c.left ? `, ${c.left} left` : ""}</span></li>`)}</ul></section>`}
    ${rec.lenses?.length > 0 && html`<section class="quality-sec" data-part="lenses" aria-label="The lenses"><h3 class="ork-label">The lenses</h3><ul class="quality-list">${rec.lenses.map((f) => html`<li key=${f.id} class="quality-line"><span>${f.what}</span><span class="cap quality-line__word">${partyName(f.party)}</span></li>`)}</ul></section>`}
    ${rec.hypothesis && html`<section class="quality-sec" data-part="hypothesis" aria-label="The hypothesis"><h3 class="ork-label">The hypothesis</h3><p class="body">${rec.hypothesis.text || rec.hypothesis.what || ""}${rec.hypothesis.state || rec.hypothesis.outcome ? html` <span class="cap">· ${rec.hypothesis.state || rec.hypothesis.outcome}</span>` : ""}</p></section>`}
    ${rec.findings?.length > 0 && html`<section class="quality-sec" data-part="findings" aria-label="The findings"><h3 class="ork-label">Findings</h3><ul class="quality-list quality-findings">${rec.findings.map((f) => html`<${Finding} key=${f.id} f=${f} busy=${busy} fix=${fix} />`)}</ul></section>`}
    ${empty && html`<p class="table-over__muted" data-state="none">Nothing was found: the goal did what its spec promised.</p>`}
  </article>`;
}
drawn("quality", QualityPage);
