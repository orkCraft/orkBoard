// Reach on a party's map (docs/specs/165-each-leaders-map-a-board-games-shape.md J, decisions §280.1, §280.3, §280.4): what a goal not yet started would change, one and two steps out, drawn on the cards of the open map.
// Painted as heat.js and concerns.js paint (a map draws nothing of it): `ideas.reach {party}` is read when the map opens and when the Board's rev moves and kept in a signal; the goal shown is the one under the pointer or focus in the hand
// (hand/reachhover.js `reachGoal`), else the goal picked. Its entry stamps `data-reach="lit|one|two|dim"` on each `[data-pick-id]` card, touching only the cards whose state changes (reach.css draws the edges: solid, dashed, dotted,
// in the goal's element). A line over the map says it in words (*changes*, *reaches*, *no test*), no count. Hovering sends no command: the answer was kept. No entry, no goal: nothing stamped, no line.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { command } from "../link.js";
import { picked } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { HUES } from "../orkui.js";
import { reachGoal } from "../hand/reachhover.js";
import { nodeOf } from "./goalmap.js";
import { hasMap } from "./concerns.js";

if (typeof document !== "undefined") {
  const href = new URL("./reach.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const AGAIN_MS = 2500, AGAIN_TIMES = 3;                    // an empty answer (nothing kept yet) is asked again this often

/** The open map's reach as the host last gave it: `{[goal slug]: {lit, one, two, no_test}}` (ids of the map's parts). */
export const reachData = signal({});

/** The state of each card for the entry: `{id: "lit" | "one" | "two" | "dim"}`; null when the entry names nothing (nothing is lit). */
export function statesOf(entry, ids) {
  if (!entry) return null;
  const lit = new Set(entry.lit || []), one = new Set(entry.one || []), two = new Set(entry.two || []);
  if (!lit.size) return null;
  const out = {};
  for (const id of ids) out[id] = lit.has(id) ? "lit" : one.has(id) ? "one" : two.has(id) ? "two" : "dim";
  return out;
}

/** Stamps `states` on the cards of `host`; only a card whose state changes is touched. Returns the cards' names by state for the line. */
export function sync(host, states, noTest = []) {
  const bad = new Set(noTest), said = { lit: [], one: [], two: [], dim: [], bare: [] };
  for (const w of host.querySelectorAll("[data-pick-id]")) {
    const want = states ? states[w.dataset.pickId] || "dim" : "";
    if ((w.dataset.reach || "") !== want) { if (want) w.dataset.reach = want; else delete w.dataset.reach; }
    if (want) {
      said[want].push(w.dataset.pickName || w.dataset.pickId);
      if (bad.has(w.dataset.pickId)) said.bare.push(w.dataset.pickName || w.dataset.pickId);
    }
  }
  return said;
}

/** The line over the map, in words and with no count: the lit parts *change*, the ones one and two steps out *reach*, those with no test are named *no test*. */
export function lineOf(said) {
  if (!said || !said.lit.length) return "";
  const parts = [`changes ${said.lit.join(", ")}`];
  const out = [...said.one, ...said.two];
  if (out.length) parts.push(`reaches ${out.join(", ")}`);
  if (said.bare.length) parts.push(`no test ${said.bare.join(", ")}`);
  return parts.join(" · ");
}

function Inner({ g, children }) {
  const host = useRef(), [line, setLine] = useState(""), rev = mapData.value?.rev;
  const slug = reachGoal.value || picked.value || "", data = reachData.value, entry = slug ? data[slug] : null, node = slug ? nodeOf(slug) : null;
  const hue = HUES.includes(node?.hue) ? node.hue : HUES.includes(node?.element) ? node.element : "dust";
  useEffect(() => {                                        // read when the map opens and when the Board changes; the host answers what it kept
    let gone = false, timer = 0, n = 0;
    const ask = async () => {
      let got = {};
      try { got = (await command("ideas.reach", { party: g.slug }, true))?.goals || {}; } catch { /* an older host, or none */ }
      if (gone) return;
      reachData.value = got && typeof got === "object" ? got : {};
      if (!Object.keys(reachData.value).length && ++n < AGAIN_TIMES) timer = setTimeout(ask, AGAIN_MS);
    };
    ask();
    return () => { gone = true; clearTimeout(timer); };
  }, [g.slug, rev]);
  useEffect(() => () => { reachData.value = {}; }, [g.slug]);        // another party's map: what was kept for this one goes
  const paint = useRef();
  paint.current = () => {
    const el = host.current;
    if (!el) return;
    const ids = [...el.querySelectorAll("[data-pick-id]")].map((w) => w.dataset.pickId);
    const said = sync(el, statesOf(entry, ids), entry?.no_test);
    const now = lineOf(said);
    setLine((was) => (was === now ? was : now));
  };
  useLayoutEffect(() => { paint.current(); }, [entry, g.slug]);
  useEffect(() => {                                        // paint again whenever the map draws a card
    const el = host.current;
    if (!el) return undefined;
    let queued = false;
    const watch = new MutationObserver((list) => {
      if (queued || list.every((m) => m.type === "attributes" && m.attributeName === "data-reach")) return;
      queued = true;
      queueMicrotask(() => { queued = false; paint.current(); });
    });
    watch.observe(el, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-pick-id"] });
    return () => watch.disconnect();
  }, []);
  useEffect(() => () => { if (host.current) for (const w of host.current.querySelectorAll("[data-reach]")) delete w.dataset.reach; }, []);
  return html`<div ref=${host} class="rc-host" style="display:contents" data-hue=${hue} data-reach-map=${g.slug}>
    <p class="rc-line" role="status" aria-live="polite" hidden=${!line}>${line}</p>
    ${children}</div>`;
}

/** A party's map with the reach of the goal shown; a party with no map is left as it is. */
export const Reach = ({ g, children }) => (hasMap(g) ? html`<${Inner} key=${g.slug} g=${g}>${children}<//>` : children);
