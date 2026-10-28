// A goal's element and the words of a flag's day (docs/specs/50-parties-and-goals.md §3.3, spec 55): pure functions over `ideas.map`'s nodes (a goal is the code's idea). No signal and no template here.

/** A goal's element and whether it is drawn dim (a raw goal, not yet read: until its draft). */
export const elementOf = (n) => ({ name: n?.element || "", dim: n?.state === "raw" || n?.state === "reading" });

/** The class of a type's sign, its goal's colour (docs/specs/55-type-top-right.md §1.2): the element's, `dim` (faint) while the element is drawn dim, `none` (muted) for a goal with no element. */
export const typeTone = (n) => { const el = elementOf(n); return el.name ? (el.dim ? "dim" : el.name) : "none"; };

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
/** "14 Oct" from a flag's time; "" when it does not read. */
export function flagDay(at) {
  const d = new Date(at);
  return Number.isNaN(d.getTime()) ? "" : `${d.getDate()} ${MONTHS[d.getMonth()]}`;
}
