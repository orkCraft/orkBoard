// The Orkmaster's tab is the Board (docs/specs/98-the-table-and-the-hand.md §3.3, decisions §143): a column a party, each standing under its party's tab — the tabs take their columns' widths while the Board is
// shown, in the same order, and the Board has no header of its own (both read the one `--lanes` of table.css). A column's cards are its tasks at work (running, testing, picking, a failure), each with its member's
// head, its goal's element top left, its name up to four lines. The Orkmaster's own column, under its tab, holds what it does itself: a goal being read or routed, as a card with its crown. A column narrower than a
// card lays its tasks as tokens (spec 67), and a column a head wide at the narrow width does too: no sideways scroll. A goal picked: its tasks alone (§136.10).
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { picked } from "../frame/state.js";
import { cardsOf, nameOf, ownOf } from "./data.js";
import { OwnCard, TaskCard, Token } from "./card.js";

const CARD_W = 128;                                                 // a card; a lane narrower than this (with its gutters) lays tokens

/** Whether the first party's column is narrower than a card: the lanes' widths are the tabs' (table.css), measured here once they are laid out. */
function useTokens(host, narrow) {
  const [tokens, setTokens] = useState(narrow);
  useLayoutEffect(() => {
    const measure = () => {
      const lane = host.current?.querySelector(".table-lane[data-party]") || host.current?.querySelector(".table-lane--own");
      setTokens(narrow || (!!lane && lane.clientWidth < CARD_W + 16));
    };
    measure();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(measure) : null;
    if (host.current) ro?.observe(host.current);
    return () => ro?.disconnect();
  }, [narrow]);
  return tokens;
}

export function BoardMap({ parties, narrow }) {
  const host = useRef(), only = picked.value, tokens = useTokens(host, narrow);
  const own = ownOf(parties, only), columns = parties.map((g) => ({ g, cards: cardsOf(g, only) }));
  const none = !own.length && columns.every((c) => !c.cards.length);
  return html`<div class="table-board" ref=${host} data-tokens=${String(tokens)} data-picked=${only || undefined}>
    <div class="table-lane table-lane--own" role="group" aria-label="The Orkmaster">
      ${own.map(({ n }) => (tokens ? html`<${Token} key=${n.slug} n=${n} lit=${!!only} />` : html`<${OwnCard} key=${n.slug} n=${n} lit=${!!only} />`))}
    </div>
    ${columns.map(({ g, cards }) => html`<div key=${g.slug} class="table-lane" data-party=${g.slug} role="group" aria-label=${nameOf(g)}>
      ${cards.map(({ n, t }) => (tokens ? html`<${Token} key=${`${n.slug}/${t.id}`} n=${n} t=${t} lit=${!!only} />` : html`<${TaskCard} key=${`${n.slug}/${t.id}`} n=${n} t=${t} lit=${!!only} />`))}
    </div>`)}
    <div class="table-lane table-lane--free">${none && html`<p class="table-board__none">${only ? "Nothing of this goal is at work" : "Nothing is at work"}</p>`}</div>
  </div>`;
}
