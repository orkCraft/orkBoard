// The gem and its words (docs/specs/98-the-table-and-the-hand.md §4.4, decisions §160.6): a card that spends carries orkUI's gem (`4%`, a share of the limits);
// lifted, its words say plainly what happens (*about 4% of Claude's week*). A card that spends nothing has none. What a card spends is what it starts again or
// sets going: a plan's *Start*, a failure's *Retry*, a plan change; a question, a pick, a to-do, a result and a sign-in cost nothing of their own.
// The shares come from spend.js (the host's learnt rate over the tool's window); with no rate learnt the gem says the price at API prices, as the old hand did.
import { html } from "../html.js";
import { town } from "../link.js";
import { pctRange, pctShort, rated, shareOf } from "../spend.js";
import { wayOf } from "./ways.js";

const num = (n, cents) => (cents ? Number(n).toFixed(2) : String(Math.round(n)));
const usdRange = (low, high) => {
  const [a, b] = [Math.abs(low), Math.abs(high)].sort((x, y) => x - y), cents = a < 1, from = num(a, cents), to = num(b, cents);
  return from === to ? `$${from}` : `$${from}–${to}`;
};

/** What the tool's window is called: the host's rate names it (`rate.window`); the share of a week where it says so, else the five-hour window it learnt. */
function windowWords() {
  const r = town.value?.rate;
  return r?.window === "week" ? "week" : "five-hour window";
}

/** The id of the tool whose share it is (`rate.tool`), Claude with none known. */
const toolId = () => town.value?.rate?.tool || "claude";

/** The tool whose share it is (`rate.tool`, named as the limits name it), Claude with none known. */
function toolName() {
  const id = toolId();
  return (town.value?.limits || []).find((l) => l.provider === id)?.name || id.charAt(0).toUpperCase() + id.slice(1);
}

/** What a share of the limits looks like on a gem: `4%`, `3–8%`, `<1%`; the price at API prices (`$1–3`) with no rate learnt; "" with no number. */
function gemOf(low, high) {
  if (!Number.isFinite(low) || !Number.isFinite(high) || (!low && !high)) return "";
  if (!rated()) return usdRange(low, high);
  if (low === high) return pctShort(low).replace(/\s+%$/, "%");
  return pctRange(low, high).replace(/\s*%\s*of 5h$/, "%");
}

/** Where a stop's price is: a plan's estimate, a plan change's range, a failed task's last cost. `{low, high, saves}` in dollars, null for a card that spends nothing. */
export function priceOf(s) {
  const registered = wayOf(s.kind);
  if (registered?.price) return registered.price(s);                         // a goal's way's card says its own price (spec 100: the route's)
  const n = s.node, row = s.row;
  if (s.kind === "plan") {
    const e = n?.plan_estimate || n?.estimate;
    return e && Number.isFinite(Number(e.usd_low)) ? { low: Number(e.usd_low), high: Number(e.usd_high ?? e.usd_low) } : null;
  }
  if (s.kind === "change" && row && (Number(row.usd_low) || Number(row.usd_high))) {
    return { low: Number(row.usd_low), high: Number(row.usd_high), saves: Number(row.usd_high) < 0 };
  }
  if (s.kind === "failed" && s.task && Number.isFinite(Number(s.task.cost)) && Number(s.task.cost) > 0) return { low: Number(s.task.cost), high: Number(s.task.cost) };
  return null;
}

/** `{gem, words, share, saves, tool, spend, taken}` of a stop that spends, null of one that does not. */
export function costOf(s) {
  const own = wayOf(s.kind)?.cost;                                         // a card paid by an API says its own price in dollars, never a share of a window (spec 105 §3)
  if (own) return own(s);
  const p = priceOf(s);
  if (!p) return null;
  const gem = gemOf(Math.min(p.low, p.high), Math.max(p.low, p.high));
  if (!gem) return null;
  const sign = p.saves ? "−" : p.low < 0 ? "−" : "";
  const words = rated() ? `about ${sign}${gem} of ${toolName()}'s ${windowWords()}` : `about ${sign}${gem} at API prices`;
  const high = Math.max(Math.abs(p.low), Math.abs(p.high));       // the mana's potion (mana.js) hatches this much of its tool's top: `spend` 0 to 1 of the window, `taken` as a gem says it
  const spend = rated() && !p.saves && p.low >= 0 ? Math.min(1, shareOf(high) / 100) : 0;
  return { gem: `${sign}${gem}`, words, share: rated(), saves: !!p.saves, tool: toolId(), spend, taken: spend ? pctShort(high).replace(/\s+%$/, "%") : "" };
}

/** The gem on a card: nothing for a card that spends nothing. */
export function Gem({ cost }) {
  if (!cost) return null;
  return html`<span class=${cost.share ? "ork-gem share" : "ork-gem"} data-cost=${cost.gem}>${cost.gem}</span>`;
}

/** The gem with its words, on the lifted card. */
export function Spend({ cost }) {
  if (!cost) return null;
  return html`<div class="hand-spend"><${Gem} cost=${cost} /><span class="hand-spend__words">${cost.words}</span></div>`;
}
