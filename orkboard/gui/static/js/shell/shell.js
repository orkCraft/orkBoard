// The one window (docs/specs/98-the-table-and-the-hand.md §7, decisions §145.1): the table (the leaders' tabs and the pane) over the hand (the deck, the stacks, the discard), nothing else — no top bar, no left column,
// no right column, no dialog (frame/frame.js). What was a dialog or the drawer lies over the pane (frame/state.js `openOver`). With no project the start screen is drawn in the pane. Always Office's calm look; no camp.
// Keyboard: Esc lowers a lifted card, else closes what is over the pane, else picks none (the table and the hand each take their own step and mark the key `defaultPrevented`; this is the last one); Ctrl/⌘+O opens the projects.
import { useEffect, useRef } from "preact/hooks";
import { html } from "../html.js";
import { town } from "../link.js";
import { SignIn } from "./signin.js";
import { StartScreen, currentProject, projectsOn, startForm } from "./projects.js";
import { resetFiles } from "./files.js";
import { resetGit } from "./gitpane.js";
import { refreshShell, busy, resetForProject } from "./store.js";
import { Frame } from "../frame/frame.js";
import { lifted, openOver, over, pick, picked } from "../frame/state.js";

const sheets = ["../board/board.css", "./shell.css", "./party.css", "../arena/arena.css"].map((p) => new URL(p, import.meta.url).href);
if (typeof document !== "undefined") {
  for (const href of sheets) {
    if (!document.querySelector(`link[href="${href}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      document.head.appendChild(link);
    }
  }
}

const typing = (el) => !!el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable);

/** The start screen, in a pane of its own (there is no table yet). */
function Start() {
  return html`<div class="frame" data-frame="start"><div class="frame-table"><div class="table"><section class="table-pane ork-table">
    <header class="ork-head table-title"><span class="table-title__pt" data-title>Open a project</span></header>
    <div class="table-body"><${StartScreen} /></div>
  </section></div></div></div>`;
}

export function Shell() {
  const t = town.value;
  const project = projectsOn.value ? currentProject.value?.path || "" : "-";   // "-": Orkline's one fixed project
  // Another project is shown: nothing of the last one stays (its Board, its tree, its git).
  const was = useRef(null);
  if (was.current !== project) { was.current = project; resetForProject(project); resetFiles(); resetGit(); }
  // Fresh when the town says the ideas changed, and every 10 s while a model or a task runs.
  useEffect(() => { if (project) refreshShell(); }, [t.ideas_rev, project]);
  useEffect(() => {
    const id = setInterval(() => { if (currentProject.value && busy()) refreshShell(); }, 10000);
    return () => clearInterval(id);
  }, []);
  useEffect(() => {
    const key = (e) => {
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "o") {   // the projects, as an IDE's Open Folder
        e.preventDefault();
        if (!currentProject.value) startForm.value = true;
        else if (over.value?.kind !== "projects") openOver("projects", {}, null, "Projects");
      } else if (e.key === "Escape" && !e.defaultPrevented && !typing(e.target) && !lifted.value && !over.value && picked.value) {
        e.preventDefault();
        pick("");                                      // the last step: no goal picked, the whole project again
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, []);
  return html`<div class="shell" data-frame="1" data-start=${project ? undefined : "true"}>${project ? html`<${Frame} />` : html`<${Start} />`}<${SignIn} /></div>`;
}
