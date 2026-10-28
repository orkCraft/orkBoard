// One thing over the pane (docs/specs/98-the-table-and-the-hand.md §3.6, decisions §142): `frame/state.js` `openOver(kind, props, from, title)` replaces the map with what is opened; the pane's title says where it came from
// (*← System · server/lobby.ts*), **←** or Esc goes back to the map as it was with the card it came from lit, the next replaces it, nothing is pinned, the hand stays under it. The table draws these kinds
// (frame/kinds.js): `file`, `diff`, `log`, `task`, `role`, `settings`, `projects`, `files`, `party`, `play`, `limits`, each with today's renderer imported as it is (shell/preview.js's file, diff and task
// views, shell/settings.js, shell/projects.js, shell/files.js, shell/goaldialog.js and goalwizard.js and partyremove.js, arena/play.js, arena/limits.js), drawn inside the pane, never in a drawer or a dialog:
// the forms that are a `Modal` are restyled to lie in the pane (table.css `.table-over--form`), and their own closing (`closeDialog`) is the pane's ← (places.js).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { ask } from "../board/store.js";
import { Sign, Who } from "../orkui.js";
import { roles, act } from "../shell/store.js";
import { TASK_STATE } from "../board/maplayout.js";
import { holdWords, heldByYou } from "../board/store.js";
import { pctOf } from "../spend.js";
import { ErrorLine } from "../shell/errors.js";
import { File } from "../shell/diffview.js";
import { FileView, FilesPane } from "../shell/files.js";
import { GitDiffView } from "../shell/gitpane.js";
import { SettingsDialog } from "../shell/settings.js";
import { OpenFolderDialog, closeProject, currentProject, openFolder, projectList, projectMark, showProject } from "../shell/projects.js";
import { GoalDialog } from "../shell/goaldialog.js";
import { RemovePartyDialog } from "../shell/partyremove.js";
import { Limits } from "../arena/limits.js";
import { Play } from "../arena/play.js";
import { drawn } from "../frame/kinds.js";
import { openOver, over } from "../frame/state.js";
import { readTask } from "./data.js";

/** A press inside `children` that the old window answered by opening its drawer is the pane's now: `rules` is [[selector, (target, event) => run]]. */
function Reroute({ rules, children, ...rest }) {
  const caught = (e) => {
    for (const [selector, run] of rules) {
      const hit = e.target.closest?.(selector);
      if (hit) { e.stopPropagation(); e.preventDefault(); run(hit, e); return; }
    }
  };
  return html`<div onClickCapture=${caught} ...${rest}>${children}</div>`;
}

// -- a file, a diff, a task ----------------------------------------------------------------------------------------------------------

function FileFace({ props }) {
  return html`<div class="table-over__file" data-kind="file"><${FileView} path=${props.path} /></div>`;
}

function DiffFace({ props }) {
  const [d, setD] = useState(null);
  useEffect(() => {
    if (!props.slug) return undefined;
    let live = true;
    setD(null);
    ask("ideas.diff", { slug: props.slug, task: props.task }).then((r) => { if (live) setD(r || { commits: [], files: [] }); });
    return () => { live = false; };
  }, [props.slug, props.task]);
  if (!props.slug) {
    return html`<${Reroute} rules=${[[".board-link", () => openOver("file", { path: props.path }, over.value?.from, props.path)]]}><${GitDiffView} path=${props.path} /></${Reroute}>`;
  }
  if (!d) return html`<p class="ok-tone-muted">Reading the code…</p>`;
  return html`<div class="table-over__diff" data-kind="diff">
    <h3 class="board-sub">Commits</h3>
    <ol class="shell-commits">${d.commits.map((c) => html`<li key=${c.sha}><code>${c.sha}</code> ${c.subject}</li>`)}</ol>
    <h3 class="board-sub">Files changed (${d.files.length})</h3>
    ${d.files.map((f) => html`<${File} key=${f.path} f=${f} />`)}
    ${d.truncated && html`<p class="ok-tone-muted">Some files are too large to show.</p>`}
  </div>`;
}

