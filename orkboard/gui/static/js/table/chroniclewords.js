// The chronicle's words (docs/specs/134 §D, docs/specs/156 D; realm/lexicon.py `TERMS`: chronicle, chronicle_week, how_works_now, changed_by, unreleased, party_discard). A chapter's name is the version's own, never a word of ours; a week is *The week of 3 Nov*.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "28 Oct" from a day "2026-10-28" (read as written: no time zone moves it); "" when it does not read. */
export function dayWord(day) {
  const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(day || "");
  return m && Number(m[2]) >= 1 && Number(m[2]) <= 12 ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]}` : "";
}


/** The title of a decision's entry or a goal as it was, opened over the pane from the past (chronicle.js): *Decision §238*, *The goal as it was*; the tab's own name leads (*through Design*) on a party's tab. */
export const entryTitle = (through, props = {}) => `${props.goal ? "The goal as it was" : `Decision §${props.decision || props.lit || ""}`}${through ? ` · through ${through}` : ""}`;

/** The discard's label (spec 156 D.3): *Discard* on the Orkmaster's tab and in a project with no Release party, *Design's discard* on a party's. */
export const discardLabel = (party = "") => (party ? `${party}'s discard` : "Discard");

/** *changed by §238* or *changed by §238, §240*. */
export const changedBy = (list) => `changed by ${list.map((c) => `§${c.number}`).join(", ")}`;
