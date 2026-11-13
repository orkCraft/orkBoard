// A question passed on (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part D.3, decisions §206.6): a leader's question that another party's map or the code answers is not dealt to the hand; the host keeps it
// in the snapshot's `passing` (`{id, idea, task, by, to, q, left_s, answering}`, realm/idea_pass.py) for ten seconds. **On the page** it is a small card over the Orkmaster's column's foot: its goal's rune, the two heads (who asked, who it
// is passed to), the question and *passing on · 6 s* (counted down here between snapshots). Pressed it shows **Answer it myself** (`ideas.pass_take`: the person's, dealt to the hand now) and **Pass it now** (`ideas.pass_now`).
// When the call begins (`answering`) the card flies to the answering leader's tab, which says *answering…*; the answer given, the row is gone. A flight plays once and only when seen (the page shown, no reduced motion: §89.0); otherwise the card is simply gone, the line simply there.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head } from "../orkui.js";
import { town } from "../link.js";
import { act, mapData } from "../shell/store.js";
import { boxIn, reduced, spring, tokenMs } from "../hand/motion.js";
import { nameOf, partiesAll } from "./data.js";

export const passFlights = { out: 0, now: 0 };                // how many cards have flown to a tab, and fly now (what a test reads)
const CROWN = { race: "peon", tier: "crown" };                 // the Orkmaster's head: a question asked with no party of its own
const SHOWN = 3;                                               // a round asks three questions at most (core/idea_pass.py `MAX_PASSING`)

/** The snapshot's passing questions. */
export const passingRows = () => town.value?.passing || [];

const partyOf = (slug) => partiesAll().find((g) => g.slug === slug) || null;

/** Whether a party's leader is answering a question passed to it: its tab says *answering…*. */
export const answeringOn = (slug) => passingRows().some((r) => r.answering && r.to === slug);

/** *Asked Tech* for a goal whose question waits to be passed on or is being answered by another leader, "" when it is not. */
export function askedWords(slug) {
  const r = passingRows().find((x) => x.idea === slug);
  return r ? `Asked ${nameOf(partyOf(r.to)) || r.to}` : "";
}

/** The seconds left, counted down between snapshots from the one that last said it. */
function useLeft(row) {
  const base = useRef(null), [, tick] = useState(0);
  if (!base.current || base.current.s !== row.left_s) base.current = { s: row.left_s, at: performance.now() };
  useEffect(() => { const t = setInterval(() => tick((n) => n + 1), 250); return () => clearInterval(t); }, []);
  return Math.max(0, Math.ceil(base.current.s - (performance.now() - base.current.at) / 1000));
}

const headOf = (slug) => partyOf(slug)?.leader?.head || CROWN;

function Card({ row, node }) {
  const [open, setOpen] = useState(false), [busy, setBusy] = useState(false), left = useLeft(row), a = headOf(row.by), b = headOf(row.to);
  const el = node?.element || "", hue = node?.hue || el, to = nameOf(partyOf(row.to)) || row.to, by = nameOf(partyOf(row.by)) || "The Orkmaster";
  const run = (name) => async () => { setBusy(true); try { await act(name, { id: row.id }); } finally { setBusy(false); } };
  return html`<div class=${cls("ork-card col-pass", { "is-open": open })} data-pass=${row.id} data-goal=${row.idea} data-about=${`idea:${row.idea}`}>
    <button type="button" class="col-pass__main" aria-expanded=${String(open)} aria-label=${`${by} asks ${to}: ${row.q}; passing on in ${left} seconds; press to answer it yourself or pass it now`} onClick=${() => setOpen(!open)}>
      <span class="col-pass__who"><${Elem} name=${el} hue=${hue} dim=${!el} /><${Head} race=${a.race} tier=${a.tier} /><${Head} race=${b.race} tier=${b.tier} /></span>
      <span class="col-pass__q">${row.q}</span>
      <span class="col-pass__left" data-left=${left}>passing on · ${left} s</span>
    </button>
    ${open && html`<span class="col-pass__acts">
      <button type="button" class="ork-btn quiet" data-pass-take=${row.id} disabled=${busy} title="The question is yours: it is dealt to your hand now" onClick=${run("ideas.pass_take")}>Answer it myself</button>
      <button type="button" class="ork-btn quiet" data-pass-now=${row.id} disabled=${busy} title=${`${to} answers it now, in one call`} onClick=${run("ideas.pass_now")}>Pass it now</button>
    </span>`}
  </div>`;
}

