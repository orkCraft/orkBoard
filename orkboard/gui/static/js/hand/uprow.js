// The phone's hand, its row (docs/specs/117-the-phone-a-menu-of-the-leaders.md §3.2, docs/mockups/phone/sidebar.html, decisions §195.4): one card an entry (entries.js `entriesOf`: a goal's cards one entry, a card of no goal one, a goal ready for
// main one), each showing its upper part — its element, its name (three lines at most: stopcard.js `upName`), its window with the action's sign and its asker's head small in the corner (the alert's colour when it asks or failed) —, in a row that
// scrolls sideways under the + card, which lies at the row's right end, fixed (a press opens the field: updeck.js `DeckField`). The picked entry is raised and wears the ink's frame; a press picks it (entries.js `pickEntry`). No count, and no
// edge for the rest of a goal's cards. With no entry the row is the + card alone.
// **A card that lands out of the row's view** (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.9, decisions §198.9) moves no scroll: the row's cue at its edge (scrollcue.js: the fade of what lies beyond) brightens once, at the side the card lies (`data-cue`: a strip at that
// edge for `CUE_MS`; static under reduced motion), so the person sees that a card came. A card that lands in view says nothing more; a page hidden meanwhile, none (§89.0). Layout only (upright.css); every colour, face and corner is orkUI's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { gateData } from "../shell/store.js";
import { Mark, askerOf, handsWords, headOf, labelOf, upName, whoOf } from "./stopcard.js";
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

/** What an entry's card says of itself: `{name, label, element, asker, sign, ask, fail}`; `sign` is the window's (a ready goal's is the check), `ask`/`fail` put the card in the alert's colour. */
function faceOf(e) {
  if (e.kind === "ready") {
    const name = `${e.name} is ready for ${gateData.value?.main || "main"}`;
    return { name, label: name, element: e.element, hue: e.hue || "", asker: e.head, sign: null, ask: false, fail: false };
  }
  const s = e.stops[0];
  return { name: upName(s), label: labelOf(s), element: s.node?.element || "", hue: s.node?.hue || "", asker: headOf(s), sign: s, ask: ASKS.includes(s.kind), fail: s.kind === "failed" };
}

/** One entry as a card of the row. */
function Entry({ e, on, onPick, dealt }) {
  const f = faceOf(e), ref = useRef(), from = handedName(e.key);
  useFlight(ref, dealt, true);                                         // a card handed from the crown (or the goal in the middle) flies as a copy over everything: the row clips what flies in it
  return html`<button ref=${ref} type="button" class=${cls("ork-card up-card", { asks: f.ask, fails: f.fail, "is-picked": on })} data-key=${e.key} data-kind=${e.kind} data-from=${from || undefined} aria-label=${`${f.label}${from ? `, from ${from}` : ""}`} aria-pressed=${String(on)} onClick=${onPick}>
    <span class="up-card__head"><${Elem} name=${f.element} hue=${f.hue} dim=${!f.element} /><span class="up-card__name">${f.name}</span></span>
    <span class="up-card__window">${f.sign ? html`<${Mark} s=${f.sign} big=${true} />` : html`<span class="hand-mark is-ok"><${Sign} name="check" big=${true} /></span>`}
      ${f.asker && html`<span class="up-card__asker"><${Head} race=${f.asker.race} tier=${f.asker.tier} /></span>`}</span>
  </button>`;
}

/** The row: the entries' cards, the picked one (`cur`) raised and kept in view, the + card at the end. */
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
    <div class="up-cards gui-scrolls" ref=${cards}>${entries.map((e) => html`<${Entry} key=${e.key} e=${e} on=${cur?.key === e.key} onPick=${() => pickEntry(e)} dealt=${dealt[e.key] ?? null} />`)}</div>
    <div class="up-plus"><${PlusCard} onPress=${plus} /></div>
  </div>`;
}
