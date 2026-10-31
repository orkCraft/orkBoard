// Design's map (docs/specs/102-the-other-maps-and-picking-on-them.md §1, §5.1–§5.2, mockup docs/mockups/s3/ states 1 and 2): the app's screens along their flow as `ideas.screens` reads them from dev — the steps as columns left to
// right (top to bottom at the narrow width), a screen a card (its picture in its window, else the `screen` sign), the links as arrows between them, each named as System's are —; a screen pressed is lifted where it lies and
// turns over (card.js `Lifted`: its picture large, its path, its file, its links). The pains of the project's segments (`segments`) lie pinned under their screen or step as small cards, the segment picked over the map
// as a filter (*All segments*, then each); a pain dragged onto another screen or step pins it there (`ideas.pain_pin`), or pressed and then the screen pressed. Registered for Design's tab (decisions: the pains
// belong on Design's map). A screen and a step are `Pickable` (part F). The cards: screenparts.js; the sheet: screens.css.
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Chev } from "../orkui.js";
import { command, toast, town } from "../link.js";
import { lift, lower, lifted } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { Lifted } from "./card.js";
import { mapName, partiesAll } from "./data.js";
import { mapFor, Pickable } from "./maps.js";
import { PainCard, ScreenBack, ScreenCard, screenKey } from "./screenparts.js";

const COULD_NOT = "The screens could not be read";
const DRAG = 6;                                                                           // px a mouse moves before a press on a pain is a drag
const painKey = (p) => `${p.segment}\n${p.text}`;

/** The screens of the project at dev's head, read again when the Board changes (`ideas.screens`). */
const KEPT = { project: "", doc: null };                                                   // the last answer, shown at once when the map comes back from a file opened over it
function useScreens() {
  const project = town.value?.projects?.current || "", [doc, setDoc] = useState(() => (KEPT.project === project ? KEPT.doc : null)), [err, setErr] = useState(""), rev = mapData.value?.rev;
  useEffect(() => {
    let live = true;
    command("ideas.screens", {}, true).then((r) => {
      if (!live) return;
      if (!r || r.error || !Array.isArray(r.screens)) { setErr(r?.error || COULD_NOT); return; }
      setErr("");
      KEPT.project = project;
      KEPT.doc = r;
      setDoc(r);
    }).catch((e) => { if (live) setErr(e.message || COULD_NOT); });
    return () => { live = false; };
  }, [rev, project]);
  return [doc, setDoc, err];
}

/** The map's data as it is drawn: the steps `[{n, ids, real}]` (a screen no step holds lies in a last one that cannot be pinned to), the pains with their place (`on` a screen's or a step's id, "" none or gone). */
function modelOf(doc) {
  const byId = new Map(doc.screens.map((s) => [s.id, s])), held = new Set();
  const steps = (doc.steps || []).map((ids, i) => ({ n: i + 1, real: true, ids: ids.filter((id) => byId.has(id)) }));
  steps.forEach((st) => st.ids.forEach((id) => held.add(id)));
  const rest = doc.screens.filter((s) => !held.has(s.id)).map((s) => s.id);
  if (rest.length) steps.push({ n: steps.length + 1, real: false, ids: rest });
  const stepIds = new Set(steps.filter((st) => st.real).map((st) => `step:${st.n}`));
  const pains = (doc.segments || []).flatMap((g) => (g.pains || []).map((p) => ({ segment: g.segment, text: p.text, on: byId.has(p.on) || stepIds.has(p.on) ? p.on : "" })));
  return { byId, steps, pains, stepOf: new Map(steps.flatMap((st) => st.ids.map((id) => [id, st.n]))), rooms: roomsOf(doc, byId, steps) };
}

/** The rooms (spec 117 G): for each screen the names of the screens that lead to it (`ins`: its left side's doors) and that it leads to (`outs`: its right's), a screen once in either, in the flow's order, a link to itself none; and its `tags`:
 *  `entry`, `end` (in the flow's last step that is not loose), `dead_end` (no door out and not the end) and `loose` (no door in and not the entry) — the rules of realm/map_signals.py `_design`, so a wall and a heat square agree. */
