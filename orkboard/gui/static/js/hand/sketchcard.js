// A leader's sketch (docs/specs/121-the-day-the-morning-and-the-night.md §2, §7.1, decisions §199.3; mockup docs/mockups/hearing/ §4): before a goal's spec its craft's leader makes two or three throwaway variants, kept beside the goal and never in the project's code, and the person
// touches them and picks one. It is the Needs you row of a pick (`kind: "pick"`, `task: "sketch"`, `media`: `page` for a screen drawn as one HTML page, else a picture or a sound as Pick one draws them: arena/picks.js `Tiles`) and the existing pick card's lifted face
// for such a row (stopcard.js asks `isSketch` and draws `SketchLifted` in place of the pick's tiles). Its face says who made it: the leader's head as its asker and *<Leader> sketched it* at its foot (arenawords.js `stopsOf`).
// Each variant of a `page` sketch is `text/html` served in its own sandbox (gui/media.py: no network, an opaque origin) and shown only in an `iframe` with `sandbox="allow-scripts"` and **no** `allow-same-origin` (§3.2), `title` *Sketch A by <Leader>*:
//   - on the phone (a touch window held upright, frame/upright.js) the lifted card shows **one variant at a time at the screen's width**, **A · B · C** above it as buttons (never a sideways swipe: the frame takes the gestures), the variant's line under it, then *A note (optional)*,
//     **Pick this one**, **Pick and build now** (only with *Work at night* on, quieter: the night is the default; hand/nightwords.js), **Sketch again** (a field, *What to change*) and **No sketch: go on**;
//   - on the desktop the card opens the variants side by side over the pane (the pane's `choose` kind, source `sketch`, as a fork's sides are), each frame at about a phone's width with its **Pick this one** (and **Pick and build now**) under it, and the note and the other two answers under all.
// The answers are `ideas.pick {slug, task: "sketch", key, note, via: "hand", now?}`: a variant's letter picks it (`now: true`: its plan starts at once); `key: null` with `note` (what to change) asks for new ones (**Sketch again**, three rounds at most: the host says so in words
// when it is asked a fourth time, and the card does not offer it then); `key: null` with `skip: true` is **No sketch: go on** (the goal goes on to its sections). A host answers a refusal in words (a toast); the card goes with the row when it is answered.
import { useLayoutEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { Elem, Head } from "../orkui.js";
import { board } from "../board/store.js";
import { openOver, tab } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { act, mapData } from "../shell/store.js";
import { mapName, partiesAll } from "../table/data.js";
import { Tiles, choiceOf } from "../arena/picks.js";
import { labelOf, variantOf } from "../arena/pickwords.js";
import { chooseFor } from "./choose.js";
import { nightWordsOf, workAtNight } from "./nightwords.js";

// Its sheet (hand/sketch.css) is loaded with the first sketch drawn, as choose.js loads questions.css.
const sheet = typeof document !== "undefined" ? new URL("./sketch.css", import.meta.url).href : "";
if (sheet && !document.querySelector(`link[href="${sheet}"]`)) {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = sheet;
  document.head.appendChild(link);
}

export const ROUNDS = 3;                                    // the sketch's rounds at most (realm/sketches.py): the fourth is refused
export const PICK = "Pick this one", AGAIN = "Sketch again", GO_ON = "No sketch: go on", NOTE = "A note (optional)", CHANGE = "What to change";
export const ROUNDS_WORDS = "Three rounds: pick one or go on";
export const PICK_NOW_TIP = "Picks it, and its plan starts at once instead of waiting for the night";
/** A leader's sketch among the hand's stops: the pick row of the task `sketch`. */
export const isSketch = (s) => s?.kind === "pick" && s.row?.task === "sketch";
/** The row of a goal's sketch among the Needs you rows, null when it is answered. */
export const sketchRow = (slug) => (board.value?.needs_you || []).find((r) => r.kind === "pick" && r.task === "sketch" && r.slug === slug) || null;
const leaderName = (row) => row.by?.name || "Its leader";
export const sketchedWords = (row) => `${leaderName(row)} sketched it`;
export const frameTitle = (key, row) => `Sketch ${key} by ${leaderName(row)}`;

/** One variant's page in its sandbox: scripts may run, and nothing else (no same origin: it reaches neither the Board's page nor its storage nor its socket). */
export function Frame({ row, v }) {
  return html`<iframe class="sk-frame" data-variant=${v.key} title=${frameTitle(v.key, row)} sandbox="allow-scripts" src=${v.url} referrerpolicy="no-referrer"></iframe>`;
}

/** The answers' state and the commands they send; a refused answer (the host says why in a toast) leaves the card as it is. */
function useAnswers(row) {
  const [note, setNote] = useState(""), [busy, setBusy] = useState(false), [again, setAgain] = useState(false), [change, setChange] = useState("");
  const send = async (patch) => {
    if (busy) return false;
    setBusy(true);
    try { return !!(await act("ideas.pick", { slug: row.slug, task: row.task, via: "hand", ...patch })); } finally { setBusy(false); }
  };
  return {
    note, setNote, busy, again, setAgain, change, setChange,
    take: (key, now = false) => send({ key, note: note.trim(), ...(now ? { now: true } : {}) }),
    redo: () => send({ key: null, note: change.trim() }),
    skip: () => send({ key: null, skip: true }),
  };
}

/** *A note (optional)*, the one line that goes with the pick. */
function Note({ a }) {
  return html`<input class="ork-field" name="note" aria-label=${NOTE} placeholder=${NOTE} maxlength="2000" value=${a.note} onInput=${(e) => a.setNote(e.target.value)} />`;
}

/** **Pick this one**, and beside it, quieter, **Pick and build now** with *Work at night* on (the night is the default). `k`: the variant's letter, "" with none picked. */
function PickButtons({ a, k }) {
  const now = workAtNight() ? nightWordsOf().now_sketch : "";
  return html`<button type="button" class="ork-btn primary" data-answer="pick" disabled=${a.busy || !k} title=${k ? `Goes on with ${k}` : "Pick one first"} onClick=${() => a.take(k)}>${PICK}</button>
    ${now && html`<button type="button" class="ork-btn" data-answer="pick-now" disabled=${a.busy || !k} title=${PICK_NOW_TIP} onClick=${() => a.take(k, true)}>${now}</button>`}`;
}

/** **Sketch again** (a field, *What to change*, then the press that sends it) and **No sketch: go on**. */
function Redo({ a, row }) {
  if (a.again) {
    const go = () => { if (a.change.trim() && !a.busy) a.redo(); };
    return html`<input class="ork-field" name="change" aria-label=${CHANGE} placeholder=${CHANGE} maxlength="2000" value=${a.change} autofocus
        onInput=${(e) => a.setChange(e.target.value)} onKeyDown=${(e) => { if (e.key === "Enter") { e.preventDefault(); go(); } }} />
      <div class="hand-answers hand-way__acts" role="group" aria-label="Sketch again">
        <button type="button" class="ork-btn" data-answer="again" disabled=${a.busy || !a.change.trim()} onClick=${go}>${AGAIN}</button>
        <button type="button" class="ork-btn quiet" onClick=${() => a.setAgain(false)}>Cancel</button></div>`;
  }
  const spent = (Number(row.round) || 1) >= ROUNDS;
  return html`${spent && html`<p class="sk-rounds" data-part="rounds">${ROUNDS_WORDS}</p>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Or">
      ${!spent && html`<button type="button" class="ork-btn" data-answer="again-open" disabled=${a.busy} title="Asks for new ones, with what to change" onClick=${() => a.setAgain(true)}>${AGAIN}</button>`}
      <button type="button" class="ork-btn quiet" data-answer="skip" disabled=${a.busy} title="The goal goes on to its spec without a sketch" onClick=${a.skip}>${GO_ON}</button></div>`;
}

/** The phone: one variant at a time at the screen's width, A · B · C above it as buttons, its line under it. */
function PhoneBody({ row }) {
  const a = useAnswers(row), [at, setAt] = useState(row.variants?.[0]?.key || ""), v = variantOf(row, at) || row.variants?.[0];
  if (!v) return null;
  return html`<div class="hand-way hand-way--sketch" data-kind="sketch" data-round=${row.round || 1} data-media="page">
    <div class="sk-abc" role="group" aria-label="The variants">${row.variants.map((x) => html`<button type="button" key=${x.key} class="ork-btn" data-variant=${x.key} aria-pressed=${String(x.key === v.key)}
      title=${labelOf(x)} aria-label=${labelOf(x)} onClick=${() => setAt(x.key)}>${x.key}</button>`)}</div>
    <${Frame} key=${`${row.round || 1}/${v.key}`} row=${row} v=${v} />
    <p class="sk-line"><b>${labelOf(v)}</b>${v.why ? html` · ${v.why}` : ""}</p>
    <div class="sk-acts"><${Note} a=${a} />
      <div class="hand-answers hand-way__acts" role="group" aria-label="Answers"><${PickButtons} a=${a} k=${v.key} /></div>
      <${Redo} a=${a} row=${row} /></div>
  </div>`;
}

/** A picture or a sound sketch: the pick's tiles as Pick one draws them today, the answers of a sketch under them. */
function TilesBody({ row }) {
  const a = useAnswers(row), k = choiceOf(row).key;
  return html`<div class="hand-way hand-way--sketch" data-kind="sketch" data-round=${row.round || 1} data-media=${row.media}>
    <p class="body hand-lifted__text">${row.ask || ""}</p>
    <${Tiles} row=${row} />
    <div class="sk-acts"><${Note} a=${a} />
      <div class="hand-answers hand-way__acts" role="group" aria-label="Answers"><${PickButtons} a=${a} k=${k} /></div>
      <${Redo} a=${a} row=${row} /></div>
  </div>`;
}

/** The desktop's card, lifted: it opens the variants side by side over the pane in its place (the pane's `choose`, source `sketch`). */
function PaneOpener({ s }) {
  useLayoutEffect(() => {
    openOver("choose", { source: "sketch", slug: s.row.slug }, { title: mapName(tab.value, partiesAll()), key: "" }, s.title || s.full);
  }, [s.key]);
  return html`<span class="q-opening" aria-hidden="true"></span>`;
}

/** The lifted card of a sketch (stopcard.js): the phone's one-at-a-time frame, the desktop's pane for a page, the tiles for a picture or a sound. */
export function SketchLifted({ s }) {
  const row = s.row;
  if (row.media !== "page") return html`<${TilesBody} key=${row.round || 1} row=${row} />`;
  return uprightNow.value ? html`<${PhoneBody} key=${row.round || 1} row=${row} />` : html`<${PaneOpener} s=${s} />`;
}

/** Over the pane: the variants side by side, each frame at about a phone's width with its own answer, the note and the other answers under all. */
function Desk({ row }) {
  const a = useAnswers(row), night = workAtNight() ? nightWordsOf().now_sketch : "", node = (mapData.value?.nodes || []).find((n) => n.slug === row.slug) || null, head = row.by?.head || null;
  return html`<section class="sk-pane" data-kind="sketch" data-round=${row.round || 1} aria-label=${sketchedWords(row)}>
    <h2 class="sk-title">${head && html`<${Head} race=${head.race} tier=${head.tier} />`}<span>${sketchedWords(row)}</span>
      <span class="cap">${node && html`<${Elem} name=${node.element || ""} hue=${node.hue || ""} dim=${!node.element} /> `}${node?.short || node?.title || row.short || row.idea_title || ""}</span></h2>
    <div class="sk-desk" role="group" aria-label="The variants">${row.variants.map((v) => html`<figure key=${`${row.round || 1}/${v.key}`} class="sk-one" data-variant=${v.key}>
      <${Frame} row=${row} v=${v} />
      <figcaption><span class="sk-line"><b>${labelOf(v)}</b></span>${v.why && html`<span class="sk-line">${v.why}</span>`}
        <div class="hand-answers" role="group" aria-label=${`Answers for ${v.key}`}><${PickButtons} a=${a} k=${v.key} /></div></figcaption>
    </figure>`)}</div>
    <div class="sk-acts"><${Note} a=${a} /><${Redo} a=${a} row=${row} /></div>
  </section>`;
}

/** What the pane's `choose` draws for a sketch (`props.slug`); it goes back when the sketch is answered. */
function Sketches({ props, close }) {
  const row = sketchRow(props.slug);
  useLayoutEffect(() => { if (!row) close(); }, [!row]);
  return row ? html`<${Desk} key=${row.round || 1} row=${row} />` : null;
}
chooseFor("sketch", Sketches);
