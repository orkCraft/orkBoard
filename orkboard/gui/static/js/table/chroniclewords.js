// The chronicle's words (docs/specs/134 §D; realm/lexicon.py `TERMS`: chronicle, chronicle_earlier, chronicle_week, how_works_now, changed_by). A chapter's name is the version's own, never a word of ours; a week is *The week of 3 Nov*.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "28 Oct" from a day "2026-10-28" (read as written: no time zone moves it); "" when it does not read. */
export function dayWord(day) {
  const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(day || "");
  return m && Number(m[2]) >= 1 && Number(m[2]) <= 12 ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]}` : "";
}

/** A chapter's name: the version's own, or *The week of 3 Nov*. */
export const chapterName = (c) => (c.kind === "week" ? `The week of ${dayWord(c.day)}` : c.name || dayWord(c.day));

/** The lens's line: *Earlier: v0.3 · 28 Oct* (a week: *Earlier: The week of 3 Nov*). */
export const earlierWords = (e) => (e.kind === "week" ? `Earlier: ${chapterName(e)}` : `Earlier: ${e.name}${dayWord(e.day) ? ` · ${dayWord(e.day)}` : ""}`);

/** *changed by §238* or *changed by §238, §240*. */
export const changedBy = (list) => `changed by ${list.map((c) => `§${c.number}`).join(", ")}`;
