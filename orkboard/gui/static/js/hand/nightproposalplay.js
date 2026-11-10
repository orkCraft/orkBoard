// A night's proposal in play (docs/specs/168 H3): the card of nightproposalcard.js risen at the table's foot at its left, its leader's tab opened and its goal (on Hold, in *Specs*) picked, its two ways the hand's row (sayplay.js `PlayWays`): **Take** (`take`) and **Drop** (`drop`),
// each sending `ideas.night_answer {id, take}`. A refusal is the host's toast and the card stays; answered, the row is gone and the hand lowers the card.
import { html } from "../html.js";
import { command } from "../link.js";
import { lower } from "../frame/state.js";
import { PlayWays } from "./sayplay.js";
import { DROP, TAKE } from "./nightproposalcard.js";

const send = (id, take) => command("ideas.night_answer", { id, take }).then(() => lower()).catch(() => {});      // refused: its toast says why, the card stays

/** The proposal as a card in play on the desktop: `s` its stop. */
export function NightProposalPlay({ s }) {
  const r = s.ref;
  const card = {
    title: r.title, foot: [r.when, r.text].filter(Boolean).join(" · "), sign: "alert", element: "", hue: "", head: s.head, tab: r.by,
    ways: [
      { id: "take", name: TAKE, line: "The goal goes on as any goal does: Talk, then the spec, then the work, each as you allow.", pick: false, kind: "take", run: () => send(r.id, true) },
      { id: "drop", name: DROP, line: "The proposal and its goal are gone; the leader is not asked for another tonight.", pick: false, kind: "drop", run: () => send(r.id, false) },
    ],
  };
  return html`<${PlayWays} card=${card} id=${s.key} idea=${r.goal || ""} kind="night_proposal" />`;
}
