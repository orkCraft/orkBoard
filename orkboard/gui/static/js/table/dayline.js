// The day over the pane (docs/specs/138-the-day-read-from-the-resets.md part C, decisions §245.6, §215.1; mockup docs/mockups/die-and-door/ section 4): what a potion pressed opens over the pane, drawn as **a line of time with *Now* across it**,
// one line along time and never a calendar grid. The line runs from midnight today to the end of tomorrow. Behind *Now* what used the tool today (the stretch of its window that lies today, cut by the parties' shares the host
// estimated: `ideas.usage` says shares, not hours, so the stretch is cut by share and never by an hour the host does not know); ahead the tool's windows' resets as marks (each window's `reset` of the snapshot's limits rows; a window shorter
// than a day repeats every its length) and the goals that wait for them as cards on the reset they wait for (their rune, short name and the step in words: *Talk*, *spec*, *work*; `waitTool` of lit.js says which goals wait for the tool,
// the node's `held_until` when); the person's hours (the Board's `hours`, realm/hours.py) as a lighter band under it all. A row a tool: the one pressed on top, then the others with goals waiting. **It decides nothing**: a card pressed
// picks its goal (frame/state.js `pick`, as the column's face-up card does), nothing is dragged. The old list (arena/limits.js: the tool's line and *What used it*) stays under the line, whole (table/over.js).
// Pure functions first (`dayOf`, `posOf`, `ticksOf`, `resetsAhead`, `bandsOf`, `stepWord`, `waitingAt`, `usedStretch`), then the component. Colours are orkUI's tokens only (dayline.css).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { ORKUI, Elem } from "../orkui.js";
import { town, command } from "../link.js";
import { mapData } from "../shell/store.js";
import { board } from "../board/store.js";
import { pick, picked } from "../frame/state.js";
import { spanOf } from "../hand/windows.js";
import { waitTool, defaultTool } from "./lit.js";
import { kindOf, writing } from "./piles.js";

const HOUR = 3600000, DAY = 24 * HOUR, MARKED = ["claude", "codex", "agy", "cursor", "hermes", "pi"];
const two = (n) => String(n).padStart(2, "0");
const clock = (t) => `${two(new Date(t).getHours())}:${two(new Date(t).getMinutes())}`;

/** The line's extent for a moment: from midnight today to the end of tomorrow, in the machine's local time (ms). */
export function dayOf(now = new Date()) {
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate()), end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 2);
  return { start: start.getTime(), end: end.getTime(), now: now.getTime() };
}

/** A moment's place on the line, 0 to 1 (clamped). */
export const posOf = (t, day) => Math.min(1, Math.max(0, (Number(t) - day.start) / (day.end - day.start)));

/** The hours the line is ticked at, every six: `{at, pos, label}`; the midnight between the two days says *tomorrow*. */
export function ticksOf(day) {
  const out = [];
  for (let h = 0; day.start + h * HOUR < day.end; h += 6) {
    const at = new Date(day.start + h * HOUR).getTime(), mid = new Date(at).getHours() === 0;
    out.push({ at, pos: posOf(at, day), label: mid && h > 0 ? "tomorrow" : clock(at) });
  }
  return out;
}

/** The resets of a tool's limit rows that lie ahead on the line: `[{at, window}]` sorted. A window shorter than a day repeats every its length (the 5 hours: every five hours) to the line's end; a longer one has its one. */
export function resetsAhead(rows, day) {
  const out = [];
  for (const r of rows || []) {
    const first = Date.parse(r.reset || "");
    if (!Number.isFinite(first)) continue;
    const span = spanOf(r, new Date(day.now)) * HOUR, each = Number.isFinite(span) && span > 0 && span < DAY ? span : 0;
    let at = first;
    if (each) while (at <= day.now) at += each;                                // a reset gone by: the next one of its rhythm
    for (; at > day.now && at < day.end; at += each) { out.push({ at, window: r.window || "" }); if (!each) break; }
  }
  return out.sort((a, b) => a.at - b.at);
}

