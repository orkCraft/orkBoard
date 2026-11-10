// The inventory's state (docs/specs/157 D, decisions §267.1; spec 168 H1, §283.30): what `ideas.stall {chair}` says, the way hovered in the hand, the receipt and Undo on the table's line. The call `ideas.stall_take`
// writes a slot; it answers `{stall, undo: {slot, value}}`, and Undo is a take of the old value. The page never makes a price: it draws what the host sent. A slot's *Default* is a way of its own (`default: true` on the ware), taken as any.
import { signal } from "@preact/signals";
import { ask } from "../board/store.js";
import { refreshShell } from "../shell/store.js";
import { town } from "../link.js";
import { hatched } from "../hand/state.js";
import { dealt } from "../frame/state.js";

export const makerPlate = signal("");        // a cap-stopped pick opens this maker
export const stall = signal(null);          // the host's answer for the chair open: {chair, whose, say, shelves, hand}
export const hover = signal(null);          // {slot, id}: the ware under the pointer or the focus
export const receipt = signal(null);        // {text, undo: {slot, value} | null}: the line under the table
export const pleased = signal(0);           // bumped by a take: the narrow page's merchant is pleased for a moment

let wanted = "";
/** The stall of a chair, read again (the chair, or the board's own change). */
export async function load(chair) {
  wanted = chair;
  const got = await ask("ideas.stall", { chair });
  if (wanted !== chair) return;                                           // another chair was asked for meanwhile
  stall.value = got && got.shelves ? got : null;
}

export const wareOf = (slot, id) => stall.value?.shelves.flatMap((s) => s.wares.map((w) => ({ ...w, slot: s.slot, shelf: s }))).find((w) => w.slot === slot && w.id === id) || null;
export const shelfOf = (slot) => stall.value?.shelves.find((x) => x.slot === slot) || null;
export const cardOf = (slot) => stall.value?.hand.find((c) => c.slot === slot) || null;

/** The words after a take: *Sits in your hand*, what is carried now. */
const said = (slot, was) => {
  const now = cardOf(slot);
  return now ? `${now.label}: ${now.word}${was && was !== now.word ? ` (it was ${was})` : ""}.` : "";
};

function settle(chair, slot, was, got, back = false) {
  if (!got || !got.stall) return false;
  stall.value = got.stall;
  const text = slot === "craft_tools" ? "Maker cap saved." : back ? `${cardOf(slot)?.label || slot} is back to its default. ${said(slot, was)}` : said(slot, was);
  receipt.value = { text, undo: got.undo || null, back };
  pleased.value += 1;
  return true;
}

/** A ware pressed: it is taken. `chair` the chair open. Resolves with whether it was written. */
export async function take(chair, slot, value, cap = undefined) {
  const was = cardOf(slot)?.word || "";
  const got = await ask("ideas.stall_take", { chair, slot, value, ...(cap ? { cap } : {}) });
  const ok = settle(chair, slot, was, got);
  if (ok) refreshShell();
  return ok;
}

/** Undo: a take of the value the slot had. */
export async function undo(chair) {
  const u = receipt.peek()?.undo;
  if (!u) return false;
  const got = await ask("ideas.stall_take", { chair, slot: u.slot, value: u.value });
  if (!got || !got.stall) return false;
  stall.value = got.stall;
  receipt.value = null;
  refreshShell();
  return true;
}

/** The share a hovered ware would take from the first potion: drawn on the mana's own hatching (hand/mana.js reads `hatched`); a word, a saving or money hatches nothing. */
export function spendOf(price) {
  const n = price && Number.isFinite(price.share) ? price.share : 0;
  return n > 0 ? { tool: town.value?.rate?.tool || "claude", spend: Math.min(1, n / 100), taken: `${n}%` } : null;
}
export function pointAt(slot, id, price) { hover.value = slot ? { slot, id } : null; hatched.value = slot ? spendOf(price) : null; }

/** The inventory is shut: nothing of it stays lit. */
export function reset() { stall.value = null; hover.value = null; receipt.value = null; hatched.value = null; dealt.value = ""; }
