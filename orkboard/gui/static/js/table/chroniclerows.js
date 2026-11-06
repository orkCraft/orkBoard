// A goal as it was and a decision's entry, opened in the chronicle (docs/specs/134 part B, decisions §238.4). The goal (`ideas.chronicle_goal`): its spec as built, marked *changed by §<n>* where a later decision changed a point it rests on,
// its decision, its quality record, and the living spec of its part (*How it works now*). A decision (`ideas.chronicle_decision`): its entry, its *Changes* and *changed by* as links, so its history is walked without reading the list.
// Nothing here decides or writes. What people or agents wrote (a spec's parts, an entry) keeps its words, in the body face.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { Elem } from "../orkui.js";
import { ask } from "./chronicleparts.js";
import { changedBy, dayWord } from "./chroniclewords.js";

const LEVELS = { verdict: "Not as promised", check: "A check", lens: "A look", concern: "A concern", hypothesis: "A hypothesis", measure: "A measure" };

/** A read of one command: `[data, err]`, read again when `key` changes. */
function useAsk(name, args, key) {
  const [st, set] = useState([null, ""]);
  useEffect(() => { let live = true; set([null, ""]); ask(name, args).then((r) => { if (live) set(r); }); return () => { live = false; }; }, [key]);
  return st;
}

/** Links to decisions: *§206.3 title* (a point after the number where the decision named one). */
function Links({ label, list, onDecision, point = false }) {
  if (!list?.length) return null;
  return html`<p class="chr-links" data-links=${label}><span class="ork-label">${label}</span>${list.map((c) => {
    const n = c.n ?? c.number, pt = point ? c.point : (c.points || []).join(", ");
    return html`<button type="button" key=${`${n}.${pt}`} class="ork-btn quiet chr-link" data-decision=${n} title=${c.title} onClick=${() => onDecision(n)}>§${n}${pt ? `.${pt}` : ""} ${c.title}</button>`;
  })}</p>`;
}

function Entry({ text }) {
  return text ? html`<pre class="chr-entry" aria-label="Its entry">${text}</pre>` : null;
}

function Spec({ spec }) {
  const parts = (p) => Object.entries(p || {}).filter(([, v]) => v);
  return html`<div class="chr-spec">
    ${spec.asked && html`<h4 class="ork-label">Asked</h4><p class="chr-text">${spec.asked}</p>`}
    ${spec.gist && html`<h4 class="ork-label">Gist</h4><p class="chr-text">${spec.gist}</p>`}
    ${spec.sections.map((s) => html`<section key=${s.party} class="chr-section" data-party=${s.party}><h4 class="ork-label">${s.title}</h4>
      ${parts(s.parts).map(([name, text]) => html`<p key=${name} class="chr-text"><b>${name}</b> ${text}</p>`)}</section>`)}
  </div>`;
}

/** The quality record in short: how the goal's own findings stand. */
function Quality({ q }) {
  const rows = q?.findings || [];
  if (!q || !rows.length) return null;
  return html`<section class="chr-quality" aria-label="Quality"><h4 class="ork-label">Quality</h4>
    <ul class="chr-found">${rows.map((f) => html`<li key=${f.id} data-source=${f.source}><span class="chr-found__src">${LEVELS[f.source] || f.source}</span> ${f.what || f.found}</li>`)}</ul></section>`;
}

/** `show(goal)`: the tab's *Show on <party>'s table* (spec 150 E2.2), none on the Orkmaster's tab. */
export function GoalAsItWas({ idea, onDecision, show = null }) {
  const [g, err] = useAsk("ideas.chronicle_goal", { idea }, idea);
  if (err) return html`<p class="chr-err" role="alert">${err}</p>`;
  if (!g) return html`<p class="table-over__muted">Reading the goal…</p>`;
  const d = g.decision;
  return html`<article class="chr-goal" data-goal=${g.idea}>
    <h3 class="chr-title"><${Elem} name=${g.element || ""} hue=${g.hue || ""} dim=${!g.element} /> ${g.title}</h3>
    <p class="table-over__muted">Through the portal ${dayWord(g.day)}</p>
    ${show?.(g.idea)}
    ${g.changed_by.length > 0 && html`<p class="chr-changed" data-changed="1"><span class="chr-changed__by">${changedBy(g.changed_by)}</span>
      ${g.changed_by.map((c) => html`<button type="button" key=${c.number} class="ork-btn quiet chr-link" data-decision=${c.number} title=${c.title} onClick=${() => onDecision(c.number)}>§${c.number} ${c.title}</button>`)}</p>`}
    <${Spec} spec=${g.spec} />
    ${d && html`<section class="chr-decision" aria-label="Its decision"><h4 class="ork-label">Decision</h4>
      <p><button type="button" class="ork-btn quiet chr-link" data-decision=${d.number} onClick=${() => onDecision(d.number)}>§${d.number} ${d.title}</button> <span class="table-over__muted">${dayWord(d.day)}</span></p>
      <${Entry} text=${d.entry} /></section>`}
    <${Quality} q=${g.quality} />
    ${g.how_now.length > 0 && html`<section class="chr-now" aria-label="How it works now"><h4 class="ork-label">How it works now</h4>
      <ul class="chr-found">${g.how_now.map((c) => html`<li key=${c.capability} data-capability=${c.capability}>${c.title}</li>`)}</ul></section>`}
  </article>`;
}

export function Decision({ number, onDecision, onGoal, show = null }) {
  const [d, err] = useAsk("ideas.chronicle_decision", { number }, number);
  if (err) return html`<p class="chr-err" role="alert">${err}</p>`;
  if (!d) return html`<p class="table-over__muted">Reading the decision…</p>`;
  return html`<article class="chr-decision-page" data-decision=${d.number}>
    <h3 class="chr-title">§${d.number} ${d.title}</h3>
    <p class="table-over__muted">${dayWord(d.day)}</p>
    ${show?.(d.goal)}
    ${d.goal && html`<p><button type="button" class="ork-btn quiet" data-goal=${d.goal} onClick=${() => onGoal(d.goal)}>The goal it came from</button></p>`}
    <${Links} label="Changes" list=${d.changes} onDecision=${onDecision} point=${true} />
    <${Links} label=${"Changed by"} list=${d.changed_by} onDecision=${onDecision} />
    <${Entry} text=${d.entry} />
  </article>`;
}
