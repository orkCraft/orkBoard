// The past deeper in the discard (docs/specs/156-one-pick-and-the-release-column.md D.5, decisions §261.9; before it the chronicle over the pane, spec 150 E2.2): under the goals done and not yet seen, in Release's lane, *Unreleased* and then **a deck a
// version**, newest first, through the open tab's eyes (`party` of every `ideas.chronicle*` command, spec 150 E1: none on the Orkmaster's, Release's and Live's tabs). A deck pressed deals its cards in place, pressed again gathers them (a version is read when it is
// first dealt: `ideas.chronicle_chapter`). A goal's card is **picked** (part B): the table shows it as it was; a decision's card opens its entry over the pane (chronicle.js). The past is looked at once the lane is scrolled to it: that party's newest decision is seen
// (pastseen.js) and the dot on its tab goes (pastdot.js). It decides nothing and writes nothing but that look; no count of what is in a deck. Layout only: lane.css, with orkUI's tokens.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { pick, picked } from "../frame/state.js";
import { Card, Deck, ask } from "./chronicleparts.js";
import { UNRELEASED, chapterName, dayWord } from "./chroniclewords.js";
import { openChronicle } from "./chronicle.js";
import { markSeen } from "./pastseen.js";

const withParty = (args, party) => (party ? { ...args, party } : args);

/** The cards of a deck: its goals (a goal that went through the portal) and its decisions of no goal. */
export const itemsOf = (c) => [
  ...(c?.goals || []).map((g) => ({ type: "goal", id: g.idea, title: g.title, element: g.element, hue: g.hue, day: g.day, decision: g.decision, in: g.in })),
  ...(c?.decisions || []).map((d) => ({ type: "decision", id: d.number, title: d.title, element: "", hue: "", day: d.day, decision: 0, in: d.in })),
];

export function PastDecks({ party = "", seeing = null }) {
  const [d, setD] = useState(null), [open, setOpen] = useState([]), [loaded, setLoaded] = useState({}), host = useRef();
  useEffect(() => {                                                       // the past of the open tab; read again when the tab changes
    let live = true;
    setD(null); setOpen([]); setLoaded({});
    ask("ideas.chronicle", withParty({}, party)).then(([r]) => { if (live) setD(r); });
    return () => { live = false; };
  }, [party]);
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
      ${open.includes(x.id) && html`<ul class="release-lane__deal" data-deck=${x.id}>${itemsOf(full(x.id)).map((it) => html`<${Card} key=${`${it.type}/${it.id}`} item=${it} version=${x.name} lit=${it.type === "goal" && picked.value === it.id} onOpen=${open_} onDecision=${(n) => openChronicle({ decision: n })} />`)}</ul>`}
    </div>`)}
  </section>`;
}
