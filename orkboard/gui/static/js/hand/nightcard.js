// The morning's card (docs/specs/121-the-day-the-morning-and-the-night.md §5, §7.2, decisions §199.5; mockup docs/mockups/hearing/ §5): what the night did, said by the Orkmaster as the first card of the hand once the night's window did something, and gone when the next night comes. The record is
// the host's (`ideas.night` → `{since, hours, into, goals: [{slug, short, title, goal, done, screens: [{screen, name, path}]}], failed: [{slug, short, title, task, why}], reverts: [{sha, subject, at}], checks: [{slug, short, title, task, check}], play, empty}`, null when the night did
// nothing); `useNight()` (called by the hand) reads it when the project is shown and again, at most every half minute, when the Board changes. `nightStops()` is the card as a stop of the hand (hand.js puts it first): the moon sign in its window, the Orkmaster's crowned head as its asker,
// *The night: 3 goals in dev* as its name (a count of what was done, never of what waits), *Since 01:00* at its foot, no price, under the first lane. Lifted: a row a goal (its rune, its short name, the screens it changed) with **Play it** (`ideas.play {path, idea}` of its first screen,
// opened over the pane and the die thrown as the die throws it: arena/play.js; a goal with no screen of its own is played at the preview's first page), then *Failed: <goal>* with its reason, *Reverted* and *Checks red: <check>* rows (each failed or red one a way to its goal: it is picked), and **Done**,
// which sends the card away until the next night (kept on this device by the night's start). `ideas.night {opened: true}` is sent once for a night when the card is lifted. On the phone Play is the computer's: the rows stay and a line says **Play it on the computer**.
import { useEffect } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { command } from "../link.js";
import { board, hhmm } from "../board/store.js";
import { ORKMASTER, openOver, openTab, picked, tab } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { currentProject } from "../shell/projects.js";
import { mapData } from "../shell/store.js";
import { mapName, partiesAll } from "../table/data.js";
import { orkHeadOf } from "./context.js";
import { at } from "./entries.js";
import { way } from "./ways.js";

// Its sheet (hand/night.css) is loaded with the first card drawn, as choose.js loads questions.css.
const sheet = typeof document !== "undefined" ? new URL("./night.css", import.meta.url).href : "";
if (sheet && !document.querySelector(`link[href="${sheet}"]`)) {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = sheet;
  document.head.appendChild(link);
}

export const PLAY_IT = "Play it", PLAY_ON_COMPUTER = "Play it on the computer", DONE = "Done", OPEN = "Open";
const MIN_MS = 30_000, FIRST_MS = 400;                          // the record is asked again at most this often when the Board changes; the first ask waits a moment
const KEPT = "orkboard.night.done";

/** *The night: 3 goals in dev*, *The night: 1 goal in dev*, *The night: no goal reached dev* (a count of what was done). */
export function nightWords(r) {
  const n = (r?.goals || []).length;
  return n ? `The night: ${n} ${n === 1 ? "goal" : "goals"} in dev` : "The night: no goal reached dev";
}

/** The screens of a goal said in a line: *Results · Lobby*; "" with none. */
export const screensWords = (g) => (g.screens || []).map((s) => s.name).filter(Boolean).join(" · ");

// -- the record --------------------------------------------------------------------------------------------------------------------------------------------------------------------

export const nightRecord = signal(null);                        // ideas.night, null when the night did nothing (or the host does not know the command)
const sent = signal(readDone());                                 // {<project>: the `since` of the night whose card was sent away with Done}
const opened = new Set();                                        // the nights whose lifting was told to the host in this run
let seq = 0, last = 0, timer = 0;

function readDone() {
  try { return JSON.parse(localStorage.getItem(KEPT)) || {}; } catch { return {}; }
}
const projectKey = () => currentProject.value?.path || "";

/** The card is sent away until the next night. */
export function done() {
  const r = nightRecord.value;
  if (!r) return;
  sent.value = { ...sent.value, [projectKey()]: r.since };
  try { localStorage.setItem(KEPT, JSON.stringify(sent.value)); } catch { /* this run only */ }
}

let coming = true;                                               // the project was just shown: its first record, when it has a card, is what the phone opens on

function ask() {
  const mine = ++seq;
  last = Date.now();
  command("ideas.night", {}, true).then((r) => {
    if (mine !== seq) return;
    nightRecord.value = r && Array.isArray(r.goals) && !r.empty ? r : null;
    const first = nightStops()[0];
    if (coming && first) { at.value = `card:${first.key}`; picked.value = ""; }                 // the morning's card is the first thing the phone shows (its middle is the entry `at` names; no goal is picked)
    coming = false;
  }).catch(() => { if (mine === seq) { nightRecord.value = null; coming = false; } });
}

