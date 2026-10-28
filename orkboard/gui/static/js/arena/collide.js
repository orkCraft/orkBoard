// The hand's `collide` stop (docs/specs/71-orkmaster-keeps-parties-apart.md §6, decisions §86): the Orkmaster asks which of two goals of different parties goes first, or whether a spec changed under another
// party's goal should be re-planned. Its two goals (stopcard.js lists them), the judge's why (the card's note), and its answers as buttons that say what
// happens (collidewords.js `answersOf`); a press sends `ideas.collide_answer {id, answer}`. The stop is drawn by hand/stopcard.js.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { toast } from "../link.js";
import { act } from "../shell/store.js";
import { answersOf } from "./collidewords.js";

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
