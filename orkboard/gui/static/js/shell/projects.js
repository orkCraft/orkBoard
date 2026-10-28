// The projects (docs/specs/37-board-and-line.md §8, docs/specs/98-the-table-and-the-hand.md §3.1, §7): what the projects are (the host sends `projects` with every snapshot, projects.list, so the marks are live; showing another
// project stops nothing in the others), the Open folder place over the pane (its form, and *Start git here?* for a folder with none), and the start screen when no project is open (its form lies in the pane too).
// The question before a project with running tasks is closed lies in the projects' place (table/over.js), in the card it confirms.
import { useEffect, useRef, useState } from "preact/hooks";
import { computed, signal } from "@preact/signals";
import { html } from "../html.js";
import { town, command, toast } from "../link.js";
import { Place, closePlace } from "../frame/place.js";
import { keepTabsBy } from "../frame/state.js";
import { leaving } from "./store.js";

export const projectList = computed(() => town.value?.projects || { current: null, open: [], recent: [] });
/** Orkboard's host sends `projects`; Orkline's page (same shell) has one fixed project and none of this. */
export const projectsOn = computed(() => !!town.value?.projects);
export const currentProject = computed(() => {
  const p = projectList.value;
  return p.open.find((o) => o.path === p.current) || null;
});
keepTabsBy(() => currentProject.value?.path || "");       // the open tab is kept per project (frame/state.js)
/** An open project's one mark in the switcher (spec 87 §6), never a count: orkUI's alert sign when something of it waits for the person (`needs_you`), else the busy mark while a task of it is at work
 *  (`working`), else nothing. */
export const projectMark = (p) => (p.needs_you > 0 ? "alert" : p.working > 0 ? "busy" : "");

/** Open a folder: a refusal comes back in words (the dialog shows it); a folder without git is offered Start git here. */
export async function openFolder(path) {
  let got;
  try { got = await command("projects.open", { path, device: "desktop" }); } catch { return { ok: false, error: "" }; }
  return got;
}

export function showProject(path) {
  return leaving(() => command("projects.use", { path }).catch(() => {}));
}

/** Closes a project; with tasks running in it the host refuses and says how many: `{path, name, running}` for the question that asks to stop them (`stop`: they are stopped), else null. */
export async function closeProject(path, stop = false) {
  let got;
  try { got = await command("projects.close", { path, ...(stop ? { stop: true } : {}) }); } catch { return null; }
  if (!got?.running) return null;
  return { path, name: projectList.value.open.find((o) => o.path === path)?.name || "the project", running: got.running };
}

export async function startGit(path) {
  try {
    const got = await command("projects.start_git", { path });
    if (got?.error) { toast(got.error, "error"); return false; }
    toast(got.said || "Git is started", "information");
    return true;
  } catch { return false; }
}

const PICK_POLL_MS = 300;

/** The system's folder dialog (gui/folder_dialog.py): the host opens it, the page asks what came of it while `alive`.
 *  {state: "done", path} | {state: "none"} (cancelled) | {state: "error", why} (no dialog here: the path is typed). */
export async function chooseFolder(start, alive) {
  let token;
  try { ({ token } = await command("folders.pick", { start })); } catch { return { state: "error", why: "" }; }
  while (alive.current) {
    await new Promise((r) => setTimeout(r, PICK_POLL_MS));
    let got;
    try { got = await command("folders.picked", { token }); } catch { return { state: "error", why: "" }; }
    if (got?.state !== "open") return got || { state: "error", why: "" };
  }
  return { state: "none" };
}

