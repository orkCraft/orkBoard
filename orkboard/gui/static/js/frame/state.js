// What the window as two parts remembers while it is open (docs/specs/98-the-table-and-the-hand.md §0.2, decisions §110.1, §142, §145):
// the open tab and the picked goal (the two axes: through whom, and what is looked at), what is open over the pane (one thing,
// nothing pinned), and the one card lifted on the table or in the hand. The seam the table (js/table/) and the hand (js/hand/)
// share: written by the lead, changed by neither. Signals only; the open tab is kept per project on this device.
import { effect, signal, untracked } from "@preact/signals";

export const ORKMASTER = "orkmaster";
const TAB_KEPT = "orkboard.frame.tab";

let projectKey = () => "";
/** Says which project is shown (shell/projects.js `currentProject`): the tab is kept per project. A function, so this seam imports nothing. */
export const keepTabsBy = (fn) => { projectKey = fn; };
const keptTabs = () => { try { return JSON.parse(localStorage.getItem(TAB_KEPT)) || {}; } catch { return {}; } };

export const tab = signal(keptTabs()[projectKey()] || ORKMASTER);   // "orkmaster" or a party's slug (the code's goal)
export const picked = signal("");      // the picked goal's slug (the code's idea), "" for the whole project
export const over = signal(null);      // what is open over the pane: {kind, title, from, props}, null for the map
export const lifted = signal("");      // the key of the one lifted card (a map's card or a hand's card), "" for none
export const inventory = signal(null);   // the inventory (the merchant's stall, spec 157 D): the chair open, "" the Orkmaster's, a party's slug a leader's; null while it is shut
export const carried = signal("");       // the slot of the card of what you carry lifted in the stall (table/stallstate.js), "" for none

/** The chair of a tab, as the stall says it: "" for the Orkmaster's. */
export const chairOf = (slug) => (!slug || slug === ORKMASTER ? "" : slug);
export const openInventory = (slug = tab.peek()) => { carried.value = ""; inventory.value = chairOf(slug); };
export const closeInventory = () => { carried.value = ""; inventory.value = null; };

/** The person opens a tab (never the code under them: §139.3). Kept for the project on this device. */
export function openTab(slug) {
  tab.value = slug || ORKMASTER;
  if (inventory.peek() !== null) { carried.value = ""; inventory.value = chairOf(tab.value); }      // a tab pressed while the stall is open picks the chair
  try { localStorage.setItem(TAB_KEPT, JSON.stringify({ ...keptTabs(), [projectKey()]: tab.value })); } catch { /* this run only */ }
}

/** The keys of a part of the System and of a link between two containers, lifted on the table (table/card.js `Lifted`). */
export const partKey = (party, path) => `t:part:${party}:${path}`;
export const linkKey = (party, key) => `t:link:${party}:${key}`;

/** Play stays open when another tab is opened (docs/specs/115-the-live-product-under-each-leaders-eyes.md §6.1): `openTab` never closes it — the lens over the frame changes (arena/playlens.js reads `tab`), the iframe is the same element all through —,
 *  and the pane's title follows the tab: Play, open, takes the new tab's map as the place it came from (`title`, the map's name). Nothing else open over the pane is touched. */
export function followTab(title) {
  const o = over.peek();
  if (o?.kind === "play" && o.from?.title !== title) over.value = { ...o, from: { ...(o.from || {}), title, key: o.from?.key || "" } };
}

/** The tab kept for the project now shown (on a project switch). */
export function restoreTab() { tab.value = keptTabs()[projectKey()] || ORKMASTER; closeInventory(); }

/** One thing over the pane (§142): `kind` one of kinds.js `KINDS`, `props` what its face reads, `from` where it came from
 *  (`{title, key}`: the title's *← System* and the card lit on the way back). The next replaces it. */
export function openOver(kind, props = {}, from = null, title = "") {
  over.value = { kind, title, from, props };
  lifted.value = "";
}

/** ← or Esc: the map as it was left; the card it came from is lit (`from.key`). */
export function closeOver() {
  const was = over.value;
  over.value = null;
  return was?.from?.key || "";
}

/** A goal picked (its stack, a card of it, a goal in the deck's row or the discard); the same goal again, or "", picks none. */
export function pick(slug) { picked.value = slug && slug !== picked.value ? slug : ""; }

