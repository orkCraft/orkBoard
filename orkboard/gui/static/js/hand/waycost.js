// The cost of the way picked, for the opened card's foot (docs/specs/147-one-card-four-corners.md D.1, decisions §251.6): a question whose ways carry a price (`asked[].costs[i]`: `{usd_low, usd_high}`, from the host) is answered by picking a way and pressing *Answer*;
// the foot's bottom right shows the picked way's cost, and the card's own cost while no way with a price is picked. Nothing here is drawn: answers.js sets it, stopcard.js reads it.
import { signal } from "@preact/signals";
import { costOf } from "./cost.js";

/** The way picked on the opened card with this `key`: `{key, cost}` (`cost`: `costOf`'s, or null for a way without one). */
export const pickedWay = signal({ key: "", cost: null });

/** The cost of a way priced `{usd_low, usd_high}` as the cards say it (the gem and its words); null for a way without a price. */
export function wayCostOf(price) {
  const low = Number(price?.usd_low), high = Number(price?.usd_high ?? price?.usd_low);
  return Number.isFinite(low) && Number.isFinite(high) ? costOf({ kind: "plan", node: { plan_estimate: { usd_low: low, usd_high: high } } }) : null;
}

/** Picks the way (or, with `cost` null, the way without a price) on the card `key`. */
export const pickWay = (key, cost) => { pickedWay.value = { key, cost: cost || null }; };

/** Puts the pick away when the card is lowered or its answers are gone. */
export const clearWay = (key) => { if (pickedWay.value.key === key) pickedWay.value = { key: "", cost: null }; };

/** The cost the foot of the card `key` shows: the way picked when it has a price, else the card's own (`own`). */
export const footCost = (key, own) => (pickedWay.value.key === key && pickedWay.value.cost ? pickedWay.value.cost : own);
