// Heat on a party's map (docs/specs/165-each-leaders-map-a-board-games-shape.md H, decisions §280.1, §183.5): what code found on a part, drawn on its card as at most three hollow squares beside the concern's mark.
// Painted as concerns.js paints (a map draws nothing of it): each card `[data-pick-id]` with hints gets a slot of its own (`.ht-slot`) in the home concerns.js gives its marks; the squares are decoration, a press falls through to the card.
// `ideas.heat {party}` is read when the map opens and when the Board's rev moves; the host answers what it kept (never a wait), so an empty answer is asked again a few times.
import { render } from "preact";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";
import { mapData } from "../shell/store.js";
import { cardEl } from "./pickbox.js";
import { hasMap, homeOf } from "./concerns.js";

if (typeof document !== "undefined") {
  const href = new URL("./heat.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const SHOWN = 3;                                           // squares on a card, at most
const AGAIN_MS = 2500, AGAIN_TIMES = 3;                    // an empty answer (nothing kept yet) is asked again this often

/** Every kind map_signals and map_signals_crafts give, in words (no game's name). */
export const HEAT_WORDS = {
  cycle: "parts that use one another in a loop", fan_in: "used by many parts", fan_out: "uses many parts", big: "holds a big file", hotspot: "big and often changed",
  shared_churn: "shared by many containers and often changed", unstable: "used by many and itself changing", untested_churn: "often changed and no test mapped",
  loose: "nothing leads here", dead_end: "leads nowhere", no_picture: "no picture kept", no_states: "says nothing of loading, error or empty states", a11y: "a hint on accessibility",
  pains: "many pains pinned here", pain_loose: "pains pinned to no part", unserved: "no goal serves this job", no_evidence: "no experiment tests the goals that serve it", vague_outcome: "an outcome with no number",
  off_tree: "goals in line serve no job", untested: "rests on an untested hypothesis",
  no_source: "a currency with no source", pile_up: "a currency that piles up", no_reward: "a loop that gives no reward", unfed: "a step that feeds nothing", flat: "a flat stretch",
  spike: "a sudden jump in intensity", no_hook: "no reason to come back on the first day", unground: "rests on no file",
  mixed_sizes: "pictures of many sizes", naming: "a name with a space or a capital", heavy: "a heavy file", unused: "no source file names it",
  big_batch: "a big batch waits for main", stale: "has waited long for main", no_changelog: "no changelog", reverts: "changes waiting that were reverts",
  no_channel: "no way to reach people", aso_title: "a store title that is too long", aso_short: "a store description that is too long", no_shots: "no screenshots in the store's files",
  no_onboarding: "nothing leads a new person to the first win", no_return: "nothing brings people back", no_revenue: "nothing says how it earns", no_share: "nothing lets people share it",
};
export const heatWords = (kind) => HEAT_WORDS[kind] || String(kind).replace(/_/g, " ");

/** The first SHOWN kinds, each once, in the hints' order. */
const kindsOf = (list) => [...new Set(list.map((h) => h.kind))].slice(0, SHOWN);

function Squares({ kinds }) {
  return html`${kinds.map((k) => html`<i key=${k} class="ht-sq" role="img" data-kind=${k} aria-label=${heatWords(k)} title=${heatWords(k)}></i>`)}`;
}

/** Paints the hints of the party's heat on the cards of `host`: a slot with squares on each card hints are on, no slot left behind. */
export function sync(host, heat) {
  const by = new Map(), used = new Set();
  for (const h of heat) if (h.on) by.set(h.on, [...(by.get(h.on) || []), h]);
  for (const w of host.querySelectorAll("[data-pick-id]")) {
    const list = by.get(w.dataset.pickId), card = cardEl(w), home = list && homeOf(card);
    if (!list || !home) continue;
    let slot = [...home.children].find((x) => x.classList?.contains("ht-slot") && x.dataset.htFor === w.dataset.pickId);
    if (!slot) {
      slot = document.createElement("span");
      slot.className = "ht-slot";
      slot.dataset.htFor = w.dataset.pickId;
      home.appendChild(slot);
    }
    used.add(slot);
    render(html`<${Squares} kinds=${kindsOf(list)} />`, slot);
  }
  for (const slot of host.querySelectorAll(".ht-slot")) if (!used.has(slot)) { render(null, slot); slot.remove(); }
}

function Inner({ g, children }) {
  const host = useRef(), [heat, setHeat] = useState([]), rev = mapData.value?.rev, state = useRef();
  state.current = heat;
  useEffect(() => {                                        // read when the map opens and when the Board changes
    let gone = false, timer = 0, n = 0;
    const ask = async () => {
      let got = [];
      try { got = (await command("ideas.heat", { party: g.slug }, true))?.heat || []; } catch { /* an older host, or none */ }
      if (gone) return;
      setHeat(Array.isArray(got) ? got : []);
      if (!got.length && ++n < AGAIN_TIMES) timer = setTimeout(ask, AGAIN_MS);
    };
    ask();
    return () => { gone = true; clearTimeout(timer); };
  }, [g.slug, rev]);
  useEffect(() => {                                        // paint again whenever the map draws a card (our slots, and concerns', are not watched)
    const el = host.current;
    if (!el) return undefined;
    let queued = false;
    const mine = (n) => n.classList?.contains("ht-slot") || n.classList?.contains("cn-slot");
    const ours = (m) => !!m.target.closest?.(".ht-slot, .cn-slot") || (m.type === "childList" && m.addedNodes.length + m.removedNodes.length > 0 && [...m.addedNodes, ...m.removedNodes].every(mine));
    const watch = new MutationObserver((list) => {
      if (queued || list.every(ours)) return;
      queued = true;
      queueMicrotask(() => { queued = false; sync(el, state.current); });
    });
    watch.observe(el, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-pick-id"] });
    return () => watch.disconnect();
  }, []);
  useLayoutEffect(() => { if (host.current) sync(host.current, heat); }, [heat]);
  useEffect(() => () => { if (host.current) for (const slot of host.current.querySelectorAll(".ht-slot")) render(null, slot); }, []);
  return html`<div ref=${host} class="ht-host" style="display:contents" data-heat-map=${g.slug}>${children}</div>`;
}

/** A party's map with its heat; a party with no map is left as it is. */
export const Heat = ({ g, children }) => (hasMap(g) ? html`<${Inner} key=${g.slug} g=${g}>${children}<//>` : children);
