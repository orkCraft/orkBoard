// The chronicle's words (docs/specs/134 §D, docs/specs/150 E2.2; realm/lexicon.py `TERMS`: chronicle, chronicle_week, how_works_now, changed_by, past, past_through, past_search, past_line, show_on_table). A chapter's name is the version's own, never a word of ours; a week is *The week of 3 Nov*.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "28 Oct" from a day "2026-10-28" (read as written: no time zone moves it); "" when it does not read. */
export function dayWord(day) {
  const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(day || "");
  return m && Number(m[2]) >= 1 && Number(m[2]) <= 12 ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]}` : "";
}

/** A chapter's name: the version's own, or *The week of 3 Nov*. */
export const chapterName = (c) => (c.kind === "week" ? `The week of ${dayWord(c.day)}` : c.name || dayWord(c.day));

export const UNRELEASED = "Unreleased";

/** The past's title, both axes (spec 150 E2.2): *The past · through Design · every version*, *· v0.3*; `through` is the open tab's name (*the Orkmaster* on the Orkmaster's). */
export const pastTitle = (through, deck = "") => `The past · through ${through} · ${deck || "every version"}`;

/** The search's words: *Search Design's past…*; on the Orkmaster's tab, the whole project's. */
export const pastSearch = (party = "") => (party ? `Search ${party}'s past…` : "Search the past…");

/** The lich's line in the table's edge: *Design's past ›*, *The project's past ›*. */
export const pastLine = (party = "") => (party ? `${party}'s past ›` : "The project's past ›");

/** A card lifted in the past, to the tab's table. */
export const showOn = (party) => `Show on ${party}'s table`;

/** *changed by §238* or *changed by §238, §240*. */
export const changedBy = (list) => `changed by ${list.map((c) => `§${c.number}`).join(", ")}`;
