// Play under each leader's eyes (docs/specs/115-the-live-product-under-each-leaders-eyes.md §6.1–§6.3, mockup docs/mockups/play-lenses/ states 1–3 and 8; the probe's protocol is gui/static/play/probe.js, its host side gui/ideas_play_mark.py).
// Play is one more map, the product itself, shared by every party: another tab never closes it, it changes the lens over it (frame/state.js `followTab`; the iframe is the same element all through, never reloaded).
// `useProbe` is the page's end of the probe: it hears only the frame's own window at the frame's own origin (`place`, `event`), says `hello`, asks (`under`, `picture`, `state`: an answer carries the ask's `kind` and `id`; none
// in 1.5 s is `null`) and forwards the events to the host (`ideas.play_events`) in batches every 2 s. A Play with no probe (`probe: false`: `preview_probe = false`, or its proxy would not start) has the iframe's `src` path as its place and
// asks nothing; its strip says *Marks keep the picture and the place only*.
// `useLens` is what the open tab's leader sees there: the place (`ideas.play_place`: Design's screen and the parts of every map this page touches, helped by the files of the elements the probe names, found by asking `under` over a grid
// of the frame), the leader's concerns of the parts on this page (the record is table/concerns.js's: `ideas.concerns`), and the hints of code of this leader's craft (`ideas.play_hints`: Tech's error, failed, slow; Design's dead_press, again).
// `LensStrip` is the strip under Play's bar, as the concerns' strip is on a map (`cn-strip`): the leader's head and *<Leader> on <screen>*, the rubric's short, its aspects in their state for this page's parts alone; *Not on <map>* when this page has none
// of the leader's parts. The project's tab (the Orkmaster's) has no strip. What has no element in the frame stands in the strip, a press on it opens its back.
// `MarksLayer` is the frame's layer that lets presses through (`pointer-events: none`, its tags `auto`): a concern is an outline in the alert or the muted ink with the leader's small head at its corner, a hint a dotted outline with a hollow square;
// only what the probe can place by an element has one. A press on a tag opens its back (`Back`: a concern's is `ConcernsBack`, a hint's its words, **Make it a goal** and **Not a problem**, hidden for this play). *Hide the marks* (the bar's) hides the layer.
// No count, no badge.
import { useCallback, useEffect, useMemo, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Head, Sign } from "../orkui.js";
import { command } from "../link.js";
import { ORKMASTER, tab } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { mapName, partiesAll } from "../table/data.js";
import { craftOf } from "../table/maps.js";
import { ConcernsBack, aspectWords, hasMap, read as readConcerns, recordOf, theLeader } from "../table/concerns.js";

export const HIDE = "Hide the marks", SHOW = "Show the marks";
export const NO_PROBE = "Marks keep the picture and the place only";
export const notOn = (map) => `Not on ${map}`;

const FLUSH_MS = 2000, ASK_MS = 1500, GRID = 3, KEPT = 600, FILES = 12;
const MAP_OF = { tech: "system", design: "screens", product: "product", "game-design": "game-design", art: "art", marketing: "marketing", release: "release" };      // a craft's map (realm/map_parts.py MAPS)
const LENS_CRAFT = { system: "tech", screens: "design" };                                                                                                      // the maps the live product has hints for
const CRAFT_OF_KIND = { error: "tech", failed: "tech", slow: "tech", dead_press: "design", again: "design" };                                                    // realm/play_signals.py CRAFT
const ASPECT_OF_KIND = { error: "safety", failed: "safety", slow: "hotspots", dead_press: "flow", again: "status" };                                              // realm/lens_rubrics.py: each kind in one aspect

/** The hints let be for a play (*Not a problem*): play id → keys. Kept for the play only. */
const letBe = signal({});
export const hintKey = (h) => `${h.kind}|${h.on?.selector || h.words}`;
export const letHintBe = (play, h) => { letBe.value = { ...letBe.peek(), [play]: [...(letBe.peek()[play] || []), hintKey(h)] }; };

const sameJson = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const originOf = (url) => { try { return new URL(url).origin; } catch { return ""; } };

