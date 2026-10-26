// The board's state (docs/specs/29a-board-focus.md §6–7): what the host last said of the goals and ideas, the page of
// the open idea, and the one way to ask the host. The v1 shell (js/shell/store.js) refreshes it with Review and Agents.
import { signal, batch } from "@preact/signals";
import { useEffect } from "preact/hooks";
import { command, toast, say, town } from "../link.js";

export const board = signal(null);          // ideas.board
export const opened = signal("");           // slug of the idea in the preview (the shell sets it)
export const page = signal(null);           // ideas.page of the open idea
export const track = signal("");            // the track shown ("" = all)
export const adding = signal(false);        // the Drop it field is up

export const ops = signal(null);            // ops.list: Operations of the person (docs/specs/38-operations.md §11)
export const OPS = "@operations";           // the goal select's last choice: Operations in place of Needs you and the ideas

export const PROJECT = "@project";         // the project's level (spec 70): the parties as columns, their goals as decks; shown like Operations, in place of a party

export const BUSY = ["reading", "planning", "working"];

/** A command of the contract; a plain-words error comes back as a toast and a null. */
export async function ask(name, args = {}) {
  try {
    const got = await command(name, args);
    if (got && got.error) { toast(got.error, "error"); return null; }
    return got || {};
  } catch { return null; }
}

export function busy() {
  const b = board.value;
  return !!b && b.ideas.some((i) => BUSY.includes(i.state));
}

/** An idea's state in the person's words (§7). */
export function stateWords(i) {
  const p = i.progress || { done: 0, total: 0 };
  return say({ raw: "new", reading: "drafting", asks: "asks you", ready: "ready", planning: "planning", proposed: "proposed",
    plan: "plan ready", working: `working ${p.done}/${p.total}`, done: "done", failed: "needs you" }[i.state] || i.state);
}

export const PRIORITY_WORDS = { high: "High", normal: "Normal", low: "Low" };
const PRIORITY_ORDER = ["high", "normal", "low"];

/** The parties a person can choose for a goal (spec 35 §3: General is the system's, never listed; the Team party holds Operations, not goals: spec 92 §3), by priority, then the person's order. */
export function goalList() {
  const tracks = (board.value?.tracks || []).filter((g) => g.slug !== "general" && g.recipe !== "team");
  return [...tracks].sort((a, b) => PRIORITY_ORDER.indexOf(a.priority) - PRIORITY_ORDER.indexOf(b.priority) || a.order - b.order);
}

/** "2026-10-18T18:00:00" → "18:00". */
export const hhmm = (iso) => (String(iso || "").length >= 16 ? String(iso).slice(11, 16) : String(iso || ""));

/** A section's list (`- x`, `1. x`), or its lines when it has none (realm/ideas.py `items`). */
export function items(text) {
  const lines = String(text || "").split("\n").map((l) => l.trim()).filter(Boolean);
  const marked = lines.filter((l) => /^([-*+]|\d+[.)])\s+/.test(l)).map((l) => l.replace(/^([-*+]|\d+[.)])\s+/, ""));
  return marked.length ? marked : lines;
}

/** A held task's note in words (spec 35 §11.5): the limits, the person's reserve (§6), or another idea on the same files
 *  (§5; after the wait, beside it). `title` is that idea's title when the host sent it. `why`: the host's own sentence for a hold by the reserve
 *  or the week's pace (*Waits for Claude's limit: 14 % of the week left, kept for you until 12:00*: the tool, its share, until when); a hold
 *  from before it was written says what it can. */
export function holdWords(note, title = "", why = "") {
  const n = String(note || "");
  let m;
  if (why && /^(reserve|week)/.test(n)) return why;
  if ((m = /^reserve · after (.+)$/.exec(n))) return `Waits for your reserve: kept for you until ${m[1]}`;
  if ((m = /^week · after (.+)$/.exec(n))) return `Waits for the week's pace until ${m[1]}`;
  if ((m = /^after (\d\d:\d\d)$/.exec(n))) return `waits for limits · after ${m[1]}`;
  if ((m = /^files beside · (.+)$/.exec(n))) return `beside ${title || m[1]} · same files`;
  if ((m = /^files · (.+)$/.exec(n))) return `waits for ${title || m[1]} · same files`;
  return n;
}

/** A task the person's reserve or the week's pace holds: what Start now lets go (the window of a tool, or another goal's files, it cannot). */
export const heldByYou = (t) => t?.state === "held" && /^(reserve|week)/.test(String(t.note || ""));

let opsLoading = null;
/** Operations again (`ops.list`): the person's, the same in every project and with none open. */
export function refreshOps() {
  if (!opsLoading) opsLoading = ask("ops.list").then((got) => { if (got) ops.value = got; }).finally(() => { opsLoading = null; });
  return opsLoading;
}

/** Operations is read now and again whenever the host's `ops_rev` moves. */
export function useOps() {
  const rev = town.value?.ops_rev;
  useEffect(() => { if (rev !== undefined) refreshOps(); }, [rev]);   // Orkline's page has no Operations
  return ops.value;
}

export const runOf = (id) => (ops.value?.runs || []).find((r) => r.id === id) || null;
export const templateOf = (name) => (ops.value?.templates || []).find((t) => t.name === name) || null;
