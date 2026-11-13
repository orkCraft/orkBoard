// A task's failure thrown from its card to the hand (below), and the place its card leaves in the lane.
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { DEAL_MS, boxIn, reduced } from "../hand/motion.js";

// -- a failure thrown to the hand (docs/specs/128 C.2, decisions §206.7) -------------------------------------------------------------------------------------------------------------------
// A task that failed turns its card red where it lies (`fails`); after a beat the hand takes the failure as a card, dealt from that card (hand/motion.js `useHanded`, orkUI's `.ork-deal`, which turns a little as it flies), and the lane's card leaves a dashed place
// (orkUI's `.ork-card-place`) saying *Back here on Start again* (the failure card's button), for as long as the failure lies in the hand. Answered, the failure card flies back to the place (hand/stacks.js: its origin is the task's own card or its place) and the card returns.
// The hand calls `useThrown(stops)`: it holds a fresh failure back for the beat (the card is red meanwhile), and keeps `thrown` (the lane's tasks that lie in the hand, `goal/task` → the card's height) that `TaskCard` reads. A failure already there when the
// page is drawn, one the page was not shown for, one of a task with no card in view (another tab, a phone) and reduced motion: no beat, no flight: the failure is in the hand and the place is in the lane.

export const thrown = signal(new Map());                  // "goal/task" → {h}: the tasks whose failure lies in the hand
export const BEAT_MS = 700;                               // how long a failed card stays red where it lies before it is thrown
const sheet = typeof document !== "undefined" ? new URL("./flight.css", import.meta.url).href : "";
if (sheet && !document.querySelector(`link[href="${sheet}"]`)) {
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = sheet;
  document.head.appendChild(link);
}

/** The key a failure of a task is thrown under, "" for a stop that is not a failed task. */
export const failKey = (s) => (s.kind === "failed" && s.node && s.task ? `${s.node.slug}/${s.task.id}` : "");

const cardOf = (k) => {
  const [goal, task] = [k.slice(0, k.indexOf("/")), k.slice(k.indexOf("/") + 1)];
  return boxIn(document.querySelector(`.frame-table [data-goal="${CSS.escape(goal)}"][data-task="${CSS.escape(task)}"].table-card`));
};
const put = (k, v) => { const m = new Map(thrown.peek()); if (v) m.set(k, v); else m.delete(k); thrown.value = m; };

/** The hand's stops with the failures that are still red left out (they come after the beat); keeps `thrown` for the lanes. `stops`: the hand's stops, `ready`: the project is drawn (what is there at its first draw is not thrown). */
export function useThrown(stops, ready = true) {
  const keys = stops.map(failKey).filter(Boolean), st = useRef(null), [, tick] = useState(0);
  if (st.current === null) st.current = { adm: new Set(), wait: new Map(), gone: new Map(), first: true, seeded: false };
  if (ready && !st.current.seeded) { st.current.seeded = true; for (const k of keys) st.current.adm.add(k); }           // what is there at the project's first draw is in the hand at once
  const { adm, wait, gone } = st.current;
  useLayoutEffect(() => {
    if (!ready) return;                                                                    // the project is not drawn yet: its first draw is still to come
    const now = new Set(keys), first = st.current.first;
    st.current.first = false;
    const admit = (k) => {
      const box = cardOf(k);
      clearTimeout(gone.get(k)); gone.delete(k);
      adm.add(k);
      put(k, { h: box ? Math.round(box.height) : 0 });
    };
    for (const k of [...adm]) if (!now.has(k)) {                                          // its failure left the hand (tried again, dropped): the place stays while the card flies back, then the card returns
      adm.delete(k);
      gone.set(k, setTimeout(() => { gone.delete(k); put(k, null); }, DEAL_MS + 100));
    }
    for (const [k, t] of [...wait]) if (!now.has(k)) { clearTimeout(t); wait.delete(k); }
    for (const k of now) {
      if (first) { admit(k); continue; }                                                   // already failed when the page was drawn: in the hand, its place in the lane, no flight
      if (adm.has(k) || wait.has(k)) continue;
      if (reduced() || document.hidden || !cardOf(k)) { admit(k); tick((n) => n + 1); continue; }
      wait.set(k, setTimeout(() => {                                                       // the beat is over: the card's place is laid, then the hand takes the failure (a moment later: the card is in the hand's frame once the place is in the lane)
        admit(k);
        setTimeout(() => { wait.delete(k); tick((n) => n + 1); }, 60);
      }, BEAT_MS));
    }
  });
  useLayoutEffect(() => () => { for (const t of [...wait.values(), ...gone.values()]) clearTimeout(t); }, []);
  return stops.filter((s) => { const k = failKey(s); return !k || adm.has(k) && !wait.has(k); });
}

/** A lane's place for a failure that lies in the hand: orkUI's card outline where the card lay, its height kept, *Back here on Try again*. */
export function ThrownPlace({ n, t, h = 0 }) {
  return html`<div class="ork-card-place table-thrown" data-goal=${n.slug} data-task=${t.id} data-about=${`idea:${n.slug} task:${n.slug}/${t.id}`} data-place="thrown" style=${h ? `height:${h}px` : undefined} aria-label=${`${t.title}: back here when you try again`}>
    <span class="table-thrown__words ork-plate">Back here on <i>Start again</i></span></div>`;
}
