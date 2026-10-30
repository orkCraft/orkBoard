// A question is a card (docs/specs/100-a-goals-way-as-cards.md §2.1, §2.4; decisions §153.5–§153.6, §167.2): the face of the hand's (stopcard.js) with the sign `question` and its leader's head over it, the question at its foot; a goal's
// questions (`talk`) or the project's (`project_q`) a stack, one a card. Lifted, the card deals its choices over the pane (choose.js, kind `choose`, source `question`): a press on a choice answers at once, the next of the stack comes on top,
// the answers go together after the last (`ideas.talk_answer`, `ideas.project_answer`: questions.js `sendRow`); *Let <leader> decide* answers the rest with the picks (`decide: true`); *Other…* answers with the person's words; the
// questions together open over the pane on request (table/talkpage.js, kind `talk`). A bug's case questions ride in the cause's stack (causecard.js) the same way. The lifted card itself is the pane's: it lowers as it opens it.
// Upright on a touch phone (docs/specs/103 §1.1) the card on top of the one stack already is the lifted card, and its choices lie on it (`QuestionHere`: the same cards, two by two), answered by the same `asking`.
import { useLayoutEffect } from "preact/hooks";
import { html } from "../html.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { ORKMASTER, openOver, over, tab } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { mapName, partiesAll } from "../table/data.js";
import { Choose, ChoiceCard, OtherCard, chooseFor } from "./choose.js";
import { stopsOfProject } from "./data.js";
import { give, givePicks, given, cardSig, cardsOf, sendRow } from "./questions.js";
import { named } from "./todoform.js";
import { way } from "./ways.js";

/** The line under the first card of a stack: what an answer becomes (once, spec 100 §0). */
const hintOf = (s) => (s.kind === "project_q" || s.card?.project ? "Pick an answer: the leader keeps it for the project" : "Pick an answer: the leader writes it into the spec");

/** What the answers to a question do, for the pane's choices and for the card upright: `top` the first card of its stack not answered, `mine` the stack's cards, `from` where the pane came from. */
function asking(top, mine, from) {
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
  const together = row.kind === "talk" ? { label: "All the questions", onTogether: () => openOver("talk", { idea: row.idea, together: true }, from, top.title) } : null;
  return { c, row, first, choices, answer, together, decide: { label: `Let ${named(lead)} decide`, onDecide: decide } };
}

/** The lifted card of a question: upright on a touch phone its choices lie on the card; else it opens them over the pane, in place of the aside (hand.css hides it for the frame it takes). */
export function QuestionLifted({ s }) {
  return uprightNow.value ? html`<${QuestionHere} s=${s} />` : html`<${QuestionOpens} s=${s} />`;
}

function QuestionOpens({ s }) {
  useLayoutEffect(() => {
    openOver("choose", { source: "question", scope: s.scope }, { title: mapName(tab.value, partiesAll()), key: "" }, s.title || s.full);
  }, [s.key]);
  return html`<span class="q-opening" aria-hidden="true"></span>`;
}

/** A question's choices on the card itself, upright on a touch phone: the cards `Choose` deals (two by two at this width), *Other…* and *Let <leader> decide*. The question is the card's title and its why is the context's, so no choice repeats it. */
function QuestionHere({ s }) {
  const stops = stopsOfProject(mapData.value, board.value?.needs_you || [], ORKMASTER), mine = stops.filter((x) => x.scope === s.scope && x.card), top = mine.find((x) => x.key === s.key) || mine[0];
  if (!top) return null;
  const a = asking(top, mine, { title: mapName(tab.value, partiesAll()), key: "" }), seed = (a.choices[a.c.pick] || a.choices[0] || {}).name || "";
  return html`<div class="q-choose q-here" data-kind="choose" role="group" aria-label="Choices">
    <div class="q-choose__row" key=${a.c.q}>
      ${a.choices.map((c, i) => html`<${ChoiceCard} key=${c.id} c=${{ ...c, why: "" }} i=${i} picked=${c.id === String(a.c.pick)} element=${top.node?.element || ""} by=${top.party?.name || ""} head=${top.head}
        onPress=${() => a.answer({ pick: Number(c.id) })} />`)}
      <${OtherCard} key="other" i=${a.choices.length} seed=${seed} onOther=${(text) => a.answer({ text })} />
    </div>
    <div class="q-choose__acts"><button type="button" class="ork-btn quiet" onClick=${a.decide.onDecide}>${a.decide.label}</button></div>
  </div>`;
}

/** What the pane's `choose` draws for a stack of questions (`props.scope`): the first of them not answered, its choices as cards. It goes back when none is left. */
function Questions({ props, close }) {
  const stops = stopsOfProject(mapData.value, board.value?.needs_you || [], tab.value), mine = stops.filter((s) => s.scope === props.scope && s.card), top = mine[0];
  useLayoutEffect(() => { if (!top) close(); }, [!top]);
  if (!top) return null;
  const a = asking(top, mine, over.value?.from || { title: mapName(tab.value, partiesAll()), key: "" });
  return html`<${Choose} question=${a.c.q} choices=${a.choices} pick=${String(a.c.pick)} by=${top.party?.name || ""} element=${top.node?.element || ""} head=${top.head}
    hint=${a.first && a.row.kind !== "cause" ? hintOf(top) : ""} onChoose=${(id) => a.answer({ pick: Number(id) })} onOther=${(text) => a.answer({ text })}
    decide=${a.decide} together=${a.together} onBack=${close} />`;
}
chooseFor("question", Questions);

// `talk`: a goal's questions, the stack's cards; `project_q`: the project's. Both wear the sign `question`.
way("talk", { sign: "question", Lifted: QuestionLifted });
way("project_q", { sign: "question", Lifted: QuestionLifted });
