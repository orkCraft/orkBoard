// A mat opened has its address (goal 171 stage I; decisions §299.3, §300): its seat and its goal in the page's URL, `#mat=<seat>:<goal>` (a spread of a goal: track, gate, deal,
// battle), `#mat=<seat>` (cost, duel, sort), `#mat=table:<party>:<framework>[:<part>]` (a leader's table). Opening a mat pushes a step of the history, so a phone's Back (or the
// browser's) puts it away; closing it by Esc or *Close* takes the step off again; a reload, a link from the feed or the journal opens the mat again once the Board is there.
// The pick's own `#goal=` (frame/state.js) is another address and is left alone. Only the table of cards reads or writes it.
import { effect, untracked } from "@preact/signals";
import { mapData } from "../shell/store.js";
import { giveBack } from "./back.js";
import { closeSpread, openSpread, spread } from "./spreads/open.js";
import { FRAMEWORKS, laid, laidAt, laidFrom, tables } from "./tables/state.js";

const OF_GOAL = new Set(["track", "gate", "deal", "battle"]), ALONE = new Set(["cost", "duel", "sort"]);
const PREFIX = "#mat=";

const enc = (parts) => PREFIX + parts.map(encodeURIComponent).join(":");
/** The address a hash holds: its parts, or null when it is none of a mat's. */
export function parse(hash = location.hash) {
  if (!hash.startsWith(PREFIX)) return null;
  try {
    const parts = hash.slice(PREFIX.length).split(":").map(decodeURIComponent);
    if (OF_GOAL.has(parts[0]) && parts[1]) return parts.slice(0, 2);
    if (ALONE.has(parts[0])) return parts.slice(0, 1);
    if (parts[0] === "table" && parts[1] && FRAMEWORKS[parts[2]]) return parts.slice(0, 4);
  } catch { /* a hash that does not decode is no address */ }
  return null;
}

/** The address of the mat open now, or null (a mat with none, as a change's words, has none). */
function wanted() {
  const s = spread.value;
  if (s) return OF_GOAL.has(s.kind) && s.slug ? [s.kind, s.slug] : ALONE.has(s.kind) ? [s.kind] : null;
  const party = laid.value;
  if (!party) return null;
  const fw = laidAt.value?.framework || Object.keys(tables.value?.[party] || {}).find((k) => FRAMEWORKS[k]);
  return fw ? ["table", party, fw, ...(laidAt.value?.card ? [laidAt.value.card] : [])] : null;
}

let pending = null;           // the address read on load, until the Board has what it needs to open it

/** Opens the mat an address names; false while the Board has not come to it, null when it never will (an unknown goal or party). */
function lay(a) {
  if (OF_GOAL.has(a[0])) {
    if (!mapData.value) return false;
    if (!(mapData.value.nodes || []).some((n) => n.slug === a[1])) return null;
    openSpread({ kind: a[0], slug: a[1] });
    return true;
  }
  if (ALONE.has(a[0])) { if (!mapData.value) return false; openSpread({ kind: a[0] }); return true; }
  if (!tables.value) return false;
  if (!tables.value[a[1]]?.[a[2]]) return null;
  laidAt.value = a[3] ? { party: a[1], framework: a[2], card: a[3] } : null;
  laidFrom.value = null;
  laid.value = a[1];
  return true;
}

const base = () => location.pathname + location.search;
function write(want) {
  const have = parse();
  if (want ? have && enc(want) === enc(have) : !have) return;
  try {
    if (want && have) history.replaceState(history.state, "", base() + enc(want));
    else if (want) history.pushState({ orkboardMat: 1 }, "", base() + enc(want));
    else if (history.state?.orkboardMat) history.back();
    else history.replaceState(history.state, "", base());
  } catch { /* no history: the mat lives in the page only */ }
}

function settle() {
  const a = pending, did = lay(a);
  if (did === false) return;
  pending = null;
  try {
    history.replaceState(history.state, "", base());
    if (did) history.pushState({ orkboardMat: 1 }, "", base() + enc(a));          // a reload leaves a step under the mat, so Back puts it away
  } catch { /* no history */ }
}

if (typeof addEventListener === "function") {
  pending = parse();
  effect(() => {
    const want = wanted();
    void mapData.value; void tables.value;                                 // read, so the load's address is tried again when the Board has come
    untracked(() => { if (pending) settle(); else write(want); });
  });
  addEventListener("popstate", () => {
    const a = parse(), now = wanted();
    if (a) { if (!now || enc(now) !== enc(a)) { pending = null; lay(a); } return; }
    if (spread.peek()) closeSpread();
    if (laid.peek()) { const from = laidFrom.peek(); laidAt.value = null; laid.value = ""; laidFrom.value = null; giveBack(from); }
  });
}