function roomsOf(doc, byId, steps) {
  const rank = new Map(steps.flatMap((st) => st.ids).map((id, i) => [id, i])), ins = new Map(), outs = new Map(), seen = new Set();
  for (const l of doc.links || []) {
    if (l.from === l.to || !byId.has(l.from) || !byId.has(l.to) || seen.has(`${l.from}>${l.to}`)) continue;
    seen.add(`${l.from}>${l.to}`);
    ins.set(l.to, [...(ins.get(l.to) || []), l.from]);
    outs.set(l.from, [...(outs.get(l.from) || []), l.to]);
  }
  const loose = new Set(doc.loose || []), last = (doc.steps || []).filter((row) => row.length > 0 && !row.every((id) => loose.has(id))).slice(-1)[0] || [];
  const byFlow = (ids) => [...(ids || [])].sort((a, b) => (rank.get(a) ?? 0) - (rank.get(b) ?? 0)).map((id) => byId.get(id).name);
  return new Map(doc.screens.map((s) => {
    const tags = [s.id === doc.entry && "entry", last.includes(s.id) && "end", !outs.has(s.id) && !last.includes(s.id) && !loose.has(s.id) && "dead_end", !ins.has(s.id) && s.id !== doc.entry && "loose"].filter(Boolean).join(" ");
    return [s.id, { ins: byFlow(ins.get(s.id)), outs: byFlow(outs.get(s.id)), tags }];
  }));
}

/** The arrows between the cards (forward links only: a link back, or within a step, is in the screens' backs): each its path through a lane of the gap after its source's step, its name (the target's) at the target. */
function arrowsOf(links, geo, stepOf, byId) {
  const cols = new Map();                                                                  // step number → {x, r}: the cards' left and right edge
  for (const [id, g] of Object.entries(geo)) {
    const n = stepOf.get(id), c = cols.get(n) || { x: g.x, r: g.x + g.w };
    cols.set(n, { x: Math.min(c.x, g.x), r: Math.max(c.r, g.x + g.w) });
  }
  const fwd = links.filter((l) => geo[l.from] && geo[l.to] && stepOf.get(l.to) > stepOf.get(l.from));
  const lanes = new Map();
  for (const l of fwd) lanes.set(stepOf.get(l.from), [...(lanes.get(stepOf.get(l.from)) || []), l]);
  const out = [];
  for (const [n, group] of lanes) {
    group.sort((a, b) => geo[a.to].y - geo[b.to].y || geo[a.from].y - geo[b.from].y);
    const from = cols.get(n), next = cols.get(n + 1) || { x: from.r + 72 };
    group.forEach((l, k) => {
      const s = geo[l.from], t = geo[l.to], lane = from.r + ((next.x - from.r) * (k + 1)) / (group.length + 1);
      out.push({ key: `${l.from}>${l.to}`, d: `M${s.x + s.w} ${s.y + s.h / 2}H${lane}V${t.y + t.h / 2}H${t.x - 2}`, x: t.x, y: t.y + t.h / 2, name: byId.get(l.to).name, from: byId.get(l.from).name });
    });
  }
  return out;
}

