// The decision's card (docs/specs/100-a-goals-way-as-cards.md §3.1; docs/specs/99-a-goals-way.md §6; decisions §118.1, §134.5, §147.3): what the Orkmaster worded after Talk, for the person to read and confirm. The row is
// `{kind: "decision", idea, number, title, text, confirmed, error}` (`text`: *Why: …* and the points numbered, as the project's decisions file words them). Its face is the hand's card (stopcard.js): the sign `page`, the
// Orkmaster's crowned head as its asker, *Decision <n>* at its foot, no gem (it spends nothing new), under the first lane. Lifted: its title (the card's own header), *Why* and its numbered points, *Edit*, which opens the whole
// entry as a field on the card (what is written there is sent as `text`, kept as written), and one button, **Confirm and start** (`ideas.confirm`): the entry is written into the project's decisions file and committed, the leaders
// write their sections. After a failed *Confirm* the entry is written already (`confirmed` and the `error`): the button asks the sections again and *Edit* is gone.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { act } from "../shell/store.js";
import { orkHead } from "./routecard.js";
import { way } from "./ways.js";

/** The decision's body as the file words it: `{why, points}`; null when it is another shape (a correction's own words), which is then drawn whole. */
export function bodyOf(text) {
  const src = String(text || "").replace(/\r\n/g, "\n").trim(), m = /^Why:[ \t]*([\s\S]*?)(?:\n\s*\n|$)([\s\S]*)$/.exec(src);
  if (!m) return null;
  const points = m[2].split("\n").map((l) => /^\s*\d+[.)]\s+(.*\S)\s*$/.exec(l)).filter(Boolean).map((x) => x[1]);
  return { why: m[1].trim(), points, rest: points.length ? "" : m[2].trim() };
}

/** *Decision 118*, or *Decision* before a number is read. */
export const decisionWords = (row) => (Number(row?.number) > 0 ? `Decision ${row.number}` : "Decision");

/** The entry as a field opens it: its heading line (the title is its first line when it is a heading), then the body. */
const entryOf = (row) => `## ${Number(row.number) > 0 ? `${row.number}. ` : ""}${row.title}\n\n${String(row.text || "").trim()}`;

export function DecisionLifted({ s, close }) {
  const row = s.row || {}, body = bodyOf(row.text), [edit, setEdit] = useState(false), seed = entryOf(row), [text, setText] = useState(seed), [busy, setBusy] = useState(false), box = useRef();
  useEffect(() => { if (edit) box.current?.focus({ preventScroll: true }); }, [edit]);
  const confirm = async () => {
    setBusy(true);
    try {
      const got = await act("ideas.confirm", { idea: row.idea, ...(edit && text.trim() && text !== seed ? { text } : {}) });
      if (got) close?.();
    } finally { setBusy(false); }
  };
  const key = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setEdit(false); } };
  return html`<div class="hand-way hand-way--decision" data-confirmed=${row.confirmed ? "1" : undefined}>
    ${edit ? html`<textarea ref=${box} class="ork-field hand-way__entry" aria-label="The decision’s text" rows="12" value=${text} onInput=${(e) => setText(e.target.value)} onKeyDown=${key}></textarea>`
      : body ? html`<div class="hand-way__why"><span class="ork-label">Why</span><p class="body">${body.why}</p></div>
          ${body.points.length > 0 && html`<ol class="hand-way__points" aria-label="The points">${body.points.map((p, i) => html`<li key=${i} class="body">${p}</li>`)}</ol>`}
          ${body.rest && html`<p class="body hand-way__words">${body.rest}</p>`}`
        : html`<p class="body hand-way__words">${String(row.text || "").trim()}</p>`}
    ${row.confirmed && html`<p class="cap hand-way__place" data-note="written">${row.error ? `${row.error}. ` : ""}The decision is written already: Confirm and start asks the sections again.</p>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      <button type="button" class="ork-btn primary" disabled=${busy || (edit && !text.trim())}
        title="The decision is written into the project’s decisions file and committed, then the leaders write their sections" onClick=${confirm}>Confirm and start</button>
      ${!row.confirmed && (edit ? html`<button type="button" class="ork-btn quiet" disabled=${busy} onClick=${() => { setEdit(false); setText(seed); }}>Cancel</button>`
        : html`<button type="button" class="ork-btn quiet" disabled=${busy} title="Change the words before they are written" onClick=${() => setEdit(true)}>Edit</button>`)}
    </div>
  </div>`;
}

// The face: the page sign, the Orkmaster as its asker (it words the decision), *Decision <n>* at its foot, no price.
way("decision", { sign: "page", head: orkHead, foot: (s) => decisionWords(s.row), price: () => null, Lifted: DecisionLifted });
