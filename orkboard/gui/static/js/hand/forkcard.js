// A fork (docs/specs/100-a-goals-way-as-cards.md §3.2; docs/specs/99-a-goals-way.md §7.3; decisions §117.3): what two leaders' sections disagree on, in the person's hand. The row is `{kind: "fork", idea, id, about,
// sides: [{party, leader, says, why}]}`, the goal's first fork open. Its face is the hand's card (stopcard.js): the question sign, the first side's leader's head as its asker, *<A> and <B> disagree* at its foot, under the first lane
// (data.js `laneOf`). Lifted, it deals the sides over the pane (choose.js, kind `choose`, source `fork`): one card a side — its leader's head in its window, what it says as its name, its why at its foot, its party in the
// label row — a press on one answering at once (`ideas.fork_answer {idea, side}`: the side's way stands, the other sides' leaders write their sections again), *Other…* the blank card for the person's own words
// (`text`: every side's section is written again). Under the cards the pane shows the goal's Spec (table/specpage.js) with the sections of the sides lit. The next fork of the goal, if one is left, takes the pane's place.
import { useLayoutEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { board } from "../board/store.js";
import { openOver, tab } from "../frame/state.js";
import { act, mapData } from "../shell/store.js";
import { mapName, nameOf, partiesNow } from "../table/data.js";
import { SpecPage } from "../table/specpage.js";
import { Choose, chooseFor } from "./choose.js";
import { way } from "./ways.js";

const partyBy = (slug) => partiesNow().find((g) => g.slug === slug) || null;
const sideName = (side) => nameOf(partyBy(side.party)) || side.party;

/** *Design and Tech disagree*, *Design, Tech and Art disagree*. */
export function disagreeWords(sides) {
  const names = (sides || []).map(sideName);
  return names.length < 2 ? "" : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]} disagree`;
}

/** The lifted card of a fork: opens the sides over the pane, in place of the aside (hand/questions.css hides it for the frame it takes). */
export function ForkLifted({ s }) {
  useLayoutEffect(() => {
    openOver("choose", { source: "fork", idea: s.row.idea }, { title: mapName(tab.value, partiesNow()), key: "" }, s.title || s.full);
  }, [s.key]);
  return html`<span class="q-opening" aria-hidden="true"></span>`;
}

/** What the pane's `choose` draws for a fork (`props.idea`): its sides as cards, the goal's Spec under them. It goes back when no fork is left. */
function Forks({ props, close }) {
  const row = (board.value?.needs_you || []).find((r) => r.kind === "fork" && r.idea === props.idea) || null, [busy, setBusy] = useState(false);
  useLayoutEffect(() => { if (!row) close(); }, [!row]);
  if (!row) return null;
  const element = (mapData.value?.nodes || []).find((n) => n.slug === props.idea)?.element || "";
  const answer = async (args) => {
    if (busy) return;
    setBusy(true);
    try { await act("ideas.fork_answer", { idea: row.idea, ...args }); } finally { setBusy(false); }
  };
  const choices = (row.sides || []).map((side) => {
    const head = partyBy(side.party)?.leader?.head || null;
    return { id: side.party, name: side.says, why: side.why || "", head, by: sideName(side) };
  });
  return html`<div class="spec-fork" data-kind="fork" data-fork=${row.id || ""}>
    <${Choose} question=${row.about} choices=${choices} pick="" element=${element} hint="The side you pick stands; the other leaders write their sections again" onChoose=${(id) => answer({ side: id })}
      onOther=${(text) => answer({ text })} onBack=${close} />
    <${SpecPage} props=${{ idea: row.idea }} />
  </div>`;
}
chooseFor("fork", Forks);

// The face: the question sign, the first side's leader as its asker, the sides at its foot (stopcard.js asks the way's `head` and `foot`).
way("fork", { sign: "question", head: (s) => partyBy(s.row?.sides?.[0]?.party)?.leader?.head || null, foot: (s) => disagreeWords(s.row?.sides), Lifted: ForkLifted });
