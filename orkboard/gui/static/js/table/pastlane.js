// The past deeper in the discard (docs/specs/156-one-pick-and-the-release-column.md D.5, decisions §261.9; before it the chronicle over the pane, spec 150 E2.2): under the goals done and not yet seen, in Release's lane, *Unreleased* and then **a deck a
// version**, newest first, through the open tab's eyes (`party` of every `ideas.chronicle*` command, spec 150 E1: none on the Orkmaster's, Release's and Live's tabs). A deck pressed deals its cards in place, pressed again gathers them (a version is read when it is
// first dealt: `ideas.chronicle_chapter`). A goal's card is **picked** (part B): the table shows it as it was; a decision's card opens its entry over the pane (chronicle.js). The past is looked at once the lane is scrolled to it: that party's newest decision is seen
// (pastseen.js) and the dot on its tab goes (pastdot.js). It decides nothing and writes nothing but that look; no count of what is in a deck. Layout only: lane.css, with orkUI's tokens.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { pick, picked } from "../frame/state.js";
import { town } from "../link.js";
import { Icon } from "../orkui.js";
import { Card, Deck, ask } from "./chronicleparts.js";
import { UNRELEASED, byDay, chapterName, dayWord, itemsOf } from "./chroniclewords.js";
import { openChronicle } from "./chronicle.js";
import { markSeen } from "./pastseen.js";

const withParty = (args, party) => (party ? { ...args, party } : args);

export { itemsOf, byDay };

/** How many cards a deck deals before *All · search* (the line's seven, decisions §277.5). */
export const DEAL = 7;

/** *All · search* pressed on a deck: the whole deck over the pane, with its search (pastdeck.js, spec 162 I). */
export const openDeck = (deck) => openChronicle({ deck: { id: deck.id, name: deck.name } });

export function PastDecks({ party = "", seeing = null }) {
  const [d, setD] = useState(null), [open, setOpen] = useState([]), [loaded, setLoaded] = useState({}), host = useRef();
  useEffect(() => {                                                       // the past of the open tab; read again when the tab changes
    let live = true;
    setD(null); setOpen([]); setLoaded({});
    ask("ideas.chronicle", withParty({}, party)).then(([r]) => { if (live) setD(r); });
    return () => { live = false; };
  }, [party]);
  const rev = town.value?.ideas_rev, empty = !!d && !(d.unreleased || (d.chapters || []).length);
  useEffect(() => {                                                       // a first open reads the past while the flags of the goals laid done are being raised (spec 162 J): an empty past is read again when the Board changes
    if (!empty) return undefined;
    let live = true;
    ask("ideas.chronicle", withParty({}, party)).then(([r]) => { if (live && r) setD(r); });
    return () => { live = false; };
  }, [rev, empty]);
  useEffect(() => {                                                       // scrolled to: the party's newest decision is seen
    const el = host.current, root = seeing?.current;
    if (!el || typeof IntersectionObserver !== "function") return undefined;
    const io = new IntersectionObserver((es) => { if (es.some((e) => e.isIntersecting)) markSeen(party); }, { root: root || null, threshold: 0.01 });
    io.observe(el);
    return () => io.disconnect();
  }, [party, !!d]);
  if (!d) return null;
  const decks = [...(d.unreleased ? [{ id: "unreleased", name: UNRELEASED }] : []), ...(d.chapters || []).map((c) => ({ id: c.id, name: chapterName(c), day: c.kind === "week" ? "" : dayWord(c.day) }))];
  if (!decks.length) return null;
  const full = (id) => (id === "unreleased" ? d.unreleased : loaded[id] || (d.chapters || []).find((c) => c.id === id && c.goals));
  const press = (x) => {
    const on = open.includes(x.id);
    setOpen(on ? open.filter((id) => id !== x.id) : [...open, x.id]);
    if (on || x.id === "unreleased" || full(x.id) || loaded[x.id] === false) return;
    setLoaded((l) => ({ ...l, [x.id]: false }));
    ask("ideas.chronicle_chapter", withParty({ id: x.id }, party)).then(([r]) => setLoaded((l) => ({ ...l, [x.id]: r || { goals: [], decisions: [] } })));
  };
  const open_ = (it) => (it.type === "goal" ? pick(it.id) : openChronicle({ decision: it.id }));
  return html`<section class="release-lane__past" ref=${host} aria-label="The past" data-past=${party || "orkmaster"}>
    ${decks.map((x) => html`<div key=${x.id} class="release-lane__deck" data-version=${x.id}>
      <${Deck} deck=${x} on=${open.includes(x.id)} onPress=${() => press(x)} />
      ${open.includes(x.id) && html`<${DealtDeck} x=${x} party=${party} items=${byDay(full(x.id))} lit=${picked.value} open_=${open_} />`}
    </div>`)}
  </section>`;
}

/** A deck dealt in place: its newest seven, and past seven an eighth card, *All · search*, in the line's face (cascade.js `table-lstrip--all`). */
function DealtDeck({ x, party, items, lit, open_ }) {
  const more = items.length > DEAL;
  return html`<ul class="release-lane__deal" data-deck=${x.id}>
    ${items.slice(0, DEAL).map((it) => html`<${Card} key=${`${it.type}/${it.id}`} item=${it} version=${x.name} lit=${it.type === "goal" && lit === it.id} onOpen=${open_} onDecision=${(n) => openChronicle({ decision: n })} />`)}
    ${more && html`<li class="release-lane__all"><button type="button" class="ork-card table-gstrip table-lstrip table-lstrip--all" data-deck-all=${x.id} aria-label=${`All of ${x.name}, with a search`} onClick=${() => openDeck(x)}><${Icon} name="search" /><span class="table-gstrip__nm">All · search</span></button></li>`}
  </ul>`;
}
