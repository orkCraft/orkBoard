// The moment of a hearing's row (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.7): no imports, so the places that only name it need not load the hearing. A throw is sent at once now (the host takes it back, `ideas.unthrow`), so no row is held back here any more.

/** The moment of a Needs you row: a hearing row's own (`talk`), a fork row's `fork`. */
export const momentOf = (row) => (row?.kind === "fork" ? "fork" : row?.moment || "talk");
