// A whole deck of the past over the pane, with its search (docs/specs/162-the-past-from-history-on-the-parties-tables.md I, decisions §277.5): *All · search* on a deck of more than seven (pastlane.js) opens kind `chronicle` with `{deck: {id, name}}`, titled
// the deck's name through the open tab. The deck's cards are listed whole, by day, newest first as the lane deals them; the search field is focused, and what is typed narrows the deck to the cards it is in (`ideas.chronicle_find` with the deck's id and the
// tab's party; every word must be in a card). A goal's card closes the view and picks the goal (the table shows it as it was: pastgoal.js); a decision's card opens its entry (chronicle.js). Esc and ← give the lane back with focus on the card that opened it.
// It decides nothing and writes nothing. Layout only: chronicle.css, with orkUI's tokens.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { closeOver, over, pick } from "../frame/state.js";
import { Card, ask, whose } from "./chronicleparts.js";
import { byDay } from "./chroniclewords.js";
import { openChronicle } from "./chronicle.js";

const withParty = (args, party) => (party ? { ...args, party } : args);

/** What a search found in the one deck, as the deck's own shape: `{goals, decisions}` (found cards say where the words are, not their day). */
const foundIn = (r, id) => (id === "unreleased" ? r.unreleased : (r.chapters || []).find((c) => c.id === id)) || { goals: [], decisions: [] };

export function PastDeck({ deck }) {
  const { party } = whose(), [all, setAll] = useState(null), [query, setQuery] = useState(""), [found, setFound] = useState(null), [err, setErr] = useState(""), field = useRef();
  useEffect(() => { field.current?.focus(); }, []);
  useEffect(() => () => {                                                                       // gone with nothing else opened (← or Esc): the lane is back, focus on the card that opened it
    setTimeout(() => { if (!over.peek()) document.querySelector(`[data-deck-all="${CSS.escape(deck.id)}"]`)?.focus(); }, 0);
  }, []);
  useEffect(() => {                                                                             // the whole deck, read once
    let live = true;
    const read = deck.id === "unreleased" ? ask("ideas.chronicle", withParty({}, party)).then(([r, e]) => [r && (r.unreleased || { goals: [], decisions: [] }), e])
      : ask("ideas.chronicle_chapter", withParty({ id: deck.id }, party));
    read.then(([r, e]) => { if (live) { setAll(r || { goals: [], decisions: [] }); setErr(r ? "" : e); } });
    return () => { live = false; };
  }, [deck.id, party]);
  const words = query.trim();
  useEffect(() => {                                                                             // the words asked of the host, a breath after the last key
    if (!words) { setFound(null); return undefined; }
    let live = true;
    const t = setTimeout(() => ask("ideas.chronicle_find", withParty({ query: words, id: deck.id }, party)).then(([r, e]) => { if (live) { setFound(r ? { ...foundIn(r, deck.id), more: r.more || 0 } : { goals: [], decisions: [], more: 0 }); setErr(r ? "" : e); } }), 180);
    return () => { live = false; clearTimeout(t); };
  }, [words, deck.id, party]);
  const shown = words ? found : all, items = shown ? byDay(shown) : [];
  const open = (it) => { if (it.type === "goal") { closeOver(); pick(it.id); } else openChronicle({ decision: it.id }); };
  const keys = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeOver(); } };
  return html`<div class="table-over__chronicle chr-deck-all" data-deck-all-view=${deck.id}>
    <div class="chr-search"><input ref=${field} type="search" class="ork-field" value=${query} placeholder="Search this deck" aria-label=${`Search ${deck.name}`} autocomplete="off" onInput=${(e) => setQuery(e.target.value)} onKeyDown=${keys} /></div>
    ${err && html`<p class="chr-err" role="alert">${err}</p>`}
    ${!err && !shown && html`<p class="chr-none">Reading the past…</p>`}
    ${shown && !items.length && !err && html`<p class="chr-none" role="status">${words ? `Nothing in ${deck.name} has those words.` : `${deck.name} holds nothing.`}</p>`}
    ${items.length > 0 && html`<ul class="chr-deal" aria-label=${deck.name}>
      ${items.map((it) => html`<${Card} key=${`${it.type}/${it.id}`} item=${it} version=${deck.name} found=${!!words} onOpen=${open} onDecision=${(n) => openChronicle({ decision: n })} />`)}
    </ul>`}
    ${words && found?.more > 0 && html`<p class="chr-none">More cards have these words: add a word to narrow them.</p>`}
  </div>`;
}
