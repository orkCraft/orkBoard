// What a goal reaches on the open tab's map, before it starts (docs/specs/117-each-lens-a-games-shape.md §4.2–§4.4, decisions §195): a goal under the pointer in the hand (hand/stopcard.js, `reachGoal`) or picked (frame/state.js `picked`) is
// asked of the host with `ideas.reach {party, slug}` → `{map, slug, element, state: "ok" | "no_will" | "none", near: {part id: 0 | 1 | 2}, guard?: {part id: bool}, links?: [[from, to]]}` — the parts it changes (0), what a change of those
// reaches one step out (1) and two (2), by the map's own relation (read by code, no call), and, on System alone, whether a test checks each. The cards of the map are painted as the heat is (heat.js) — any element carrying `data-pick-id`: in `near`,
// an edge `<i class="rc-edge" data-near>` inside the card (inset, in the goal's element: solid, dashed, dotted; the card's notch would clip an outline), on the touched card the element's rune at its top left, on a reached part of System the
// shield sign or *no test* there; the others dim (`data-reach-dim`). The edges come in nearest first (reach.css), none under reduced motion. The goal leaves and everything is as it was. `shownReach` is the reach on show,
// `{party, ...answer}` or null, for the links of System to light by (spec 117 F). `ReachLine` is the strip's line (concerns.js): *<goal> changes 2 parts · reaches 3 through what uses them · 2 with no test · through the hotspot lobby.ts*.
import { useEffect, useRef } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { Elem } from "../orkui.js";
import { command } from "../link.js";
import { picked } from "../frame/state.js";
import { reachGoal } from "../hand/state.js";
import { mapData } from "../shell/store.js";
import { mapName, partiesAll } from "./data.js";
import { cardEl } from "./pickbox.js";