export function ScreensMap({ g, narrow }) {
  const [doc, setDoc, err] = useScreens(), [seg, setSeg] = useState(""), [carry, setCarry] = useState(null), [drag, setDrag] = useState(null);
  const [geo, setGeo] = useState({}), host = useRef(), flow = useRef(), scroller = useRef(), seen = useRef({ top: 0, left: 0, at: 0 });
  const model = useMemo(() => (doc ? modelOf(doc) : null), [doc]);
  const key = lifted.value, id = key.startsWith(`t:screen:${g.slug}:`) ? key.slice(`t:screen:${g.slug}:`.length) : "";
  const from = { title: mapName(g.slug, partiesAll()), key };

  useEffect(() => { seen.current = { top: scroller.current?.scrollTop || 0, left: scroller.current?.scrollLeft || 0, at: Date.now() }; }, [id]);   // where the map was when a screen was lifted: a scroll away lowers it

  // the cards' places, for the arrows (wide only): measured, so a wrapped name or a rail of pains cannot throw them off
  useLayoutEffect(() => {
    if (narrow || !flow.current || !model) { setGeo((was) => (Object.keys(was).length ? {} : was)); return undefined; }
    const measure = () => {
      const base = flow.current.getBoundingClientRect(), next = {};
      flow.current.querySelectorAll("[data-screen]").forEach((el) => {
        const r = el.getBoundingClientRect();
        next[el.dataset.screen] = { x: Math.round(r.left - base.left), y: Math.round(r.top - base.top), w: Math.round(r.width), h: Math.round(r.height) };
      });
      setGeo((was) => (JSON.stringify(was) === JSON.stringify(next) ? was : next));
    };
    measure();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(measure) : null;
    ro?.observe(flow.current);
    return () => ro?.disconnect();
  }, [model, seg, narrow, carry, drag === null]);

  useEffect(() => {                                                                        // Esc puts a carried pain down
    if (!carry) return undefined;
    const esc = (e) => { if (e.key === "Escape") { e.preventDefault(); setCarry(null); } };
    addEventListener("keydown", esc);
    return () => removeEventListener("keydown", esc);
  }, [carry]);

  if (err && !doc) return html`<div class="scr-map" data-state="error"><p class="scr-note scr-note--blank">${err}</p></div>`;
  if (!doc) return html`<div class="scr-map" data-state="loading"></div>`;
  if (!doc.screens.length) return html`<div class="scr-map" data-state="none"><p class="scr-note scr-note--blank">Nothing to read yet: the app's routes or its screens' folder</p></div>`;

  const segments = (doc.segments || []).filter((s) => (s.pains || []).length > 0).map((s) => s.segment);
  const shown = seg && segments.includes(seg) ? seg : "";
  const pains = model.pains.filter((p) => !shown || p.segment === shown);
  const under = (at) => pains.filter((p) => p.on === at);
  const loose = under(""), pictureless = doc.screens.filter((s) => !s.picture).length;

  /** Pins `p` to `on` ("" none): shown at once, the host's answer then replaces it. */
  const pin = (p, on) => {
    setCarry(null);
    if (!p || p.on === on) return;
    const before = doc;
    setDoc({ ...doc, segments: doc.segments.map((s) => (s.segment === p.segment ? { ...s, pains: s.pains.map((x) => (x.text === p.text ? { ...x, on } : x)) } : s)) });
    command("ideas.pain_pin", { segment: p.segment, pain: p.text, on }, true).then((r) => {
      if (r?.segments) setDoc((d) => ({ ...(d || before), segments: r.segments }));
    }).catch((e) => { setDoc(before); toast(e.message || "The pain could not be pinned", "error"); });
  };
  const carried = (p) => !!carry && carry.segment === p.segment && carry.text === p.text;
  const press = (p) => setCarry(carried(p) ? null : { segment: p.segment, text: p.text });
  const target = (at) => (carry ? () => pin(model.pains.find((p) => p.segment === carry.segment && p.text === carry.text), at) : null);

  // a pain dragged with a mouse: it follows the pointer, the screen or step under it is aimed, letting go pins it there (a touch screen presses the pain and then the screen)
  const down = (p) => (e) => {
    if (e.button > 0 || e.pointerType === "touch") return;
    const x0 = e.clientX, y0 = e.clientY;
    let on = false, over = null;
    const at = (ev) => { const el = document.elementsFromPoint(ev.clientX, ev.clientY).find((n) => n.closest?.("[data-drop]")); return el ? el.closest("[data-drop]").getAttribute("data-drop") : null; };
    const move = (ev) => {
      if (!on && Math.hypot(ev.clientX - x0, ev.clientY - y0) < DRAG) return;
      on = true;
      over = at(ev);
      setDrag({ p, x: ev.clientX, y: ev.clientY, over });
    };
    const done = (ev) => {
      removeEventListener("pointermove", move);
      removeEventListener("pointerup", done);
      removeEventListener("pointercancel", done);
      if (!on) return;
      setDrag(null);
      const to = ev.type === "pointerup" ? at(ev) : null;
      if (to !== null) pin(p, to);
      const stop = (c) => { c.stopPropagation(); c.preventDefault(); };                    // the click that follows a drag is not a press
      addEventListener("click", stop, { capture: true, once: true });
      setTimeout(() => removeEventListener("click", stop, true), 0);
    };
    addEventListener("pointermove", move);
    addEventListener("pointerup", done);
    addEventListener("pointercancel", done);
  };

  const painsAt = (at, step = false) => {
    const list = under(at);
    return list.length > 0 ? html`<div class=${cls("scr-rail", { "is-step": step })} data-on=${at}>${list.map((p) =>
      html`<${PainCard} key=${painKey(p)} p=${p} carried=${carried(p)} dragging=${drag?.p === p} onPress=${() => press(p)} onDown=${down(p)} />`)}</div>` : null;
  };
  const card = (sid, step) => {
    const s = model.byId.get(sid);
    return html`<div class="scr-item" key=${sid}>
      <${ScreenCard} s=${s} party=${g.slug} step=${step} room=${model.rooms.get(sid)} on=${key === screenKey(g.slug, sid)} carry=${!!carry} over=${drag?.over === sid}
        onPress=${target(sid) || (() => lift(key === screenKey(g.slug, sid) ? "" : screenKey(g.slug, sid)))} />
      ${painsAt(sid)}
    </div>`;
  };
  const stepHead = (st) => {
    const aim = target(`step:${st.n}`);
    return html`<button type="button" class=${cls("ork-label scr-steplab", { "is-aim": !!aim && st.real, "is-over": drag?.over === `step:${st.n}` })} disabled=${!aim || !st.real}
      aria-label=${aim && st.real ? `Step ${st.n}: pin the pain here` : `Step ${st.n}`} onClick=${aim}>Step ${st.n}</button>`;
  };
  const column = (st) => html`<${Pickable} key=${st.n} map="screens" id=${`step:${st.n}`} name=${`Step ${st.n}`}>
    <section class=${cls("scr-step", { "is-over": drag?.over === `step:${st.n}` })} data-step=${st.n} data-drop=${st.real ? `step:${st.n}` : undefined} aria-label=${`Step ${st.n}`}>
      ${stepHead(st)}
      ${st.real && html`${painsAt(`step:${st.n}`, true)}`}
      <div class="scr-step__cards">${st.ids.map((sid) => card(sid, st.n))}</div>
    </section>
  </${Pickable}>`;
  // at the narrow width the steps lie top to bottom, the links that enter a step as chips between it and the one before
  const entering = (st) => (doc.links || []).filter((l) => st.ids.includes(l.to) && model.byId.has(l.from) && model.stepOf.get(l.from) < st.n);
  const narrowStep = (st, i) => html`<${Pickable} key=${st.n} map="screens" id=${`step:${st.n}`} name=${`Step ${st.n}`}>
    <section class=${cls("scr-step scr-step--row", { "is-over": drag?.over === `step:${st.n}` })} data-step=${st.n} data-drop=${st.real ? `step:${st.n}` : undefined} aria-label=${`Step ${st.n}`}>
      ${i > 0 && entering(st).length > 0 && html`<div class="scr-links">${entering(st).map((l) => html`<span class="scr-links__one" key=${`${l.from}>${l.to}`} title=${`${model.byId.get(l.from).name} to ${model.byId.get(l.to).name}`}>
        <span class="ork-chip">${model.byId.get(l.to).name}</span><${Chev} /></span>`)}</div>`}
      ${stepHead(st)}
      ${st.real && html`${painsAt(`step:${st.n}`, true)}`}
      <div class="scr-step__cards">${st.ids.map((sid) => card(sid, st.n))}</div>
    </section>
  </${Pickable}>`;
  const arrows = narrow ? [] : arrowsOf(doc.links || [], geo, model.stepOf, model.byId);
  const open = id && model.byId.get(id);
  const here = open ? model.pains.filter((p) => p.on === id) : [];

  return html`<div class=${cls("scr-map", { "is-carrying": !!carry, "is-dragging": !!drag })} ref=${host} data-state="read">
    <div class="scr-head">
      ${segments.length > 0 && html`<div class="scr-seg" role="group" aria-label="Segment">
        <button type="button" class="ork-chip" aria-pressed=${String(!shown)} data-segment="" onClick=${() => setSeg("")}>All segments</button>
        ${segments.map((s) => html`<button type="button" key=${s} class="ork-chip" aria-pressed=${String(shown === s)} data-segment=${s} onClick=${() => setSeg(shown === s ? "" : s)}>${s}</button>`)}
      </div>`}
      <span class="scr-grow"></span>
      <span class="scr-note" role="status">${carry ? "Press a screen or a step to pin the pain there · Esc puts it down"
        : `Read from dev: ${doc.screens.length} ${doc.screens.length === 1 ? "screen" : "screens"}, ${(doc.links || []).length} ${(doc.links || []).length === 1 ? "link" : "links"}${pictureless ? ` · ${pictureless} without a picture yet` : ""}`}</span>
    </div>
    <div class="scr-scroll" ref=${scroller} onScroll=${(e) => { if (id && !narrow && Date.now() - seen.current.at > 300 && Math.abs(e.currentTarget.scrollTop - seen.current.top) + Math.abs(e.currentTarget.scrollLeft - seen.current.left) > 40) lower(); }}>
      <div class=${cls("scr-flow", { "is-narrow": narrow })} ref=${flow}>
        ${!narrow && html`<svg class="scr-lines" width=${Math.max(...Object.values(geo).map((b) => b.x + b.w), 0) + 8} height=${Math.max(...Object.values(geo).map((b) => b.y + b.h), 0) + 8} aria-hidden="true">
          ${arrows.map((a) => html`<path key=${a.key} d=${a.d} />`)}</svg>`}
        ${narrow ? html`<div class="scr-steps">${model.steps.map(narrowStep)}</div>` : model.steps.map(column)}
        ${!narrow && arrows.map((a) => html`<span key=${a.key} class="scr-arrow" style=${`left:${a.x}px;top:${a.y}px`} data-link=${a.key} title=${`${a.from} to ${a.name}`}>
          <span class="ork-chip scr-arrow__name">${a.name}</span><i class="ork-chev right"></i></span>`)}
      </div>
      ${(loose.length > 0 || drag) && html`<div class="scr-loose" data-drop="" aria-label="Pains not on a screen">
        <span class=${cls("ork-label", { "is-over": drag?.over === "" })}>Not on a screen yet</span>
        ${painsAt("")}
      </div>`}
    </div>
    ${drag && html`<div class="ork-card scr-ghost" style=${`left:${drag.x}px;top:${drag.y}px`} aria-hidden="true"><span class="scr-pain__sg">${drag.p.segment}</span><span class="scr-pain__nm">${drag.p.text}</span></div>`}
    ${open && html`<${Lifted} host=${host} name=${open.name} narrow=${narrow}><${ScreenBack} s=${open} doc=${doc} party=${g.slug} from=${from} pains=${here} byId=${model.byId} lift=${(sid) => lift(screenKey(g.slug, sid))} /></${Lifted}>`}
  </div>`;
}

mapFor("design", ScreensMap);
