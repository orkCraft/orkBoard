// What the hand remembers while it is open (docs/specs/98-the-table-and-the-hand.md §4): the + card grown into the field (its text and pictures kept when it
// closes). The seam with the window is frame/state.js (`tab`, `picked`, `over`, `lifted`): the hand reads and writes those, and
// keeps the rest here. A lifted card of the hand has the key `hand:<stop key>` in `lifted`; the table's cards have their own.
import { signal } from "@preact/signals";
import { ORKMASTER } from "../frame/state.js";

export const fieldOpen = signal(false);        // the + card has grown into the field
export const fieldText = signal("");           // what was written, kept when the field closes (Esc, a press away)
export const fieldPhotos = signal([]);         // the pictures pasted, as data URLs (board/pictures.js `shrink`)
export const fieldType = signal(null);        // the goal type taken with @ (mention.js): {id, name, sign, party}; sent as `type` while the goal is addressed to that party
export const fieldOff = signal("");            // the tab whose address the person took off (*→ Tech ×*): the goal is then general

export const HAND = "hand:";
export const liftKey = (stopKey) => `${HAND}${stopKey}`;
export const stopKeyOf = (lifted) => (String(lifted || "").startsWith(HAND) ? lifted.slice(HAND.length) : "");

/** Where a goal written in the field goes: the party named with *@Tech* in the text, else the party whose tab is open (unless the person took it off), else
 *  none: the Orkmaster routes it by code (`ideas.add` with no party). `parties`: [{slug, name}]. Returns {party, name, by: "text" | "tab" | ""}. */
export function addressOf(text, tab, off, parties) {
  const lower = String(text || "").toLowerCase();
  const named = [...parties].sort((a, b) => b.name.length - a.name.length).find((p) => {
    const at = lower.indexOf(`@${p.name.toLowerCase()}`);
    return at >= 0 && (at === 0 || /\s/.test(lower[at - 1])) && !/[\w-]/.test(lower[at + 1 + p.name.length] || "");
  });
  if (named) return { party: named.slug, name: named.name, by: "text" };
  const open = parties.find((p) => p.slug === tab);
  if (open && tab !== ORKMASTER && off !== tab) return { party: open.slug, name: open.name, by: "tab" };
  return { party: "", name: "", by: "" };
}

/** The text without the *@Tech* that addressed it. */
export function withoutAddress(text, name) {
  if (!name) return String(text || "").trim();
  const re = new RegExp(`(^|\\s)@${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}(?![\\w-])`, "i");
  return String(text || "").replace(re, "$1").replace(/[ \t]{2,}/g, " ").trim();
}