/** The person's hours as bands on the line: `[{from, to}]` in ms, clipped to it. `hours`: `[{days: [0..6] (Monday 0), from: "HH:MM", to: "HH:MM"}]`; a `to` not after its `from` runs over midnight (equal is the whole day). */
export function bandsOf(hours, day) {
  const out = [], first = new Date(day.start), at = (d, t) => new Date(d.getFullYear(), d.getMonth(), d.getDate(), Number(t.slice(0, 2)), Number(t.slice(3, 5))).getTime();
  for (const r of Array.isArray(hours) ? hours : []) {
    if (!/^\d\d:\d\d$/.test(r?.from || "") || !/^\d\d:\d\d$/.test(r?.to || "")) continue;
    for (let i = -1; i <= 2; i += 1) {
      const d = new Date(first.getFullYear(), first.getMonth(), first.getDate() + i);
      if (!(r.days || []).includes((d.getDay() + 6) % 7)) continue;
      const from = at(d, r.from);
      let to = at(d, r.to);
      if (to <= from) to += DAY;
      if (to > day.start && from < day.end) out.push({ from: Math.max(from, day.start), to: Math.min(to, day.end) });
    }
  }
  return out.sort((a, b) => a.from - b.from);
}

/** The step a goal waits to take, in a word: *Talk* (its leaders talk it over), *spec* (the spec is next or being written), *work* (its tasks). */
export function stepWord(n) {
  const k = kindOf(n);
  if (n.state === "talk") return "Talk";
  return k && (k.pile === "analysis" || (k.pile === "review" && writing(n))) ? "spec" : "work";
}

/** The goals waiting for one tool, each with the moment it waits for: `[{n, at}]`. Its `held_until` when it has one (then the first reset at or after it, within a minute, when the tool has one: the reset it waits for),
 *  a wait of a spent window the tool's first reset ahead, a To review spec its own wait's end. A goal whose moment is not on the line is left out. */
export function waitingAt(nodes, provider, resets, day, dflt = defaultTool()) {
  const out = [];
  for (const n of nodes || []) {
    if (waitTool(n, dflt, day.now) !== provider) continue;
    const held = Date.parse(n.held_until || ""), left = Number(n.back?.ripe?.left_s);
    let at = Number.isFinite(held) && held > day.now ? held : null;
    if (at !== null) at = resets.find((r) => r.at >= at - 60000)?.at ?? at;
    else if (["limits", "reserve"].includes(n.waits?.kind) || !Number.isFinite(left)) at = resets[0]?.at ?? null;
    else at = day.now + left * 1000;
    if (at !== null && at > day.now && at < day.end) out.push({ n, at });
  }
  return out.sort((a, b) => a.at - b.at);
}

/** The stretch of the window that lies today, behind *Now*: `{from, to}` in ms, null when the window's length is not known. `got`: the answer of `ideas.usage` (its `window` and `reset`). */
export function usedStretch(got, day) {
  const reset = Date.parse(got?.reset || ""), span = spanOf({ window: got?.window, reset: got?.reset }, new Date(day.now)) * HOUR;
  if (!Number.isFinite(span) || span <= 0) return null;
  const from = Number.isFinite(reset) && reset > day.now ? reset - span : day.now - Math.min(span, DAY);
  return { from: Math.max(day.start, from), to: day.now };
}

const width = (from, to, day) => `left:${(posOf(from, day) * 100).toFixed(3)}%;width:${((posOf(to, day) - posOf(from, day)) * 100).toFixed(3)}%`;

function Name({ l }) {
  return html`<span class="dayline__tool">${MARKED.includes(l.provider) && html`<img class="ork-mark" src=${`${ORKUI}/marks/harness-${l.provider}-ink.png`} alt="" draggable="false" />`}<span>${l.name || l.provider}</span></span>`;
}

function Card({ n }) {
  const name = n.short || n.title || n.slug, step = stepWord(n), words = `${n.title || name}: ${step}`;
  return html`<button type="button" class=${cls("dayline__card", { "ork-picked": picked.value === n.slug })} data-goal=${n.slug} data-step=${step} title=${words} aria-label=${words} aria-pressed=${String(picked.value === n.slug)} onClick=${() => pick(n.slug)}>
    <${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} /><span class="dayline__nm">${name}</span><span class="dayline__step">${step}</span></button>`;
}

