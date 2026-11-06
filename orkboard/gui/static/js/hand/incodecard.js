// The Orkmaster's question about the Board in the code (docs/specs/151 F.1, F.3, decisions §255.10): a card of no goal's, thrown while the repository is public or unreadable and the person has not said whether the Board goes into it.
// The row is `{kind: "in_code", step, title, text, ask, held, words, pages_in_history}` (gui/ideas_in_code.py; the words are the glossary's: `Your goals, their specs, the leaders' words and the decisions will be public, in the repository's history:
// a later No does not take them back.` and, when there are some, how many pages of the Board are in its history already). Its face is the hand's card (stopcard.js): the alert sign, the Orkmaster's crowned head as its asker, the question as its name.
// Lifted, `step: "publish"`: the words and **Publish the Board** (`ideas.in_code {answer: "publish"}`) / **Keep the Board off the repository** (`{answer: "off"}`); a repository found public since says what waits (`held`: the Board's pushes).
// `step: "private"` (a remote Orkboard cannot read) asks *Is this repository private?* first: **Private** (`{answer: "private"}`) / **Public**, which only goes on to the publish question. The card leaves once answered.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { act } from "../shell/store.js";
import { orkHead } from "./routecard.js";
import { way } from "./ways.js";

/** The lifted card: the question and its two answers. */
export function InCodeLifted({ s, close }) {
  const row = s.row || {}, w = row.words || {}, [asPublic, setPublic] = useState(false), [busy, setBusy] = useState(false), ask = row.step === "private" && !asPublic;
  const answer = async (a) => {
    setBusy(true);
    try { if (await act("ideas.in_code", { answer: a })) close?.(); } finally { setBusy(false); }
  };
  return html`<div class="hand-way hand-way--in-code" data-in-code=${ask ? "private" : "publish"}>
    ${row.held && !ask && html`<p class="body hand-way__goes" data-line="held">${row.held}</p>`}
    <p class="body hand-way__words" data-line="ask">${ask ? row.ask : row.text}</p>
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      ${ask ? html`<button type="button" class="ork-btn primary" data-answer="private" disabled=${busy} title="Nothing is public: the Board goes into the repository" onClick=${() => answer("private")}>${w.private}</button>
          <button type="button" class="ork-btn" data-answer="public" disabled=${busy} title="Then the Board asks whether to publish it" onClick=${() => setPublic(true)}>${w.public}</button>`
        : html`<button type="button" class="ork-btn primary" data-answer="publish" disabled=${busy} title="The Board goes into the repository's history; a later No does not take it back" onClick=${() => answer("publish")}>${w.publish}</button>
          <button type="button" class="ork-btn" data-answer="off" disabled=${busy} title="The Board stays on this computer; no rules are written" onClick=${() => answer("off")}>${w.off}</button>`}
    </div>
  </div>`;
}

way("in_code", { sign: "alert", head: orkHead, foot: (s) => s.row?.held || "", price: () => null, Lifted: InCodeLifted });
