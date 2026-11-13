// **Spec 147 A (decisions §251): a lane's task card is 5 : 7 at the frame's `--card-w` and read by its four corners (corners.js): the goal's rune and the kind's sign at the top, the title in two lines, the window onto the work, and at the foot the seat's head and word and the one figure (cost, time left, time it took, *asks you*). The former label row is the foot; a task at work shows the flame as its top rune glowing.**
// A card of the Board (docs/specs/101-the-cards-the-cascade-and-the-hand-under-the-lanes.md §2, decisions §167.1; the lifting of docs/specs/98-the-table-and-the-hand.md §3.5, §6, decisions §120.1; one rune per stack: docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.1,
// decisions §187.1–§187.2): 144 wide, its task's name at the top of its header (the pixel face is never used for it; three lines at most; **no rune**: the goal's rune stands once, on the strip over its stack), under it a window (the card's own fill, a hairline, 92 px high) that is a window onto the work by the task's state (spec 142 C, decisions §249.3): waiting, the head of the seat that takes it, faint; at work, its steps; failed, the alert and its reason; done or at Review, what it made by its craft (made.js, spec 142 D: Tech's files as bars, Art's image, Design's screen, Release's checks, Product's hypothesis); else one sign
// at the signs' big size, toned down — the task's type —, and its label row: the stage's small sign and word, the gem at its right when it spends. **A task at work shows the flame**: the goal's rune, glowing (orkUI's `.is-glowing`), takes the place of the stage's
// small sign, on its card; it is the card's only motion of the work, and it stands still under reduced motion.
// A card is **lifted where it lies** and turns over (`Lifted`): its back the details and **Open**; Esc or a press away lowers it, one at a time. A card leans toward the pointer and rises on orkUI's motion tokens (`.ork-leans`, the page sets `--ork-lean-x/-y`); nothing moves under
// reduced motion (orkUI's own rule). At the narrow width what is lifted is a screen.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";

import { signal } from "@preact/signals";

import { html, cls } from "../html.js";

import { Sign, WhoHead, headWords } from "../orkui.js";

import { lifted, lift, lower, picked, pick, openOver, partKey, linkKey } from "../frame/state.js";

import { TASK_STATE } from "../board/maplayout.js";

import { typeTone } from "../arena/goalwords.js";

import { aliveState, useChanged, useWorked, workedWords } from "./worktime.js";

import { ConcernsBack } from "./concerns.js";
                       // a marked card's back lists its leader's concerns (spec 108 B)
import { cascadeOf, footWords, readTask, stageOf, typeSignOf, gemOf, STAGES } from "./data.js";

import { StepsList, StepsWindow, WaitingWindow, FailedWindow, labelWords, showsSteps, stepsOf, seatWords } from "./steps.js";
       // a task's steps: the label row's count, pips and step now, the lifted card's list (spec 129 H2)
import { CornerTop, CornerFoot, muchOf, figureOf, timeWords, secondsBetween } from "./corners.js";
                 // a card is read by its four corners (spec 147 A, decisions §251)
import { CardWindow, windowOf } from "./cardwindow.js";
                // a window never empty: the goal's picture, else words (spec 148)
import { MadeWindow, madeOf } from "./made.js";
                           // what a task done or at Review made, by its craft (spec 142 D)
import { movesOn } from "./lit.js";
                                  // a rune glows only on the goal that moves: the one picked, else the first at work (spec 140 C3)
import { ThrownPlace, thrown } from "./flight.js";
                         // a failed task's card thrown to the hand leaves its place (spec 128 C.2)

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
export { partKey, linkKey };
export const mineKey = (key) => typeof key === "string" && key.startsWith("t:");

/** What a card of this goal says it is about (the hand's lifted card marks it, hand/about.js): the goal and, for a task, itself. */
export const aboutTokens = (n, tasks = []) => `idea:${n.slug}${tasks.map((t) => ` task:${n.slug}/${t.id}`).join("")}`;

/** A lane card's window by its task's state, from the snapshot as it is (spec 142 C, decisions §249.3): failed, the alert and its reason; at work, the steps (else its doing line, else today's sign); waiting, the head of the seat that takes it,
 *  faint; otherwise the type's sign. Its height is fixed (table/work.css), so a lane's cards line up. */
const AT_WORK = ["doing", "checking"];
function TaskWin({ n, t, st, alive }) {
  const sign = typeSignOf(n, t), doing = String(t.steps?.doing ?? "").trim(), made = madeOf(t);
  let inside = null, kind = "sign";
  if (t.state === "failed") { inside = html`<${FailedWindow} reason=${t.error} />`; kind = "fail"; }
  else if (made) { inside = html`<${MadeWindow} t=${t} />`; kind = "made"; }
  else if (st) { inside = html`<${StepsWindow} st=${st} head=${t.head} element=${n.hue || n.element} alive=${alive} />`; kind = "steps"; }
  else if (doing && AT_WORK.includes(stageOf(t))) { inside = html`<${StepsWindow} st=${{ items: [], now: -1, done: 0, total: 0, source: "activity", doing }} head=${t.head} alive=${alive} />`; kind = "steps"; }
  else if (t.state === "waiting" || t.state === "ready") { inside = html`<${WaitingWindow} head=${t.head} />`; kind = inside ? "wait" : "sign"; }
  if (!inside) {                                                                      // where it would draw the type's sign alone: the goal's picture, else the task's words (spec 148 B.4, decisions §252.3)
    const words = t.short && t.short !== t.title ? t.title : "";
    if (windowOf({ picture: n.picture, words }).kind !== "none") return html`<${CardWindow} of=${{ picture: n.picture, words, name: n.title }} />`;
  }
  return html`<span class=${cls("table-card__win is-window", `is-${typeTone(n)}`, { "is-danger": kind === "fail" })} data-window=${kind}>${inside || (sign && (sign.startsWith("tool:") ? html`<span class=${`ork-tool ${sign.slice(5)}`} aria-hidden="true"></span>` : html`<${Sign} name=${sign} big=${true} />`))}</span>`;
}

