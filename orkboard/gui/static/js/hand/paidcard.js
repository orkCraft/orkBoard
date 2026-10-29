// The Orkmaster's *Go on paid?* (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §3; decisions §177.3): every subscription is out, and a tool turned on is billed by its API. The row is
// `{kind: "paid", tool, name, until, usd_task, text}` (realm/paid.py; `until` the soonest reset, a local ISO time; `usd_task` about what a task of that tool costs, or null). A row of no goal's: arenawords.js
// `paidStopsOf` makes its stop, under the first lane (data.js `laneOf`). Its face is the hand's card (stopcard.js): the alert sign in the window (orkUI has no coins sign among its signs), the Orkmaster's
// crowned head as its asker, *Go on paid?* as its name, the price (*$0.40*) as its gem, *Holds until the next reset* at its foot. Lifted: what it asks in words, and two answers, **Go on, paid**
// (`ideas.paid {yes: true}`: the work goes on with that tool until the reset) and **Wait for Thu 18:00** (`ideas.paid {yes: false}`: not asked again before it). Nothing is run by a tool paid by its API without the yes.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { act } from "../shell/store.js";
import { paidWords, untilWords } from "../arena/arenawords.js";
import { orkHead } from "./routecard.js";
import { way } from "./ways.js";

/** *$0.40* of a task's cost; null while it is not known (the card then says so in its words and has no gem). */
export const priceWords = (row) => (row?.usd_task != null && Number.isFinite(Number(row.usd_task)) ? `$${Number(row.usd_task).toFixed(2)}` : "");

/** The second answer: *Wait for Thu 18:00*, or *Wait* while no reset is known. */
export const waitWords = (row) => { const at = untilWords(row?.until); return at ? `Wait for ${at}` : "Wait"; };

/** The lifted card of *Go on paid?*: its words and its two answers. */
export function PaidLifted({ s, close }) {
  const row = s.row || {}, [busy, setBusy] = useState(false);
  const answer = async (yes) => {
    setBusy(true);
    try { if (await act("ideas.paid", { yes })) close?.(); } finally { setBusy(false); }
  };
  return html`<div class="hand-way hand-way--paid">
    <p class="body hand-way__words">${paidWords(row)}</p>
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      <button type="button" class="ork-btn primary" disabled=${busy} data-answer="yes"
        title=${`${row.name || "The tool"} is billed by its API: it is paid per task. The yes holds until the next reset`} onClick=${() => answer(true)}>Go on, paid</button>
      <button type="button" class="ork-btn quiet" disabled=${busy} data-answer="wait"
        title="Nothing is spent: the work waits, and the Orkmaster does not ask again before the reset" onClick=${() => answer(false)}>${waitWords(row)}</button>
    </div>
  </div>`;
}

/** The gem: the price in dollars, as the tool's API bills it (never a share of a window); none while the cost is not known. */
const costOf = (s) => {
  const gem = priceWords(s.row);
  return gem ? { gem, words: `about ${gem} a task, paid by ${s.row.name || "its tool"}’s API`, share: false, saves: false, tool: s.row.tool || "", spend: 0, taken: "" } : null;
};

way("paid", { sign: "alert", head: orkHead, foot: () => "Holds until the next reset", price: () => null, cost: costOf, Lifted: PaidLifted });
