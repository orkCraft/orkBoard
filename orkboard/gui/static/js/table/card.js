// A card of the Board (docs/specs/101-the-cards-the-cascade-and-the-hand-under-the-lanes.md §2, decisions §167.1; the lifting of docs/specs/98-the-table-and-the-hand.md §3.5, §6, decisions §120.1): 144 wide, its goal's element
// bare at the left of its header and its name beside it (the pixel face, three lines at most), under it a window (the card's own fill, a hairline) with one sign at the signs' big size, toned down — the task's type —, and its
// label row: the stage's small sign and word, the gem at its right when it spends. The tasks behind the front one lie as a fan (`fanOf`, `TaskEdge`). No foot and no head: who works is on its back and in its party's header. A card is **lifted where it lies** and turns over (`Lifted`): its back
// the details and **Open**; Esc or a press away lowers it, one at a time. A card leans toward the pointer and rises on orkUI's motion tokens (`.ork-leans`, the page sets `--ork-lean-x/-y`); nothing moves under reduced motion
// (orkUI's own rule). At the narrow width a lane a token wide lays a goal as one token (`Token`) with its stack's edges, and what is lifted is a screen.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Elem, Sign, WhoHead, headWords } from "../orkui.js";
import { lifted, lift, lower, picked, pick, openOver, partKey, linkKey } from "../frame/state.js";
import { TASK_STATE } from "../board/maplayout.js";
import { typeTone } from "../arena/goalwords.js";
import { cascadeOf, footWords, doingWords, readTask, stageOf, typeSignOf, gemOf, STAGES } from "./data.js";

/** The key of the card that was lit on the way back from a thing opened over the pane, "" none (a press or a key puts it out). */
export const litKey = signal("");

/** Lean toward the pointer (a mouse; a touch has no hover): the pointer's place on the card, -1 to 1, for orkUI's lean and rise. */
export const leans = {
  onPointerMove: (e) => {
    if (e.pointerType !== "mouse") return;
    const r = e.currentTarget.getBoundingClientRect();
    e.currentTarget.style.setProperty("--ork-lean-x", String(Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width) * 2 - 1)).toFixed(2)));
    e.currentTarget.style.setProperty("--ork-lean-y", String(Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height) * 2 - 1)).toFixed(2)));
  },
  onPointerLeave: (e) => { e.currentTarget.style.removeProperty("--ork-lean-x"); e.currentTarget.style.removeProperty("--ork-lean-y"); },
};

export const taskKey = (n, t) => `t:task:${n.slug}/${t.id}`;
export const ownKey = (n) => `t:orc:${n.slug}`;
export { partKey, linkKey };
export const mineKey = (key) => typeof key === "string" && key.startsWith("t:");

/** What a card of this goal says it is about (the hand's lifted card marks it, hand/about.js): the goal and, for a task, itself. */
export const aboutTokens = (n, tasks = []) => `idea:${n.slug}${tasks.map((t) => ` task:${n.slug}/${t.id}`).join("")}`;

/** The stage's small sign (14 px) and its word, as a label row or a strip says it. */
export function Stage({ stage }) {
  const s = STAGES[stage] || STAGES.routing;
  return html`<span class="table-stage"><${Sign} name=${s.sign} />${s.word}</span>`;
}

/** The card's window: one sign at the signs' big size, in the goal's colour toned down (an opacity on orkUI's token, table.css). `moon`: the moon beside it (a goal that waits for the reset). */
function Win({ n, sign, moon = false, danger = false }) {
  return html`<span class=${cls("table-card__win", `is-${typeTone(n)}`, { "is-danger": danger })}>${sign && html`<${Sign} name=${sign} big=${true} />`}${moon && html`<${Sign} name="moon" big=${true} />`}</span>`;
}

