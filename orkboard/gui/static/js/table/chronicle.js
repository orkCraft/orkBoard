// The past over the pane (docs/specs/150-the-table-its-edge-and-the-past-through-the-open-tab.md E2.2, decisions §254.7; docs/specs/134-release-keeps-the-chronicle.md part B, decisions §238.3–§238.4; mockup docs/mockups/table-edge/ section 5):
// the lich (and a step of the pyramid) opens it over the pane **through the open tab**: on a party's tab that craft's past, on the Orkmaster's the whole project's (`party` of every `ideas.chronicle*` command; none on the Orkmaster's). Its title says both axes
// (*The past · through Design · every version*, *· v0.3*), its search the whose (*Search Design's past…*). At its left **a deck a version** (*Unreleased* on top, then the versions newest first, or the weeks of a project with no version yet): a deck
// pressed deals its cards, none pressed, every version is dealt newest first, each card's version at its bottom right. A search dims the decks with no find and lights the cards found. A card pressed is lifted: a goal as it was, a decision with its *Changes*
// and *changed by*, and, on a party's tab, **Show on <party>'s table** (that tab, the goal it touched lit). The pane's ← goes back to the tab's table. It decides nothing and writes nothing but the party's last look (pyramid.js: the newest decision seen,
// per party, in this browser); every command it asks reads (`ideas.chronicle*`, gui/ideas_chronicle.py). Answers are keys and data; the words are said here (chroniclewords.js). Not on the phone (§238.6).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { drawn } from "../frame/kinds.js";
import { closeOver, openOver, openTab, over, picked, tab } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { mapName, partiesAll } from "./data.js";
import { Decision, GoalAsItWas } from "./chroniclerows.js";
import { Card, Deck, ask, whose } from "./chronicleparts.js";
import { UNRELEASED, chapterName, dayWord, pastSearch, pastTitle, showOn } from "./chroniclewords.js";
import { markSeen } from "./pastseen.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as mapkit.js links its own
  const href = new URL("./chronicle.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const FIND_WAIT = 250;
const through = (name) => name || "the Orkmaster";

/** Opens the past over the pane from where it is pressed (the lich, a step of the pyramid, a conflict's earlier decision), through the open tab. `props`: `{goal}` or `{decision}` to land on one, `{lit}` (a decision's number) to deal its deck with its card lit. */
export function openChronicle(props = {}) {
  const w = whose();
  openOver("chronicle", props, { title: mapName(tab.value, partiesAll()), key: "" }, pastTitle(through(w.name)));
}

const itemsOf = (c) => [
  ...(c.goals || []).map((g) => ({ type: "goal", id: g.idea, title: g.title, element: g.element, hue: g.hue, day: g.day, decision: g.decision, in: g.in })),
  ...(c.decisions || []).map((d) => ({ type: "decision", id: d.number, title: d.title, element: "", hue: "", day: d.day, decision: 0, in: d.in })),
];
const withParty = (args, party) => (party ? { ...args, party } : args);

function List({ party, name, lit, onOpen, onDecision, setTitle }) {
  const [d, setD] = useState(null), [err, setErr] = useState(""), [loaded, setLoaded] = useState({}), [deck, setDeck] = useState(""), [q, setQ] = useState(""), [f, setF] = useState(null), [chosen, setChosen] = useState(false);
  useEffect(() => {                                                     // the past of the open tab; read again when the tab changes
    let live = true;
    setD(null); setLoaded({}); setDeck(""); setF(null);
    ask("ideas.chronicle", withParty({}, party)).then(([r, e]) => { if (live) { setD(r); setErr(e); } });
    return () => { live = false; };
  }, [party]);
  useEffect(() => {
    const want = q.trim();
    if (!want) { setF(null); return undefined; }
    let live = true;
    const id = setTimeout(() => ask("ideas.chronicle_find", withParty({ query: want }, party)).then(([r, e]) => { if (live) { setF(r); setErr(e); } }), FIND_WAIT);
    return () => { live = false; clearTimeout(id); };
  }, [q, party]);
  const decks = d ? [...(d.unreleased ? [{ id: "unreleased", name: UNRELEASED, kind: "unreleased" }] : []), ...(d.chapters || []).map((c) => ({ id: c.id, name: chapterName(c), kind: c.kind, day: c.kind === "week" ? "" : dayWord(c.day) }))] : [];
  const full = (id) => (id === "unreleased" ? d?.unreleased : loaded[id] || (d?.chapters || []).find((c) => c.id === id && c.goals));
  const shown = deck ? decks.filter((x) => x.id === deck) : decks;
  useEffect(() => {                                                     // the decks that are dealt and not read yet: an older version is read when it is wanted
    if (!d) return undefined;
    let live = true;
    for (const x of shown) {
      if (x.id === "unreleased" || full(x.id) || loaded[x.id] === false) continue;
      setLoaded((l) => (x.id in l ? l : { ...l, [x.id]: false }));
      ask("ideas.chronicle_chapter", withParty({ id: x.id }, party)).then(([r, e]) => { if (!live) return; if (r) setLoaded((l) => ({ ...l, [x.id]: r })); else { setErr(e); setLoaded((l) => ({ ...l, [x.id]: { goals: [], decisions: [] } })); } });
    }
    return () => { live = false; };
  }, [d, deck]);
  const litIn = (it) => lit > 0 && ((it.type === "decision" && it.id === lit) || (it.type === "goal" && it.decision === lit));
  useEffect(() => {                                                     // a decision named to be lit: its deck is dealt once every deck is read
    if (!lit || chosen || !d || decks.some((x) => x.id !== "unreleased" && !full(x.id))) return;
    setChosen(true);
    const at = decks.find((x) => itemsOf(full(x.id) || { goals: [], decisions: [] }).some(litIn));
    if (at) setDeck(at.id);
  }, [d, loaded]);
  const name_ = deck ? decks.find((x) => x.id === deck)?.name || "" : "";
  useEffect(() => { setTitle(name_); }, [name_, name]);
  const finds = f && q.trim() ? [...(f.unreleased && (f.unreleased.goals?.length || f.unreleased.decisions?.length) ? [{ id: "unreleased", name: UNRELEASED, ...f.unreleased }] : []), ...(f.chapters || []).map((c) => ({ ...c, name: chapterName(c) }))] : null;
  const hit = new Set((finds || []).map((c) => c.id));
  const press = (x) => setDeck((now) => (now === x.id ? "" : x.id));
  return html`<div class="chr" data-lit=${lit || undefined}>
    <div class="chr-search"><${Icon} name="search" /><input type="search" class="ork-field" aria-label=${pastSearch(name)} placeholder=${pastSearch(name)} value=${q} onInput=${(e) => setQ(e.currentTarget.value)} /></div>
    ${err && html`<p class="chr-err" role="alert">${err}</p>`}
    ${d && html`<div class="chr-table">
      <div class="chr-decks" role="group" aria-label="Versions">${decks.map((x) => html`<${Deck} key=${x.id} deck=${x.id === "unreleased" ? { ...x, day: (d.unreleased ? itemsOf(d.unreleased).length : 0) + " in dev" } : x} on=${deck === x.id} dim=${!!finds && !hit.has(x.id)} onPress=${() => press(x)} />`)}</div>
      ${finds
        ? (finds.length ? html`<ul class="chr-deal" data-finds=${f.found}>${finds.flatMap((c) => itemsOf(c).map((it) => html`<${Card} key=${`${c.id}/${it.type}/${it.id}`} item=${it} version=${c.name} found=${true} lit=${true} onOpen=${onOpen} onDecision=${onDecision} />`))}</ul>
            ${f.more > 0 && html`<p class="table-over__muted">${f.more} more match. Add a word to narrow it.</p>`}`
          : html`<p class="table-over__muted" data-finds="none">Nothing in the past matches.</p>`)
        : html`<ul class=${cls("chr-deal", { "is-one": !!deck })} data-deck=${deck || "all"}>${shown.flatMap((x) => itemsOf(full(x.id) || { goals: [], decisions: [] }).map((it) => html`<${Card} key=${`${x.id}/${it.type}/${it.id}`} item=${it} version=${x.name} lit=${litIn(it)} onOpen=${onOpen} onDecision=${onDecision} />`))}
          ${!decks.length && html`<li class="table-over__muted" data-chronicle="empty">Nothing has gone through the portal yet.</li>`}</ul>`}
    </div>`}
  </div>`;
}

/** The face of kind `chronicle`: the deal, or a goal as it was, or a decision. A press inside walks on and the quiet button above walks back to the deal; the pane's ← leaves for the tab's table. */
export function Chronicle({ props }) {
  const w = whose(), [view, setView] = useState(props?.goal ? { goal: props.goal } : props?.decision ? { decision: props.decision } : null);
  const goal = (idea) => setView({ goal: idea }), decision = (number) => setView({ decision: number });
  useEffect(() => { markSeen(w.party); }, [w.party]);                        // the party's past is looked at: its newest decision is seen (the pyramid's mark goes)
  const setTitle = (deck) => { const o = over.peek(); if (o?.kind === "chronicle") over.value = { ...o, title: pastTitle(through(w.name), deck) }; };
  const show = w.party ? (slug) => html`<p class="chr-show"><button type="button" class="ork-btn" data-show-on=${w.party} onClick=${() => {
    closeOver();                                                        // to the table of the tab, the goal it touched lit
    openTab(w.party);
    if (slug && (mapData.value?.nodes || []).some((n) => n.slug === slug)) picked.value = slug;
  }}>${showOn(w.name)}</button></p>` : null;
  return html`<div class="table-over__chronicle" data-view=${!view ? "list" : view.goal ? "goal" : "decision"} data-party=${w.party || undefined}>
    ${view && html`<p class="chr-back"><button type="button" class="ork-btn quiet" onClick=${() => { setView(null); setTitle(""); }}><${Icon} name="arrow-left" /> The past</button></p>`}
    <div class="chr-deal-host" hidden=${!!view}><${List} key=${w.party} party=${w.party} name=${w.name} lit=${Number(props?.lit) || 0} onOpen=${(it) => (it.type === "goal" ? goal(it.id) : decision(it.id))} onDecision=${decision} setTitle=${setTitle} /></div>
    ${!view ? null
      : view.goal ? html`<${GoalAsItWas} key=${view.goal} idea=${view.goal} onDecision=${decision} show=${show} />`
      : html`<${Decision} key=${view.decision} number=${view.decision} onDecision=${decision} onGoal=${goal} show=${show} />`}
  </div>`;
}

drawn("chronicle", Chronicle);
