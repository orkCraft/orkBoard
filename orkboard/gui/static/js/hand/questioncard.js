// A question is a card (docs/specs/100-a-goals-way-as-cards.md §2.1, §2.4; decisions §153.5–§153.6, §167.2): the face of the hand's (stopcard.js) with the sign `question` and its leader's head over it, the question at its foot; a goal's
// questions (`talk`) or the project's (`project_q`) a stack, one a card. Lifted, the card deals its choices over the pane (choose.js, kind `choose`, source `question`): a press on a choice answers at once, the next of the stack comes on top,
// the answers go together after the last (`ideas.talk_answer`, `ideas.project_answer`: questions.js `sendRow`); *Let <leader> decide* answers the rest with the picks (`decide: true`); *Other…* answers with the person's words; the
// questions together open over the pane on request (table/talkpage.js, kind `talk`). A bug's case questions ride in the cause's stack (causecard.js) the same way. The lifted card itself is the pane's: it lowers as it opens it.
import { useLayoutEffect } from "preact/hooks";
import { html } from "../html.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { openOver, over, tab } from "../frame/state.js";
import { mapName, partiesNow } from "../table/data.js";
import { Choose, chooseFor } from "./choose.js";
import { stopsOfProject } from "./data.js";
import { give, givePicks, given, cardSig, cardsOf, sendRow } from "./questions.js";
import { named } from "./todoform.js";
import { way } from "./ways.js";

/** The line under the first card of a stack: what an answer becomes (once, spec 100 §0). */
const hintOf = (s) => (s.kind === "project_q" || s.card?.project ? "Pick an answer: the leader keeps it for the project" : "Pick an answer: the leader writes it into the spec");

/** The lifted card of a question: opens its choices over the pane, in place of the aside (hand.css hides it for the frame it takes). */
export function QuestionLifted({ s }) {
  useLayoutEffect(() => {
    openOver("choose", { source: "question", scope: s.scope }, { title: mapName(tab.value, partiesNow()), key: "" }, s.title || s.full);
  }, [s.key]);
  return html`<span class="q-opening" aria-hidden="true"></span>`;
}

/** What the pane's `choose` draws for a stack of questions (`props.scope`): the first of them not answered, its choices as cards. It goes back when none is left. */
function Questions({ props, close }) {
  const stops = stopsOfProject(mapData.value, board.value?.needs_you || [], tab.value), mine = stops.filter((s) => s.scope === props.scope && s.card), top = mine[0];
  useLayoutEffect(() => { if (!top) close(); }, [!top]);
  if (!top) return null;
  const c = top.card, row = top.ref, lead = top.party?.lead, last = mine.length === 1, first = !cardsOf(row).some((x) => given.value[cardSig(top.scope, x)]);
  const answer = (said) => {
    give(top.scope, c, said);
    if (last && row.kind !== "cause") sendRow(row, lead);                       // the last of the stack: the answers go together (a bug's go with the cause's answer)
  };
  const decide = () => {
    if (row.kind === "cause") { givePicks(top.scope, cardsOf(row)); return; }    // a bug's guess is still the person's: the case questions take their picks, the guess comes on top
    sendRow(row, lead, true);
  };
  const choices = c.choices.map((name, i) => ({ id: String(i), name, why: i === c.pick ? c.why : "" }));
  const from = over.value?.from || { title: mapName(tab.value, partiesNow()), key: "" };
  const together = row.kind === "talk" ? { label: "All the questions", onTogether: () => openOver("talk", { idea: row.idea, together: true }, from, top.title) } : null;
  return html`<${Choose} question=${c.q} choices=${choices} pick=${String(c.pick)} by=${top.party?.name || ""} element=${top.node?.element || ""} head=${top.head}
    hint=${first && row.kind !== "cause" ? hintOf(top) : ""} onChoose=${(id) => answer({ pick: Number(id) })} onOther=${(text) => answer({ text })}
    decide=${{ label: `Let ${named(lead)} decide`, onDecide: decide }} together=${together} onBack=${close} />`;
}
chooseFor("question", Questions);

// `talk`: a goal's questions, the stack's cards; `project_q`: the project's. Both wear the sign `question`.
way("talk", { sign: "question", Lifted: QuestionLifted });
way("project_q", { sign: "question", Lifted: QuestionLifted });
