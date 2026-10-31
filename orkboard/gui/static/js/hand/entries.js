// What the phone's hand goes through, one goal at a time (docs/decisions.md §180.3, docs/specs/103 As built A and "Changed since"): every stop in Needs you's order grouped by its goal — a card of no goal (*Go on paid?*, a sign-in, a
// project's question) is an entry of its own —, then each goal ready for main (hand/readycard.js), the ones put back with *Later* left out. The screen shows the entry `at` names: its first card on top, the rest of its cards
// under it as edges. The arrows and a swipe move along the entries; answering the last card of an entry leaves it, and the place it held is the next one's.
// Since spec 117 B (decisions §195.4) the arrows and the swipe are gone: the hand's row (uprow.js) is one card an entry and a press picks it (`pickEntry`); the entry's other cards show no edge, no count. The menu of the leaders (upmenu.js, spec 117 C)
// picks a goal (`pickGoal`: its entry on the screen when it has one) or a party (`pickParty`).
import { signal } from "@preact/signals";
import { mapData } from "../shell/store.js";
import { ORKMASTER, openTab, picked, tab } from "../frame/state.js";
import { contextOf } from "./context.js";
import { goalOfStop } from "./data.js";
import { lichOf } from "../table/discard.js";

export const at = signal("");                      // the key of the entry on the screen
export const later = signal([]);                   // goals ready for main put back with *Later* (this session's view only; the goal stays ready in the discard)
let was = 0;                                       // the place the entry on the screen held, for when it goes

const goalKey = (s) => { const g = goalOfStop(s); return g && !g.startsWith("party:") ? `goal:${g}` : `card:${s.key}`; };

/** The entries: `{key, kind: "stops" | "ready", stops, ready?, head, element, name}`; `head`, `element` and `name` are what an arrow to it draws and says. */
export function entriesOf(stops, readyGoals = [], hidden = later.value) {
  const out = [], by = new Map();
  for (const s of stops) {
    const key = goalKey(s);
    if (!by.has(key)) {
      const c = contextOf(s);
      by.set(key, out.length);
      out.push({ key, kind: "stops", stops: [], head: c.head, element: s.node?.element || "", name: c.goal?.name || c.project || s.title || s.full || "" });
    }
    out[by.get(key)].stops.push(s);
  }
  const nodes = Object.fromEntries((mapData.value?.nodes || []).map((n) => [n.slug, n]));
  for (const g of readyGoals) {
    if (hidden.includes(g.slug)) continue;
    const n = nodes[g.slug] || { slug: g.slug, title: g.title };
    out.push({ key: `ready:${g.slug}`, kind: "ready", stops: [], ready: g, node: n, head: lichOf(), element: n.element || "", name: n.short || n.title || g.title });
  }
  return out;
}

/** The place of the entry on the screen: the one `at` names, else the place the last one held (so the next entry comes when one goes), else 0. Remembers it. */
export function placeOf(entries) {
  let i = entries.findIndex((e) => e.key === at.value);
  if (i < 0) i = Math.max(0, Math.min(was, entries.length - 1));
  was = i;
  return i;
}

/** The goal an entry is about ("" for a card of no goal). */
export const goalOfEntry = (e) => (e.kind === "ready" ? e.ready.slug : goalOfStop(e.stops[0]) || "");

/** A press on an entry of the hand's row: it is the one on the screen, and its goal the picked one (a party picked in the menu is let go). */
export function pickEntry(e) {
  at.value = e.key;
  picked.value = goalOfEntry(e);
  if (tab.value !== ORKMASTER) openTab(ORKMASTER);
}

/** A goal picked in the menu (upmenu.js): it is the picked one, and its entry in the hand, when it has one, the one on the screen. */
export function pickGoal(entries, slug) {
  const e = entries.find((x) => goalOfEntry(x) === slug);
  if (e) at.value = e.key;
  picked.value = slug;
  if (tab.value !== ORKMASTER) openTab(ORKMASTER);
}

/** A party picked in the menu: its leader's header is what is looked at (`tab` its slug), no goal picked. */
export function pickParty(slug) {
  picked.value = "";
  openTab(slug);
}