// -- the pick in the address (docs/specs/156-one-pick-and-the-release-column.md part B.1, decisions §261.2, §262.4) --------------------------------------
// **This file is the one writer and reader of `#goal=<slug>`, and the one handler of the pick's Esc.** The pick is whatever sets `picked` (a press, a hand's card, a result of the host); an effect writes it to the address:
// `pushState` from none to a goal (so the browser's and the phone's back put it away), `replaceState` from a goal to another, and from a goal to none the entry is taken off again (`history.back()`) when it is ours, else the hash is cleared in place.
// The address is read on load (a slug the snapshot does not have reads as none, once there is a snapshot to say so) and on `popstate`. The narrow page's back entry (table.js `useBackButton`) is pushed over the pick's, so a file opened over a pick closes on the first back, the pick on the second.
const HASH = /^#goal=(.+)$/;
let goals = { known: () => true, route: () => null };
/** Says which goals the snapshot has and which parties a goal's route passes (table/data.js): functions, so this seam imports nothing. */
export const keepGoalsBy = (g) => { goals = { ...goals, ...g }; };
const hashSlug = () => { try { const m = HASH.exec(decodeURIComponent(location.hash)); return m ? m[1] : ""; } catch { return ""; } };
let inAddress = hashSlug(), wanted = inAddress, expectPop = 0;           // `inAddress`: the goal the address says; `wanted`: read from it and not yet found in a snapshot

const clearHash = () => { try { history.replaceState(history.state, "", location.pathname + location.search); } catch { /* no history */ } };
function writeAddress(slug) {
  try {
    const url = `${location.pathname}${location.search}#goal=${encodeURIComponent(slug)}`;
    if (slug && !inAddress) history.pushState({ orkboardPick: 1 }, "", url);
    else if (slug) history.replaceState(history.state?.orkboardPick ? history.state : { orkboardPick: 1 }, "", url);
    else if (history.state?.orkboardPick) { expectPop += 1; history.back(); }
    else clearHash();
  } catch { /* no history: the pick lives in the page only */ }
  inAddress = slug;
}

/** A goal whose route leaves out the open tab's party gives way to the Orkmaster's tab (as the person's own press: §139.3 holds; decisions §261.3). */
function followPick(slug) {
  const route = slug ? goals.route(slug) : null, now = tab.peek();
  if (route && now !== ORKMASTER && !route.has(now)) openTab(ORKMASTER);
}

/** The snapshot has come (or changed): a goal the address asked for is picked once it is there; one it never has reads as none. Table calls it when the snapshot changes. */
export function settleAddress(haveSnapshot) {
  if (!wanted || !haveSnapshot) return;
  const slug = wanted;
  wanted = "";
  if (goals.known(slug)) { if (picked.peek() !== slug) picked.value = slug; }
  else if (inAddress === slug) { inAddress = ""; clearHash(); }
}

/** A project switched: nothing is picked and the address says so, without a step in the history. */
export function dropPick() { wanted = ""; picked.value = ""; if (inAddress) { inAddress = ""; clearHash(); } }

effect(() => {
  const slug = picked.value;
  untracked(() => {
    if (!slug && wanted) return;                                          // the address asks for a goal the snapshot has not come to yet
    if (slug !== inAddress) writeAddress(slug);
    followPick(slug);
  });
});

if (typeof addEventListener === "function") {
  addEventListener("keydown", (e) => {                                   // Esc closes the stall first: a card lifted is lowered, then the stall shuts (spec 157 D.1)
    if (e.key !== "Escape" || e.defaultPrevented || inventory.peek() === null || over.peek()) return;
    const el = e.target;
    if (el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable || el.closest?.(".table-drop, [role=dialog], [role=alertdialog], [role=menu]"))) return;
    e.preventDefault();
    if (carried.peek()) carried.value = ""; else closeInventory();
  });
  addEventListener("popstate", () => {
    if (expectPop > 0) { expectPop -= 1; return; }                       // the step back we took ourselves: `picked` is already none
    const slug = hashSlug();
    inAddress = slug;
    if (!slug) { wanted = ""; if (picked.peek()) picked.value = ""; return; }
    if (goals.known(slug)) { wanted = ""; if (picked.peek() !== slug) picked.value = slug; } else { wanted = slug; if (picked.peek()) picked.value = ""; }
  });
  // Esc, with nothing open over the pane and nothing lifted, puts the pick away. What something else took (a menu, a question, the column's choices) is theirs.
  addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || e.defaultPrevented || !picked.peek() || over.peek() || lifted.peek()) return;
    const el = e.target;
    if (el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable || el.closest?.(".table-drop, [role=dialog], [role=alertdialog], [role=menu]"))) return;
    e.preventDefault();
    picked.value = "";
  });
}

/** A card lifted where it lies (§120.1), one at a time on the table and in the hand. */
export function lift(key) { lifted.value = key || ""; }
export function lower() { lifted.value = ""; }
