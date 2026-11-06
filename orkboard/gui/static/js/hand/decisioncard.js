// (Spec 150 E2.1: while the row says `conflicted`, a conflict card of the hand is open and **Confirm and start** is not shown.)
// The decision's card (docs/specs/100-a-goals-way-as-cards.md §3.1; docs/specs/99-a-goals-way.md §6; decisions §118.1, §134.5, §147.3): what the Orkmaster worded after Talk, for the person to read and confirm. The row is
// `{kind: "decision", idea, number, title, text, confirmed, error}` (`text`: *Why: …* and the points numbered, as the project's decisions file words them). Its face is the hand's card (stopcard.js): the sign `page`, the
// Orkmaster's crowned head as its asker, *Decision <n>* at its foot, no gem (it spends nothing new), under the first lane. Lifted: its title (the card's own header), *Why* and its numbered points, **Change…** (spec 132 A, decisions §237.3), which opens the whole
// entry as a field on the card and, under it, one line, *Or say what to change* (`ideas.decision_change {idea, text?, say?}`: the field is kept as written, the line is worded again by the Orkmaster, one call, its price said when it is done; **Change** sends them, **Cancel** puts them away, and **Confirm and start** with the field changed sends it as `text` as it did), and one button, **Confirm and start** (`ideas.confirm`): the entry is written into the project's decisions file and committed, the leaders
// write their sections; **Start** instead when the leaders all agreed and the wait was held (spec 120 §6.8). After a failed *Confirm* the entry is written already (`confirmed` and the `error`): the button asks the sections again and *Edit* is gone.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { act, mapData } from "../shell/store.js";
import { toast } from "../link.js";
import { spendWords } from "./costline.js";
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

/** Whether the goal's wait was held (spec 120 §6.8): the leaders agreed, the person pressed **Hold** (or a stop or a spent window did), so the decision's one button says **Start**. */
export const heldWait = (idea) => !!(mapData.value?.nodes || []).find((n) => n.slug === idea)?.back?.ripe?.held;

export function DecisionLifted({ s, close }) {
  const row = s.row || {}, held = heldWait(row.idea), body = bodyOf(row.text), [edit, setEdit] = useState(false), seed = entryOf(row), [text, setText] = useState(seed), [say, setSay] = useState(""), [busy, setBusy] = useState(false), box = useRef();
  useEffect(() => { if (edit) box.current?.focus({ preventScroll: true }); }, [edit]);
  const confirm = async () => {
    setBusy(true);
    try {
      const got = await act("ideas.confirm", { idea: row.idea, ...(edit && text.trim() && text !== seed ? { text } : {}) });
      if (got) close?.();
    } finally { setBusy(false); }
  };
  const change = async () => {                                         // the field kept as written, the line worded again: one command, the card is read again
    const kept = text.trim() && text !== seed ? text : "", said = say.trim();
    if (!kept && !said) return;
    setBusy(true);
    try {
      const got = await act("ideas.decision_change", { idea: row.idea, ...(kept ? { text: kept } : {}), ...(said ? { say: said } : {}) });
      if (got) {
        const price = got.reworded && got.cost ? spendWords(got.cost.usd_high) : "";
        toast(got.reworded ? `The Orkmaster words the decision again${price ? `: ${price}` : ""}` : "The decision is changed", "information");
        setEdit(false); setSay("");
      }
    } finally { setBusy(false); }
  };
  const key = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setEdit(false); } };
  return html`<div class="hand-way hand-way--decision" data-confirmed=${row.confirmed ? "1" : undefined}>
    ${edit ? html`<textarea ref=${box} class="ork-field hand-way__entry" aria-label="The decision’s text" rows="12" value=${text} onInput=${(e) => setText(e.target.value)} onKeyDown=${key}></textarea>
        <label class="hand-way__why hand-way__say"><span class="ork-label">Or say what to change</span>
          <input class="ork-field" name="say" aria-label="Or say what to change" maxlength="2000" value=${say} onInput=${(e) => setSay(e.target.value)} onKeyDown=${key} placeholder="The Orkmaster words it again" /></label>`
      : body ? html`<div class="hand-way__why"><span class="ork-label">Why</span><p class="body">${body.why}</p></div>
          ${body.points.length > 0 && html`<ol class="hand-way__points" aria-label="The points">${body.points.map((p, i) => html`<li key=${i} class="body">${p}</li>`)}</ol>`}
          ${body.rest && html`<p class="body hand-way__words">${body.rest}</p>`}`
        : html`<p class="body hand-way__words">${String(row.text || "").trim()}</p>`}
    ${row.conflicted && html`<p class="cap hand-way__place" data-note="conflicted">It goes against an earlier decision: answer that card first.</p>`}
    ${held && !row.confirmed && html`<p class="cap hand-way__place" data-note="held">Held: start it when you are ready</p>`}
    ${row.confirmed && html`<p class="cap hand-way__place" data-note="written">${row.error ? `${row.error}. ` : ""}The decision is written already: Confirm and start asks the sections again.</p>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      ${!row.conflicted && html`<button type="button" class="ork-btn primary" disabled=${busy || (edit && (!text.trim() || !!say.trim()))}
        title="The decision is written into the project’s decisions file and committed, then the leaders write their sections" onClick=${confirm}>${held ? "Start" : "Confirm and start"}</button>`}
      ${!row.confirmed && (edit ? html`<button type="button" class="ork-btn" data-answer="change" disabled=${busy || (text === seed && !say.trim())}
          title=${say.trim() ? "The field is kept as written; what you say is worded again by the Orkmaster: one call" : "Keep the decision as written"} onClick=${change}>Change</button>
        <button type="button" class="ork-btn quiet" disabled=${busy} onClick=${() => { setEdit(false); setText(seed); setSay(""); }}>Cancel</button>`
        : html`<button type="button" class="ork-btn quiet" data-answer="change" disabled=${busy} title="Change the words, or say what to change: the Orkmaster words it again" onClick=${() => setEdit(true)}>Change…</button>`)}
    </div>
  </div>`;
}

// The face: the page sign, the Orkmaster as its asker (it words the decision), *Decision <n>* at its foot, no price.
way("decision", { sign: "page", head: orkHead, foot: (s) => decisionWords(s.row), price: () => null, Lifted: DecisionLifted });
