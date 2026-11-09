// What the column's cards wait for, and which one moves (docs/specs/138-the-day-read-from-the-resets.md part A.2 and docs/specs/140-the-window-made-lighter.md C3, decisions §245.2, §247.8). Pure over a node but for the signals it reads.
// **`waitTool(n, dflt)`**: the id of the AI tool a goal waits for, "" when it waits for none: `held_until` in the future, a `waits` of kind *limits* or *reserve*, a To review spec whose wait runs (it starts on a tool), a goal at work held by its tool's spent window.
// The tool is the one the node names (`held_tool`, `waits.tool`, `back.ripe.tool`, `tool`); where the snapshot does not say, the default tool's (`defaultTool`: `town.mana.now`, else the Main tool, else the first). A potion hovered (`litTool`) leaves
// the cards waiting for it as they are and dims every other (piles.js `.is-dim`, never hidden).
// **`movesOn(slug)`**: one place moves at a time (spec 140 C3, decisions §247.8): a motion that runs on (the face-down card's ring, a rune's glow) runs only on the goal picked, else on the first goal at work in the Orkmaster's order (the column's
// order, `pilesOf` in piles.js: the one its leaders are on in In analysis, then At work); every other card shows its state still. Motions played once are not this one's (§89.0).
import { computed } from "@preact/signals";
import { town } from "../link.js";
import { picked } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { ACTIVE, kindOf, pilesOf } from "./piles.js";

const LIMITS = ["limits", "reserve"];                                    // `waits.kind` that is a spent window's

/** The tool the page's default is: the one the work goes to now, else the Main tool, else the first read. */
export function defaultTool(snapshot = town.value) {
  return snapshot?.mana?.now || snapshot?.mana?.main || snapshot?.limits?.[0]?.provider || "";
}

/** The id of the tool a goal waits for, "" when none (see above). `dflt`: the default tool, for a node that does not say. */
export function waitTool(n, dflt = defaultTool(), now = Date.now()) {
  const k = kindOf(n);
  if (!k) return "";
  const ripe = n.back?.ripe, held = Date.parse(n.held_until || "") > now, limits = LIMITS.includes(n.waits?.kind), review = k.pile === "review" && !!ripe && !ripe.by && !ripe.held;
  if (!held && !limits && !review) return "";
  return n.held_tool || n.waits?.tool || ripe?.tool || n.tool || dflt || "";
}

/** The goal that moves when none is picked: the first at work in the column's order (`pilesOf`): in In analysis the one the Orkmaster or its leaders are on (`ACTIVE`: reading, writing, in Talk), then the ones at work (not put off). */
export function firstAtWork(nodes) {
  const piles = pilesOf(nodes);
  return ([...piles.analysis, ...piles.review].find((x) => ACTIVE.includes(x.n.state)) || piles.work.find((x) => !x.off))?.n.slug || "";
}

const mover = computed(() => picked.value || firstAtWork(mapData.value?.nodes));

/** Whether a goal's running motion plays: it is the goal picked, else the first at work. Read in a component, it follows the pick and the map. */
export const movesOn = (slug) => !!slug && mover.value === slug;
