// The phone's hand, its row (docs/specs/147-one-card-four-corners.md part F.2, decisions §251.5; before: docs/specs/117-the-phone-a-menu-of-the-leaders.md §3.2, decisions §195.4): one card an entry (entries.js `entriesOf`: a goal's cards one entry, a card of no goal one, a goal ready for main one), **laid by leader**: before each
// group a 22 px separator with the leader's head (the crown's for the project's lane, then each party's leader, the goals ready for main last under the lich's), in the lanes' order. A card is 80 x 112, **cut at 62** by the row: its rune and kind and its title in two lines show; under the cut why it is asked, who
// asks and what it costs. **Pressed, a card rises and shows the rest; tapped, it opens** (a press picks it: entries.js `pickEntry`, the middle shows it opened). The picked entry wears the ink's frame. The row scrolls sideways under the + card, which lies at its right end, fixed (a press opens the field: updeck.js `DeckField`).
// No count, and no edge for the rest of a goal's cards. With no entry the row is the + card alone.
// **A card that lands out of the row's view** (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.9, decisions §198.9) moves no scroll: the row's cue at its edge (scrollcue.js: the fade of what lies beyond) brightens once, at the side the card lies (`data-cue`: a strip at that
// edge for `CUE_MS`; static under reduced motion), so the person sees that a card came. A card that lands in view says nothing more; a page hidden meanwhile, none (§89.0). Layout only (upright.css); every colour, face and corner is orkUI's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { gateData } from "../shell/store.js";
import { CornerFoot, CornerTop, muchOf } from "../table/corners.js";
import { partiesNow } from "../table/data.js";
import { actionOf, askerOf, footOf, handsWords, headOf, labelOf, signalOf, upName, whoOf } from "./stopcard.js";
import { costOf } from "./cost.js";
import { laneOf } from "./data.js";
import { laneHead } from "./stacks.js";
import { handedName, useFlight, useHanded } from "./motion.js";
import { pickEntry } from "./entries.js";
import { PlusCard } from "./pluscard.js";
import { useScrollCue } from "../scrollcue.js";

const ASKS = ["asks", "goal", "pick", "collide"];
export const CUE_MS = 1400;                                  // how long the edge cue is bright

/** Which side of the row a card lies out of view on: "right" (past the clear part, the + card lies over the row's right end), "left", "" when it is wholly in view or not drawn. */
export function sideOut(row, el, plusW = 0) {
  if (!row || !el) return "";
  const r = row.getBoundingClientRect(), c = el.getBoundingClientRect();
  return c.right > r.right - plusW + 0.5 ? "right" : c.left < r.left - 0.5 ? "left" : "";
}

/** What an entry's card says of itself, read by its four corners (spec 147 A): `{name, label, element, hue, kind, signal, why, asker, cost, ask, fail}`; a ready goal's kind is the check in the success colour, it asks nothing and costs nothing; `ask`/`fail` put the card in the alert's frame. */
function faceOf(e) {
  if (e.kind === "ready") {
    const name = `${e.name} is ready for ${gateData.value?.main || "main"}`;
    return { name, label: name, element: e.element, hue: e.hue || "", kind: "check", signal: "success", why: "", asker: e.head, cost: null, ask: false, fail: false };
  }
  const s = e.stops[0], cost = costOf(s);
  return { name: upName(s), label: labelOf(s), element: s.node?.element || "", hue: s.node?.hue || "", kind: actionOf(s).sign, signal: signalOf(s), why: footOf(s), asker: headOf(s), cost: cost ? { ...muchOf({ cost: cost.gem }), share: !!cost.share } : null, ask: ASKS.includes(s.kind), fail: s.kind === "failed" };
}

