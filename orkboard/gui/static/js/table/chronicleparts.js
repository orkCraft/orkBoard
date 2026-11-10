// What the past (chronicle.js, history.js) is drawn of: a call to the host and the open tab's party (docs/specs/150 E2.2, decisions §254.7; docs/specs/134 part B). A goal that went through the portal is a card (its rune, the sign `check`, its name,
// its day, the version it went out in at its bottom right); a decision of no goal is a card of its own (the sign `page`, *§<n>*); the decision a goal carries is a small link beside its card (§238.4: it does not stand in the deal twice).
// A card is pressed to be lifted: the goal as it was or the decision's entry (chroniclerows.js). Colours and corners are orkUI's (chronicle.css).
import { command } from "../link.js";
import { ORKMASTER, tab } from "../frame/state.js";
import { nameOf, partiesAll } from "./data.js";

export const COULD_NOT = "The past could not be read";

/** One call to the host, its refusal in words: `[data, err]`. */
export async function ask(name, args) {
  try {
    const r = await command(name, args, true);
    return r && !r.error ? [r, ""] : [null, r?.error || COULD_NOT];
  } catch (e) { return [null, e?.message && e.message !== "offline" ? e.message : COULD_NOT]; }
}

/** The past is read through the open tab: `{party, name}`, the party's slug and its name (*Design*), both "" on the Orkmaster's tab. Read in a component, it follows the tab. */
export function whose() {
  const t = tab.value, g = t && t !== ORKMASTER ? partiesAll().find((x) => x.slug === t) : null;
  return g ? { party: g.slug, name: nameOf(g) } : { party: "", name: "" };
}