function Track({ l, day, first, hours, used }) {
  const resets = resetsAhead(l.rows, day), cards = waitingAt(mapData.value?.nodes, l.provider, resets, day);
  const named = new Map(resets.map((r) => [r.at, r.window])), at = [...new Set([...resets.map((r) => r.at), ...cards.map((c) => c.at)])].sort((a, b) => a - b);
  const tall = Math.max(0, ...at.map((t) => cards.filter((c) => c.at === t).length));                // the most cards on one reset: the row's height
  return html`<div class="dayline__row" data-provider=${l.provider} data-first=${first ? "1" : undefined}>
    <${Name} l=${l} />
    <div class="dayline__track" style=${`min-height:calc(var(--ork-6) * ${1 + tall * 2})`}>
      ${bandsOf(hours, day).map((b) => html`<i key=${b.from} class="dayline__hours" data-hours="1" style=${width(b.from, b.to, day)}></i>`)}
      ${used?.stretch && html`<span class="dayline__used" data-used="1" style=${width(used.stretch.from, used.stretch.to, day)}>
        ${used.rows.map((r) => html`<i key=${r.party} data-party=${r.party} title=${`${r.title}: ${r.share >= 1 ? Math.round(r.share) : "<1"} %`} style=${`flex:${Math.max(1, r.share)}`}></i>`)}</span>`}
      ${at.map((t) => html`<span key=${t} class=${cls("dayline__reset", { "is-own": !named.has(t), "is-late": posOf(t, day) > 0.7 })} data-reset=${clock(t)} style=${`left:${(posOf(t, day) * 100).toFixed(3)}%`} title=${named.has(t) ? `${named.get(t)} resets at ${clock(t)}` : clock(t)}>
        <b>${clock(t)}</b>${cards.filter((c) => c.at === t).map((c) => html`<${Card} key=${c.n.slug} n=${c.n} />`)}</span>`)}
    </div>
  </div>`;
}

/** The day over the pane for the tool pressed: its line on top, then the lines of the other tools that have goals waiting. */
export function DayLine({ provider }) {
  const [now, setNow] = useState(() => new Date());
  const [got, setGot] = useState(null);
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 60000); return () => clearInterval(t); }, []);
  useEffect(() => {
    let live = true;
    command("ideas.usage", { provider, scope: "project" }, true).then((a) => { if (live) setGot(a); }).catch(() => {});
    return () => { live = false; };
  }, [provider, now.getHours()]);
  const day = dayOf(now), dflt = defaultTool(), limits = (town.value?.limits || []).map((l) => ({ ...l, name: l.name || l.provider })), nodes = mapData.value?.nodes || [];
  const mine = limits.find((l) => l.provider === provider), others = limits.filter((l) => l.provider !== provider && nodes.some((n) => waitTool(n, dflt, day.now) === l.provider));
  if (!mine && !others.length) return null;
  const used = got && !got.tokens_only && (got.rows || []).length ? { stretch: usedStretch(got, day), rows: got.rows } : null;
  const hours = board.value?.hours || [], nowAt = `left:${(posOf(day.now, day) * 100).toFixed(3)}%`;
  return html`<section class="dayline" aria-label="The day" data-dayline="1">
    <div class="dayline__axis"><span class="dayline__lead" aria-hidden="true"></span><div class="dayline__ticks" aria-hidden="true">${ticksOf(day).map((t) => html`<span key=${t.at} style=${`left:${(t.pos * 100).toFixed(3)}%`}>${t.label}</span>`)}</div></div>
    ${mine && html`<${Track} l=${mine} day=${day} first=${true} hours=${hours} used=${used} />`}
    ${others.map((l) => html`<${Track} key=${l.provider} l=${l} day=${day} hours=${hours} />`)}
    <div class="dayline__over" aria-hidden="true"><span class="dayline__lead"></span><div class="dayline__plane"><i class="dayline__now" data-now="1" style=${nowAt}></i><b class="dayline__nowword" style=${nowAt}>Now</b></div></div>
  </section>`;
}