/** A task, as a card in its goal's cascade: the task's name (no rune: the goal's is on its strip), the type in the window, the stage and, at its right, the gem when it spends. A task at work shows the flame in the stage's sign's place and says the time it has
 *  worked; a card whose state changed flashes its frame once (spec 107 §7, table.css; the flash is not played under reduced motion, the time still ticks). */
export function TaskCard({ n, t }) {
  const key = taskKey(n, t), on = lifted.value === key, bad = t.state === "failed", asks = t.state === "picking", gem = gemOf(t), alive = aliveState(t.state), done = t.state === "merged" || t.state === "review";
  const worked = useWorked(t.started, alive), changed = useChanged(t.state), away = thrown.value.get(`${n.slug}/${t.id}`);
  const st = showsSteps(t) ? stepsOf(t) : null, time = st && worked >= 0 ? `worked ${workedWords(worked)}` : "";                    // with steps the time worked is in the card's words, not on its label (spec 129 H2.1)
  const said = st ? `${t.title}, ${n.short || n.title}: ${labelWords(t)}${bad ? ", failed" : ""}${time && `, ${time}`}` : `${t.title}, ${n.short || n.title}: ${footWords(t)}`;
  if (away) return html`<${ThrownPlace} n=${n} t=${t} h=${away.h} />`;
  const kind = typeSignOf(n, t), sign = kind.startsWith("tool:") ? n.type?.sign || "" : kind, signal = bad ? "danger" : asks ? "alert" : done ? "success" : "";
  const much = muchOf({ asks, spend: figureOf(t.spend), est: figureOf(t.spend_est), cost: gem });                 // spec 168 C5, decisions §283.17: the foot's one figure is the spend (the time is in the tooltip and the small card's preview)
  const timed = timeWords({ done, took: secondsBetween(t.started, t.finished), left: Number(t.left ?? NaN), worked: alive && !st ? worked : NaN });
  return html`<button type="button" class=${cls("ork-card ork-leans table-card table-card--task", { [`el-${n.hue || n.element}`]: !!(n.hue || n.element), fails: bad, asks, "is-lifted": on, "is-lit": litKey.value === key, "is-changed": changed })} data-lkey=${key} data-goal=${n.slug} data-task=${t.id}
    data-about=${aboutTokens(n, [t])} data-state=${t.state} data-stage=${stageOf(t)} aria-pressed=${String(on)} aria-label=${said} title=${time || timed ? `${n.title} · ${time || timed}` : n.title} onClick=${() => lift(on ? "" : key)} ...${leans}>
    <${CornerTop} rune=${{ name: n.element, hue: n.hue, dim: !n.element, glowing: alive, still: !movesOn(n.slug) }} kind=${sign} signal=${signal} />
    <span class="table-card__head"><span class="table-card__nm" title=${t.title}>${t.short || t.title}</span></span>
    <${TaskWin} n=${n} t=${t} st=${st} alive=${alive} />
    <${CornerFoot} who=${t.head ? { heads: [t.head], word: seatWords(t.head) } : null} much=${much} />
  </button>`;
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
  const strip = host.querySelector(":scope > .cn-strip"), floor = strip ? Math.max(0, strip.getBoundingClientRect().bottom - h.top) : 0;       // a leader's strip (concerns.js) stays pressable above the back
  const left = Math.max(0, Math.min(c.left - h.left, h.width - w)), top = Math.max(floor, Math.min(c.top - h.top, h.height - t));
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
    <${ConcernsBack} el=${elOf(key)} />
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
    ${stepsOf(t) && html`<${Sec} label="Steps"><${StepsList} st=${stepsOf(t)} /></${Sec}>`}
    ${error && html`<${Sec} label="What went wrong"><span class="is-danger">${error}</span></${Sec}>`}
    ${full?.brief && html`<${Sec} label="Brief"><span class="table-back__text">${full.brief}</span></${Sec}>`}
    ${t.made && html`<${Sec} label="What it made"><span>${t.made}</span></${Sec}>`}
    ${mates.length > 0 && html`<${Sec} label="Its tasks"><span class="table-back__tasks">${mates.map((m) => html`<button type="button" key=${m.id} class="ork-btn quiet table-back__task" data-task=${m.id} onClick=${() => lift(taskKey(n, m))}>
      <${Sign} name=${STAGES[stageOf(m)].sign} /><span>${m.short || m.title}</span></button>`)}</span></${Sec}>`}
    <div class="table-back__acts"><${PickGoal} n=${n} /><button type="button" class="ork-btn table-back__open" onClick=${open}>Open</button></div>`;
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