/** A task, as a card in its goal's cascade: the goal's element and the task's name, the type in the window, the stage and, at its right, the gem when it spends. */
export function TaskCard({ n, t }) {
  const key = taskKey(n, t), on = lifted.value === key, bad = t.state === "failed", asks = t.state === "picking", gem = gemOf(t);
  const said = `${t.title}, ${n.short || n.title}: ${footWords(t)}`;
  return html`<button type="button" class=${cls("ork-card ork-leans table-card", { fails: bad, asks, "is-lifted": on, "is-lit": litKey.value === key })} data-lkey=${key} data-goal=${n.slug} data-task=${t.id}
    data-about=${aboutTokens(n, [t])} data-state=${t.state} data-stage=${stageOf(t)} aria-pressed=${String(on)} aria-label=${said} title=${n.title} onClick=${() => lift(on ? "" : key)} ...${leans}>
    <span class="table-card__head"><${Elem} name=${n.element} dim=${!n.element} /><span class="table-card__nm" title=${t.title}>${t.short || t.title}</span></span>
    <${Win} n=${n} sign=${typeSignOf(n, t)} />
    <span class="table-card__row"><${Stage} stage=${stageOf(t)} />${gem && html`<span class="ork-gem share" data-cost=${gem}>${gem}</span>`}</span>
  </button>`;
}

// -- the fan: the cards behind the front one (spec 101 §7.2, decisions §168.4) ------------------------------------------------------------

/** How many cards behind the front one are drawn on a goal's fan (the rest wait for the goal to be picked, which unfolds them all). */
export const BEHIND = 5;
const SEEN = 3, PEEK = 20, OPEN = 30, HINT = 5;                  // three edges with their sign, the next only a hint; an edge's height at rest and opened, a hint's
const TURNS = [2, -1.5, 2.5, -1, 1.5, -2.5], ASIDE = [3, -4, 4, -2, 3, -3];      // a turn (degrees) and a push aside (px) by the card's place from the front: fixed, never random, so a redraw shakes nothing

/** The layout of a fan of `count` cards behind the front one, the farthest first: for each its slot's style (`--dy` its top at rest, `--ov` opened, `--rot` and `--dx` its turn and push aside by its place from the front, `--z`
 *  its order) and whether it is only a hint; and the fan's own heights (`--of` at rest, `--span` opened). */
export function fanOf(count) {
  let at = 0, open = 0;
  const cards = [];
  for (let j = 0; j < count; j++) {
    const place = count - j - 1, seen = place < SEEN;
    cards.push({ hint: !seen, style: `--dy:${at}px;--ov:${open}px;--rot:${TURNS[place % TURNS.length]}deg;--dx:${ASIDE[place % ASIDE.length]}px;--z:${j + 1}` });
    at += seen ? PEEK : HINT;
    open += seen ? OPEN : HINT;
  }
  return { cards, style: `--of:${at}px;--span:${open}px` };
}

/** A task behind the front one, as its edge on the goal's fan: the goal's element and the stage's small sign, no name until the fan is opened by a hover or the focus; a press lifts the task. */
export function TaskEdge({ n, t, hint = false }) {
  const key = taskKey(n, t), on = lifted.value === key, bad = t.state === "failed", asks = t.state === "picking";
  return html`<button type="button" class=${cls("ork-card table-fan__card table-tedge", { fails: bad, asks, "is-lifted": on, "is-lit": litKey.value === key, "is-hint": hint })} data-lkey=${key} data-goal=${n.slug} data-task=${t.id}
    data-about=${aboutTokens(n, [t])} data-state=${t.state} data-stage=${stageOf(t)} aria-pressed=${String(on)} aria-label=${`${t.title}: ${STAGES[stageOf(t)].word}${bad ? ", failed" : ""}`} title=${t.title}
    onClick=${() => lift(on ? "" : key)}><${Elem} name=${n.element} dim=${!n.element} /><span class="table-fan__nm">${t.short || t.title}</span><${Sign} name=${STAGES[stageOf(t)].sign} /></button>`;
}

/** A goal the Orkmaster reads, routes or joins itself, as a card in the first lane (under its strip): the same face, its stage *Reading*, *Routing* or *Joining*. */
export function OwnCard({ n, stage }) {
  const key = ownKey(n), on = lifted.value === key;
  return html`<button type="button" class=${cls("ork-card ork-leans table-card table-card--own", { "is-lifted": on, "is-lit": litKey.value === key })} data-lkey=${key} data-goal=${n.slug} data-about=${aboutTokens(n)} data-state=${n.state}
    data-stage=${stage} aria-pressed=${String(on)} aria-label=${`${n.title}: ${doingWords(n)}`} onClick=${() => lift(on ? "" : key)} ...${leans}>
    <span class="table-card__head"><${Elem} name=${n.element} dim=${!n.element || n.state === "reading"} /><span class="table-card__nm" title=${n.title}>${n.short || n.title}</span></span>
    <${Win} n=${n} sign=${n.type?.sign || ""} />
    <span class="table-card__row"><${Stage} stage=${stage} /></span>
  </button>`;
}

