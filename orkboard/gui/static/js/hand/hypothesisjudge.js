// *Did it hold?* with what a hypothesis now carries (docs/specs/146-a-hypothesis-on-the-page.md B; decisions §235.2, §235.3, §235.5, §237.4; spec 133 B.4): the measures' values one line each against their bars, the condition
// code met marked (*Holds: met*, *Refuted, <name>: met*) and never a verdict of its own; a measure with no value asked of the person (a number, *From*, **Keep**: `ideas.hypothesis_value`, the one answer here that is
// typed); the answers — **Held**; **Refuted**, which with ways asks *Which way?* (the one met by code first; a single way is taken at once); **Not sure yet**, which asks a day (*Look again on*, today + 7 at first) —;
// and the draft of the decision under **More**, changed in words (`draft`). hand/hypothesiscard.js lays them in the lifted card. The sheet is hypothesisjudge.css.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { act } from "../shell/store.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as routecard.js links way.css
  const href = new URL("./hypothesisjudge.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const SYM = { ">=": "≥", ">": ">", "<=": "≤", "<": "<", "=": "=" };
const pad = (n) => String(n).padStart(2, "0");
/** The day `n` days from now, `YYYY-MM-DD`, the person's own calendar. */
export const inDays = (n) => {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
};

/** A measure's bars as words: *the bar ≤ 70*, then each way's (*the look > 100*). */
export function barsWords(m) {
  const b = m.bars || {};
  return [b.holds && `the bar ${SYM[b.holds.op] || b.holds.op} ${b.holds.n}`, ...(b.refuted || []).map((w) => `${w.way || "refuted"} ${SYM[w.op] || w.op} ${w.n}`)].filter(Boolean).join(" · ");
}

/** The conditions code met that this measure bears on: *Holds: met*, *Refuted, <name>: met*. */
export function metWords(m, met = {}) {
  const b = m.bars || {};
  return [met.holds === true && b.holds ? "Holds: met" : "", ...(met.refuted || []).filter((n) => (b.refuted || []).some((w) => w.way === n)).map((n) => (n ? `Refuted, ${n}: met` : "Refuted: met"))].filter(Boolean);
}

/** A measure with no value: a number, *From* (optional) and **Keep**. */
function ValueAsk({ row, m }) {
  const [n, setN] = useState(""), [from, setFrom] = useState(""), [busy, setBusy] = useState(false), ok = n.trim() !== "" && Number.isFinite(Number(n));
  const keep = async () => {
    setBusy(true);
    try { await act("ideas.hypothesis_value", { id: row.id, measure: m.id, n: Number(n), ...(from.trim() ? { from: from.trim() } : {}) }); } finally { setBusy(false); }
  };
  return html`<span class="hj-ask" role="group" aria-label=${`The value of ${m.what}`}>
    <input class="ork-field hj-ask__n" type="number" step="any" name=${`value-${m.id}`} aria-label=${`Value of ${m.what}`} value=${n} onInput=${(e) => setN(e.target.value)} />
    <input class="ork-field hj-ask__from" name=${`from-${m.id}`} maxlength="120" aria-label=${`From, for ${m.what}`} placeholder="From (optional)" value=${from} onInput=${(e) => setFrom(e.target.value)} />
    <button type="button" class="ork-btn" disabled=${busy || !ok} data-keep=${m.id} onClick=${keep}>Keep</button>
  </span>`;
}

/** The measures, one line each: the value with its unit and the bar, or the field that asks for it. */
export function Measures({ row }) {
  const ms = row.measures || [];
  if (!ms.length) return null;
  return html`<div class="hand-way__why" data-part="measures"><span class="ork-label">Measures</span>
    <ul class="hand-way__points hj-measures" aria-label="Measures">${ms.map((m) => {
      const unit = m.bars?.holds?.unit || (m.bars?.refuted || []).find((w) => w.unit)?.unit || "", marks = metWords(m, row.met);
      return html`<li key=${m.id} class="body" data-measure=${m.id}>${m.value
        ? html`<span class="hj-line">${m.what}: ${m.value.n}${unit ? ` ${unit}` : ""}${barsWords(m) ? ` — ${barsWords(m)}` : ""}</span>${marks.map((w) => html` <span key=${w} class="ork-chip hj-met">${w}</span>`)}`
        : html`<span class="hj-line">${m.what}: not read yet${barsWords(m) ? ` — ${barsWords(m)}` : ""}</span> <${ValueAsk} row=${row} m=${m} />`}</li>`;
    })}</ul></div>`;
}

/** The three answers, the way picked, the day asked and the draft under **More**. `why`: the *Why* line's words; `close()` after a verdict was kept. */
export function Judge({ row, why, close }) {
  const ways = row.refuted || [], draft = row.draft || { held: "", refuted: {} }, met = row.met?.refuted || [];
  const [busy, setBusy] = useState(false), [ask, setAsk] = useState(""), [more, setMore] = useState(false), [editing, setEditing] = useState(""), [edits, setEdits] = useState({}), [day, setDay] = useState(() => inDays(7));
  const drafts = [...(draft.held ? [{ key: "held", label: "If it holds", text: draft.held }] : []),
    ...ways.filter((w) => w.change || draft.refuted?.[w.name]).map((w) => ({ key: `refuted:${w.name}`, label: w.name ? `If it is refuted, ${w.name}` : "If it is refuted", text: draft.refuted?.[w.name] ?? w.change }))];
  const changed = (key) => {
    const mine = (edits[key] || "").trim(), was = drafts.find((d) => d.key === key)?.text || "";
    return mine && mine !== was.trim() ? { draft: mine } : {};
  };
  const send = async (state, extra = {}) => {
    setBusy(true);
    try {
      if (await act("ideas.hypothesis_judge", { id: row.id, state, ...(why.trim() ? { why: why.trim() } : {}), ...extra })) close?.();
    } finally { setBusy(false); }
  };
  const refute = (w) => send("refuted", { ...(w?.name ? { way: w.name } : {}), ...changed(`refuted:${w?.name || ""}`) });
  const refuted = () => {
    if (ways.length > 1) setAsk(ask === "refuted" ? "" : "refuted");
    else refute(ways[0]);
  };
  const choices = [...ways].sort((a, b) => met.includes(b.name) - met.includes(a.name));
  return html`<div class="hj-judge">
    ${drafts.length > 0 && html`<div class="hand-way__why hj-more" data-part="draft">
      <button type="button" class="ork-btn quiet" aria-expanded=${String(more)} onClick=${() => setMore(!more)}>More</button>
      ${more && drafts.map((d) => html`<div key=${d.key} class="hj-draft" data-draft=${d.key}><span class="ork-label">${d.label}</span>
        ${editing === d.key
          ? html`<textarea class="ork-field" name="draft" rows="4" maxlength="6000" aria-label=${`${d.label}, in words`} value=${edits[d.key] ?? d.text} onInput=${(e) => setEdits({ ...edits, [d.key]: e.target.value })}></textarea>`
          : html`<p class="body hj-draft__t">${edits[d.key] ?? d.text}</p><button type="button" class="ork-btn quiet" aria-label=${`Change it in words: ${d.label}`} onClick=${() => { setEdits({ ...edits, [d.key]: edits[d.key] ?? d.text }); setEditing(d.key); }}>Change it in words</button>`}
      </div>`)}
    </div>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      <button type="button" class="ork-btn primary" disabled=${busy} data-answer="held" title="It holds: a decision is written" onClick=${() => send("held", changed("held"))}>Held</button>
      <button type="button" class="ork-btn danger" disabled=${busy} data-answer="refuted" title="It does not hold: a decision is written" onClick=${refuted}>Refuted</button>
      <button type="button" class="ork-btn quiet" disabled=${busy} data-answer="unsure" title="It stays open; the why is kept as what was found" onClick=${() => setAsk(ask === "unsure" ? "" : "unsure")}>Not sure yet</button>
    </div>
    ${ask === "refuted" && html`<div class="hand-answers hj-pick" role="group" aria-label="Which way?"><span class="ork-label">Which way?</span>
      ${choices.map((w, i) => html`<button key=${i} type="button" class="ork-btn" disabled=${busy} data-way=${w.name} onClick=${() => refute(w)}>${w.name || w.when}${met.includes(w.name) ? " · met" : ""}</button>`)}</div>`}
    ${ask === "unsure" && html`<div class="hj-day" role="group" aria-label="Look again on"><label class="hand-way__why"><span class="ork-label">Look again on</span>
      <input class="ork-field" type="date" name="look-on" min=${inDays(1)} value=${day} onInput=${(e) => setDay(e.target.value)} /></label>
      <button type="button" class="ork-btn" disabled=${busy || !day} data-answer="unsure-on" onClick=${() => send("unsure", { date: day })}>Keep it open</button></div>`}
  </div>`;
}
