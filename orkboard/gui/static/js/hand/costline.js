// A change's cost in one line (docs/specs/132-four-levels-the-way-down-and-findings.md C.2, A; decisions §237.7): the sentence a card or a toast says of what a step spends, from `{usd_low, usd_high}` as the host gives it
// and in the gems' words (cost.js: *about 4% of Claude's week*). Pure functions; nothing is drawn here.
import { costOf } from "./cost.js";
import { plural } from "../arena/arenawords.js";

/** *about 4% of Claude's week* for a price in dollars, "" with none. */
export function spendWords(low, high = low) {
  const lo = Number(low), hi = Number(high ?? low);
  if (!Number.isFinite(lo) || !Number.isFinite(hi) || (!lo && !hi)) return "";
  return costOf({ kind: "plan", node: { plan_estimate: { usd_low: Math.min(lo, hi), usd_high: Math.max(lo, hi) } } })?.words || "";
}

/** What a way down pulls (realm/way_down.py `pulls`): *2 sections, 3 tasks*, "" with nothing. */
export function pullsWords(p) {
  if (!p) return "";
  const parts = [];
  const sections = (p.sections || []).length, tasks = (p.tasks || []).length, checks = Number(p.checks) || 0;
  if (sections) parts.push(plural(sections, "section", "sections"));
  if (tasks) parts.push(plural(tasks, "task", "tasks"));
  if (checks) parts.push(plural(checks, "check", "checks"));
  return parts.join(", ");
}

/** The one line of a change (§237.7): *About 4% of Claude's week: 2 sections, 3 tasks*; the price alone with nothing pulled; the pulls alone with no price known; "" with neither. */
export function changeLine(p) {
  const cost = spendWords(p?.estimate?.usd_low, p?.estimate?.usd_high), pulls = pullsWords(p);
  const head = cost ? cost.charAt(0).toUpperCase() + cost.slice(1) : "";
  return head && pulls ? `${head}: ${pulls}` : head || (pulls ? pulls.charAt(0).toUpperCase() + pulls.slice(1) : "");
}