/** The same at a lane a token wide (spec 101 §5): a goal is one token with its stack's edges — its element, its front task's type and stage —; a press lifts the front task, whose back lists the goal's tasks.
 *  `tasks`: the goal's tasks, the front one first; none for a goal the Orkmaster does itself (`stage` says what). */
export function Token({ n, tasks = [], stage = "" }) {
  const front = tasks[0], key = front ? taskKey(n, front) : ownKey(n), on = lifted.value === key || tasks.some((t) => lifted.value === taskKey(n, t)), bad = tasks.some((t) => t.state === "failed");
  const st = front ? stageOf(front) : stage, words = front ? `${n.title}: ${footWords(front)}` : `${n.title}: ${doingWords(n)}`;
  const edges = Math.min(5, Math.max(0, tasks.length - 1));
  return html`<span class="table-stack" data-n=${edges}>
    ${Array.from({ length: edges }, (_, k) => html`<i key=${k} class="ork-card table-edge" style=${`--ork-deck-i:${k + 1}`} aria-hidden="true"></i>`)}
    <button type="button" class=${cls("ork-card table-token", { fails: bad, "is-lifted": on, "is-lit": litKey.value === key, "ork-picked": picked.value === n.slug })} data-lkey=${key} data-goal=${n.slug} data-task=${front?.id}
      data-about=${aboutTokens(n, tasks)} data-state=${front ? front.state : n.state} data-stage=${st} aria-pressed=${String(on)} aria-label=${words} title=${words} onClick=${() => lift(lifted.value === key ? "" : key)}>
      <span class="table-card__top"><${Elem} name=${n.element} dim=${!n.element} /><${Sign} name=${(STAGES[st] || STAGES.routing).sign} /></span>
      <${Win} n=${n} sign=${front ? typeSignOf(n, front) : n.type?.sign || ""} danger=${bad} />
    </button>
  </span>`;
}

// -- a card lifted where it lies -----------------------------------------------------------------------------------------------------

/** The element of a lifted card's key on the table: a Board card is ours (`data-lkey`), a part of the System is the map's own. */
export function elOf(key) {
  if (key.startsWith("t:part:")) {
    const path = key.split(":").slice(3).join(":");
    return document.querySelector(`.table-sys .sys-part[data-part="${CSS.escape(path)}"]`);
  }
  if (key.startsWith("t:link:")) return document.querySelector(`.table-sys .arch-link[data-link="${CSS.escape(key.split(":").slice(3).join(":"))}"]`);
  return document.querySelector(`[data-lkey="${CSS.escape(key)}"]`);
}

/** The back's place: over the card where it lies, kept inside the pane's body (the whole body at the narrow width). */
function place(el, host, back) {
  if (!el || !host || !back) return;
  const h = host.getBoundingClientRect(), c = el.getBoundingClientRect(), w = back.offsetWidth, t = back.offsetHeight;
  const left = Math.max(0, Math.min(c.left - h.left, h.width - w)), top = Math.max(0, Math.min(c.top - h.top, h.height - t));
  back.style.left = `${left}px`;
  back.style.top = `${top}px`;
}

/** The lifted card turned over (`children`: its back's details), over the card where it lies. `host`: the ref of the pane's body it is placed in; `name`: its label. */
export function Lifted({ host, name, narrow, children }) {
  const back = useRef(), key = lifted.value;
  useLayoutEffect(() => {
    if (narrow || !back.current) return undefined;
    const put = () => place(elOf(key), host.current, back.current);
    put();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(put) : null;
    ro?.observe(host.current);
    ro?.observe(back.current);
    return () => ro?.disconnect();
  }, [key, narrow]);
  return html`<aside class=${cls("ork-frame table-back", { "is-screen": narrow })} ref=${back} aria-label=${`${name}, turned over`} data-lifted=${key} role="dialog" aria-modal="false">
    ${narrow && html`<button type="button" class="ork-btn quiet table-back__x" aria-label="Back" onClick=${() => lower()}><svg class="ork-icon g7" aria-hidden="true"><use href="/ds/orkui/icons/icons.svg#arrow-left" /></svg></button>`}
    ${children}
  </aside>`;
}