/** A task as the old drawer showed it: its state, its goal, its brief and its log (read again every 5 s while it runs). `log`: the log first (a failure's lines). */
function TaskFace({ props, log = false }) {
  const [t, setT] = useState(null), ref = useRef();
  const read = () => readTask(props.slug, props.task).then((r) => r && setT(r));
  useEffect(() => { setT(null); read(); }, [props.slug, props.task]);
  const live = t && (t.state === "running" || t.state === "testing");
  useEffect(() => {
    if (!live) return undefined;
    const id = setInterval(read, 5000);
    return () => clearInterval(id);
  }, [live]);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [t?.log]);
  if (!t) return html`<p class="ok-tone-muted">Opening…</p>`;
  const facts = html`<dl class="shell-facts">
    <dt>State</dt><dd data-state=${t.state}>${TASK_STATE[t.state] || t.state}${t.note ? html` <span class="ok-tone-muted">${t.state === "held" ? holdWords(t.note, "", t.held_why) : t.note}</span>` : ""}</dd>
    <dt>Goal</dt><dd>${t.idea_title}</dd>
    <dt>Tier</dt><dd>${t.head ? html`<${Who} head=${t.head} />` : t.tier}</dd>
    <dt>Branch</dt><dd><code>${t.branch || "—"}</code></dd>
    <dt>Round</dt><dd>${t.round || 1}</dd>
    <dt>Spend</dt><dd>${t.cost != null ? (pctOf(t.cost) ? `≈${pctOf(t.cost)}` : `$${t.cost.toFixed(2)}`) : "—"}</dd>
  </dl>`;
  const lines = html`<h3 class="board-sub">Log</h3><pre class="shell-log" ref=${ref} aria-label="Log">${t.log || "Nothing logged yet."}</pre>`;
  return html`<div class="shell-task table-over__task" data-kind=${log ? "log" : "task"}>
    ${log ? lines : facts}
    ${t.error && html`<${ErrorLine} text=${t.error} />`}
    ${t.state === "failed" && html`<div class="board-row"><button class="ork-btn primary" title="Its goal's tasks that are not merged or at Review run again" onClick=${() => act("ideas.start", { slug: props.slug })}>Start again</button></div>`}
    ${heldByYou(t) && html`<div class="board-row"><button class="ork-btn primary" data-act="start-now" title="Runs it now, without keeping your reserve" onClick=${() => act("ideas.start_now", { slug: props.slug })}>Start now</button></div>`}
    ${!log && html`<h3 class="board-sub">Brief</h3><p class="shell-brief">${t.brief}</p>`}
    ${t.state === "review" && html`<p><button class="ork-btn primary" onClick=${() => openOver("diff", { slug: props.slug, task: props.task }, over.value?.from, t.title)}>Open the result</button></p>`}
    ${live && html`<p><button class="ork-btn danger" onClick=${() => act("ideas.stop_task", { slug: props.slug, task: props.task })}>Stop</button></p>`}
    ${log ? facts : lines}
  </div>`;
}

