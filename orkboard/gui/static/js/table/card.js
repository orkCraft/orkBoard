// A map's card on the table (docs/specs/98-the-table-and-the-hand.md §3.3, §3.5, §6; decisions §104.2, §120.1): 128 × 180, its goal's element top left, its kind's sign top right, its
// name up to four lines, at its foot the member's head and what it does. A card is **lifted where it lies** and turns over (`Lifted`): its back the details and **Open**; Esc or a press away lowers it,
// one at a time. A card leans toward the pointer and rises on orkUI's motion tokens (`.ork-leans`, the page sets `--ork-lean-x/-y`); nothing moves under reduced motion (orkUI's own rule).
// At the narrow width a column a head wide lays its tasks as tokens (`Token`), and what is lifted is a screen.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Elem, Head, Sign, WhoHead, headWords } from "../orkui.js";
import { lifted, lift, lower, picked, pick, openOver, partKey, linkKey } from "../frame/state.js";
import { TASK_STATE } from "../board/maplayout.js";
import { typeTone } from "../arena/goalwords.js";
import { footWords, doingWords, readTask } from "./data.js";

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

const typeOf = (n) => (n?.type?.sign ? html`<span class=${`table-card__type ${typeTone(n)}`} title=${n.type.name}><${Sign} name=${n.type.sign} /></span>` : null);

/** A task at work, as a card in its party's column: the goal's element, the type's sign (the alert sign when it failed or asks), its name, its member's head and what it does. */
export function TaskCard({ n, t, lit = false, dim = false }) {
  const key = taskKey(n, t), on = lifted.value === key, bad = t.state === "failed", asks = t.state === "picking";
  const said = `${t.title}, ${n.short || n.title}: ${footWords(t)}`;
  return html`<button type="button" class=${cls("ork-card ork-leans table-card", { fails: bad, asks, "is-lifted": on, "is-lit": lit || litKey.value === key, "is-dim": dim })} data-lkey=${key} data-goal=${n.slug} data-task=${t.id}
    data-about=${`idea:${n.slug} task:${n.slug}/${t.id}`} data-state=${t.state} aria-pressed=${String(on)} aria-label=${said} title=${n.title} onClick=${() => lift(on ? "" : key)} ...${leans}>
    <span class="table-card__top"><${Elem} name=${n.element} dim=${!n.element} />
      ${bad || asks ? html`<span class=${bad ? "is-danger" : "is-alert"}><${Sign} name="alert" /></span>` : typeOf(n)}</span>
    <span class="table-card__nm table-clamp" title=${t.title}>${t.short || t.title}</span>
    <span class="table-card__foot">${t.head ? html`<${WhoHead} head=${t.head} size="mid" />` : t.state === "running" || t.state === "testing" ? html`<span class="ork-busy" title="working"></span>` : null}
      <span class="table-card__cap">${footWords(t)}</span></span>
  </button>`;
}

/** A goal the Orkmaster reads or routes itself, as a card in its own column: its element, its name, its kind's sign, under it its crown and what it is doing. */
export function OwnCard({ n, lit = false }) {
  const key = ownKey(n), on = lifted.value === key;
  return html`<button type="button" class=${cls("ork-card ork-leans table-card table-card--own", { "is-lifted": on, "is-lit": lit || litKey.value === key })} data-lkey=${key} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state}
    aria-pressed=${String(on)} aria-label=${`${n.title}: ${doingWords(n)}`} onClick=${() => lift(on ? "" : key)} ...${leans}>
    <span class="table-own__r1"><${Elem} name=${n.element} dim=${!n.element || n.state === "reading"} /><span class="table-own__nm table-clamp" title=${n.title}>${n.short || n.title}</span>${typeOf(n)}</span>
    <span class="table-own__r2"><${Head} race="peon" tier="crown" /><span class="table-own__word">${doingWords(n)}</span></span>
  </button>`;
}

/** The same at a column a head wide (spec 67): a token with its element and its member's head, its name in the label and the title. */
export function Token({ n, t = null, lit = false }) {
  const key = t ? taskKey(n, t) : ownKey(n), on = lifted.value === key, bad = t?.state === "failed";
  const words = t ? `${t.title}, ${n.short || n.title}: ${footWords(t)}` : `${n.title}: ${doingWords(n)}`;
  return html`<button type="button" class=${cls("ork-card table-token", { fails: bad, "is-lifted": on, "is-lit": lit || litKey.value === key })} data-lkey=${key} data-goal=${n.slug} data-task=${t?.id} data-about=${t ? `idea:${n.slug} task:${n.slug}/${t.id}` : `idea:${n.slug}`} data-state=${t ? t.state : n.state}
    aria-pressed=${String(on)} aria-label=${words} title=${words} onClick=${() => lift(on ? "" : key)}>
    <span class="table-card__top"><${Elem} name=${n.element} dim=${!n.element} />${bad ? html`<span class="is-danger"><${Sign} name="alert" /></span>` : typeOf(n)}</span>
    ${t ? (t.head ? html`<${WhoHead} head=${t.head} />` : null) : html`<${Head} race="peon" tier="crown" />`}
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
  const error = full?.error || t.error || "";
  return html`<h3 class="table-back__nm">${t.title}</h3>
    <p class="table-back__cap">${n.title}</p>
    <${Sec} label="State"><span data-state=${t.state}>${TASK_STATE[t.state] || t.state}${t.note ? ` · ${t.note}` : ""}</span></${Sec}>
    ${t.head && html`<${Sec} label="Does it"><span class="table-back__who"><${WhoHead} head=${t.head} /> ${t.by?.name || ""} <span class="table-back__muted">${headWords(t.head)}</span></span></${Sec}>`}
    ${error && html`<${Sec} label="What went wrong"><span class="is-danger">${error}</span></${Sec}>`}
    ${full?.brief && html`<${Sec} label="Brief"><span class="table-back__text">${full.brief}</span></${Sec}>`}
    ${t.made && html`<${Sec} label="What it made"><span>${t.made}</span></${Sec}>`}
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
