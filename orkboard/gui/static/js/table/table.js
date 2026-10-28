// The table (docs/specs/98-the-table-and-the-hand.md §3, §5, §6; decisions §104.0, §145.1): the leaders' tabs over the pane — *what and why, through whose eyes*. `frame/frame.js` draws `Table` over the hand while the
// page is opened with `?frame=1`. The open tab and the goal picked are `frame/state.js`'s (the person's: nothing here switches a tab under them, but a goal picked from the hand opens on its party's tab); what is
// open over the pane is its `over`. This file holds the tabs and the pane together with what they share: the width (under 760 px the tabs are heads and what opens over the pane is a screen, ← the browser's back),
// Esc (lowers a lifted card, else goes back from what is over the pane) and the project shown (the tab kept for it). Each part is its own module: tabs.js, pane.js (title, over, lifted), boardmap.js, header.js,
// seatpop.js, syspane.js, card.js, over.js (the kinds) and places.js (the forms that were dialogs).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { ORKMASTER, closeOver, lifted, lower, openTab, over, picked, restoreTab, tab } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { mapData } from "../shell/store.js";
import { Tabs } from "./tabs.js";
import { Pane, back } from "./pane.js";
import { bindPlaces } from "./places.js";
import { litKey, elOf, mineKey, useLowering } from "./card.js";
import { mapName, openTabOf, partiesNow } from "./data.js";

const NARROW = "(max-width: 759px)";                       // spec 94: the phone's width is the narrow one
const SHARES = { ork: 1.3, tail: 2.2 };                      // the Board's columns, as shares of the width (table.css `--cols`): the Orkmaster's, then a party's 1 each, then the tabs' end
const FIT = 150;                                            // a party's tab keeps its name while its column is at least this wide

const typing = (el) => !!el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable);

/** Whether the window is the narrow one. */
function useNarrow() {
  const [narrow, set] = useState(() => typeof matchMedia === "function" && matchMedia(NARROW).matches);
  useEffect(() => {
    const m = matchMedia(NARROW), on = () => set(m.matches);
    m.addEventListener("change", on);
    on();
    return () => m.removeEventListener("change", on);
  }, []);
  return narrow;
}

/** The tabs keep only their heads when a column would be narrower than FIT: [ref of the table, compact]. */
function useCompact(n, narrow) {
  const host = useRef(), [compact, set] = useState(false);
  useLayoutEffect(() => {
    const measure = () => {
      const w = host.current?.clientWidth || 0;
      set(narrow || (w > 0 && w / (SHARES.ork + n + SHARES.tail) < FIT));
    };
    measure();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(measure) : null;
    if (host.current) ro?.observe(host.current);
    return () => ro?.disconnect();
  }, [n, narrow]);
  return [host, compact];
}

/** At the narrow width what opens over the pane is a screen, and the browser's back closes it (spec 94 §1.4, spec 98 §6.2): one history entry while anything is open, taken off again when it is closed otherwise. */
function useBackButton(open, narrow) {
  const pushed = useRef(false);
  useEffect(() => {
    if (open && narrow && !pushed.current) { try { history.pushState({ orkboardTable: 1 }, ""); pushed.current = true; } catch { /* no history: ← still closes it */ } }
    else if ((!open || !narrow) && pushed.current) { pushed.current = false; if (history.state?.orkboardTable) history.back(); }
  }, [open, narrow]);
  useEffect(() => {
    const pop = () => { if (!pushed.current) return; pushed.current = false; if (over.value) closeOver(); else lower(); };
    addEventListener("popstate", pop);
    return () => removeEventListener("popstate", pop);
  }, []);
}

export function Table() {
  const parties = partiesNow(), current = openTabOf(tab.value, parties), narrow = useNarrow(), [host, compact] = useCompact(parties.length, narrow);
  const where = () => ({ title: mapName(tab.value, partiesNow()), key: "" });
  useEffect(() => bindPlaces(where), []);                                                  // the forms that were dialogs lie in the pane (places.js)
  const project = currentProject.value?.path || "";
  useEffect(() => { restoreTab(); picked.value = ""; lower(); closeOver(); }, [project]);   // another project: its tab, nothing picked, nothing open
  useEffect(() => {                                                                        // a goal picked in the hand opens on its party's tab (unless the Orkmaster's Board is shown: it shows its tasks alone)
    const n = picked.value && (mapData.value?.nodes || []).find((x) => x.slug === picked.value);
    if (n && tab.value !== ORKMASTER && tab.value !== n.goal && parties.some((g) => g.slug === n.goal)) openTab(n.goal);
  }, [picked.value]);
  useEffect(() => {                                                                        // Esc: lowers a lifted card of the table, else goes back from what is over the pane (the hand's own is its)
    const key = (e) => {
      if (e.key !== "Escape" || e.defaultPrevented || typing(e.target) || document.querySelector("[aria-modal='true']")) return;
      if (lifted.value) { if (mineKey(lifted.value)) { e.preventDefault(); lower(); } return; }
      if (over.value) { e.preventDefault(); back(); }
    };
    addEventListener("keydown", key);
    return () => removeEventListener("keydown", key);
  }, []);
  useLowering(mineKey(lifted.value));
  useBackButton(!!over.value || mineKey(lifted.value), narrow);
  useEffect(() => {                                                                        // the card a thing came from stays lit until the next press or key; a part of the System is the map's own element
    const key = litKey.value;
    if (!key) return undefined;
    let tries = 0, lit = null;
    const light = () => { const el = elOf(key); if (el) { el.classList.add("is-lit"); lit = el; return true; } return ++tries > 30; };
    const poll = light() ? 0 : setInterval(() => { if (light()) clearInterval(poll); }, 100);
    const off = () => { litKey.value = ""; };
    addEventListener("pointerdown", off, true);
    addEventListener("keydown", off, true);
    return () => { clearInterval(poll); lit?.classList.remove("is-lit"); removeEventListener("pointerdown", off, true); removeEventListener("keydown", off, true); };
  }, [litKey.value]);
  return html`<div class="table" ref=${host} data-tab=${current} data-narrow=${String(narrow)} data-compact=${String(compact)} style=${`--tabs:${parties.length}`}>
    <${Tabs} parties=${parties} current=${current} narrow=${narrow} compact=${compact} />
    <${Pane} parties=${parties} tab=${current} narrow=${narrow} />
  </div>`;
}
