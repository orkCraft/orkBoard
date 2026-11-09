// The Orkmaster's line (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §4.3, decisions §177.2): when the work moved to another AI tool (or back), the Orkmaster says it once, in one line, on the table under the pane's
// title: its crowned head and the line in the body face (*Claude Code is out until Thu 18:00: the work goes on with Codex.*). The host keeps the last move in the snapshot (`town.mana.moved = {from, to, until, at, line}`).
// It is shown while this viewer has not put it away (its close button; a newer move shows again) and for a day after `at`, then it is gone. What a viewer put away is a per-viewer convenience kept in `localStorage`, per project,
// in try/catch: without it the line shows until the day is out. Not a toast: it stays where it is until it is put away.
// **While a fix runs** (docs/specs/139-the-die-the-door-and-the-bug.md A.5, decisions §246.6) the Orkmaster says that too, above the other: *Fixing Orkboard: <its line>* (hand/logsbtn.js `fixingLine`, from `town.repair.state`); a fix that is in (`ready`) and waits for the restart has no card from the host, so the line says *Orkboard was fixed: restart to take it* until the viewer puts it away (`solvedLine`); the fixing line is no line to put away, itgoes when the fix does.
import { useEffect, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { town, PRODUCT } from "../link.js";
import { currentProject } from "../shell/projects.js";
import { fixingLine, repairOf } from "../hand/logsbtn.js";

export const DAY_MS = 24 * 60 * 60 * 1000;
const KEPT = "orkboard.mana.seen";

const readSeen = () => { try { const got = JSON.parse(localStorage.getItem(KEPT)); return got && typeof got === "object" ? got : {}; } catch { return {}; } };
const SOLVED_KEPT = "orkboard.fix.seen";
const readSolved = () => { try { return String(localStorage.getItem(SOLVED_KEPT) || ""); } catch { return ""; } };
const seen = signal(readSeen());           // project → the `at` of the last move this viewer put away

/** The line to show for a move, or "": it has words, this viewer has not put it away (`dismissed`: the `at` it put away, "" none) and a day has not gone by since `at`. */
export function lineOf(moved, dismissed = "", now = Date.now()) {
  if (!moved?.line || !moved.at || String(moved.at) <= String(dismissed || "")) return "";
  const at = new Date(moved.at).getTime();
  return Number.isNaN(at) || now - at >= DAY_MS ? "" : moved.line;
}

const solvedSeen = signal(readSolved());       // the `started_at` of the last fix this viewer put away

/** The Orkmaster's line for a fix that is in and waits for the person to restart (docs/specs/139 A.5): the host sends no card for it, so the line is the fallback, shown until this viewer puts it away
 *  (a newer fix, another `started_at`, shows again); "" when there is none. */
export function solvedLine(r = repairOf(), dismissed = solvedSeen.value) {
  return r.state === "ready" && String(r.started_at ?? "") !== String(dismissed || "") ? `${PRODUCT} was fixed: restart to take it` : "";
}

/** Puts the move's line away for this viewer (a newer move shows again). */
export function dismiss(project, at) {
  seen.value = { ...seen.value, [project]: at };
  try { localStorage.setItem(KEPT, JSON.stringify(seen.value)); } catch { /* this run only */ }
}

/** The Orkmaster's unasked news now, in the order shown (a fix running, a fix in and waiting, a move): `[{key, kind, text, at, put}]`, `put` puts one away. Both faces read it; a move's day runs out by itself. */
export function useNotes() {
  const moved =town.value?.mana?.moved || null, project = currentProject.value?.path || "";
  const [, again] = useState(0), at = moved?.at ? new Date(moved.at).getTime() : NaN;
  useEffect(() => {                                              // a day after `at` the line goes by itself
    const left = at + DAY_MS - Date.now();
    if (Number.isNaN(left) || left <= 0) return undefined;
    const t = setTimeout(() => again((n) => n + 1), Math.min(left + 50, 2 ** 31 - 1));
    return () => clearTimeout(t);
  }, [at]);
  const line = lineOf(moved, seen.value[project]), fixing = fixingLine(), solved = solvedLine(), solvedAt = repairOf().started_at;
  const putAway = () => { solvedSeen.value = String(solvedAt ?? ""); try { localStorage.setItem(SOLVED_KEPT, solvedSeen.value); } catch { /* this run only */ } };
  const notes = [];
  if (fixing) notes.push({ key: "fixing", kind: "fixing", text: fixing, at: "", put: null });
  if (solved) notes.push({ key: "solved", kind: "solved", text: solved, at: "", put: putAway });
  if (line) notes.push({ key: "moved", kind: "moved", text: line, at: moved.at, put: () => dismiss(project, moved.at) });
  return notes;
}

/** The strip under the pane's title, for where the Orkmaster's column is not drawn (the narrow width); the wide page has the balloon (balloon.js). */
export function Notice() {
  const notes = useNotes();
  if (!notes.length) return null;
  return html`${notes.map((n) => html`<div class="table-notice" role="status" key=${n.key} data-fixing=${n.kind === "fixing" ? "1" : undefined} data-solved=${n.kind === "solved" ? "1" : undefined} data-at=${n.at || undefined}>
      <${Head} race="peon" tier="crown" />
      <p class="table-notice__line">${n.text}</p>
      ${n.put && html`<button type="button" class="ork-btn quiet table-notice__x" aria-label="Dismiss" title="Dismiss" onClick=${n.put}><${Icon} name="close" /></button>`}
    </div>`)}`;
}
