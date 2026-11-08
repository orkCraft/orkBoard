// The chronicle's words (docs/specs/134 §D, docs/specs/156 D; realm/lexicon.py `TERMS`: chronicle, chronicle_week, how_works_now, changed_by, unreleased, party_discard). A chapter's name is the version's own, never a word of ours; a week is *The week of 3 Nov*.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "28 Oct" from a day "2026-10-28" (read as written: no time zone moves it); "" when it does not read. */
export function dayWord(day) {
  const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(day || "");
  return m && Number(m[2]) >= 1 && Number(m[2]) <= 12 ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]}` : "";
}

/** A chapter's name: the version's own, or *The week of 3 Nov*. */
export const chapterName = (c) => (c.kind === "week" ? `The week of ${dayWord(c.day)}` : c.name || dayWord(c.day));

export const UNRELEASED = "Unreleased";

/** The title of a decision's entry or a goal as it was, opened over the pane from the past (chronicle.js): *Decision §238*, *The goal as it was*; the tab's own name leads (*through Design*) on a party's tab. */
export const entryTitle = (through, props = {}) => `${props.deck ? props.deck.name : props.goal ? "The goal as it was" : `Decision §${props.decision || props.lit || ""}`}${through ? ` · through ${through}` : ""}`;

/** The discard's label (spec 156 D.3): *Discard* on the Orkmaster's tab and in a project with no Release party, *Design's discard* on a party's. */
export const discardLabel = (party = "") => (party ? `${party}'s discard` : "Discard");

/** *changed by §238* or *changed by §238, §240*. */
export const changedBy = (list) => `changed by ${list.map((c) => `§${c.number}`).join(", ")}`;

/** The cards of a deck: its goals (a goal that went through the portal) and its decisions of no goal. */
export const itemsOf = (c) => [
  ...(c?.goals || []).map((g) => ({ type: "goal", id: g.idea, title: g.title, element: g.element, hue: g.hue, day: g.day, decision: g.decision, in: g.in })),
  ...(c?.decisions || []).map((d) => ({ type: "decision", id: d.number, title: d.title, element: "", hue: "", day: d.day, decision: 0, in: d.in })),
];

/** A deck's cards by day, newest first, across goals and decisions (on one day goals before decisions: the sort is stable and `itemsOf` lists goals first). */
export const byDay = (c) => itemsOf(c).sort((a, b) => (a.day < b.day ? 1 : a.day > b.day ? -1 : 0));

