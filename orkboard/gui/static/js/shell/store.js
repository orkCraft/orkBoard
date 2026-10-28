// The window's data (docs/specs/33-v1-shell.md §5–§7, docs/specs/98-the-table-and-the-hand.md): what the host last said of the board (js/board/store.js), of Review, the Map, the agents and roles and the gate. A refresh runs
// when the town says the ideas changed and every 10 s while a model or a task runs. What is open over the pane, the tab, the pick and the lifted card are frame/state.js's; the drawer and its tabs are gone.
import { signal, batch } from "@preact/signals";
import { command, toast } from "../link.js";
import { ask, board, opened, page, BUSY } from "../board/store.js";

export const review = signal(null);        // ideas.review_list
export const agents = signal(null);        // ideas.agents
export const roles = signal(null);         // ideas.roles: the agents, the task types and their agent, the models
export const editing = signal(null);       // the file open in the editor: {path, dirty, save()}, null when none is
export const leaveAsk = signal(null);      // {then}: the editor asks what to do with its unsaved changes before `then` runs
export const mapData = signal(null);       // ideas.map: always read (spec 49 §9)
export const gateData = signal(null);      // ideas.gate: what dev holds that main lacks

const LIVE = ["running", "testing"];

const REVIEW_NOTICE = "Results that hold now land in dev by themselves; Settings → Board to look at each one";
let reviewSaid = false, loading = false, again = false, mapLogged = false;
/** Spec 84 §1: the move of `review` to off is said once, in the window; the host forgets it when told. */
function sayReview(b) {
  if (!b?.review_notice || reviewSaid) return;
  reviewSaid = true;
  toast(REVIEW_NOTICE, "information", "", 12);
  ask("ideas.board_set", { review_notice: false });
}

export async function refreshShell() {
  if (loading) { again = true; return; }
  loading = true;
  try {
    const [b, r, a, ro, mp, gt] = await Promise.all([ask("ideas.board"), ask("ideas.review_list"), ask("ideas.agents"), ask("ideas.roles"), ask("ideas.map"), ask("ideas.gate")]);
    batch(() => {
      if (b) { board.value = b; sayReview(b); }
      if (r) review.value = r;
      if (a) agents.value = a;
      if (ro) roles.value = ro;
      if (mp && Array.isArray(mp.goals)) mapData.value = mp;
      if (gt && typeof gt.same === "boolean") gateData.value = gt;
    });
  } finally {
    loading = false;
    if (again) { again = false; refreshShell(); }
  }
}

/** A command, then everything again. */
export async function act(name, args) {
  const got = await ask(name, args);
  await refreshShell();
  return got;
}

/** What the person opened, for the day's analysis (docs/specs/33-v1-shell.md §9): the host's one loggable event. */
export function logOpened(what, ref, via = "") {
  command("ideas.log", { event: "opened", what, ref: String(ref || ""), device: "desktop", ...(via ? { via } : {}) }).catch(() => {});
}

/** Runs `then` now, or after the person says what to do with the unsaved changes of the file in the editor (asked in the editor itself). */
export function leaving(then) {
  if (editing.value?.dirty) leaveAsk.value = { then };
  else then();
}

/** Another project is shown: nothing of the last one stays on the page. */
export function resetForProject(project = "") {
  batch(() => {
    editing.value = null;
    leaveAsk.value = null;
    board.value = null; review.value = null; agents.value = null; roles.value = null;
    mapData.value = null; gateData.value = null;
    page.value = null;
    opened.value = "";
  });
  if (project && !mapLogged) { mapLogged = true; logOpened("map", ""); }       // the window is shown: once a page load
}

/** Something a model or a task does now: the shell looks again every 10 s. */
export function busy() {
  const b = board.value, a = agents.value;
  return !!(b && (b.ideas.some((i) => BUSY.includes(i.state)) || b.tracks.some((t) => t.state === "reading"))) || !!(a && a.roles.some((r) => (r.chips || []).some((c) => LIVE.includes(c.state) || (c.goal && c.state === "reading"))));
}
