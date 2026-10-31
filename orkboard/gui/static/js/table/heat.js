// Heat on a map's cards (docs/specs/117-each-lens-a-games-shape.md §4.1, decisions §195): the hints code finds on a part (`map_signals`, read by `ideas.heat {party}`: `{map, parts: {part id: [{kind, aspect, words}]}}`, three a part at most),
// drawn on it as hollow squares (concerns.css `.cn-hint`, 6 × 6), one for each kind, in the concern's slot — the box at the card's top right where a leader's mark lies (concerns.js `slotOf`), before the mark. A card with heat also carries
// `data-heat="<kind> <kind>"` so a map's sheet may style a kind. The squares' title is the hints' words, a line each. No count, no colour: the leader's alert sign stays the concern's.
// `Heat` is a box round the map (no box of its own: `display: contents`) that reads the party's heat, again when the Board moves or a task lands (`mapData.rev`; a merge moves dev), and paints on every card with a `[data-pick-id]`
// (a map's `Pickable`, System's stamped parts), as concerns.js does: a MutationObserver keeps it painted while the map draws its cards. A host without the command draws nothing and throws nothing. The last read is `heatNow`,
// which the strip's line reads for the hotspot clause (reach.js `ReachLine`).
import { useEffect, useRef } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { command } from "../link.js";
import { mapData } from "../shell/store.js";
import { cardEl } from "./pickbox.js";
import { slotOf } from "./concerns.js";                     // concerns.js loads this module too: nothing of it is used while the modules load

if (typeof document !== "undefined") {
  const href = new URL("./heat.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** The heat of the open party's map as the host last gave it: `{party, map, parts}`, null while there is none (no map, no command, a read under way for another party). */
export const heatNow = signal(null);

/** The tasks landed on the Board: the heat is read again when one more lands (a merge moves dev), as systemmap.js reads the System. */
const landedOf = (m) => (m?.nodes || []).reduce((k, n) => k + (n.tasks || []).filter((t) => t.state === "merged").length + (n.state === "done" ? 1 : 0), 0);

/** The squares of one card: a title of the hints' words, a line each. */
function squares(list) {
  const box = document.createElement("span"), words = list.map((h) => h.words).filter(Boolean);
  box.className = "cn-heat";
  box.setAttribute("role", "img");
  box.title = words.join("\n");
  box.setAttribute("aria-label", words.join("; ") || "Hints from code");
  box.dataset.kinds = list.map((h) => h.kind).join(" ");
  for (let i = 0; i < list.length; i++) {
    const sq = document.createElement("i");
    sq.className = "cn-hint";
    sq.setAttribute("aria-hidden", "true");
    box.appendChild(sq);
  }
  return box;
}

/** Paints `parts` on the cards of `host`: the squares in each card's slot, `data-heat` on the card, nothing and no slot left behind on the others. */
export function paint(host, parts) {
  const used = new Set(), held = new Set();
  for (const w of host.querySelectorAll("[data-pick-id]")) {
    const list = parts[w.dataset.pickId], card = cardEl(w);
    if (!Array.isArray(list) || !list.length || w.closest(".is-gone") || w.getAttribute("aria-hidden") === "true") continue;
    const slot = slotOf(card, w.dataset.pickId);
    if (!slot) continue;
    const kinds = list.map((h) => h.kind).join(" "), have = slot.querySelector(":scope > .cn-heat");
    if (!have || have.dataset.kinds !== kinds || have.title !== list.map((h) => h.words).filter(Boolean).join("\n")) {
      have?.remove();
      const box = squares(list);
      box.addEventListener("click", () => { if (!card.contains(box)) card.click(); });          // beside a button (System's part) the squares are not in it: a press on them is a press on the card
      slot.prepend(box);
    }
    used.add(slot);
    held.add(card);
    if (card.dataset.heat !== kinds) card.dataset.heat = kinds;
  }
  for (const slot of host.querySelectorAll(".cn-slot")) {
    if (used.has(slot)) continue;
    slot.querySelector(":scope > .cn-heat")?.remove();
    if (!slot.querySelector(".cn-slot__m")) slot.remove();
  }
  for (const el of host.querySelectorAll("[data-heat]")) if (!held.has(el)) delete el.dataset.heat;
}

/** A map with its heat: a box that reads `ideas.heat` for party `g` and paints the squares on the cards drawn inside it. */
export function Heat({ g, children }) {
  const host = useRef(), party = g.slug, rev = mapData.value?.rev, landed = landedOf(mapData.value), parts = useRef({});
  const again = () => { if (host.current) paint(host.current, parts.current); };
  useEffect(() => {                                          // read when the map is opened, when the Board changes and when a task lands
    let live = true;
    command("ideas.heat", { party }, true).then((r) => {
      if (!live) return;
      const ok = r && !r.error && r.parts && typeof r.parts === "object";
      parts.current = ok ? r.parts : {};
      heatNow.value = ok && r.map ? { party, map: r.map, parts: r.parts } : null;
      again();
    }).catch(() => { if (live) { parts.current = {}; heatNow.value = null; again(); } });
    return () => { live = false; };
  }, [party, rev, landed]);
  useEffect(() => {                                          // paint again whenever the map draws a card (the squares are ours: they are not watched)
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
    return () => { watch.disconnect(); heatNow.value = null; };
  }, [party]);
  return html`<div ref=${host} class="hs-host" style="display:contents" data-heat-map=${party}>${children}</div>`;
}
