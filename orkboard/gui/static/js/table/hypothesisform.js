// A hypothesis on Product's tree, past its two lines (docs/specs/146-a-hypothesis-on-the-page.md A; decisions §235.1, §235.2, §237.4; spec 133 A, B). The card is short until **More**: it says its text, *Holds when*
// and its signal, one line a way it is refuted and one line a measure with its day — never a value, a bar filling or a count before the day (the host strips the values until then, `hypothesis_measures.shown`).
// **More** opens, in the card's own place (it grows; nothing opens beside it), the fields of the rest: *Holds when*, *If it holds*, *Refuted when* (one to three ways, each *What it would teach*, *When*, *Then*;
// **+ A way**), *Measures* (up to four: *What*, *From*, *Whose map*, a bar for *Holds* and for each way, *For* a span or *Until* a day; **+ A measure**). **Save** sends `ideas.hypothesis_set {id, signal, if_holds,
// refuted}` and each measure that changed through `ideas.hypothesis_measure_set` (one taken off through `ideas.hypothesis_measure_drop`); the host's refusal is said under the fields in its own words; **Cancel**
// puts it back. The sheet is hypothesisform.css.
import { useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command } from "../link.js";
import { nameOf, partiesAll } from "./data.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as treemap.js links its own
  const href = new URL("./hypothesisform.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const MAX_WAYS = 3, MAX_MEASURES = 4;
export const OPS = [[">=", "at least"], [">", "more than"], ["<=", "at most"], ["<", "less than"], ["=", "exactly"]];
const SPANS = [[14, "2 weeks"], [28, "4 weeks"], [56, "8 weeks"]];
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** `2026-12-01` as *1 Dec* ("" for what is no day). */
export function dayWord(iso) {
  const m = /^(\d{4})-(\d\d)-(\d\d)/.exec(String(iso || ""));
  return m && MONTHS[Number(m[2]) - 1] ? `${Number(m[3])} ${MONTHS[Number(m[2]) - 1]}` : "";
}

const spanWord = (days) => SPANS.find(([n]) => n === days)?.[1] || (days % 7 === 0 ? `${days / 7} weeks` : `${days} days`);
const plusDays = (iso, days) => {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
};

// -- what a closed card says --------------------------------------------------------------------------------------------------------------------------

/** The lines under *Holds when* on a closed card: one a way it is refuted (*Refuted when <name>: <when>*), one a measure (*<what> · until 1 Dec*). No value, no bar: only the day. */
export function Conditions({ x }) {
  const ways = x.refuted || [], measures = x.measures || [];
  return html`${ways.map((w, i) => html`<p key=${`w${i}`} class="hy-line hy-way"><span class="tr-k">Refuted when</span> ${w.name ? `${w.name}: ` : ""}${w.when}</p>`)}
    ${measures.map((m) => html`<p key=${m.id} class="hy-line hy-measure">${m.what}${dayWord(m.date) ? ` · until ${dayWord(m.date)}` : ""}</p>`)}`;
}

// -- the fields -----------------------------------------------------------------------------------------------------------------------------------------

const bar = (b) => ({ op: b?.op || "", n: b ? String(b.n) : "", unit: b?.unit || "" });

/** The form's state from a hypothesis (the host's item): the conditions as text, each measure with a bar for *Holds* and one for each way (by the way's place, so a way renamed keeps its bars). */
export function draftOf(x) {
  const ways = (x.refuted || []).map((w) => ({ name: w.name || "", when: w.when || "", change: w.change || "" }));
  return {
    signal: x.signal || "", if_holds: x.if_holds || "", ways,
    measures: (x.measures || []).map((m) => {
      const same = x.started && m.date === plusDays(x.started, m.span_days);
      return { id: m.id, what: m.what || "", from: m.from || "", by: m.by || "", mode: !m.date || same ? "for" : "until", span: m.span_days || 28, date: m.date || "", holds: bar(m.bars?.holds),
        bars: ways.map((w) => bar((m.bars?.refuted || []).find((b) => b.way === w.name))) };
    }),
  };
}

const barArgs = (b) => (b.op && b.n !== "" && Number.isFinite(Number(b.n)) ? { op: b.op, n: Number(b.n), unit: b.unit.trim() } : null);

/** What `ideas.hypothesis_measure_set` is sent for a measure of the draft `d`: its words, its bars (`holds`, one `refuted` entry per way that has one) and its span or its day. */
export function measureArgs(d, m) {
  const refuted = d.ways.map((w, i) => ({ w, b: barArgs(m.bars[i] || bar()) })).filter((r) => r.b).map((r) => ({ way: r.w.name.trim(), ...r.b }));
  return { what: m.what.trim(), from: m.from.trim(), by: m.by, holds: barArgs(m.holds), refuted, ...(m.mode === "until" ? { date: m.date } : { span_days: Number(m.span) }) };
}

const waysOf = (d) => d.ways.map((w) => ({ name: w.name.trim(), when: w.when.trim(), change: w.change.trim() }));

/** One bar: its operator (blank: no bar), its number and its unit. */
function Bar({ label, b, set, id }) {
  return html`<div class="hf-bar" role="group" aria-label=${`The bar for ${label}`}>
    <span class="hf-bar__l">${label}</span>
    <span class="ork-select"><select class="ork-field" name=${`${id}-op`} aria-label=${`${label}: how`} value=${b.op} onChange=${(e) => set({ ...b, op: e.target.value })}>
      <option value="">no bar</option>${OPS.map(([v, w]) => html`<option key=${v} value=${v}>${w}</option>`)}</select></span>
    <input class="ork-field hf-bar__n" type="number" step="any" name=${`${id}-n`} aria-label=${`${label}: the number`} value=${b.n} onInput=${(e) => set({ ...b, n: e.target.value })} />
    <input class="ork-field hf-bar__u" name=${`${id}-unit`} maxlength="24" aria-label=${`${label}: the unit`} placeholder="unit" value=${b.unit} onInput=${(e) => set({ ...b, unit: e.target.value })} />
  </div>`;
}

function Measure({ d, m, k, set, drop, parties }) {
  const upd = (patch) => set({ ...m, ...patch }), id = `m${k}`;
  const spans = SPANS.some(([n]) => n === Number(m.span)) ? SPANS : [...SPANS, [Number(m.span), spanWord(Number(m.span))]];
  return html`<fieldset class="hf-measure" data-measure=${m.id || "new"}>
    <label class="mp-sec"><span class="ork-label">What</span><input class="ork-field" name=${`${id}-what`} maxlength="120" value=${m.what} onInput=${(e) => upd({ what: e.target.value })} /></label>
    <label class="mp-sec"><span class="ork-label">From</span><input class="ork-field" name=${`${id}-from`} maxlength="120" value=${m.from} onInput=${(e) => upd({ from: e.target.value })} /></label>
    <label class="mp-sec"><span class="ork-label">Whose map</span><span class="ork-select"><select class="ork-field" name=${`${id}-by`} value=${m.by} onChange=${(e) => upd({ by: e.target.value })}>
      <option value="">You</option>${parties.map((p) => html`<option key=${p.slug} value=${p.slug}>${p.name}</option>`)}</select></span></label>
    <${Bar} id=${`${id}-holds`} label="Holds" b=${m.holds} set=${(b) => upd({ holds: b })} />
    ${d.ways.map((w, i) => html`<${Bar} key=${i} id=${`${id}-way${i}`} label=${w.name.trim() || `Way ${i + 1}`} b=${m.bars[i] || bar()} set=${(b) => upd({ bars: d.ways.map((_, j) => (j === i ? b : m.bars[j] || bar())) })} />`)}
    <div class="hf-when">
      <span class="ork-select"><select class="ork-field" name=${`${id}-mode`} aria-label="For a span or until a day" value=${m.mode} onChange=${(e) => upd({ mode: e.target.value })}>
        <option value="for">For</option><option value="until">Until</option></select></span>
      ${m.mode === "until" ? html`<input class="ork-field" type="date" name=${`${id}-date`} aria-label="Until" value=${m.date} onInput=${(e) => upd({ date: e.target.value })} />`
        : html`<span class="ork-select"><select class="ork-field" name=${`${id}-span`} aria-label="For" value=${String(m.span)} onChange=${(e) => upd({ span: Number(e.target.value) })}>
          ${spans.map(([n, w]) => html`<option key=${n} value=${String(n)}>${w}</option>`)}</select></span>`}
    </div>
    <button type="button" class="ork-btn quiet hf-remove" aria-label=${`Remove the measure ${k + 1}`} onClick=${drop}>Remove</button>
  </fieldset>`;
}

/** **More** on a kept hypothesis: the fields of its conditions and its measures, **Save** and **Cancel**. `x`: the host's item; `onClose()` puts the card back; `onSaved()` after a save. */
export function HypMore({ x, onClose, onSaved }) {
  const first = useRef(), start = useRef(draftOf(x)), gone = useRef(new Set());
  const [d, setD] = useState(start.current), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const parties = partiesAll().map((g) => ({ slug: g.slug, name: nameOf(g) }));
  for (const m of d.measures) if (m.by && !parties.some((p) => p.slug === m.by)) parties.push({ slug: m.by, name: m.by });
  const way = (i, patch) => setD({ ...d, ways: d.ways.map((w, j) => (j === i ? { ...w, ...patch } : w)) });
  const save = async () => {
    setBusy(true);
    setErr("");
    try {
      await command("ideas.hypothesis_set", { id: x.id, signal: d.signal.trim(), if_holds: d.if_holds.trim(), refuted: waysOf(d) }, true);
      for (const old of start.current.measures) {
        if (!d.measures.some((m) => m.id === old.id) && !gone.current.has(old.id)) {
          await command("ideas.hypothesis_measure_drop", { id: x.id, measure: old.id }, true);
          gone.current.add(old.id);
        }
      }
      for (const m of d.measures) {
        const was = start.current.measures.find((o) => o.id === m.id), args = measureArgs(d, m);
        if (!m.id || JSON.stringify(args) !== JSON.stringify(measureArgs(start.current, was))) await command("ideas.hypothesis_measure_set", { id: x.id, ...(m.id ? { measure: m.id } : {}), ...args }, true);
      }
      onSaved();
    } catch (e) { setErr(e.message || "The hypothesis could not be kept"); setBusy(false); }
  };
  return html`<form class="mp-form hy-form hf-form" data-more=${x.id} onSubmit=${(e) => { e.preventDefault(); save(); }}>
    <label class="mp-sec"><span class="ork-label">Holds when</span><textarea ref=${first} class="ork-field" name="signal" maxlength="200" rows="2" value=${d.signal} onInput=${(e) => setD({ ...d, signal: e.target.value })} required></textarea></label>
    <label class="mp-sec"><span class="ork-label">If it holds</span><textarea class="ork-field" name="if_holds" maxlength="400" rows="3" value=${d.if_holds} onInput=${(e) => setD({ ...d, if_holds: e.target.value })}></textarea></label>
    <fieldset class="hf-group"><legend class="ork-label">Refuted when</legend>
      ${d.ways.map((w, i) => html`<div key=${i} class="hf-way" data-way=${i}>
        <label class="mp-sec"><span class="ork-label">What it would teach</span><input class="ork-field" name=${`way-name-${i}`} maxlength="40" value=${w.name} onInput=${(e) => way(i, { name: e.target.value })} /></label>
        <label class="mp-sec"><span class="ork-label">When</span><textarea class="ork-field" name=${`way-when-${i}`} maxlength="200" rows="2" value=${w.when} onInput=${(e) => way(i, { when: e.target.value })}></textarea></label>
        <label class="mp-sec"><span class="ork-label">Then</span><textarea class="ork-field" name=${`way-change-${i}`} maxlength="400" rows="2" value=${w.change} onInput=${(e) => way(i, { change: e.target.value })}></textarea></label>
        <button type="button" class="ork-btn quiet hf-remove" aria-label=${`Remove the way ${i + 1}`} onClick=${() => setD({ ...d, ways: d.ways.filter((_, j) => j !== i), measures: d.measures.map((m) => ({ ...m, bars: m.bars.filter((_, j) => j !== i) })) })}>Remove</button>
      </div>`)}
      ${d.ways.length < MAX_WAYS && html`<button type="button" class="ork-btn quiet hf-add" onClick=${() => setD({ ...d, ways: [...d.ways, { name: "", when: "", change: "" }], measures: d.measures.map((m) => ({ ...m, bars: [...m.bars, bar()] })) })}>+ A way</button>`}
    </fieldset>
    <fieldset class="hf-group"><legend class="ork-label">Measures</legend>
      ${d.measures.map((m, k) => html`<${Measure} key=${m.id || `n${k}`} d=${d} m=${m} k=${k} parties=${parties} set=${(n) => setD({ ...d, measures: d.measures.map((o, j) => (j === k ? n : o)) })}
        drop=${() => setD({ ...d, measures: d.measures.filter((_, j) => j !== k) })} />`)}
      ${d.measures.length < MAX_MEASURES && html`<button type="button" class="ork-btn quiet hf-add" onClick=${() => setD({ ...d, measures: [...d.measures, { id: "", what: "", from: "", by: "", mode: "for", span: 28, date: "", holds: bar(), bars: d.ways.map(() => bar()) }] })}>+ A measure</button>`}
    </fieldset>
    ${err && html`<p class="mp-err" role="alert">${err}</p>`}
    <div class="mp-acts"><button type="submit" class=${cls("ork-btn primary")} disabled=${busy || !d.signal.trim()}>Save</button>
      <button type="button" class="ork-btn" onClick=${onClose}>Cancel</button></div>
  </form>`;
}
