// What the window as two parts remembers while it is open (docs/specs/98-the-table-and-the-hand.md §0.2, decisions §110.1, §142, §145):
// the open tab and the picked goal (the two axes: through whom, and what is looked at), what is open over the pane (one thing,
// nothing pinned), and the one card lifted on the table or in the hand. The seam the table (js/table/) and the hand (js/hand/)
// share: written by the lead, changed by neither. Signals only; the open tab is kept per project on this device.
import { signal } from "@preact/signals";
import { currentProject } from "../shell/projects.js";

export const ORKMASTER = "orkmaster";
const TAB_KEPT = "orkboard.frame.tab";

const projectKey = () => currentProject.value?.path || "";
const keptTabs = () => { try { return JSON.parse(localStorage.getItem(TAB_KEPT)) || {}; } catch { return {}; } };

export const tab = signal(keptTabs()[projectKey()] || ORKMASTER);   // "orkmaster" or a party's slug (the code's goal)
export const picked = signal("");      // the picked goal's slug (the code's idea), "" for the whole project
export const over = signal(null);      // what is open over the pane: {kind, title, from, props}, null for the map
export const lifted = signal("");      // the key of the one lifted card (a map's card or a hand's card), "" for none

/** The person opens a tab (never the code under them: §139.3). Kept for the project on this device. */
export function openTab(slug) {
  tab.value = slug || ORKMASTER;
  try { localStorage.setItem(TAB_KEPT, JSON.stringify({ ...keptTabs(), [projectKey()]: tab.value })); } catch { /* this run only */ }
}

/** The tab kept for the project now shown (on a project switch). */
export function restoreTab() { tab.value = keptTabs()[projectKey()] || ORKMASTER; }

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

/** A card lifted where it lies (§120.1), one at a time on the table and in the hand. */
export function lift(key) { lifted.value = key || ""; }
export function lower() { lifted.value = ""; }
