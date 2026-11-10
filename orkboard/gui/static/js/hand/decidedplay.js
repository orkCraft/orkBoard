// A leader's decision, in play (docs/specs/168 H4, decisions §283.22): the card of decidedcard.js risen at the table's foot at its left, its goal picked and the leader's tab opened, its two ways the hand's row (sayplay.js `PlayWays`): **Accepted** (`go_on`,
// `ideas.decided_accept`) and **Replay** (`ask_more`, `ideas.decided_replay`). A refusal is the host's toast (*The goal has gone on…*) and the card stays; answered, the row's `decided` loses the decision and the hand lowers the card.
import { html } from "../html.js";
import { command } from "../link.js";
import { lower } from "../frame/state.js";
import { ACCEPTED, ACCEPTED_LINE, REPLAY, REPLAY_LINE } from "./decidedcard.js";
import { PlayWays } from "./sayplay.js";

const send = (name, idea, id) => command(name, { idea, id }).then(() => lower()).catch(() => {});      // refused: its toast says why, the card stays

/** The decision as a card in play on the desktop: `s` its stop. */
export function DecidedPlay({ s }) {
  const d = s.ref, idea = d.idea;
  const card = {
    title: s.title, foot: s.text || "", sign: "check", element: s.node?.element || "", hue: s.node?.hue || "", head: s.head, tab: d.party,
    ways: [
      { id: "accepted", name: ACCEPTED, line: ACCEPTED_LINE, pick: false, kind: "go_on", run: () => send("ideas.decided_accept", idea, d.id) },
      { id: "replay", name: REPLAY, line: REPLAY_LINE, pick: false, kind: "ask_more", run: () => send("ideas.decided_replay", idea, d.id) },
    ],
  };
  return html`<${PlayWays} card=${card} id=${s.key} idea=${idea} kind="decided" />`;
}
