// The Orkmaster's line (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §4.3, decisions §177.2): when the work moved to another AI tool (or back), the Orkmaster says it once, in one line, on the table under the pane's
// title: its crowned head and the line in the body face (*Claude Code is out until Thu 18:00: the work goes on with Codex.*). The host keeps the last move in the snapshot (`town.mana.moved = {from, to, until, at, line}`).
// It is shown while this viewer has not put it away (its close button; a newer move shows again) and for a day after `at`, then it is gone. What a viewer put away is a per-viewer convenience kept in `localStorage`, per project,
// in try/catch: without it the line shows until the day is out. Not a toast: it stays where it is until it is put away.
import { useEffect, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { town } from "../link.js";
import { currentProject } from "../shell/projects.js";

export const DAY_MS = 24 * 60 * 60 * 1000;
const KEPT = "orkboard.mana.seen";

const readSeen = () => { try { const got = JSON.parse(localStorage.getItem(KEPT)); return got && typeof got === "object" ? got : {}; } catch { return {}; } };
const seen = signal(readSeen());           // project → the `at` of the last move this viewer put away

/** The line to show for a move, or "": it has words, this viewer has not put it away (`dismissed`: the `at` it put away, "" none) and a day has not gone by since `at`. */
export function lineOf(moved, dismissed = "", now = Date.now()) {
  if (!moved?.line || !moved.at || String(moved.at) <= String(dismissed || "")) return "";
  const at = new Date(moved.at).getTime();
  return Number.isNaN(at) || now - at >= DAY_MS ? "" : moved.line;
}

/** Puts the move's line away for this viewer (a newer move shows again). */
export function dismiss(project, at) {
  seen.value = { ...seen.value, [project]: at };
  try { localStorage.setItem(KEPT, JSON.stringify(seen.value)); } catch { /* this run only */ }
}

export function Notice() {
  const moved = town.value?.mana?.moved || null, project = currentProject.value?.path || "";
  const [, again] = useState(0), at = moved?.at ? new Date(moved.at).getTime() : NaN;
  useEffect(() => {                                              // a day after `at` the line goes by itself
    const left = at + DAY_MS - Date.now();
    if (Number.isNaN(left) || left <= 0) return undefined;
    const t = setTimeout(() => again((n) => n + 1), Math.min(left + 50, 2 ** 31 - 1));
    return () => clearTimeout(t);
  }, [at]);
  const line = lineOf(moved, seen.value[project]);
  if (!line) return null;
  return html`<div class="table-notice" role="status" data-at=${moved.at}>
    <${Head} race="peon" tier="crown" />
    <p class="table-notice__line">${line}</p>
    <button type="button" class="ork-btn quiet table-notice__x" aria-label="Dismiss" title="Dismiss" onClick=${() => dismiss(project, moved.at)}><${Icon} name="close" /></button>
  </div>`;
}