/** Reads the night's record when the project is shown, and again when the Board changes (at most every half minute). Called by the hand. */
export function useNight() {
  const project = projectKey(), rev = board.value?.rev;
  useEffect(() => { nightRecord.value = null; seq += 1; coming = true; clearTimeout(timer); timer = setTimeout(ask, FIRST_MS); return () => clearTimeout(timer); }, [project]);
  useEffect(() => {
    if (rev == null || !last) return undefined;                                       // the first ask is the project's; later ones follow the Board
    clearTimeout(timer);
    timer = setTimeout(ask, Math.max(FIRST_MS, last + MIN_MS - Date.now()));
    return () => clearTimeout(timer);
  }, [rev]);
}

/** The card as a stop of the hand: `[]` with no record, or when Done sent this night's away. The first of the hand's stops. */
export function nightStops() {
  const r = nightRecord.value;
  if (!r || sent.value[projectKey()] === r.since) return [];
  const head = orkHeadOf(), title = nightWords(r);
  return [{ key: `night/${r.since}`, kind: "night", ref: r, row: { ...r, kind: "night" }, node: null, task: null, label: "Morning", gem: "", tone: "", gemTip: "", head, small: true, whoTip: "from the Orkmaster",
    title, full: title, text: "", why: "", g: null, party: { slug: "", name: "Orkmaster", head, lead: "Orkmaster" }, other: false }];
}

// -- the lifted card -----------------------------------------------------------------------------------------------------------------------------------------------------------------

/** The goal's way: it is the picked one, on the Board's tab (a failed or red goal's card, and its page on the phone). */
function openGoal(slug) {
  picked.value = slug;
  if (tab.value !== ORKMASTER) openTab(ORKMASTER);
}

/** Play opened over the pane on the goal's first screen (its route), or at the preview's first page; the die is thrown as the die throws it. */
export function playIt(g) {
  const first = (g.screens || []).find((s) => s.path);
  openOver("play", { ...(first ? { path: first.path } : {}), idea: g.slug }, { title: mapName(tab.peek(), partiesAll()), key: "" }, "Play");
}

const elementOf = (slug) => (mapData.value?.nodes || []).find((n) => n.slug === slug)?.element || "";

function Row({ cls = "", mark = null, title, line = "", slug = "", children, data }) {
  return html`<li class=${`nt-row ${cls}`} data-row=${data} data-goal=${slug || undefined}>${mark}<span class="nt-t"><b>${title}</b>${line && html`<span>${line}</span>`}</span>${children}</li>`;
}

/** The lifted card: what the night did, each goal with its screens and **Play it**, what failed, was reverted or went red, **Done**. */
export function NightLifted({ s }) {
  const r = s.row, phone = uprightNow.value;
  useEffect(() => {
    if (opened.has(r.since)) return;
    opened.add(r.since);
    command("ideas.night", { opened: true }, true).catch(() => {});
  }, [r.since]);
  const goal = (slug) => html`<button type="button" class="ork-btn" data-act="open" onClick=${() => openGoal(slug)}>${OPEN}</button>`;
  return html`<div class="hand-way hand-way--night" data-kind="night" data-since=${r.since}>
    <ul class="nt-rows" aria-label=${nightWords(r)}>
      ${(r.goals || []).map((g) => html`<${Row} key=${`goal/${g.slug}`} data="goal" slug=${g.slug} mark=${html`<${Elem} name=${elementOf(g.slug)} dim=${!elementOf(g.slug)} />`} title=${g.short || g.title} line=${screensWords(g)}>
        ${!phone && html`<button type="button" class="ork-btn" data-act="play" aria-label=${`${PLAY_IT}: ${g.short || g.title}`} onClick=${() => playIt(g)}><${Sign} name="play" /> ${PLAY_IT}</button>`}<//>`)}
      ${(r.failed || []).map((f) => html`<${Row} key=${`failed/${f.slug}/${f.task}`} data="failed" cls="is-bad" slug=${f.slug} mark=${html`<${Sign} name="cross" />`} title=${`Failed: ${f.short || f.title}`} line=${f.why || f.task}>${goal(f.slug)}<//>`)}
      ${(r.reverts || []).map((v) => html`<${Row} key=${`revert/${v.sha}`} data="reverted" cls="is-bad" mark=${html`<${Sign} name="before" />`} title="Reverted" line=${`${v.subject} · ${v.sha}`} />`)}
      ${(r.checks || []).map((c) => html`<${Row} key=${`check/${c.slug}/${c.task}`} data="checks" cls="is-bad" slug=${c.slug} mark=${html`<${Sign} name="alert" />`} title=${`Checks red: ${c.check || c.task}`} line=${[c.short || c.title, c.task].filter(Boolean).join(" · ")}>${goal(c.slug)}<//>`)}
    </ul>
    ${phone && (r.goals || []).length > 0 && html`<p class="cap nt-phone" data-part="phone">${PLAY_ON_COMPUTER}</p>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers"><button type="button" class="ork-btn primary" data-answer="done" onClick=${done}>${DONE}</button></div>
  </div>`;
}

// The face: the moon sign, the Orkmaster as its asker, *Since 01:00* at its foot, no price.
way("night", { sign: "moon", foot: (s) => `Since ${hhmm(s.row?.since)}`, price: () => null, Lifted: NightLifted });
