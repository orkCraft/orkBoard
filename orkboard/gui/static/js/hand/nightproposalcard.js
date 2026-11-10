// The morning's proposal in the hand (docs/specs/168 H3, decisions §283.32): on the night's top rung a leader picked made one proposal; it lies in the column's *Specs* marked *proposed* (table/stages.js `kindOf`) and is a card of its leader's stack, *Proposed: …*,
// with the night it was made in and its spec's first lines at its foot. Its ways are two: **Take** (`ideas.night_answer {id, take: true}`, the way's kind `take`: the goal goes on as any goal does) and **Drop** (`take: false`, `drop`: the proposal and its goal are gone). The host's row is
// the Needs you row `kind: "night_proposal"` (`gui/ideas_night.py` `night_rows`); wide only, as the concern card.
import { ORKMASTER } from "../frame/state.js";

export const PROPOSED = "Proposed", TAKE = "Take", DROP = "Drop";

/** *the night of Tue, 10 Nov*: the night a proposal was made in, from its key (`2026-11-09`, the day the night began); "" for none. */
export function nightWords(key) {
  const d = /^\d{4}-\d{2}-\d{2}$/.test(String(key || "")) ? new Date(`${key}T12:00:00`) : null;
  return d && !Number.isNaN(d.getTime()) ? `the night of ${d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" })}` : "";
}

/** The hand's stops of the proposals that wait (the Needs you rows of `night_proposal`), one after another, after the other stops, each under its leader's lane. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `goal(slug)`, `open`, `window`: the night's window). */
export function nightProposalStops(needs, ctx) {
  const out = [];
  for (const r of needs || []) {
    if (r.kind !== "night_proposal") continue;
    const party = ctx.party(r.by), g = ctx.goal(r.by);
    if (!party || !g) continue;
    const when = nightWords(r.night), line = [when && `Made in ${when}`, when && ctx.window && `(${ctx.window})`].filter(Boolean).join(" ");
    out.push({ key: `night/${r.id}`, kind: "night_proposal", ref: { ...r, when: line }, row: { ...r, goal: r.by, idea: undefined, blocks: false }, node: null, task: null, label: PROPOSED, gem: "", tone: "alert", gemTip: "", head: party.head, small: true, whoTip: "",
      title: r.title, full: r.title, text: r.text, why: r.text, g, party, other: ctx.open !== ORKMASTER && ctx.open !== r.by });
  }
  return out;
}
