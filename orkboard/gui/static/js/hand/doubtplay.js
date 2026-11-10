// A doubt left, in play (docs/specs/168 D5, decisions §283.25): the card of doubtcard.js risen at the table's foot at its left, its goal picked and the doubting leader's tab opened, its two ways the hand's row (sayplay.js `PlayWays`): **Judge again now**
// (`ask_more`, `ideas.judge_again`) and **To the hearing** (`go_on`, `ideas.to_hearing`). A refusal is the host's toast and the card stays; answered, the row's `doubts` empties and the hand lowers the card. Kept apart from doubtcard.js so the hand's data does not import the drawing.
import { html } from "../html.js";
import { command } from "../link.js";
import { lower } from "../frame/state.js";
import { JUDGE_AGAIN, TO_HEARING } from "./doubtcard.js";
import { PlayWays } from "./sayplay.js";

const send = (name, idea) => command(name, { idea }).then(() => lower()).catch(() => {});      // refused: its toast says why, the card stays

/** The doubt as a card in play on the desktop: `s` its stop. */
export function DoubtPlay({ s }) {
  const d = s.ref, idea = d.idea;
  const card = {
    title: s.title, foot: d.why || "", sign: "alert", element: s.node?.element || "", hue: s.node?.hue || "", head: s.head, tab: d.party,
    ways: [
      { id: "judge_again", name: JUDGE_AGAIN, line: "The leaders that still doubt hear the goal once more, with what you took.", pick: false, kind: "ask_more", run: () => send("ideas.judge_again", idea) },
      { id: "to_hearing", name: TO_HEARING, line: "No second judging: the goal goes to its hearing, where you decide.", pick: false, kind: "go_on", run: () => send("ideas.to_hearing", idea) },
    ],
  };
  return html`<${PlayWays} card=${card} id=${s.key} idea=${idea} kind="doubt" />`;
}