/** One entry as a card of the row: 80 x 112, cut at 62 by the row (upright.css): its rune and kind, its title in two lines; under the cut why it is asked, who asks and what it costs, which a press shows by lifting the card. */
function Entry({ e, on, onPick, dealt }) {
  const f = faceOf(e), ref = useRef(), from = handedName(e.key);
  useFlight(ref, dealt, true);                                         // a card handed from the crown (or the goal in the middle) flies as a copy over everything: the row clips what flies in it
  return html`<button ref=${ref} type="button" class=${cls("ork-card up-card", { asks: f.ask, fails: f.fail, "is-picked": on })} data-key=${e.key} data-kind=${e.kind} data-from=${from || undefined} aria-label=${`${f.label}${from ? `, from ${from}` : ""}`} aria-pressed=${String(on)} onClick=${onPick}>
    <${CornerTop} rune=${{ name: f.element, hue: f.hue, dim: !f.element }} kind=${f.kind} signal=${f.signal} />
    <span class="up-card__name">${f.name}</span>
    <span class="up-card__why">${f.why}</span>
    <${CornerFoot} who=${f.asker ? { heads: [f.asker] } : null} much=${f.cost} />
  </button>`;
}

/** The entries' groups, one a leader (the hand laid by leader, spec 147 F.2): in the lanes' order (the project's first, under the crown's head, then each party's under its leader's), the goals ready for main last under the lich's head; each `{key, lane, head, entries}`. */
export function groupsOf(entries, parties = partiesNow()) {
  const by = new Map();
  for (const e of entries) {
    const lane = e.kind === "ready" ? Infinity : laneOf(e.stops[0], parties);
    if (!by.has(lane)) by.set(lane, { key: String(lane), lane, head: e.kind === "ready" ? e.head : laneHead(lane, parties[lane - 1]), entries: [] });
    by.get(lane).entries.push(e);
  }
  return [...by.values()].sort((a, b) => a.lane - b.lane);
}

/** The row: the entries' cards laid by leader, the picked one (`cur`) raised and kept in view, the + card at the end. */
export function Row({ entries, cur, plus }) {
  const cards = useRef(), seen = useRef(null), [cue, setCue] = useState(""), dealt = useHanded(entries.filter((e) => e.kind !== "ready").map((e) => ({ key: e.key, top: true, ...whoOf(e.stops[0]), name: askerOf(e.stops[0]), words: handsWords(e.stops[0]) })));
  useEffect(() => {                                              // the picked card is kept inside the row's clear part (the + card lies over its right end)
    const row = cards.current, el = row?.querySelector('[aria-pressed="true"]');
    if (!row || !el) return;
    const r = row.getBoundingClientRect(), c = el.getBoundingClientRect(), plusW = row.parentElement.querySelector(".up-plus")?.offsetWidth || 0, gutter = 12;
    if (c.left < r.left + gutter) row.scrollLeft -= r.left + gutter - c.left;
    else if (c.right > r.right - plusW - gutter) row.scrollLeft += c.right - (r.right - plusW - gutter);
  }, [cur?.key, entries.length]);
  useScrollCue(cards);
  const keys = entries.map((e) => e.key).join("|");
  useLayoutEffect(() => {                                        // a card that came and lies out of view: the row's edge cue brightens once; the row does not scroll
    const was = seen.current, now = new Set(entries.map((e) => e.key));
    seen.current = now;
    if (!was || document.hidden) return undefined;
    const row = cards.current, plusW = row?.parentElement.querySelector(".up-plus")?.offsetWidth || 0;
    const sides = entries.filter((e) => !was.has(e.key)).map((e) => sideOut(row, row?.querySelector(`[data-key="${CSS.escape(e.key)}"]`), plusW)).filter(Boolean);
    if (!sides.length) return undefined;
    setCue(sides.includes("right") ? "right" : "left");
    const t = setTimeout(() => setCue(""), CUE_MS);
    return () => clearTimeout(t);
  }, [keys]);
  return html`<div class="up-row" role="group" aria-label="Cards in the hand" data-cue=${cue || undefined}>
    <div class="up-cards gui-scrolls" ref=${cards}>${groupsOf(entries).flatMap((g) => [
      html`<span key=${`sep:${g.key}`} class="up-sep" data-lane=${g.key} aria-hidden="true">${g.head && html`<${Head} race=${g.head.race} tier=${g.head.tier} />`}</span>`,
      ...g.entries.map((e) => html`<${Entry} key=${e.key} e=${e} on=${cur?.key === e.key} onPick=${() => pickEntry(e)} dealt=${dealt[e.key] ?? null} />`)])}</div>
    <div class="up-plus"><${PlusCard} onPress=${plus} /></div>
  </div>`;
}