/** A role's text: what the party's member is told. */
function RoleFace({ props }) {
  const r = (roles.value?.roles || []).find((x) => x.slug === props.slug), lib = (roles.value?.library || []).find((a) => a.id === props.slug);
  const head = r?.head || (lib && { craft: lib.craft, race: lib.race, tier: lib.tier });
  const text = r?.instruction || r?.told || "";
  return html`<article class="table-over__role" data-kind="role" data-role=${props.slug}>
    <h3 class="table-over__nm">${r?.name || lib?.name || props.slug}</h3>
    ${head && html`<p><${Who} head=${head} /></p>`}
    ${(lib?.line || r?.told) && html`<p class="table-over__muted">${lib?.line || r?.told}</p>`}
    ${lib?.check?.applies && html`<p><span class="ork-label">Checks</span> ${lib.check.applies}</p>`}
    <h4 class="ork-label">Its text</h4>
    ${text ? html`<pre class="shell-log table-over__text" aria-label="Its text">${text}</pre>` : html`<p class="ok-tone-muted">It has no text of its own: it works from the task's brief.</p>`}
  </article>`;
}

// -- the places ----------------------------------------------------------------------------------------------------------------------

function ProjectsFace({ props }) {
  if (props.open) return html`<${OpenFolderDialog} />`;
  const list = projectList.value, cur = currentProject.value, here = over.value?.from;
  const choose = (run) => () => run();
  return html`<section class="table-projects" data-kind="projects" aria-label="Projects">
    ${list.open.length > 0 && html`<h3 class="ork-label">Open projects</h3>`}
    <ul class="table-projects__list">${list.open.map((o) => html`<li key=${o.path}><button type="button" class=${cls("ork-row table-projects__one", { "is-on": o.path === list.current })} data-path=${o.path} title=${o.path}
      aria-current=${o.path === list.current ? "true" : undefined} onClick=${choose(() => (o.path === list.current ? null : showProject(o.path)))}>
      <span class="table-projects__nm">${o.name}</span><span class="table-over__muted">${o.path}</span>
      ${projectMark(o) === "alert" ? html`<span class="is-alert" role="img" aria-label="waits for you"><${Sign} name="alert" /></span>` : projectMark(o) === "busy" ? html`<span class="ork-busy" role="img" aria-label="at work"></span>` : null}</button></li>`)}</ul>
    ${list.recent.length > 0 && html`<h3 class="ork-label">Recent</h3>`}
    <ul class="table-projects__list">${list.recent.map((r) => html`<li key=${r.path}><button type="button" class="ork-row table-projects__one" title=${r.path} onClick=${choose(() => openFolder(r.path))}>
      <span class="table-projects__nm">${r.name}</span><span class="table-over__muted">${r.path}</span></button></li>`)}</ul>
    <p class="table-projects__acts"><button type="button" class="ork-btn primary" onClick=${() => openOver("projects", { open: true }, here, "Open a project…")}>Open a project…</button>
      ${cur && html`<button type="button" class="ork-btn" onClick=${() => closeProject(cur.path)}>Close project</button>`}</p>
  </section>`;
}

function FilesFace() {
  const here = over.value?.from;
  return html`<${Reroute} rules=${[
    [".shell-tree__row[data-path]:not([aria-expanded])", (el) => openOver("file", { path: el.dataset.path }, { title: "Files", key: here?.key || "" }, el.dataset.path)],
    [".shell-git__name", (el) => openOver("diff", { path: el.title }, { title: "Files", key: here?.key || "" }, el.title)]]} class="table-over__files" data-kind="files"><${FilesPane} /></${Reroute}>`;
}

function PartyFace({ props }) {
  if (props.remove) return html`<${RemovePartyDialog} slug=${props.slug} />`;
  return html`<${GoalDialog} slug=${props.slug || ""} then=${props.then || ""} preset=${props.preset || ""} proposal=${props.proposal || ""} />`;
}

const faces = {
  file: FileFace, diff: DiffFace, log: (p) => html`<${TaskFace} ...${p} log=${true} />`, task: TaskFace, role: RoleFace,
  settings: () => html`<${SettingsDialog} />`, projects: ProjectsFace, files: FilesFace, party: PartyFace,
  play: () => html`<${Play} />`, limits: ({ props }) => html`<${Limits} provider=${props.provider || ""} />`,
};
for (const [kind, Face] of Object.entries(faces)) drawn(kind, Face);

/** Whether a kind of the table is a form that is a `Modal` (restyled to lie in the pane; its own closing is the pane's ←). */
export const isForm = (o) => !!o && (o.kind === "settings" || o.kind === "party" || (o.kind === "projects" && !!o.props?.open));

