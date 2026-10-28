// This week (docs/specs/42-coming-back.md §6; spec 98 §7): the work of the last seven days, at API prices, beside today's spend — a place over the pane (`week`, frame/kinds.js) that the AI tools'
// limits open (table/over.js). Reads `ideas.week_work` when opened. The words are pure functions, so a face and a test read the same lines.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { Place, closePlace } from "../frame/place.js";
import { ask } from "./store.js";
import { logOpened } from "../shell/store.js";
import { pctOf } from "../spend.js";

/** *5 results in dev, 4 the first time* · *1 result in dev, the first time* · *1 result in dev*. */
export function resultsWords(m, into) {
  const n = m.tasks, f = m.first_time;
  if (n === 1) return `1 result in ${into}${f ? ", the first time" : ""}`;
  return `${n} results in ${into}${f ? `, ${f} the first time` : ""}`;
}

/** *≈$46 of work at API prices in this project: not your bill*; "" with none. */
export function weekMoney(w) {
  const dollars = (usd) => `≈$${usd < 1 ? usd.toFixed(2) : Math.round(usd)}`;
  const mine = w.usd > 0 ? w.usd : 0;
  if (!mine) return "";
  if (pctOf(mine)) return `≈${pctOf(mine)} of work in this project: an estimate`;
  return `${dollars(mine)} of work at API prices in this project: not your bill`;
}

/** *12 results in dev, 10 the first time · ≈$3.84 a result*. */
export function weekResults(w) {
  if (!w.merged) return `No results in ${w.into || "dev"} in the last 7 days`;
  return `${resultsWords({ tasks: w.merged, first_time: w.first_time }, w.into || "dev")}${w.usd_per_merged != null ? ` · ≈${pctOf(w.usd_per_merged) || `$${w.usd_per_merged.toFixed(2)}`} a result` : ""}`;
}

/** *The week: 55 % left with 2 days to go: Low work starts by day*; "" with no week read (spec 44 §5). */
export function weekPace(w) {
  if (!w?.week) return "";
  const { left, rest, pace } = w.week;
  const days = Math.max(1, Math.ceil(rest * 7 - 1e-9));
  const does = { behind: "Low work waits until the week comes back" }[pace] || "";
  return `The week: ${Math.round(left * 100)} % left with ${days} ${days === 1 ? "day" : "days"} to go${does ? `: ${does}` : ""}`;
}

/** This week, over the pane. */
export function WeekView() {
  const [w, setW] = useState(null);
  useEffect(() => { ask("ideas.week_work").then((got) => { if (got) setW(got); }); logOpened("week", "this"); }, []);
  return html`<${Place} title="This week" foot=${html`<button type="button" class="ork-btn" onClick=${closePlace}>Close</button>`}>
    ${!w ? html`<p class="ok-tone-muted">Reading the week…</p>` : html`<div class="week">
      ${weekMoney(w) && html`<p class="week__usd">${weekMoney(w)}</p>`}
      <p class="week__results">${weekResults(w)}</p>
      ${weekPace(w) && html`<p class="week__pace">${weekPace(w)}</p>`}
      ${w.last_unused != null && html`<p class="week__unused">Last week ended with ${Math.round(w.last_unused * 100)} % unused</p>`}
    </div>`}
  <//>`;
}
