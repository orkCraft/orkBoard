// A party's **…** menu (docs/specs/168 E1, decisions §283.16.2): *Edit* (the one place of the parties, opened at this party: parties.js), *Seats and tools* (the leader's inventory, where its seats and tools lie: stallseats.js; the wide window only: the narrow page keeps them in its
// header), *Ask again* (its leader looks at the map again, concerns.js `askAgain`; only for a party with a map whose host has answered with a look) and *Remove party* (the question over the pane). The pane's title draws it at the wide width, the narrow header (header.js) at the narrow one.
import { openOver, openInventory } from "../frame/state.js";
import { GENERAL, nameOf } from "./data.js";
import { openParties } from "./parties.js";
import { askAgain, hasMap, lookOf, recordOf, theLeader } from "./concerns.js";

/** The menu's items for party `g`, as menu.js has them; `from`: where the thing opened comes from `{title, key}`; `seats`: whether *Seats and tools* is offered. */
export function partyItems(g, from, seats = false) {
  const name = nameOf(g);
  const again = hasMap(g) && recordOf(g.slug) ? [["Ask again", () => askAgain(g.slug), false, "", `${theLeader(g.leader?.name)} looks at the table again`, lookOf(g.slug).status === "looking"]] : [];
  return [["Edit", () => openParties({ party: g.slug }, from)],
    ...(seats ? [["Seats and tools", () => openInventory(g.slug), false, "", "Its seats, their AI tools and the party's size, in its inventory"]] : []),
    ...again,
    ...(g.slug === GENERAL ? [] : [["Remove party", () => openOver("party", { slug: g.slug, remove: true }, from, `Remove ${name}`), true]])];
}
