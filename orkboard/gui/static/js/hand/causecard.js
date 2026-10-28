// A bug's cause (docs/specs/100-a-goals-way-as-cards.md §2.3; docs/specs/99-a-goals-way.md §5.4, decisions §158.1): the `cause` row's card, its face *The cause* and Tech's head under the sign `question`. Its questions about the
// cases are question cards of the same stack, before it (questions.js `questionStops`; a press on one deals its choices over the pane: questioncard.js). Lifted, the guess (*I think …*) with its parts named (`where`, each a press that
// lights the part on System), **Yes**, **No, it's elsewhere** (one line opens for where) and **Other…** (one line for the person's own words); each sends `ideas.cause_answer` with the case questions' answers.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { closeOver, openTab, over, partKey } from "../frame/state.js";
import { litKey } from "../table/card.js";
import { QuestionLifted } from "./questioncard.js";
import { sendCause } from "./questions.js";
import { named } from "./todoform.js";
import { way } from "./ways.js";

/** The part named is lit on Tech's System: its tab opens, the pane goes back to the map and the part is lit as the card a thing came from is. */
function light(party, path) {
  if (over.value) closeOver();
  openTab(party);
  litKey.value = partKey(party, path);
}

function Cause({ s, close }) {
  const row = s.ref, [mode, setMode] = useState(""), [line, setLine] = useState(""), [busy, setBusy] = useState(false), lead = s.party?.lead;
  const send = async (yes, text = "") => {
    setBusy(true);
    const got = await sendCause(row, lead, yes, text);
    setBusy(false);
    if (got) close();
  };
  const field = mode === "no" ? { label: "Where is it? One line", yes: false } : { label: "Your own words, one line", yes: true };
  return html`<div class="q-cause" data-kind="cause">
    <p class="cap hand-lifted__why">${s.full}</p>
    <p class="body hand-lifted__text q-cause__guess">${s.text}</p>
    ${(row.where || []).length > 0 && html`<ul class="q-cause__where" aria-label="The parts">${row.where.map((p) => html`<li key=${p}><button type="button" class="ork-btn quiet q-cause__part" data-path=${p}
      title="Lights it on the System" onClick=${() => light(row.goal, p)}>${p}</button></li>`)}</ul>`}
    ${mode ? html`<div class="hand-why">
      <input class="ork-field" value=${line} aria-label=${field.label} placeholder=${field.label} autofocus onInput=${(e) => setLine(e.target.value)}
        onKeyDown=${(e) => { if (e.key === "Enter" && line.trim()) send(field.yes, line.trim()); else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setMode(""); } }} />
      <button type="button" class="ork-btn primary" disabled=${busy || !line.trim()} onClick=${() => send(field.yes, line.trim())}>Send</button>
      <button type="button" class="ork-btn quiet" onClick=${() => setMode("")}>Cancel</button></div>`
      : html`<div class="hand-answers" role="group" aria-label="Answers">
        <button type="button" class="ork-btn primary" disabled=${busy} title=${`${named(lead)} goes on with this cause`} onClick=${() => send(true)}>Yes</button>
        <button type="button" class="ork-btn" disabled=${busy} title="One line says where" onClick=${() => { setLine(""); setMode("no"); }}>No, it's elsewhere</button>
        <button type="button" class="ork-btn" disabled=${busy} title="Your own words" onClick=${() => { setLine(""); setMode("other"); }}>Other…</button></div>`}
  </div>`;
}

/** The lifted card of a bug's stack: a case question deals its choices; the guess itself is answered here. */
function CauseLifted({ s, close }) {
  return s.card ? html`<${QuestionLifted} s=${s} />` : html`<${Cause} s=${s} close=${close} />`;
}

way("cause", { sign: "question", Lifted: CauseLifted });
