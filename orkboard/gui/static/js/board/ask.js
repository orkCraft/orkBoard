// One round of questions (docs/specs/35-goals-window.md §0, §11.2): a box per question, answered together, one Send. The
// keeper asks at most three, all at once, and asks nothing more after the answers. A question with choices shows them as buttons that fill its box;
// the choice *Pictures you like* (docs/specs/85-the-elf-asks-and-shows.md §1) takes pictures: *Add a picture* under its box, sent with the answers.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { say } from "../link.js";
import { PictureAdd, usePictures } from "./pictures.js";

const PICTURES = "Pictures you like";               // realm/idea_look.py PICTURES

/** `initial`: the answers a box starts with (the recommended ones, spec 41 §9); `hints`: a line under each question (its why); `choices`: each question's choices (none: just the box);
 *  `pictures`: whether a question that offers *Pictures you like* takes them (the goal's questions do not). `onSend(answers, pictures)`: the pictures as data URLs. */
export function Questions({ questions, onSend, busy = false, initial = [], hints = [], choices = [], pictures: takes = false }) {
  const [answers, setAnswers] = useState(() => questions.map((_, n) => initial[n] || ""));
  const [sending, setSending] = useState(false);
  const pictures = usePictures();
  const set = (n, text) => setAnswers(answers.map((a, i) => (i === n ? text : a)));
  const send = async (e) => {
    e?.preventDefault();
    if (sending) return;
    setSending(true);
    await onSend(questions.map((_, n) => (answers[n] || "").trim()), takes ? pictures.list : []);
    setSending(false);
  };
  return html`<form class="board-questions" id="board-questions" onSubmit=${send}>
    ${questions.map((q, n) => html`<div key=${n} class="board-questions__q"><label class="shell-field"><span class="ok-font-label">${q}</span>
      <textarea class="ork-field" rows="2" autofocus=${n === 0} value=${answers[n] || ""} aria-label=${`Answer ${n + 1}: ${q}`}
        onInput=${(e) => set(n, e.target.value)}
        onKeyDown=${(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send(e); }}></textarea>
      ${hints[n] && html`<small class="ok-tone-muted">${hints[n]}</small>`}</label>
      ${(choices[n] || []).length > 0 && html`<div class="board-questions__choices" role="group" aria-label=${`Choices: ${q}`}>
        ${choices[n].map((c) => html`<button type="button" key=${c} class=${cls("ork-btn quiet", { primary: (answers[n] || "").trim() === c })} aria-pressed=${(answers[n] || "").trim() === c}
          onClick=${() => set(n, c)}>${c}</button>`)}</div>`}
      ${takes && (choices[n] || []).includes(PICTURES) && html`<${PictureAdd} pictures=${pictures} />`}</div>`)}
    <div class="board-row"><button type="submit" class="ork-btn primary" disabled=${sending || busy}>Send</button>
      <span class="ok-font-status ok-tone-muted">${say("The Taskmaster reads all your answers at once and asks nothing more.")}</span></div>
  </form>`;
}
