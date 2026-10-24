// The hand's `collide` stop (docs/specs/71-orkmaster-keeps-parties-apart.md §6, decisions §86): the Orkmaster asks which of two goals of different parties goes first, or whether a spec changed under another
// party's goal should be re-planned. Its two goals (each a button with its party: a press opens the goal), the judge's why (stops.js draws it as the stop's note), and its answers as buttons that say what
// happens (collidewords.js `answersOf`); a press sends `ideas.collide_answer {id, answer}`. The stop is drawn by stops.js, which also keeps its fan, its raise and its leaving.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem } from "../orkui.js";
import { toast } from "../link.js";
import { act, showIdea } from "../shell/store.js";
import { elementOf } from "./goalwords.js";
import { answersOf, goalLine, goalsOfRow } from "./collidewords.js";

/** The two goals the stop is about, each one line: its element, its party and its title. */
export function CollideGoals({ row, see }) {
  return html`<div class="arena-hc__pair" role="group" aria-label="The goals">
    ${goalsOfRow(row).map((g) => html`<button type="button" key=${g.idea} class="arena-hc__goal" data-slug=${g.idea} data-party=${g.party} title=${`Open ${g.title} in ${g.party_name || g.party}`}
      onClick=${() => { see(); showIdea(g.idea, { via: "hand" }); }}>
      <${Elem} name=${elementOf({ element: g.element }).name} /><span class="arena-hc__goalt">${goalLine(g)}</span></button>`)}
  </div>`;
}

/** The answers: one button each, the judge's suggestion primary. A press sends the answer; the stop leaves when the Board is read again. */
export function CollideAnswers({ s }) {
  const row = s.row, [busy, setBusy] = useState(false);
  const send = async (answer) => {
    setBusy(true);
    const got = await act("ideas.collide_answer", { id: row.collide.id, answer });
    setBusy(false);
    if (got) toast(answer === "leave" ? "Left as they are." : "Sent: the Orkmaster keeps the goals apart.");
  };
  return html`${answersOf(row).map((a) => html`<button type="button" key=${a.answer} class=${cls("ork-btn arena-hc__q", { primary: a.primary })} data-answer=${a.answer} disabled=${busy} title=${a.tip}
    aria-label=${`${a.text}: ${s.full}`} onClick=${() => send(a.answer)}><span class="arena-hc__qt">${a.text}</span></button>`)}`;
}