const kept = new Map();          // id → {rect, copy, idea, to, out}: the card as it last lay (to fly from), and whether it has flown to its tab

/** A copy of the card flies from its box to a point (the tab's top middle), shrinking and fading. */
async function fly(copy, box, at) {
  const g = copy, dx = at.left - box.left, dy = at.top - box.top, away = `translate(${dx}px, ${dy}px) scale(0.25)`;
  g.classList.add("table-flyer");
  g.setAttribute("aria-hidden", "true");
  g.inert = true;
  g.style.cssText = `position:fixed;left:${box.left}px;top:${box.top}px;width:${box.width}px;height:${box.height}px;margin:0;z-index:90;pointer-events:none;transform-origin:0 0;`;
  document.body.appendChild(g);
  passFlights.now++;
  try {
    const frames = [{ transform: "none", opacity: 1 }, { transform: away, opacity: 0.2 }];
    await g.animate(frames, { duration: tokenMs("--ork-motion-play", 400) * 1.2, easing: spring(), fill: "forwards" }).finished;
  } finally { g.remove(); passFlights.now--; }
}

const seen = () => !reduced() && !document.hidden;
const tabAt = (slug) => { const r = document.getElementById(`tab-${slug}`)?.getBoundingClientRect(); return r && r.width ? { left: r.left + r.width / 2, top: r.top } : null; };

/** The card flies to the answering leader's tab once its call begins, and a copy of it flies from the tab into the goal's card once the answer is given. Not seen (the page hidden, reduced motion, no tab or card in view): no flight. */
function useFlights(rows) {
  useLayoutEffect(() => {
    const now = new Map(rows.map((r) => [r.id, r]));
    for (const [id, was] of [...kept]) {
      const r = now.get(id), tab = tabAt(was.to);
      if (r?.answering && !was.out) {
        was.out = true;
        if (was.copy && tab && seen()) { passFlights.out++; fly(was.copy.cloneNode(true), was.rect, tab).catch(() => {}); }
      } else if (!r) kept.delete(id);
    }
    for (const r of rows) {
      const el = document.querySelector(`.col-pass[data-pass="${CSS.escape(r.id)}"]`), was = kept.get(r.id);
      if (el) { const box = boxIn(el); kept.set(r.id, { rect: { left: box.left, top: box.top, width: box.width, height: box.height }, copy: el.cloneNode(true), idea: r.idea, to: r.to, out: !!was?.out }); }
      else if (!was) kept.set(r.id, { rect: null, copy: null, idea: r.idea, to: r.to, out: !!r.answering });          // already answering when the page was drawn: no flight
    }
  }, [rows.map((r) => `${r.id}:${r.answering ? 1 : 0}`).join("|")]);
}

/** The small cards over the column's foot: the questions waiting to be passed on (the ones being answered are on their leaders' tabs). */
export function Passing() {
  const rows = passingRows(), nodes = mapData.value?.nodes || [];
  useFlights(rows);
  const shown = rows.filter((r) => !r.answering).slice(0, SHOWN);
  if (!shown.length) return null;
  return html`<div class="col-passing" role="group" aria-label="Questions being passed on">${shown.map((r) => html`<${Card} key=${r.id} row=${r} node=${nodes.find((n) => n.slug === r.idea)} />`)}</div>`;
}
