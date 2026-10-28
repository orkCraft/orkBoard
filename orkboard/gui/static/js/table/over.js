// One thing over the pane (docs/specs/98-the-table-and-the-hand.md §3.6, §7, decisions §142): `frame/state.js` `openOver(kind, props, from, title)` replaces the map with what is opened; the pane's title says where it came from
// (*← System · server/lobby.ts*), **←** or Esc goes back to the map as it was with the card it came from lit, the next replaces it, nothing is pinned, the hand stays under it. The table draws these kinds
// (frame/kinds.js): `file`, `diff`, `log`, `task`, `role`, `settings`, `projects`, `files`, `party` (a party removed), `parties`, `play`, `limits`, `pair`, `week`, each with today's renderer imported as it is (shell/preview.js's task view, shell/files.js,
// shell/settings.js, shell/projects.js, shell/partyremove.js and the parties' place (parties.js), shell/pair.js, board/week.js, arena/play.js, arena/limits.js), drawn inside the pane, never in a drawer or a dialog:
// the forms lie in a `Place` (frame/place.js), and their own closing is the pane's ←. The update's offer (shell/update.js) and the hand's (hand/hand.js) are drawn by their own parts.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { ask } from "../board/store.js";
import { Sign, Who } from "../orkui.js";
import { roles } from "../shell/store.js";
import { Task } from "../shell/preview.js";
import { File } from "../shell/diffview.js";
import { FileView, FilesPane } from "../shell/files.js";
import { GitDiffView } from "../shell/gitpane.js";
import { SettingsPlace } from "../shell/settings.js";
import { OpenFolderPlace, closeProject, currentProject, openFolder, projectList, projectMark, showProject } from "../shell/projects.js";
import { RemovePartyPlace } from "../shell/partyremove.js";
import { PairPlace } from "../shell/pair.js";
import { WeekView } from "../board/week.js";
import { openPlace } from "../frame/place.js";
import { Limits } from "../arena/limits.js";
import { Play } from "../arena/play.js";
import { drawn } from "../frame/kinds.js";
import { openOver, over } from "../frame/state.js";
import { town } from "../link.js";
import { readTask } from "./data.js";

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
    return html`<${GitDiffView} path=${props.path} onFile=${(path) => openOver("file", { path }, over.value?.from, path)} />`;
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

/** A task: shell/preview.js's view of it, read again every 5 s while it runs. `log`: the log first (a failure's lines). */
function TaskFace({ props, log = false }) {
  const [t, setT] = useState(null);
  const read = () => readTask(props.slug, props.task).then((r) => r && setT(r));
  useEffect(() => { setT(null); read(); }, [props.slug, props.task]);
  const live = t && (t.state === "running" || t.state === "testing");
  useEffect(() => {
    if (!live) return undefined;
    const id = setInterval(read, 5000);
    return () => clearInterval(id);
  }, [live]);
  return html`<div class="table-over__task"><${Task} d=${t && { task: { ...t, idea: t.idea || props.slug, id: t.id || props.task } }} log=${log} /></div>`;
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
  const [closing, setClosing] = useState(null);                 // {path, name, running}: a project with tasks running, asked before it is closed
  if (props.open) return html`<${OpenFolderPlace} />`;
  const list = projectList.value, cur = currentProject.value, here = over.value?.from;
  const close = async (path, stop = false) => { setClosing(await closeProject(path, stop)); };
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
    ${closing && html`<div class="table-projects__ask" role="group" aria-label="Close project">
      <p><b>Close project.</b> ${closing.running} task${closing.running === 1 ? " is" : "s are"} running in ${closing.name}.</p>
      <p class="ok-font-status ok-tone-muted">Stopping them ends their work; what they wrote so far stays in their branches.</p>
      <p class="table-projects__acts"><button type="button" class="ork-btn" onClick=${() => setClosing(null)}>Keep it open</button>
        <button type="button" class="ork-btn danger" onClick=${async () => { await closeProject(closing.path, true); setClosing(null); }}>Stop them and close</button></p></div>`}
    <p class="table-projects__acts"><button type="button" class="ork-btn primary" onClick=${() => openOver("projects", { open: true }, here, "Open a project…")}>Open a project…</button>
      ${cur && html`<button type="button" class="ork-btn" onClick=${() => close(cur.path)}>Close project</button>`}</p>
  </section>`;
}

function FilesFace() {
  const here = over.value?.from, from = { title: "Files", key: here?.key || "" };
  return html`<div class="table-over__files" data-kind="files"><${FilesPane} onFile=${(path) => openOver("file", { path }, from, path)} onDiff=${(path) => openOver("diff", { path }, from, path)} /></div>`;
}

/** The AI tools' limits: what is left of one and what used it, with today's spend and the week's work (a place of its own). */
function LimitsFace({ props }) {
  const hud = town.value?.hud || {}, spend = hud.show_gold ? hud.gold : hud.lumber;
  return html`<div class="table-over__limits"><${Limits} provider=${props.provider || ""} />
    <p><button type="button" class="ork-btn" aria-label=${`Spend today: ${spend ?? "—"}. This week's work`} onClick=${() => openPlace("week", {}, "This week")}>Spend today <b>${spend ?? "—"}</b> · This week's work</button></p></div>`;
}

/** The question that follows a party's *Remove party*. Making and editing the parties is the one place of them (parties.js, kind `parties`). */
function PartyFace({ props }) {
  return props.remove ? html`<${RemovePartyPlace} slug=${props.slug} />` : null;
}

const faces = {
  file: FileFace, diff: DiffFace, log: (p) => html`<${TaskFace} ...${p} log=${true} />`, task: TaskFace, role: RoleFace,
  settings: () => html`<${SettingsPlace} />`, projects: ProjectsFace, files: FilesFace, party: PartyFace,
  play: () => html`<${Play} />`, limits: LimitsFace, pair: () => html`<${PairPlace} />`, week: () => html`<${WeekView} />`,
};
for (const [kind, Face] of Object.entries(faces)) drawn(kind, Face);

/** Whether a kind is a form in a `Place` (frame/place.js): it has its own padding and pins its buttons at its foot. */
export const isForm = (o) => !!o && (["settings", "party", "pair", "week", "update"].includes(o.kind) || (o.kind === "projects" && !!o.props?.open));

