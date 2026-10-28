// The views the drawer had that the pane keeps (docs/specs/33-v1-shell.md §6, spec 39 §3; docs/specs/98-the-table-and-the-hand.md §7): a task's state, brief and log (`Task`, drawn over the map by table/over.js) and the money of a goal so far
// (`spendWords`, read by hand/resultface.js, which draws a result's tests, changes, commits and files with the answers of Review at its foot). The drawer itself is gone.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { Who } from "../orkui.js";
import { ErrorLine } from "./errors.js";
import { holdWords, heldByYou } from "../board/store.js";
import { TASK_STATE } from "../board/maplayout.js";
import { act } from "./store.js";
import { closeOver, openOver, over } from "../frame/state.js";
import { pctOf, pctShort } from "../spend.js";

/** A failed task's way on: run its goal's tasks again, or drop it (asked first, in the card). */
function FailedActions({ t }) {
  const [sure, setSure] = useState(false);
  const drop = async () => { const got = await act("ideas.drop_task", { slug: t.idea, task: t.id }); if (got?.ok) closeOver(); };
  return html`<div class="board-row">
    <button class="ork-btn primary" title="Its goal's tasks that are not merged or at Review run again" onClick=${() => act("ideas.start", { slug: t.idea })}>Start again</button>
    ${sure ? html`<span>Drop this task? Its worktree goes; its branch stays.</span>
      <button class="ork-btn danger" onClick=${drop}>Drop it</button><button class="ork-btn" onClick=${() => setSure(false)}>Keep it</button>`
      : html`<button class="shell-quiet" onClick=${() => setSure(true)}>Drop…</button>`}</div>`;
}

/** A task: its state, its goal, who does it, its brief and its log (`d.task`, `ideas.task`; the caller reads it again while it runs). `log`: the log first (a failure's lines). */
export function Task({ d, log = false }) {
  const t = d?.task;
  const ref = useRef();
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [t?.log]);
  if (!t) return html`<p class="ok-tone-muted">Opening…</p>`;
  const live = t.state === "running" || t.state === "testing";
  const facts = html`<dl class="shell-facts">
      <dt>State</dt><dd data-state=${t.state}>${TASK_STATE[t.state] || t.state}${t.note ? html` <span class="ok-tone-muted">${t.state === "held" ? holdWords(t.note, "", t.held_why) : t.note}</span>` : ""}</dd>
      <dt>Goal</dt><dd>${t.idea_title}</dd>
      <dt>Tier</dt><dd>${t.head ? html`<${Who} head=${t.head} />` : t.tier}</dd>
      <dt>Branch</dt><dd><code>${t.branch || "—"}</code></dd>
      <dt>Round</dt><dd>${t.round || 1}</dd>
      <dt>Spend</dt><dd>${t.cost != null ? (pctOf(t.cost) ? `≈${pctOf(t.cost)}` : `$${t.cost.toFixed(2)}`) : "—"}</dd>
    </dl>`;
  const lines = html`<h3 class="board-sub">Log</h3><pre class="shell-log" ref=${ref} aria-label="Log">${t.log || "Nothing logged yet."}</pre>`;
  return html`<div class="shell-task" data-kind=${log ? "log" : "task"}>
    ${log ? lines : facts}
    ${t.error && html`<${ErrorLine} text=${t.error} />`}
    ${t.state === "failed" && html`<${FailedActions} t=${t} />`}
    ${heldByYou(t) && html`<div class="board-row"><button class="ork-btn primary" data-act="start-now" title="Runs it now, without keeping your reserve" onClick=${() => act("ideas.start_now", { slug: t.idea })}>Start now</button></div>`}
    ${!log && html`<h3 class="board-sub">Brief</h3><p class="shell-brief">${t.brief}</p>`}
    ${t.state === "review" && html`<p><button class="ork-btn primary" onClick=${() => openOver("result", { idea: t.idea, task: t.id }, over.value?.from, t.title)}>Open the result</button></p>`}
    ${live && html`<p><button class="ork-btn danger" onClick=${() => act("ideas.stop_task", { slug: t.idea, task: t.id })}>Stop</button></p>`}
    ${log ? facts : lines}
  </div>`;
}

const STAGE_WORDS = [["goal", "party"], ["spec", "spec"], ["plan", "plan"], ["work", "work"], ["rework", "rework"], ["dropped", "dropped"]];

/** The idea's money so far, by stage (spec 36 §5): stages at 0 left out, — when nothing is priced. */
export function spendWords(s) {
  if (!s || !s.stages) return "";
  if (s.usd == null) return "This goal so far: —";
  const parts = STAGE_WORDS.map(([k, w]) => [w, s.stages[k]?.usd]).filter(([, v]) => v).map(([w, v]) => `${w} ${pctShort(v) || v.toFixed(2)}`);
  const total = `≈${pctOf(s.usd) || `$${s.usd < 10 ? s.usd.toFixed(2) : Math.round(s.usd)}`}`;
  return `This goal so far: ${total}${parts.length ? ` — ${parts.join(" · ")}` : ""}`;
}
