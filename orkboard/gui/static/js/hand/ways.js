// The goal's way as cards (docs/specs/100-a-goals-way-as-cards.md): a part registers, from its own module, what a row kind of spec 99 draws in the
// hand — its window's sign and its lifted card — so the parts are built side by side and the hand's card stays one (stopcard.js). Written by the lead.
const WAYS = {};

/** `kind` (a Needs you row's: `route`, `start`, `talk`, `cause`, `decision`, `fork`, `project_q`) draws `{sign, Lifted}`: the sign of its window
 *  (orkUI's sign name) and, lifted, `({s, close}) => html` in place of the plain answers. */
export function way(kind, face) { WAYS[kind] = { ...(WAYS[kind] || {}), ...face }; }

/** What a part registered for `kind`, or null. */
export const wayOf = (kind) => WAYS[kind] || null;
