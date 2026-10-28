// A party's header (docs/specs/98-the-table-and-the-hand.md §3.4, docs/specs/95-the-window-as-decided.md §2.5): its name, its squad's heads grouped *Leads* | *Does* | *Checks* (at most seven), each head with its AI
// tool's mark in ink beside it and its tier in the gear on its head (the leader its race's higher form), and its size in one word. A head pressed opens its popover (seatpop.js: nothing only on hover). The party's
// **…** has *Edit* (today's form over the pane) and *Remove party* (today's question over the pane). Another party than Tech has no map yet, so its tab is this header alone.
import { useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, TIER_WORDS, RACE_WORDS } from "../orkui.js";
import { openOver } from "../frame/state.js";
import { GENERAL, MARKED, groupsOf, nameOf, markSrc, sizeTip, sizeWord, toolOf } from "./data.js";
import { SeatPop } from "./seatpop.js";
import { Menu } from "./menu.js";

function Seat({ g, m, open, onPress }) {
  const tool = toolOf(g, m), words = `${m.name}, ${TIER_WORDS[m.head?.tier] || ""} ${RACE_WORDS[m.head?.race] || ""}`.replace(/\s+/g, " ").trim();
  return html`<button type="button" class=${cls("table-seat", { "is-on": open, "is-work": m.state === "work", "is-needs": m.state === "needs" })} data-seat=${m.slug} data-band=${m.band}
    aria-haspopup="dialog" aria-expanded=${String(open)} aria-label=${`${words}, runs on ${tool.name}`} title=${`${m.name} · ${tool.name}`} onClick=${onPress}>
    ${m.head && html`<${Head} race=${m.head.race} tier=${m.head.tier} />`}
    ${MARKED.includes(tool.id) && html`<img class="ork-mark" src=${markSrc(tool.id)} srcset=${`${markSrc(tool.id, true)} 2x`} alt="" draggable="false" />`}
    ${m.state === "work" && html`<span class="ork-busy" title="at work"></span>`}
  </button>`;
}

export function Header({ g, from }) {
  const [seat, setSeat] = useState(""), box = useRef();
  const groups = groupsOf(g), size = sizeWord(g), name = nameOf(g);
  const edit = () => openOver("party", { slug: g.slug }, from, `Edit ${name}`);
  const remove = () => openOver("party", { slug: g.slug, remove: true }, from, `Remove ${name}`);
  const items = [["Edit", edit], ...(g.slug === GENERAL ? [] : [["Remove party", remove, true]])];
  return html`<section class="table-head" aria-label=${`${name}: its squad`} data-party=${g.slug} ref=${box}>
    <h2 class="ork-head table-head__name" title=${g.title}>${name}</h2>
    <div class="table-squad">${groups.map((x) => html`<div key=${x.band} class="table-group" role="group" aria-label=${x.word} data-band=${x.band}>
      <span class="ork-label">${x.word}</span>
      <span class="table-seats">${x.seats.map((m) => html`<${Seat} key=${m.slug} g=${g} m=${m} open=${seat === m.slug} onPress=${() => setSeat(seat === m.slug ? "" : m.slug)} />`)}</span>
    </div>`)}</div>
    ${size && html`<span class="ork-chip table-size" title=${sizeTip(g)}>${size}</span>`}
    <span class="table-grow"></span>
    <${Menu} label=${`${name}'s menu`} items=${items} />
    ${seat && html`<${SeatPop} g=${g} slug=${seat} from=${from} onClose=${() => setSeat("")} />`}
  </section>`;
}
