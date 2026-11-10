// The history (docs/specs/168-the-window-played-as-a-card-games-table.md G3, decisions §283.16.14–15, §283.28, §285.3): what the book at the hand's right end (hand/book.js) opens over the pane. **A grid of goal cards that scrolls, a row a day**, a day's many cards
// as a cascade lying across (each card half over the one before it, so the row never grows past the pane); the goal's cards are the small face-up card, 56 x 78 (smallcard.js: the row of a day holds about a dozen side by side at 1366 x 768, a cascade past them, and a card
// hovered or focused is shown at 144 x 202 beside it, preview.js). **Dated by** *agreed* (the default), *done* or *in main*, a switch in the header (`ideas.history` gives each goal its three days: realm/history_day.py `dates`); a goal that lacks the chosen day lies in the last
// row, *No date*. **A version's plate** stands on the day it was released (the tags or the changelog: realm/chronicle_versions.py). **A search** over the titles, the gists and the decisions (`ideas.chronicle_find`): the cards found are lit and the rest dim. Read **through the
// open tab's eyes**: the Orkmaster's tab the whole project, a leader's the goals its party worked on (`party` of the commands). A card pressed puts the history away and picks the goal: the table shows its result (goalview.js; a goal of the past as it was: pastgoal.js).
// It decides nothing and writes nothing but the party's last look at the past (pastseen.js). Layout only: history.css, with orkUI's tokens. Not on the narrow page or the phone.
import { useEffect, useMemo, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { closeOver, openOver, pick, picked, tab } from "../frame/state.js";
import { drawn } from "../frame/kinds.js";
import { town } from "../link.js";
import { mapName, partiesAll } from "./data.js";
import { ask, whose } from "./chronicleparts.js";
import { dayWord } from "./chroniclewords.js";
import { markSeen } from "./pastseen.js";
import { SmallCard } from "./smallcard.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as chronicle.js links its own
  const href = new URL("./history.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const WAYS = [["agreed", "agreed"], ["done", "done"], ["main", "in main"]];     // the three days a goal is dated by; the first is the default
export const NO_DATE = "No date";
export const SEARCH = "Search the history";

const withParty = (args, party) => (party ? { ...args, party } : args);
const yearOf = (day) => (/^(\d{4})/.exec(day || "") || [])[1] || "";

/** The rows of the grid: the goals grouped by the day they are dated by (`by`), newest day first, the version plates on their days, and the goals without that day in a last row. */
export function rowsOf(goals, versions, by) {
  const days = new Map(), none = [];
  for (const g of goals) {
    const d = g.dates?.[by] || "";
    if (!d) none.push(g);
    else days.set(d, [...(days.get(d) || []), g]);
  }
  const all = [...days.keys()].sort(), lo = all[0], hi = all.at(-1);
  for (const v of versions || []) if (lo && v.day >= lo && v.day <= hi && !days.has(v.day)) days.set(v.day, []);
  const rows = [...days.keys()].sort().reverse().map((day) => ({ day, goals: days.get(day), plates: (versions || []).filter((v) => v.day === day) }));
  return none.length ? [...rows, { day: "", goals: none, plates: [] }] : rows;
}

/** The title of the history over the pane: *History*, and *History · through Design* on a leader's tab. */
export const historyTitle = (through) => `History${through ? ` · through ${through}` : ""}`;

/** Opens the history over the pane (the book's press), through the open tab. */
export function openHistory() {
  openOver("history", {}, { title: mapName(tab.value, partiesAll()), key: "" }, historyTitle(whose().name));
}

function Row({ row, lit, dim, newest, onPress }) {
  const n = row.goals.length, year = yearOf(row.day), word = row.day ? dayWord(row.day) : NO_DATE;
  const cols = n > 1 ? `repeat(${n - 1}, minmax(10px, 62px)) 56px` : "56px";                // the last card whole, the ones before it as far apart as the row allows: past that they lie across each other
  return html`<li class="hist-row" data-day=${row.day || "none"}>
    <div class="hist-day"><b class="hist-day__nm" title=${row.day || undefined}>${word}</b>${row.day && year && year !== newest ? html`<small class="hist-day__yr">${year}</small>` : null}
      ${row.plates.map((v) => html`<span key=${v.id} class="ork-plaque hist-plate" data-version=${v.id}>${v.name}</span>`)}</div>
    ${n > 0 && html`<ul class="hist-cards" style=${`grid-template-columns:${cols}`} data-count=${n}>
      ${row.goals.map((g) => html`<li key=${g.idea} class=${cls("hist-card", { "is-lit": lit(g), "is-dim": dim(g) })} data-lit=${lit(g) ? "1" : undefined}>
        <${SmallCard} n=${{ slug: g.idea, title: g.title, element: g.element, hue: g.hue }} parties=${g.party ? [g.party] : []} done=${g.party ? [g.party] : []} onPress=${() => onPress(g)} />
      </li>`)}
    </ul>`}
  </li>`;
}

export function History() {
  const { party } = whose(), [d, setD] = useState(null), [err, setErr] = useState(""), [by, setBy] = useState(WAYS[0][0]), [query, setQuery] = useState(""), [found, setFound] = useState(null), field = useRef();
  useEffect(() => { field.current?.focus(); }, []);
  useEffect(() => { markSeen(party); }, [party]);                                                   // the past is looked at: the party's newest decision is seen
  useEffect(() => {
    let live = true;
    setD(null); setErr("");
    ask("ideas.history", withParty({}, party)).then(([r, e]) => { if (live) { setD(r); setErr(r ? "" : e); } });
    return () => { live = false; };
  }, [party]);
  const rev = town.value?.ideas_rev, empty = !!d && !d.goals?.length;
  useEffect(() => {                                                                                  // a first open reads the past while the flags of the goals laid done are being raised (spec 162 J): an empty history is read again when the Board changes
    if (!empty) return undefined;
    let live = true;
    ask("ideas.history", withParty({}, party)).then(([r]) => { if (live && r) setD(r); });
    return () => { live = false; };
  }, [rev, empty]);
  const words = query.trim();
  useEffect(() => {                                                                                  // the words asked of the host, a breath after the last key
    if (!words) { setFound(null); return undefined; }
    let live = true;
    const t = setTimeout(() => ask("ideas.chronicle_find", withParty({ query: words }, party)).then(([r, e]) => {
      if (!live) return;
      const slugs = new Set([...(r?.chapters || []), ...(r?.unreleased ? [r.unreleased] : [])].flatMap((c) => (c.goals || []).map((g) => g.idea)));
      setFound(r ? { slugs, more: r.more || 0 } : { slugs, more: 0 });
      if (!r) setErr(e);
    }), 180);
    return () => { live = false; clearTimeout(t); };
  }, [words, party]);
  const rows = useMemo(() => rowsOf(d?.goals || [], d?.versions || [], by), [d, by]);
  const lit = (g) => !!found && found.slugs.has(g.idea), dim = (g) => !!found && !found.slugs.has(g.idea);
  const press = (g) => { closeOver(); if (picked.peek() !== g.idea) pick(g.idea); };
  const keys = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeOver(); } };
  return html`<div class="hist" data-history data-by=${by} data-party=${party || undefined}>
    <header class="hist-head">
      <div class="hist-by" role="group" aria-label="Dated by">${WAYS.map(([id, word]) => html`<button key=${id} type="button" class=${cls("ork-btn quiet hist-by__b", { "is-on": by === id })} data-by=${id} aria-pressed=${String(by === id)} onClick=${() => setBy(id)}>${word}</button>`)}</div>
      <input ref=${field} type="search" class="ork-field hist-search" value=${query} placeholder=${SEARCH} aria-label=${SEARCH} autocomplete="off" onInput=${(e) => setQuery(e.target.value)} onKeyDown=${keys} />
    </header>
    <div class="hist-scroll" data-scroll>
      ${err && html`<p class="chr-err" role="alert">${err}</p>`}
      ${!err && !d && html`<p class="chr-none">Reading the past…</p>`}
      ${d && !rows.length && !err && html`<p class="chr-none" role="status">The history holds nothing yet.</p>`}
      ${found && !found.slugs.size && rows.length > 0 && html`<p class="chr-none" role="status">Nothing in the history has those words.</p>`}
      ${rows.length > 0 && html`<ol class="hist-rows" aria-label="History">${rows.map((r) => html`<${Row} key=${r.day || "none"} row=${r} lit=${lit} dim=${dim} newest=${yearOf(rows[0].day)} onPress=${press} />`)}</ol>`}
      ${found?.more > 0 && html`<p class="chr-none">More cards have these words: add a word to narrow them.</p>`}
    </div>
  </div>`;
}

drawn("history", History);
