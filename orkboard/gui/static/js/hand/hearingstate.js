// What a hearing holds back while its throw can still be taken back (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.7, decisions §198.6): a drop is sent only when its toast goes (6 s), and until then the hearing's row is
// not in the hand (data.js `stopsOfProject` leaves out what `isHeld` says), so the card is gone from the hand at once and comes back with *Undo*. No imports but the signals: data.js reads it, hearing.js writes it.
import { signal } from "@preact/signals";

export const holding = signal([]);                       // [{key, idea, moment}] the throws held for Undo

/** The moment of a Needs you row: a hearing row's own (`talk`), a fork row's `fork`. */
export const momentOf = (row) => (row?.kind === "fork" ? "fork" : row?.moment || "talk");

/** Whether the row's hearing was thrown and is held (a drop for its six seconds). */
export const isHeld = (row) => holding.value.some((h) => h.idea === row?.idea && h.moment === momentOf(row)) && (row?.kind === "hearing" || row?.kind === "fork");