if (typeof document !== "undefined") {
  const href = new URL("./reach.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** The reach on show: `{party, map, slug, element, state, near, guard, links}`, null for none. */
export const shownReach = signal(null);

const KEPT = 40;                                           // answers kept (per party, goal and revision of the Board)
const kept = new Map();
const WAIT_MS = 60;                                        // a pointer sweeping across the hand's cards asks for the one it rests on
const ELEMENTS = ["meadow", "ice", "dust", "void", "lava"];

/** The goal the table shows the reach of: the one under the pointer or focus in the hand, else the picked one (at the narrow width, with no pointer, the picked goal: a press on a card of the hand picks it), "" none. */
export const goalShown = () => reachGoal.value || picked.value || "";

const TEST = "A test checks it";

/** The edge of one card: `near` 0, 1 or 2; `guard` whether a test checks the part (System, a reached part), undefined where the map says nothing. */
function edgeOf(near, element, guard, sig) {
  const e = document.createElement("i");
  e.className = "rc-edge";
  e.dataset.near = String(near);
  e.dataset.elem = element;
  e.dataset.sig = sig;
  if (near === 0) {
    const rune = document.createElement("span");
    rune.className = `ork-elem ${element}`;
    rune.setAttribute("aria-hidden", "true");
    e.appendChild(rune);
  } else if (guard !== undefined) {
    const g = document.createElement("span");
    if (guard) {
      g.className = "rc-guard";
      g.title = TEST;
      g.setAttribute("role", "img");
      g.setAttribute("aria-label", TEST);
      const sign = document.createElement("span");
      sign.className = "ork-sign shield";
      sign.setAttribute("aria-hidden", "true");
      g.appendChild(sign);
    } else {
      g.className = "rc-guard is-none";
      g.textContent = "no test";
    }
    e.appendChild(g);
  }
  return e;
}

/** Paints the reach `r` (or none) on the cards of `host`: an edge on each part in `near`, the others dimmed while the goal reaches something, nothing left behind. */
export function paint(host, r) {
  const near = r?.near && Object.keys(r.near).length ? r.near : null, element = ELEMENTS.includes(r?.element) ? r.element : "dust";
  const wanted = new Map(), dim = new Set();
  if (near) {
    for (const w of host.querySelectorAll("[data-pick-id]")) {
      const id = w.dataset.pickId, card = cardEl(w), n = near[id];
      if (n === undefined) { dim.add(card); continue; }
      const guard = n > 0 && r.guard && typeof r.guard[id] === "boolean" ? r.guard[id] : undefined;
      wanted.set(card, { n, guard, sig: `${n}|${guard}|${element}` });
    }
  }
  for (const e of host.querySelectorAll(".rc-edge")) if (wanted.get(e.parentElement)?.sig !== e.dataset.sig) e.remove();
  for (const [card, o] of wanted) {
    if (card.querySelector(":scope > .rc-edge")) continue;
    if (getComputedStyle(card).position === "static") card.dataset.rcHost = "";
    card.prepend(edgeOf(o.n, element, o.guard, o.sig));
  }
  for (const el of host.querySelectorAll("[data-reach-dim]")) if (!dim.has(el)) delete el.dataset.reachDim;
  for (const el of dim) if (el.dataset.reachDim === undefined) el.dataset.reachDim = "";
}

/** A map with the reach of the goal shown: a box that asks the host for it (per party, goal and revision of the Board) and paints the cards drawn inside it. */
export function Reach({ g, children }) {
  const host = useRef(), party = g.slug, goal = goalShown(), rev = mapData.value?.rev, now = useRef(null);
  const again = () => { if (host.current) paint(host.current, now.current); };
  useEffect(() => {                                          // asked when the goal shown changes and when the Board does (the same goal keeps its picture until the new answer comes)
    let live = true, timer = 0;
    const key = `${party}|${goal}|${rev}`;
    const show = (r) => { now.current = r; shownReach.value = r; again(); };
    if (!goal) { show(null); return undefined; }
    if (now.current && now.current.slug !== goal) show(null);
    if (kept.has(key)) show(kept.get(key));
    else {
      timer = setTimeout(() => {
        command("ideas.reach", { party, slug: goal }, true).then((r) => {
          if (!live) return;
          const ok = r && !r.error && r.near && typeof r.near === "object" && r.map;
          const got = ok ? { party, ...r } : null;
          if (got) { kept.set(key, got); if (kept.size > KEPT) kept.delete(kept.keys().next().value); }
          show(got);
        }).catch(() => { if (live) show(null); });
      }, WAIT_MS);
    }
    return () => { live = false; clearTimeout(timer); };
  }, [party, goal, rev]);
  useEffect(() => {                                          // paint again whenever the map draws a card (the edges and the squares are ours: they are not watched)
    const el = host.current;
    if (!el) return undefined;
    let queued = false;
    const mine = (n) => n.classList?.contains("cn-slot") || n.classList?.contains("rc-edge");
    const ours = (m) => !!m.target.closest?.(".cn-slot, .rc-edge") || (m.type === "childList" && m.addedNodes.length + m.removedNodes.length > 0 && [...m.addedNodes, ...m.removedNodes].every(mine));
    const watch = new MutationObserver((list) => {
      if (queued || list.every(ours)) return;
      queued = true;
      queueMicrotask(() => { queued = false; again(); });
    });
    watch.observe(el, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-pick-id"] });
    return () => { watch.disconnect(); shownReach.value = null; };
  }, [party]);
  return html`<div ref=${host} class="rc-host" style="display:contents" data-reach-map=${party}>${children}</div>`;
}

// -- the strip's line --------------------------------------------------------------------------------------------------------------------------------------------------------

/** What each map's reach goes through, in the words after *reaches n* (spec 117 §0). */
const THROUGH = { system: "through what uses them", screens: "through the screens that lead to them", product: "through their jobs, goals and tests", "game-design": "through what their currencies feed", release: "with the goals it takes to main" };

const parts = (n) => `${n} ${n === 1 ? "part" : "parts"}`;

/** The words of a reach: what it changes, what it reaches, how many of those have no test and the hotspots it passes (each only when it is not nothing); `names` says a part's name for a reader. */
export function reachWords(r, heat, names = (id) => id) {
  const ids = Object.keys(r.near || {}), changed = ids.filter((id) => r.near[id] === 0), reached = ids.filter((id) => r.near[id] > 0);
  const open = r.guard ? reached.filter((id) => r.guard[id] === false) : [], hot = reached.filter((id) => (heat?.parts?.[id] || []).some((h) => h.kind === "hotspot"));
  return [changed.length && `changes ${parts(changed.length)}`, reached.length && `reaches ${reached.length} ${THROUGH[r.map] || ""}`.trim(), open.length && `${open.length} with no test`,
    hot.length && `through the hotspot ${hot.map(names).join(", ")}`].filter(Boolean).join(" · ");
}

/** The strip's line under the aspects while a goal is shown (spec 117 §0, §4.4): its element's rune first; *<goal>: what it reaches is known once its spec says what will change*, *<goal> changes nothing on <map>*, or the reach's words.
 *  Nothing while no goal is shown, or one shown for another party. `heat`: the party's heat (heat.js `heatNow`), for the hotspots. */
export function ReachLine({ party, heat }) {
  const r = shownReach.value;
  if (!r || r.party !== party) return null;
  const title = (mapData.value?.nodes || []).find((n) => n.slug === r.slug)?.title || r.slug, map = mapName(party, partiesAll());
  const names = (id) => document.querySelector(`.table-body [data-pick-id="${CSS.escape(id)}"]`)?.dataset.pickName || id;
  const words = r.state === "no_will" ? `${title}: what it reaches is known once its spec says what will change`
    : r.state === "ok" && Object.keys(r.near || {}).length ? reachWords(r, heat?.party === party ? heat : null, names) : "";
  return html`<div class="rc-line" data-state=${r.state} data-elem=${r.element} data-goal=${r.slug}>
    <${Elem} name=${r.element} />
    ${r.state === "ok" && words ? html`<span><b>${title}</b> ${words}</span>` : html`<span>${words || `${title} changes nothing on ${map}`}</span>`}
  </div>`;
}
