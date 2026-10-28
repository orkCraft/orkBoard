// The start card (docs/specs/100-a-goals-way-as-cards.md §1, part A; docs/specs/99-a-goals-way.md §4.6; decisions §136.2): the card a goal gets when its route grew after the person said Talk. Its face is the route
// card's (the route's sign, the Orkmaster's head, the new cost's gem); lifted it says the new cost with the old one beside it, struck, and one act, **Start** (`ideas.start {idea}`). The row is
// `{kind: "start", idea, cost, was}`: `cost` the cost now, `was` the cost the person was told. Shares routecard.js's helpers.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { act } from "../shell/store.js";
import { CostLine, orkHead } from "./routecard.js";
import { way } from "./ways.js";

const priceFrom = (c) => (c && Number.isFinite(Number(c.usd_low)) ? { low: Number(c.usd_low), high: Number(c.usd_high ?? c.usd_low) } : null);

/** The start card lifted: what was added, the new cost, the old one struck, **Start**. */
export function StartLifted({ s, close }) {
  const row = s.row || {}, [busy, setBusy] = useState(false);
  const start = async () => {
    setBusy(true);
    try { if (await act("ideas.start", { idea: row.idea })) close?.(); } finally { setBusy(false); }
  };
  return html`<div class="hand-way hand-way--start">
    <p class="body hand-way__words">${row.party_name ? `${row.party_name}’s step is planned and waits for your Start.` : s.text || "A step was added to the route."}</p>
    <${CostLine} cost=${row.cost} />
    ${row.was && html`<div class="hand-way__was"><span class="cap">Before</span><del class="hand-way__old" title="What you were told before"><${CostLine} cost=${row.was} /></del></div>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      <button type="button" class="ork-btn primary" disabled=${busy} title="The work goes on with the new route, at the new cost" onClick=${start}>Start</button>
    </div>
  </div>`;
}

way("start", { sign: "after", head: orkHead, price: (s) => priceFrom(s.row?.cost), Lifted: StartLifted });
