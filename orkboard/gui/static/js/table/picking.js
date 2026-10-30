// Picking on a party's map (docs/specs/102-the-other-maps-and-picking-on-them.md §6, decisions §141, §152, docs/mockups/s3/ state 7). While the + card's field is addressed to a party (*→ Tech ×* or *@Tech*), that
// party's map is in picking: the strip over it (*Pick a part to point at it* · *Stop picking*; with another tab open, *Open Tech's map to pick*), a press on a card toggles it as a mark (orkUI's `.ork-picked` brackets, lifted),
// a drag from the map's empty place draws the box and takes what it covers (pickbox.js: Shift adds; on a touch screen a long press on the empty place, then a drag), a box that takes a whole group pins the group
// (one mark `{map, group, name}`), the whole map *all of <map>* (read as no mark, sent as none). The marks lie on the field as chips (a name and ×; past five, the first five and *and n more*). Picking ends with *Stop
// picking*, Esc, sending, or the address taken off; what was taken stays the idea's marks until it is sent.
// A card of a map is any element carrying `data-pick-map`, `data-pick-id`, `data-pick-name` (and `data-pick-group`, `data-pick-group-name`): maps.js `Pickable` draws a wrapper (`display: contents`, the card its first child)
// with them; System's own cards are stamped with them by syspane.js. Which cards are marked is painted on the cards by `sync` (classes and `data-picked`), so a map draws nothing of picking itself.
import { Fragment } from "preact";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { computed, effect, signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { openTab, tab } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { addressOf, fieldOff, fieldOpen, fieldText } from "../hand/state.js";
import { partiesOf, partyCard } from "../hand/data.js";
import { leadsSystem, mapName, partiesAll } from "./data.js";
import { mapOf, pickWith } from "./maps.js";
import { cardEl, cardsIn, gestureEnded, usePickGestures } from "./pickbox.js";

if (typeof document !== "undefined") {
  const href = new URL("./picking.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const SHOWN = 5;                                   // the chips shown before *and n more*

// -- the state -------------------------------------------------------------------------------------------------------------------------------------------------------------------

/** The marks: a card `{map, id, name, group?}`, a whole group `{map, group, name}`, a whole map `{map, all: true, name}`. Kept with the field's text; sent and emptied with the idea. */
export const marks = signal([]);
export const pickOff = signal("");                        // the party whose picking the person ended (Stop picking, Esc): picking begins again with the field
export const chipsAll = signal(false);                    // a press on *and n more* shows every chip

effect(() => { if (!fieldOpen.value) { pickOff.value = ""; chipsAll.value = false; } });

/** Where the goal in the field goes now (hand/state.js `addressOf`): the party its text names, else the open tab's, unless taken off. Reads the signals, so it can be used outside a component. */
export function addressNow() {
  return addressOf(fieldText.value, tab.value, fieldOff.value, partiesOf(mapData.value).map(partyCard));
}

/** The party whose map is in picking now (`{party, name}`), or null: the field is open, addressed to a party with a map, and picking not ended. */
export const pickFor = computed(() => {
  if (!fieldOpen.value) return null;
  const a = addressNow(), g = a.party ? partiesAll().find((x) => x.slug === a.party) : null;
  return g && pickOff.value !== g.slug && (leadsSystem(g) || mapOf(g)) ? { party: g.slug, name: a.name } : null;
});

export const stopPicking = () => { if (pickFor.value) pickOff.value = pickFor.value.party; };

/** What the idea is sent with: the cards and groups, never the whole map (it reads as no mark). */
export const marksToSend = () => marks.value.filter((m) => !m.all).map(({ map, id, name, group }) => ({ map, ...(id ? { id } : {}), name, ...(group ? { group } : {}) }));
export function resetMarks() { marks.value = []; chipsAll.value = false; }

// -- the marks ---------------------------------------------------------------------------------------------------------------------------------------------------------------------

const asMark = (c) => ({ map: c.map, id: c.id, name: c.name, ...(c.group ? { group: c.group } : {}) });
const isMarked = (list, c) => list.some((m) => m.map === c.map && (m.all || (m.id ? m.id === c.id : m.group === c.group && !!c.group)));

/** A map's marks as its cards: a group or the whole map becomes the cards it holds (those the page draws); a mark of a card no longer drawn stays as it is. */
function expand(list, cards) {
  return list.flatMap((m) => {
    if (m.id) return [m];
    const held = m.all ? cards : cards.filter((c) => c.group === m.group);
    return held.length ? held.map(asMark) : [m];
  });
}

/** Cards taken as marks: all of a group's cards (a group of two or more) the group, all the map's cards (two or more) the map. */
export function collapse(units, cards, label) {
  const map = cards[0]?.map || units[0]?.map || "", have = new Set(units.filter((u) => u.id).map((u) => u.id));
  if (cards.length > 1 && cards.every((c) => have.has(c.id))) return [{ map, all: true, name: `all of ${label}` }];
  const out = [], pinned = new Set();
  for (const u of units) {
    const held = u.group ? cards.filter((c) => c.group === u.group) : [];
    if (held.length > 1 && held.every((c) => have.has(c.id))) {
      if (!pinned.has(u.group)) { pinned.add(u.group); out.push({ map, group: u.group, name: held[0].groupName || u.group }); }
    } else out.push(u);
  }
  return out;
}

const dedupe = (units) => units.filter((u, i) => units.findIndex((x) => x.id === u.id && x.group === u.group && x.map === u.map) === i);

/** A press on a card: it is marked or not marked. Taking one off a group or the whole map leaves the others as they are (the other groups stay groups). */
export function toggle(card, cards, label) {
  const mine = marks.value.filter((m) => m.map === card.map), rest = marks.value.filter((m) => m.map !== card.map);
  const units = expand(mine, cards), at = units.findIndex((u) => u.id === card.id);
  const pinned = mine.some((m) => !m.id);
  const next = at >= 0 ? units.filter((_, i) => i !== at) : [...units, asMark(card)];
  marks.value = [...rest, ...(at >= 0 && pinned ? collapse(next, cards, label) : next)];
}

/** A box has taken `taken` (cards of one map): it replaces that map's marks, Shift adds to them. A box that took nothing changes nothing. */
export function take(taken, cards, label, shift) {
  if (!taken.length) return;
  const map = taken[0].map, mine = marks.value.filter((m) => m.map === map), rest = marks.value.filter((m) => m.map !== map);
  const units = dedupe([...(shift ? expand(mine, cards) : []), ...taken.map(asMark)]);
  marks.value = [...rest, ...collapse(units, cards, label)];
}

export const takeOff = (m) => { marks.value = marks.value.filter((x) => x !== m); };

// -- painting the cards -----------------------------------------------------------------------------------------------------------------------------------------------------------

/** Paints which cards of `host` are marked (while picking): orkUI's brackets and the rise, on the card itself. The page may redraw a card's classes; the host's observer paints again. */
export function sync(host, on, list) {
  for (const w of host.querySelectorAll("[data-pick-id]")) {
    const el = cardEl(w), marked = on && isMarked(list, { map: w.dataset.pickMap, id: w.dataset.pickId, group: w.dataset.pickGroup || "" });
    if (el.classList.contains("ork-picked") !== marked) el.classList.toggle("ork-picked", marked);
    if (el.classList.contains("pick-lifted") !== marked) el.classList.toggle("pick-lifted", marked);
    if ((el.dataset.picked === "true") !== marked) { if (marked) el.dataset.picked = "true"; else delete el.dataset.picked; }
  }
}

// -- the strip, the host ------------------------------------------------------------------------------------------------------------------------------------------------------

/** The strip over a map in picking: with the addressed party's tab open, *Pick a part to point at it*; with another open, *Open Tech's map to pick* (a link; the person's tab is kept). */
export function PickStrip({ tab: open }) {
  const on = pickFor.value;
  if (!on) return null;
  return html`<div class="pick-strip" role="status" data-picking="1" data-here=${String(on.party === open)}>
    ${on.party === open ? html`<span class="pick-strip__say">Pick a part to point at it</span>`
      : html`<button type="button" class="ork-btn quiet pick-strip__open" onClick=${() => openTab(on.party)}>Open ${on.name}'s map to pick</button>`}
    <span class="pick-strip__grow"></span>
    <button type="button" class="ork-btn pick-strip__stop" onClick=${stopPicking}>Stop picking</button>
  </div>`;
}

/** A party's map, with picking on it: no box of its own (`display: contents`), the box and the gestures on the cards inside. `g`: the party. */
export function PickHost({ g, children }) {
  const host = useRef(), on = pickFor.value?.party === g.slug, list = marks.value, [rect, setRect] = useState(null);
  const label = mapName(g.slug, partiesAll());
  const state = useRef();
  state.current = { on };
  useEffect(() => {                                                                      // paint the marks; again whenever the map draws a card or the page rewrites a class
    const el = host.current;
    if (!el) return undefined;
    let queued = false;
    const paint = () => { queued = false; sync(el, state.current.on, marks.peek()); };
    const watch = new MutationObserver(() => { if (!queued) { queued = true; queueMicrotask(paint); } });
    watch.observe(el, { subtree: true, childList: true, attributes: true, attributeFilter: ["class", "data-pick-id", "data-pick-group"] });
    paint();
    return () => watch.disconnect();
  }, []);
  useLayoutEffect(() => { if (host.current) sync(host.current, on, list); }, [on, list]);
  usePickGestures(host, on, setRect, (taken, shift) => {
    const cards = cardsIn(host.current).filter((c) => !taken.length || c.map === taken[0].map);
    take(taken, cards, label, shift);
  });
  const press = (e) => {                                                                 // a press on a card toggles it; a drag's end is not a press
    if (!on) return;
    const w = e.target.closest?.("[data-pick-id]");
    if (!w || !host.current?.contains(w)) return;
    e.preventDefault();
    e.stopPropagation();
    if (gestureEnded()) return;
    const c = cardsIn(host.current).find((x) => x.el === w);
    toggle(c, cardsIn(host.current).filter((x) => x.map === c.map), label);
  };
  return html`<div ref=${host} class="pick-host" style="display:contents" data-picking=${on ? "1" : undefined} data-picking-map=${on ? g.slug : undefined} onClickCapture=${press}>
    ${children}
    ${rect && html`<div class="ork-box pick-box" style=${`left:${rect.x}px;top:${rect.y}px;width:${rect.w}px;height:${rect.h}px`}></div>`}
  </div>`;
}

// -- the card of a map, as maps.js `Pickable` draws it -------------------------------------------------------------------------------------------------------------------------

pickWith(({ map, id, name, group = "", groupName = "", children }) => html`<div class="pick" style="display:contents" data-pick-map=${map} data-pick-id=${id} data-pick-name=${name}
  data-pick-group=${group || undefined} data-pick-group-name=${groupName || undefined}>${children}</div>`);

// Esc, with the focus on the map (the field's own Esc closes the field, which ends picking too): picking ends, the field stays.
if (typeof window !== "undefined") {
  window.addEventListener("keydown", (e) => {
    if (e.key !== "Escape" || e.defaultPrevented || !pickFor.value || e.target?.closest?.(".hand-field")) return;
    e.preventDefault();
    stopPicking();
  }, true);
}

// -- the chips on the field ---------------------------------------------------------------------------------------------------------------------------------------------------------

/** The marks as chips (a name and ×) on the field's card; past five, the first five and *and n more*, a press showing all. */
export function MarkChips() {
  const list = marks.value, all = chipsAll.value, shown = all ? list : list.slice(0, SHOWN), more = list.length - shown.length;
  if (!list.length) return null;
  return html`<${Fragment}>${shown.map((m) => html`<span key=${`${m.map}:${m.all ? "*" : ""}${m.id || m.group || ""}`} class=${cls("ork-chip hand-chip pick-chip", { "is-group": !m.id })} data-mark=${m.id || m.group || "all"} data-map=${m.map}>
      <span class="pick-chip__name">${m.name}</span>
      <button type="button" class="ork-btn quiet hand-chip__off" aria-label=${`Take ${m.name} off`} title=${`Take ${m.name} off`} onClick=${() => takeOff(m)}><${Icon} name="close" /></button></span>`)}
    ${more > 0 && html`<button type="button" class="ork-btn quiet pick-more" aria-label=${`and ${more} more: show all`} onClick=${() => { chipsAll.value = true; }}>and ${more} more</button>`}<//>`;
}
