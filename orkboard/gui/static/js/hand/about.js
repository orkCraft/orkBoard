// The cards of the table a lifted card of the hand is about rise a little (docs/specs/98-the-table-and-the-hand.md §4.4, §6.1; today's `aboutOf` in arena/stops.js).
// The seam with the table: a card of the table that a stop can be about carries `data-about="idea:<goal> task:<goal>/<task>"` (space-separated tokens: its goal's slug,
// and for a task its `<goal>/<task>`). While a card of the hand is lifted, every element of `.frame-table` whose tokens name what the card is about wears `.is-about`
// (hand.css lifts it by orkUI's rise token; under reduced motion it is marked by its edge instead, nothing moves). `aboutNow` carries the same, for a table that would
// rather read a signal: `{task: "<goal>/<task>"}`, `{idea: "<goal>"}` or null. Nothing here draws a card of the table.
import { signal } from "@preact/signals";
import { useEffect } from "preact/hooks";
import { aboutOf } from "../arena/arenawords.js";

export const aboutNow = signal(null);

/** The tokens an `aboutOf` names: a task is its own token and its goal's; a goal is its slug. */
export function tokensOf(about) {
  if (!about) return [];
  if (about.task) return [`task:${about.task}`];
  return about.idea ? [`idea:${about.idea}`] : [];
}

/** Marks, while `s` (a stop, or null) is lifted, the cards of the table it is about. */
export function useAbout(s) {
  useEffect(() => {
    const about = s ? aboutOf({ ...s, other: false }) : null;        // the table shows every party's cards on the Orkmaster's tab: a stop of another party is about them too
    aboutNow.value = about;
    const tokens = tokensOf(about);
    if (!tokens.length) return undefined;
    const table = document.querySelector(".frame-table");
    if (!table) return undefined;
    const marked = new Set();
    const mark = () => {
      for (const el of table.querySelectorAll("[data-about]")) {
        const has = el.dataset.about.split(/\s+/);
        const on = tokens.some((t) => has.includes(t));
        if (on && !marked.has(el)) { el.classList.add("is-about"); marked.add(el); }
        else if (!on && marked.has(el)) { el.classList.remove("is-about"); marked.delete(el); }
      }
    };
    mark();
    const watch = typeof MutationObserver === "function" ? new MutationObserver(mark) : null;
    watch?.observe(table, { childList: true, subtree: true, attributes: true, attributeFilter: ["data-about"] });
    return () => { watch?.disconnect(); for (const el of marked) el.classList.remove("is-about"); aboutNow.value = null; };
  }, [s?.key]);
}
