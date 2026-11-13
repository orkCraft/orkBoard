// A party's header (docs/specs/123-the-leaders-at-the-table.md §5, docs/specs/168 E1). **At the wide width** (760 px and up) a leader's tab with no goal picked has the header of small cards (leaderhead.js: *At work*, *Concerns*, *Ask*), held while the table scrolls, and the seats
// and tools it showed lie in the leader's inventory (stallseats.js) and the party's **…** is the pane's title's (partymenu.js). **At the narrow width** the header is what it was: one row of its squad on its lens — *Does* (orkUI's sword, the word, its AI tool's ink mark when
// the whole side runs on one tool) and its seats, *Checks* (the shield, the word, its tool) and its seats, the size in one word, then at the right the aspects its leader looks at (concerns.js `Aspects`) and the party's **…** (*Edit*, *Ask again*, *Remove party*). A seat is its head
// with its role under it (the caption face, muted, cut at 76 px), its own tool's mark only when it is not its side's, the busy mark while it works; pressed it opens its popover (seatpop.js: nothing only on hover). `Seat` is also the phone's (hand/upparty.js), which draws it as it
// did: the head and its tool's mark, no role under it.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";

import { Head, Sign, TIER_WORDS } from "../orkui.js";

import { MARKED, nameOf, wide, markSrc, sizeTip, sizeWord, squadOf, toolOf } from "./data.js";

import { SeatPop } from "./seatpop.js";

import { Menu } from "./menu.js";

import { Aspects } from "./concerns.js";

import { partyItems } from "./partymenu.js";

import { LeaderHead } from "./leaderhead.js";


const SIDE_SIGN = { build: "sword", check: "shield" };

/** The ink mark of a tool, when the tool has one. */
export const ToolMark = ({ id }) => (MARKED.includes(id) ? html`<img class="ork-mark" src=${markSrc(id)} srcset=${`${markSrc(id, true)} 2x`} alt="" draggable="false" />` : null);

/** A seat's head. In a header (`side` given: the id of the tool its whole side runs on, "" when the side's seats run on several) its role stands under it, its own tool's mark only when it is not the side's; the phone's (`side` undefined) is the head and its tool's mark. */
export function Seat({ g, m, open, onPress, side }) {
  const tool = toolOf(g, m), row = side !== undefined;
  const words = row ? `${m.name}, runs on ${tool.name}` : `${[m.name, TIER_WORDS[m.head?.tier]].filter(Boolean).join(", ")}, runs on ${tool.name}`;
  const busy = m.state === "work" && html`<span class="ork-busy" title="at work"></span>`;
  return html`<button type="button" class=${cls("table-seat", { "is-on": open, "is-work": m.state === "work", "is-needs": m.state === "needs", "has-role": row })} data-seat=${m.slug} data-band=${m.band}
    aria-haspopup="dialog" aria-expanded=${String(open)} aria-label=${words} title=${`${m.name} · ${tool.name}`} onClick=${onPress}>
    ${row
      ? html`<span class="table-seat__hw">${m.head && html`<${Head} race=${m.head.race} tier=${m.head.tier} />`}${tool.id !== side && html`<${ToolMark} id=${tool.id} />`}${busy}</span>
        <span class="table-seat__role">${m.name}</span>`
      : html`${m.head && html`<${Head} race=${m.head.race} tier=${m.head.tier} />`}<${ToolMark} id=${tool.id} />${busy}`}
  </button>`;
}

/** The AI tool a whole side runs on: `{id, name}`, or null when its seats run on more than one. */
function sideTool(g, seats) {
  const tools = seats.map((m) => toolOf(g, m));
  return tools.length && tools.every((t) => t.id === tools[0].id) ? tools[0] : null;
}

/** The party's squad: the groups of seats, each side's AI tool and a seat's popover. The narrow header draws it; at the wide width the leader's inventory does (stallseats.js). */
export function Squad({ g, from }) {
  const [seat, setSeat] = useState(""), squad = squadOf(g);
  return html`<div class="table-squad">${squad.map((x) => {
      const tool = sideTool(g, x.seats), said = tool ? `${x.word} on ${tool.name}` : x.word;
      return html`<div key=${x.band} class="table-group" role="group" aria-label=${x.word} data-band=${x.band}>
        <span class="table-side" title=${said} data-tool=${tool?.id || undefined}><${Sign} name=${SIDE_SIGN[x.band]} /><span class="table-side__w">${x.word}</span>${tool && html`<${ToolMark} id=${tool.id} />`}</span>
        <span class="table-seats">${x.seats.map((m) => html`<${Seat} key=${m.slug} g=${g} m=${m} side=${tool?.id || ""} open=${seat === m.slug} onPress=${() => setSeat(seat === m.slug ? "" : m.slug)} />`)}</span>
      </div>`;
    })}${seat && html`<${SeatPop} g=${g} slug=${seat} from=${from} onClose=${() => setSeat("")} />`}</div>`;
}

/** A leader's tab with no goal picked: at the wide width the header of small cards (leaderhead.js), at the narrow one the squad and its **…** as it was. */
export function Header({ g, from }) {
  if (wide.value) return html`<${LeaderHead} g=${g} from=${from} />`;
  const name = nameOf(g), size = sizeWord(g);
  return html`<section class="table-head" aria-label=${`${name}: its squad`} data-party=${g.slug}>
    <${Squad} g=${g} from=${from} />
    ${size && html`<span class="ork-chip table-size" title=${sizeTip(g)}>${size}</span>`}
    <span class="table-grow"></span>
    <${Aspects} g=${g} />
    <${Menu} label=${`${name}'s menu`} items=${partyItems(g, from)} />
  </section>`;
}
