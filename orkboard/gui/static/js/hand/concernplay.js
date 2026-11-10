// A concern in play (docs/specs/168 D4, decisions §283.21): the card of concerncard.js risen at the table's foot at its left, the leader's tab opened, its three ways the hand's row (sayplay.js `PlayWays`), each with its `way_kind`.
// Kept apart from concerncard.js so the hand's data (data.js) does not import the cards' drawing.
import { html } from "../html.js";
import { lower } from "../frame/state.js";
import { answerConcern } from "../table/concerns.js";
import { CONCERN_ACTS } from "./concerncard.js";
import { PlayWays } from "./sayplay.js";

/** The concern as a card in play on the desktop: `s` its stop. */
export function ConcernPlay({ s }) {
  const c = s.ref, party = s.party?.slug || s.row?.goal || "";
  const card = {
    title: c.what, foot: c.why || c.name || "", sign: "alert", element: "", hue: "", head: s.head, tab: party,
    ways: CONCERN_ACTS.map((w) => ({ id: w.kind, name: w.name, line: w.line, pick: false, kind: w.kind, run: () => answerConcern(w.kind, party, c.id, lower) })),
  };
  return html`<${PlayWays} card=${card} id=${s.key} idea="" kind="concern" />`;
}
