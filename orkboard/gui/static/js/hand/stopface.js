// A stop of the hand opened over the pane (`stop`, docs/specs/98-the-table-and-the-hand.md §0.2): what a card has no room for. A lifted card's *Open…* opens it here, whole: the
// stop's text and why, a plan's tasks, a failure's error and log, a question's choices, a pick's variants large with their note (the old drawer's `PickView`), and the same answers as the
// lifted card. Props: `{key}` of the stop (data.js `stopsOfProject`). When the stop is answered it is gone from the Board and the pane goes back.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { Elem, Head } from "../orkui.js";
import { command } from "../link.js";
import { closeOver } from "../frame/state.js";
import { PickView } from "../shell/pickview.js";
import { askedOf } from "../arena/arenawords.js";
import { TASK_STATE } from "../board/maplayout.js";
import { stopsOfProject } from "./data.js";
import { Answers } from "./answers.js";
import { costOf, Spend } from "./cost.js";
import { Mark, labelOf } from "./stopcard.js";

/** A failed task's log, read once. */
function useLog(s) {
  const [log, setLog] = useState(null), slug = s?.node?.slug, task = s?.task?.id;
  useEffect(() => {
    if (s?.kind !== "failed" || !slug || !task) return undefined;
    let live = true;
    command("ideas.task", { slug, task }).then((t) => { if (live) setLog(t && !(t.error && !t.id) ? t : {}); }).catch(() => { if (live) setLog({}); });   // a failed task carries its own `error`: only one with no id is a refusal
    return () => { live = false; };
  }, [slug, task]);
  return log;
}

export function StopFace({ props }) {
  const s = stopsOfProject().find((x) => x.key === props?.key) || null, log = useLog(s);
  useEffect(() => { if (!s) closeOver(); }, [!s]);
  if (!s) return html`<p class="ok-tone-muted">That card is answered.</p>`;
  const cost = costOf(s), head = s.head || s.party?.head, tasks = s.kind === "plan" || s.kind === "failed" ? (s.node?.tasks || []).filter((t) => t.state !== "dropped") : [];
  const asked = s.kind === "asks" ? askedOf(s.row, s.node) : [];
  return html`<article class="hand-stopface" data-key=${s.key} data-kind=${s.kind} aria-label=${labelOf(s)}>
    <header class="hand-stopface__head"><${Mark} s=${s} /><div class="hand-stopface__titles"><p class="cap">${s.label}${s.other && s.party?.name ? ` · ${s.party.name}` : ""}</p>
      <h2 class="hand-stopface__title">${s.full}</h2></div>${head && html`<${Head} race=${head.race} tier=${head.tier} size="big" />`}</header>
    ${s.kind === "pick" ? html`<${PickView} p=${{ slug: s.row.slug, task: s.row.task }} />` : html`
      ${s.text && html`<p class="body hand-stopface__text">${s.text}</p>`}
      ${s.why && html`<p class="cap">${s.why}</p>`}
      ${asked.map((q, i) => html`<div key=${i} class="hand-stopface__ask"><p class="body">${q.ask}</p>${q.why && html`<p class="cap">${q.why}</p>`}
        ${q.choices.length > 0 && html`<ul class="hand-stopface__choices">${q.choices.map((c, k) => html`<li key=${c} class=${k === q.pick ? "is-picked" : ""}>${k === q.pick ? "● " : ""}${c}</li>`)}</ul>`}</div>`)}
      ${tasks.length > 0 && html`<h3 class="board-sub">Tasks</h3><ul class="hand-stopface__tasks">${tasks.map((t) => html`<li key=${t.id} data-state=${t.state}>
        <span class="body">${t.title}</span><span class="cap">${t.by?.name || ""} · ${TASK_STATE[t.state] || t.state}${t.error ? ` · ${t.error}` : ""}</span></li>`)}</ul>`}
      ${log && html`<h3 class="board-sub">Log</h3><pre class="shell-log" aria-label="Log">${log.log || "Nothing logged yet."}</pre>`}
      <div class="hand-answers" role="group" aria-label="Answers"><${Answers} s=${s} here=${true} /></div>
      <${Spend} cost=${cost} />`}
  </article>`;
}