/** Open folder, a place over the pane (`onClose`: where Cancel and Esc go; ←, by default). */
export function OpenFolderPlace({ onClose = closePlace }) {
  const [path, setPath] = useState("");
  const [why, setWhy] = useState("");
  const [busy, setBusy] = useState(false);
  const [choosing, setChoosing] = useState(false);
  const [nogit, setNogit] = useState("");        // the folder just opened that has no git
  const alive = useRef(true);
  const recent = projectList.value.recent;
  const go = async (e, p = path) => {
    e?.preventDefault();
    if (!p.trim() || busy) return;
    setBusy(true);
    const got = await openFolder(p.trim());
    setBusy(false);
    if (!got.ok) { if (got.error) setWhy(got.error); return; }
    if (got.git === false) { setNogit(p.trim()); return; }
    onClose();
  };
  // As an IDE's Open Folder: the system's dialog at once (quiet when there is none here), Choose… to open it again;
  // the folder chosen opens, and the path can still be typed or a recent one taken.
  const choose = async (quiet = false) => {
    if (choosing) return;
    setChoosing(true);
    setWhy("");
    const got = await chooseFolder(path.trim(), alive);
    if (!alive.current) return;
    setChoosing(false);
    if (got.state === "done" && got.path) { setPath(got.path); go(null, got.path); }
    else if (got.state === "error" && got.why && !quiet) setWhy(got.why);
  };
  useEffect(() => { choose(true); return () => { alive.current = false; }; }, []);
  if (nogit) {
    return html`<${Place} title="Start git here?" onClose=${onClose}
      foot=${html`<button type="button" class="ork-btn" onClick=${onClose}>Not now</button>
        <button type="button" class="ork-btn primary" onClick=${async () => { if (await startGit(nogit)) onClose(); }}>Start git here</button>`}>
      <p>This folder has no git. The Board works on a repository, so its tasks need one.</p>
      <p class="ok-font-status ok-tone-muted">Start git here makes a first commit of the folder's files as they are, and changes nothing else.</p>
    <//>`;
  }
  return html`<${Place} title="Open folder" onClose=${onClose}
    foot=${html`<button type="button" class="ork-btn" onClick=${onClose}>Cancel</button>
      <button type="submit" form="open-folder-form" class="ork-btn primary" disabled=${!path.trim() || busy}>Open folder</button>`}>
    <form id="open-folder-form" class="shell-form" onSubmit=${go}>
      <div class="shell-field"><label class="ok-font-label" for="open-folder-path">Folder</label>
        <div class="shell-pick"><input id="open-folder-path" class="ork-field" autofocus value=${path} aria-label="Folder"
          placeholder="The path of a project's folder, such as ~/code/shop" onInput=${(e) => { setPath(e.target.value); setWhy(""); }} />
          <button type="button" class="ork-btn" disabled=${choosing || busy} onClick=${() => choose()}>Choose…</button></div>
        ${choosing && html`<p class="ok-font-status ok-tone-muted" role="status">Choose the folder in the dialog that opened, or type its path.</p>`}</div>
      ${why && html`<p class="ok-tone-error" role="alert">${why}</p>`}
      <p class="ok-font-status ok-tone-muted">The folder becomes a project: its parties, goals and tasks are kept in it, apart from your other projects.</p>
      ${recent.length > 0 && html`<div class="shell-field" role="group" aria-label="Recent"><span class="ok-font-label">Recent</span>
        <div class="shell-menu__list">${recent.map((r) => html`<button type="button" key=${r.path} class="shell-menu__item" title=${r.path}
          onClick=${(e) => go(e, r.path)}>${r.name} <span class="ok-tone-muted">${r.path}</span></button>`)}</div></div>`}
    </form>
  <//>`;
}

/** The start screen's form is out (Open folder…, Ctrl+O). */
export const startForm = signal(false);

/** No project is open: Open folder… and the recent ones, drawn in the pane. */
export function StartScreen() {
  const recent = projectList.value.recent;
  return html`<main class="shell-start" aria-label="Start">
    <h1>Open a project</h1>
    <p class="ok-tone-muted">A project is a repository's folder. Its parties, goals and tasks are kept in it.</p>
    ${startForm.value ? html`<${OpenFolderPlace} onClose=${() => { startForm.value = false; }} />`
      : html`<p><button class="ork-btn primary" onClick=${() => { startForm.value = true; }}>Open folder…</button>
        <span class="ok-tone-muted"> Ctrl+O</span></p>`}
    ${recent.length > 0 && !startForm.value && html`<section class="shell-start__recent" aria-label="Recent"><h2 class="ok-font-label">Recent</h2>
      <ul>${recent.map((r) => html`<li key=${r.path}><button class="board-link" title=${r.path} onClick=${() => openFolder(r.path)}>${r.name}</button>
        <span class="ok-font-status ok-tone-muted">${r.path}</span></li>`)}</ul></section>`}
  </main>`;
}
