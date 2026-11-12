// What a paid pass of a leader costs, said before it runs (docs/specs/171 Tech: *ideas.reply and ideas.ask_leader say their cost before the pass runs*): the host's
// read-only `ideas.ask_cost {}` (gui/ideas_mats.py: `{calls, usd_high}`, the most one pass is capped at under the Target) asked when a field opens, shown beside its *Send*,
// which waits for the answer. Both commands also send their seal (`sealed: true`): a paid pass goes only on it.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";

/** The words of a cost: *A paid pass: one call, up to $0.25*; a cost the host did not say is said so. */
export function costWords(c) {
  if (!c || typeof c.usd_high !== "number") return "A paid pass: its cost is not known yet";
  const calls = c.calls === 1 ? "one call" : `${c.calls} calls`;
  return `A paid pass: ${calls}, up to $${c.usd_high.toFixed(2)}`;
}

/** `[cost, words]`: the cost the host said (null until asked, `false` when it said none) and the line to show; `ready` once it has answered either way. */
export function useAskCost() {
  const [cost, setCost] = useState(null);
  useEffect(() => {
    let live = true;
    command("ideas.ask_cost", {}, true).then((r) => live && setCost(r || false)).catch(() => live && setCost(false));
    return () => { live = false; };
  }, []);
  return { ready: cost !== null, words: cost === null ? "" : costWords(cost || null) };
}

/** The line under a field: what the pass costs, before *Send*. */
export const AskCost = ({ words }) => html`<small class="cards-cost" data-ask-cost role="status">${words}</small>`;
