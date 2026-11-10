// What a party's past was last looked at (docs/specs/150 E2.3, decisions §254.7): the newest decision number seen, per party (*orkboard.past.seen.<party>*, `orkboard.past.seen.orkmaster` for the whole project's), a per-viewer convenience in this browser's
// localStorage (it works without it: kept in memory for the page). Never looked at, nothing is new: the tab's dot (pastdot.js) takes the newest as seen the first time it reads. Written when the history is opened (history.js); read by the tab's dot (pastdot.js),
// which marks a decision newer than it (spec 156 D.5).
import { signal } from "@preact/signals";
import { ask } from "./chronicleparts.js";

const KEY = "orkboard.past.seen.";
const keyOf = (party) => `${KEY}${party || "orkmaster"}`;
const mem = {};                                                      // what the page saw, when the browser keeps nothing
export const seenTick = signal(0);                                   // bumped when a look is written: the tabs' dots read the mark again

/** The newest decision number seen of a party's past; null when it was never looked at. */
export function seenOf(party) {
  let got = null;
  try { const v = localStorage.getItem(keyOf(party)); got = v === null ? null : Number(v) || 0; } catch { /* the page's own */ }
  return got ?? mem[keyOf(party)] ?? null;
}

/** Writes the look: the newest decision number `n` is seen from now (never lowers it). */
export function setSeen(party, n) {
  if (!(n > (seenOf(party) ?? -1))) return;
  mem[keyOf(party)] = n;
  try { localStorage.setItem(keyOf(party), String(n)); } catch { /* seen on this page only */ }
  seenTick.value += 1;
}

/** The past was looked at: the newest decision of the party's last three is seen from now. The host is asked (by code, no call to a model). */
export async function markSeen(party) {
  const [r] = await ask("ideas.chronicle_last", { ...(party ? { party } : {}), n: 3 });
  const top = Math.max(0, ...((r?.decisions || []).map((d) => Number(d.number) || 0)));
  if (top) setSeen(party, top);
}
