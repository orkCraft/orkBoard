// The hand's stops of a card at its turns and of a battle (decisions §298.6, §298.7), read by hand/data.js; their cards in play are hand/turncards.js's. The table of cards only: nothing else
// imports the hand's faces here. The host answers neither of them for this page yet: the moves that wait are `ideas.turns` (the hand's cards of them are stage K's) and a battle is what a mat of
// its own goal lays (gui/ideas_mats.py holds no battle), so no stop is dealt here; what is not laid lies empty, never an example (decisions §301.1).
import { signal } from "@preact/signals";
import { way } from "./ways.js";

way("turn", { sign: "flag", tone: "alert" });
way("battle", { sign: "flag", tone: "alert" });

export const settled = signal([]);              // `slug:kind` of the turns answered on this page: their cards are gone from the hand

export const settle = (slug, kind) => { settled.value = [...settled.value, `${slug}:${kind}`]; };

/** What a battle says of what it goes against: a decision by its §, a goal by its title (*vs §240 and The table, its edge*). */
export const vsWords = (against) => `vs ${(against || []).map((a) => (a.kind === "decision" ? a.ref : a.title)).join(" and ")}`;

/** The hand's stops of the turns that wait: none until the host lays them (stage K reads `ideas.turns`). */
export function turnStops() {
  return [];
}
