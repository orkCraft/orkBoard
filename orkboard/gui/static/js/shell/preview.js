// The views the drawer had that the pane keeps (docs/specs/33-v1-shell.md §6, spec 39 §3; docs/specs/98-the-table-and-the-hand.md §7): a task's state, brief and log (`Task`, drawn over the map by table/over.js) and the money of a goal so far
// (`spendWords`, read by hand/resultface.js, which draws a result's tests, changes, commits and files with the answers of Review at its foot). The drawer itself is gone.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Who } from "../orkui.js";
import { ErrorLine } from "./errors.js";
import { LogTerm, LogView } from "./logview.js";
import { wide } from "../table/data.js";
import { holdWords, heldByYou } from "../board/store.js";
import { TASK_STATE } from "../board/maplayout.js";
import { act } from "./store.js";
import { closeOver, openInventory, openOver, over } from "../frame/state.js";
import { StepsList, stepsOf } from "../table/steps.js";
import { toolName } from "../table/tabmarks.js";
import { town } from "../link.js";
import { pctOf, pctShort } from "../spend.js";

/** A failed task's way on: run its goal's tasks again, or drop it (asked first, in the card). */
function FailedActions({ t }) {
  const [sure, setSure] = useState(false);
  const drop = async () => { const got = await act("ideas.drop_task", { slug: t.idea, task: t.id }); if (got?.ok) closeOver(); };
  return html`<div class="board-row">
    <button class="ork-btn primary" title=${"Its goal's tasks that are not merged or at Review run again" + (t.holds_commits ? ". The task's work is thrown away and made again" : "")} onClick=${() => act("ideas.start", { slug: t.idea })}>Start again</button>
    ${sure ? html`<span>Drop this task? Its worktree goes; its branch stays.</span>
      <button class="ork-btn danger" onClick=${drop}>Drop it</button><button class="ork-btn" onClick=${() => setSure(false)}>Keep it</button>`
      : html`<button class="shell-quiet" onClick=${() => setSure(true)}>Drop…</button>`}</div>`;
}

const OWN_TOOL = "This task was run in your own AI tool, so Orkboard has no log of it. What it made is in its branch and its commits.";

/** A seat's work, its header (spec 168 I1, decisions §283.16.9): the seat's head with its tier, race and craft, the AI tool it runs on, and an edit mark that opens its leader's inventory. */
function SeatHeader({ t }) {
  const tool = t.tool || town.value?.mana?.main || "";
  const edit = () => { closeOver(); openInventory(t.party); };
  return html`<header class="shell-seat" data-seat>
    ${t.head ? html`<${Who} head=${t.head} />` : html`<span class="shell-seat__tier">${t.tier}</span>`}
    ${tool && html`<span class="shell-seat__tool" data-tool=${tool}><span class="ork-label">Tool</span> ${toolName(tool)}</span>`}
    <button type="button" class="ork-btn quiet shell-seat__edit" data-edit-inventory aria-label="Edit its leader's inventory" title="Opens its leader's inventory: its tool and its tier" onClick=${edit}>Edit</button>
  </header>`;
}

/** A task: its state, its goal, who does it, its brief and its log (`d.task`, `ideas.task`; the caller reads it again while it runs). `log`: the log first (a failure's lines). */
export function Task({ d, log = false }) {
  const t = d?.task;
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
  const lines = t.own_tool
    ? html`<p class="shell-owntool" data-own-tool>${OWN_TOOL}</p>`                       // the host never saw that session: it has no log of it
    : wide.value ? html`<${LogTerm} text=${t.log} label="Log" />` : html`<${LogView} text=${t.log} label="Log" />`;      // the terminal from 760 px up; the narrow page keeps its log as it was (spec 168, *Every stage keeps*)
  const steps = stepsOf(t);
  return html`<div class="shell-task" data-kind=${log ? "log" : "task"}>
    <${SeatHeader} t=${t} />
    ${steps && html`<div class="shell-task__steps" data-steps><${StepsList} st=${steps} /></div>`}
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

/** Tokens in a few words: *3.1 million tokens*, *412 thousand tokens*, *900 tokens*. */
export function tokenWords(n) {
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)} million tokens`;
  if (n >= 1e3) return `${Math.round(n / 1e3)} thousand tokens`;
  return `${n} token${n === 1 ? "" : "s"}`;
}

/** The share of a tool's window the goal took (`s.share`: `{name, window, share}`, the limits read at its first call and now): *about 2% of Codex's week*; "" when the host read it twice for none. */
export function shareWords(share) {
  if (!share || !Number.isFinite(Number(share.share))) return "";
  const n = Number(share.share), w = String(share.window || ""), window = w.endsWith("week") ? "week" : w.endsWith("5h") ? "five-hour window" : "";
  return window ? `${n < 1 ? "under 1%" : `about ${Math.round(n)}%`} of ${share.name || share.tool}'s ${window}` : "";
}

/** The idea's money so far, by stage (spec 36 §5): stages at 0 left out. With no price known (a tool whose prices are not in the table), what is known: the tokens and the share of the tool's window, never a dollar (spec 149 H.2); — when nothing is. */
export function spendWords(s) {
  if (!s || !s.stages) return "";
  if (s.usd == null) {
    const share = shareWords(s.share);
    return s.tokens > 0 ? `This goal so far: ${tokenWords(s.tokens)}${share ? ` · ${share}` : ""}` : "This goal so far: —";
  }
  const parts = STAGE_WORDS.map(([k, w]) => [w, s.stages[k]?.usd]).filter(([, v]) => v).map(([w, v]) => `${w} ${pctShort(v) || v.toFixed(2)}`);
  const total = `≈${pctOf(s.usd) || `$${s.usd < 10 ? s.usd.toFixed(2) : Math.round(s.usd)}`}`;
  return `This goal so far: ${total}${parts.length ? ` — ${parts.join(" · ")}` : ""}`;
}