/** A back's section: a label over its lines. */
export const Sec = ({ label, children }) => html`<div class="table-back__sec"><span class="ork-label">${label}</span>${children}</div>`;

/** The goal, with a press that picks it (or takes the pick off): the other cards of that goal are lit. */
export function PickGoal({ n }) {
  const on = picked.value === n.slug;
  return html`<button type="button" class="ork-btn quiet table-back__pick" aria-pressed=${String(on)} onClick=${() => pick(n.slug)}>${on ? "Picked: put it down" : "Pick this goal"}</button>`;
}

/** The back of a task's card: its state, who does it, its brief, what it made, and **Open** (a failure's lines, a result's diff, the task). `from`: the card's key and the map's name, for ←. */
export function TaskBack({ n, t, mapName }) {
  const [full, setFull] = useState(null);
  useEffect(() => {
    let live = true;
    setFull(null);
    readTask(n.slug, t.id, true).then((r) => { if (live && r) setFull(r); });
    return () => { live = false; };
  }, [n.slug, t.id, t.state]);
  const from = { title: mapName, key: taskKey(n, t) };
  const open = () => (t.state === "failed" ? openOver("log", { slug: n.slug, task: t.id }, from, t.title)
    : t.state === "review" || t.state === "merged" ? openOver("diff", { slug: n.slug, task: t.id }, from, t.title) : openOver("task", { slug: n.slug, task: t.id }, from, t.title));
  const error = full?.error || t.error || "", mates = cascadeOf(n).filter((x) => x.id !== t.id);
  return html`<h3 class="table-back__nm">${t.title}</h3>
    <p class="table-back__cap">${n.title}</p>
    <${Sec} label="State"><span data-state=${t.state}>${TASK_STATE[t.state] || t.state}${t.note ? ` · ${t.note}` : ""}</span></${Sec}>
    ${t.head && html`<${Sec} label="Does it"><span class="table-back__who"><${WhoHead} head=${t.head} /> ${t.by?.name || ""} <span class="table-back__muted">${headWords(t.head)}</span></span></${Sec}>`}
    ${error && html`<${Sec} label="What went wrong"><span class="is-danger">${error}</span></${Sec}>`}
    ${full?.brief && html`<${Sec} label="Brief"><span class="table-back__text">${full.brief}</span></${Sec}>`}
    ${t.made && html`<${Sec} label="What it made"><span>${t.made}</span></${Sec}>`}
    ${mates.length > 0 && html`<${Sec} label="Its tasks"><span class="table-back__tasks">${mates.map((m) => html`<button type="button" key=${m.id} class="ork-btn quiet table-back__task" data-task=${m.id} onClick=${() => lift(taskKey(n, m))}>
      <${Sign} name=${STAGES[stageOf(m)].sign} /><span>${m.short || m.title}</span></button>`)}</span></${Sec}>`}
    <div class="table-back__acts"><${PickGoal} n=${n} /><button type="button" class="ork-btn table-back__open" onClick=${open}>Open</button></div>`;
}

/** The back of a goal the Orkmaster reads or routes. */
export function OwnBack({ n }) {
  return html`<h3 class="table-back__nm">${n.title}</h3>
    <p class="table-back__cap">${n.state === "reading" ? "The Orkmaster is reading it." : "The Orkmaster is routing it: which party does what."}</p>
    <div class="table-back__acts"><${PickGoal} n=${n} /></div>`;
}

/** Esc lowers a lifted card; a press away does too (one at a time, never over what it is about). Kept while a card of the table is lifted. */
export function useLowering(on) {
  useEffect(() => {
    if (!on) return undefined;
    const away = (e) => {
      if (e.target.closest?.(".table-back, [data-lkey], .table-sys .sys-part, .table-sys .arch-link, .table-seatpop")) return;
      lower();
    };
    document.addEventListener("pointerdown", away, true);
    return () => document.removeEventListener("pointerdown", away, true);
  }, [on]);
}