/** The page's path and route from the iframe's own address (a Play with no probe). */
function placeOf(url) {
  try {
    const u = new URL(url), frag = u.hash.replace(/^#!?/, "");
    if (!/^https?:$/.test(u.protocol)) return { path: "/", route: "", viewport: null };            // a data: page and the like have no path of a route
    return { path: u.pathname || "/", route: frag.startsWith("/") ? frag.split("?")[0] : "", viewport: null };
  } catch { return { path: "/", route: "", viewport: null }; }
}

/** The path as the host takes it (`ideas.play_place`, `ideas.play_mark`): the route of a hash-routed page after a `#`. */
export const pathOf = (place) => (place ? place.path + (place.route ? `#${place.route}` : "") : "");

// -- the probe ----------------------------------------------------------------------------------------------------------------------------------------------

/** The page's end of the probe (see the head). `frame`: the iframe's ref; `b`: the build (`url`, `play`, `probe`). Returns `{probing, place, ask, events, sent, hello}`: `events` the probe's events kept (a ref's array, the newest last), `sent` counts the batches the host has. */
export function useProbe(frame, b) {
  const probing = b.probe === true, origin = originOf(b.url);
  const st = useRef({ waits: new Map(), n: 0, out: [], kept: [], placed: false }).current;
  const [place, setPlace] = useState(() => placeOf(b.url));
  const [sent, setSent] = useState(0);
  useEffect(() => {
    if (!probing || !origin) { setPlace(placeOf(b.url)); return undefined; }
    const win = () => frame.current?.contentWindow || null;
    const heard = (e) => {
      const m = e.data;
      if (!win() || e.source !== win() || e.origin !== origin || !m || m.ork !== 1) return;
      if (b.play && m.play && m.play !== b.play) return;
      if (m.kind === "place") { st.placed = true; setPlace((old) => { const next = { path: String(m.path || "/"), route: String(m.route || ""), viewport: m.viewport || null }; return sameJson(old, next) ? old : next; }); }
      else if (m.kind === "event") { const { ork, kind, ...e2 } = m; st.out.push(e2); st.kept.push(e2); if (st.kept.length > KEPT) st.kept.splice(0, st.kept.length - KEPT); }
      else if (m.id != null && st.waits.get(m.id)?.kind === m.kind) st.waits.get(m.id).done(m);
    };
    addEventListener("message", heard);
    const hello = () => win()?.postMessage({ ork: 1, kind: "hello", play: b.play }, origin);
    st.hello = hello;
    hello();
    const hi = setInterval(() => { if (st.placed) clearInterval(hi); else hello(); }, 800);
    const flush = () => {
      if (!st.out.length) return;
      const events = st.out.splice(0, 200);
      command("ideas.play_events", { play: b.play, events }, true).then(() => setSent((n) => n + 1)).catch(() => {});
    };
    const timer = setInterval(flush, FLUSH_MS);
    return () => { st.hello = null; removeEventListener("message", heard); clearInterval(hi); clearInterval(timer); flush(); };
  }, [probing, origin, b.play, b.url]);
  const ask = useCallback((kind, extra = {}, ms = ASK_MS) => new Promise((resolve) => {
    const w = frame.current?.contentWindow;
    if (!probing || !w || !origin) { resolve(null); return; }
    const id = ++st.n, t = setTimeout(() => { st.waits.delete(id); resolve(null); }, ms);
    st.waits.set(id, { kind, done: (m) => { clearTimeout(t); st.waits.delete(id); resolve(m); } });
    w.postMessage({ ork: 1, kind, id, play: b.play, ...extra }, origin);
  }), [probing, origin, b.play]);
  return { probing, place, ask, events: st.kept, sent, hello: () => st.hello?.() };
}

/** The errors on this page and the requests that failed or were slow, as the host counts them for a mark (gui/ideas_play_mark.py `_ring_seen`), from the events kept here. */
export function tally(events, path, slowMs = 1000) {
  const asked = new Map(), errors = new Set();
  let requests = 0;
  for (const e of events) if (e.event === "request") asked.set(e.path, (asked.get(e.path) || 0) + 1);
  for (const e of events) {
    if (e.event === "error" && e.page === path && e.message) errors.add(e.message);
    else if (e.event === "request") {
      const s = Number(e.status) || 0, failed = s >= 500 || (s >= 400 && s < 500 && s !== 401 && !(s === 404 && (asked.get(e.path) || 0) < 2));
      if (failed || Number(e.ms) > slowMs) requests += 1;
    }
  }
  return { errors: Math.min(errors.size, 10), requests: Math.min(requests, 10) };
}

// -- the lens -----------------------------------------------------------------------------------------------------------------------------------------------

/** The elements the probe can name over the whole frame: a grid of cells, each asked with `under`. */
async function scan(probe, stage) {
  const el = stage.current, w = el?.clientWidth || 0, h = el?.clientHeight || 0;
  if (!w || !h) return [];
  const asks = [];
  for (let i = 0; i < GRID; i++) for (let j = 0; j < GRID; j++) asks.push(probe.ask("under", { box: { x: (i * w) / GRID, y: (j * h) / GRID, w: w / GRID, h: h / GRID } }));
  const by = new Map();
  for (const r of await Promise.all(asks)) for (const e of r?.elements || []) if (e.rect && !by.has(e.selector)) by.set(e.selector, e);
  return [...by.values()];
}

const inPart = (file, part) => { const f = String(file || "").replace(/\\/g, "/"); return !!part && part !== "." && (f === part || f.startsWith(`${part}/`) || f.includes(`/${part}/`)); };

/** What the open tab's leader sees on this page: `{lens, where, hints}`; `lens` is null on the project's tab and under a party with no map. `stage`: the frame's box (a ref). */
export function useLens(b, probe, stage) {
  const t = tab.value, g = t === ORKMASTER ? null : partiesAll().find((x) => x.slug === t) || null, party = g && hasMap(g) ? g.slug : "";
  const rec = party ? recordOf(party) : null, rev = mapData.value?.rev, pk = pathOf(probe.place), path = probe.place?.path || "";
  const [where, setWhere] = useState({ screen: null, parts: {} }), [seen, setSeen] = useState([]), [hints, setHints] = useState([]);
  useEffect(() => {                                                    // the leader's record, as its map reads it (a look under way is asked after again)
    if (!party) return undefined;
    let live = true, timer = 0;
    const go = async () => { const r = await readConcerns("ideas.concerns", party); if (live && r?.status === "looking") timer = setTimeout(go, 2500); };
    go();
    return () => { live = false; clearTimeout(timer); };
  }, [party, rev]);
  useEffect(() => {                                                    // where the page is: the elements the probe names, then the parts they touch
    if (!pk) return undefined;
    let live = true;
    const run = async () => {
      const found = probe.probing ? await scan(probe, stage) : [];
      if (!live) return;
      setSeen((old) => (sameJson(old, found) ? old : found));
      const files = [...new Set(found.map((e) => e.file).filter(Boolean))].slice(0, FILES);
      const r = await command("ideas.play_place", { path: pk, files }, true).catch(() => null);
      if (live && r) setWhere((old) => { const next = { screen: r.screen || null, parts: r.parts || {} }; return sameJson(old, next) ? old : next; });
    };
    const times = [setTimeout(run, 150), setTimeout(run, 2200)];
    return () => { live = false; times.forEach(clearTimeout); };
  }, [pk, probe.probing]);
  useEffect(() => {                                                    // the hints of code of this play, again when a batch of events reached the host
    if (!probe.probing || !path) return;
    let live = true;
    command("ideas.play_hints", { play: b.play, path }, true).then((r) => { if (live) setHints((old) => (sameJson(old, r?.hints || []) ? old : r?.hints || [])); }).catch(() => {});
    return () => { live = false; };
  }, [path, probe.probing, probe.sent]);
  const gone = new Set(letBe.value[b.play] || []);
  if (!g || !party) return { lens: null, where, hints };
  const mapId = rec?.map || MAP_OF[craftOf(g)] || "", mine = where.parts[mapId] || [], ids = new Set(mine.map((p) => p.id)), craft = LENS_CRAFT[mapId] || "";
  const lead = { name: g.leader?.name || "Taskmaster", head: g.leader?.head || null };
  const open = (rec?.concerns || []).filter((c) => ids.has(c.on) && !(c.idea || c.goal)), items = [];
  const byPart = new Map();
  for (const c of open) byPart.set(c.on, [...(byPart.get(c.on) || []), c]);
  for (const [on, list] of byPart) {
    items.push({ key: `c:${on}`, kind: "concern", level: list.some((c) => c.level === "alert") ? "alert" : "note", words: list[0].what, on, concerns: list, aspects: new Set(list.map((c) => c.aspect)),
      rect: seen.find((e) => inPart(e.file, on))?.rect || null });
  }
  const shown = craft ? hints.filter((h) => CRAFT_OF_KIND[h.kind] === craft && !gone.has(hintKey(h))) : [];
  for (const h of shown) items.push({ key: `h:${hintKey(h)}`, kind: "hint", level: "hint", words: h.words, hint: h, aspects: new Set([ASPECT_OF_KIND[h.kind]]), rect: h.on?.rect || null });
  const rubric = rec?.rubric?.aspects?.length ? rec.rubric : null;
  const aspects = rubric ? rubric.aspects.map((a) => {
    const cs = open.filter((c) => c.aspect === a.id), code = shown.some((h) => ASPECT_OF_KIND[h.kind] === a.id) || (rec.hints || []).some((h) => ids.has(h.on) && h.aspect === a.id);
    return { id: a.id, name: a.name, ask: a.ask, n: cs.length, state: cs.some((c) => c.level === "alert") ? "alert" : cs.length ? "note" : code ? "hint" : rec.at ? "clear" : "unlooked" };
  }) : [];
  const screen = where.screen, here = screen ? screen.name : path || "/";
  const words = mapId === "screens" ? `${here}${screen?.step ? ` · Step ${screen.step}` : ""}` : `${here}${mine.length ? ` · ${mine.slice(0, 2).map((p) => p.name).join(", ")}` : ""}`;
  return { where, hints, lens: { party, g, lead, mapId, mapTitle: mapName(party, partiesAll()), on: mine.length > 0, parts: mine, short: rubric?.short || "", aspects, items, words, ready: !!rec } };
}

// -- the strip ----------------------------------------------------------------------------------------------------------------------------------------------

const AspectMark = ({ state }) => (state === "alert" ? html`<${Sign} name="alert" />` : state === "note" ? html`<i class="cn-dot" aria-hidden="true"></i>`
  : state === "hint" ? html`<i class="cn-hint" aria-hidden="true"></i>` : state === "clear" ? html`<${Sign} name="check" />` : null);

/** The strip under Play's bar: the lens (see the head), or, for a Play with no probe, the one sentence it has. Nothing on the project's tab (unless there is no probe: marks there keep the picture and the place only). */
export function LensStrip({ lens, probing, onOpen }) {
  const turn = useRef({ of: "", i: -1 });
  if (!probing) return html`<div class="cn-strip play-lens" role="status" data-state="noprobe"><${Sign} name="alert" /><span class="play-lens__not">${NO_PROBE}</span></div>`;
  if (!lens) return null;
  const name = theLeader(lens.lead.name), loose = lens.items.filter((i) => !i.rect);
  const step = (id) => {                                              // a press on an aspect opens the next of its marks
    const mine = lens.items.filter((i) => i.aspects.has(id));
    if (!mine.length) return;
    turn.current = { of: id, i: turn.current.of === id ? (turn.current.i + 1) % mine.length : 0 };
    onOpen(mine[turn.current.i].key);
  };
  return html`<div class="cn-strip play-lens" role="status" data-state=${lens.on ? "lens" : "off"} data-party=${lens.party} data-map=${lens.mapId}>
    ${lens.lead.head && html`<${Head} race=${lens.lead.head.race} tier=${lens.lead.head.tier} />`}
    <span class="cn-strip__say play-lens__say"><b>${name}</b> on ${lens.words}</span>
    ${lens.on && lens.short && html`<span class="play-lens__short">${lens.short}</span>`}
    ${!lens.on && html`<span class="play-lens__not" data-not-on="">${notOn(lens.mapTitle)}</span>`}
    ${lens.on && lens.aspects.length > 0 && html`<div class="cn-aspects play-lens__aspects" role="group" aria-label=${`What ${name} looks at here`}>
      ${lens.aspects.map((a) => {
        const props = { class: "ork-chip cn-aspect", "data-state": a.state, "data-aspect": a.id, "aria-label": aspectWords(a), title: a.ask };
        return lens.items.some((i) => i.aspects.has(a.id)) ? html`<button type="button" key=${a.id} ...${props} onClick=${() => step(a.id)}><${AspectMark} state=${a.state} />${a.name}</button>`
          : html`<span role="img" key=${a.id} ...${props}><${AspectMark} state=${a.state} />${a.name}</span>`;
      })}
    </div>`}
    ${loose.length > 0 && html`<div class="play-lens__loose">${loose.map((i) => html`<button type="button" key=${i.key} class="ork-btn quiet play-lens__item" data-kind=${i.kind} data-level=${i.level} onClick=${() => onOpen(i.key)}>
      ${i.kind === "hint" ? html`<i class="cn-hint" aria-hidden="true"></i>` : i.level === "alert" ? html`<${Sign} name="alert" />` : html`<i class="cn-dot" aria-hidden="true"></i>`}<span>${i.words}</span></button>`)}</div>`}
  </div>`;
}

// -- the marks on the frame ---------------------------------------------------------------------------------------------------------------------------------

const clamp = (n, lo, hi) => Math.max(lo, Math.min(n, Math.max(lo, hi)));

/** The frame's layer of marks (see the head): one box and tag for each item the probe placed on an element. `open`: the key of the item whose back is open. */
export function MarksLayer({ lens, open, onOpen }) {
  const placed = (lens?.items || []).filter((i) => i.rect && i.rect.w >= 0 && i.rect.h >= 0);
  if (!placed.length) return null;
  return html`<div class="play-marks" data-marks="">${placed.map((i, n) => {
    const r = i.rect, low = r.y < 18;
    const words = i.kind === "hint" ? `A hint from code: ${i.words}` : `${theLeader(lens.lead.name)}: ${i.words}`;
    return html`<div key=${i.key} class=${cls("play-mark", { "is-open": open === i.key })} data-kind=${i.kind} data-level=${i.level} data-key=${i.key} style=${`left:${r.x}px;top:${r.y}px;width:${r.w}px;height:${r.h}px`}>
      <button type="button" class=${cls("play-tag", { "is-low": low })} style=${`margin-right:${n % 2 ? 22 : 0}px`} aria-label=${words} title=${words} aria-expanded=${String(open === i.key)} onClick=${() => onOpen(open === i.key ? "" : i.key)}>
        ${i.kind === "hint" ? html`<i class="cn-hint" aria-hidden="true"></i>` : html`${lens.lead.head && html`<${Head} race=${lens.lead.head.race} tier=${lens.lead.head.tier} />`}${i.level === "alert" ? html`<${Sign} name="alert" />` : html`<i class="cn-dot" aria-hidden="true"></i>`}`}
      </button></div>`;
  })}</div>`;
}

/** A hint's back: its words, **Make it a goal** (the mark field, as a Bug on its element) and **Not a problem** (not shown again in this play). */
function HintBack({ item, onGoal, onNo }) {
  const h = item.hint;
  return html`<div class="table-back__sec cn-back" data-hint-back="">
    <div class="cn-item" data-level="hint">
      <p class="cn-item__what"><i class="cn-hint" aria-hidden="true"></i><span><span class="ork-label">Hint from code</span> ${h.words}</span></p>
      <div class="table-back__acts cn-item__acts">
        <button type="button" class="ork-btn primary cn-item__make" onClick=${() => onGoal(item)}>Make it a goal</button>
        <button type="button" class="ork-btn cn-item__no" onClick=${() => onNo(h)}>Not a problem</button>
      </div></div></div>`;
}

/** The open item's back, lifted over the frame beside its mark (or, with no element, at the frame's corner): a concern's is `ConcernsBack` (the part's concerns), a hint's is its own. `size`: the frame's. */
export function Back({ lens, item, size, onClose, onGoal, onNo }) {
  const r = item.rect, W = 340, left = r ? (r.x + r.w + 12 + W <= size.w ? r.x + r.w + 12 : clamp(r.x - W - 12, 8, size.w - W - 8)) : 8, top = r ? clamp(r.y, 8, size.h - 160) : 8;
  const fake = useMemo(() => ({ closest: () => ({ dataset: { pickId: item.on } }) }), [item.on]);       // ConcernsBack reads a card's part from its element
  return html`<div class="ork-card play-back" role="dialog" aria-label=${item.kind === "hint" ? "A hint from code" : `${theLeader(lens.lead.name)}: a concern`} data-key=${item.key} style=${`left:${left}px;top:${top}px`}>
    <div class="play-back__head"><span class="ork-label">${item.kind === "hint" ? "Hint" : theLeader(lens.lead.name)}</span>
      <button type="button" class="ork-btn quiet play-back__close" aria-label="Close" onClick=${onClose}>Close</button></div>
    ${item.kind === "hint" ? html`<${HintBack} item=${item} onGoal=${onGoal} onNo=${onNo} />` : html`<${ConcernsBack} el=${fake} />`}
  </div>`;
}

/** The frame's size, kept (a ref's box measured when it changes). */
export function useSize(ref) {
  const [size, setSize] = useState({ w: 0, h: 0 });
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const measure = () => setSize((o) => (o.w === el.clientWidth && o.h === el.clientHeight ? o : { w: el.clientWidth, h: el.clientHeight }));
    measure();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(measure) : null;
    ro?.observe(el);
    return () => ro?.disconnect();
  }, []);
  return size;
}
