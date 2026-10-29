// The Tech lens's System as the project's architecture (docs/specs/90-what-the-first-look-said.md §6.7, decisions §104.2, §105.6): `ideas.system`'s `overview` (realm/system_overview.py, read with no model)
// laid on the table as the field's cards, never a diagram. Each container is a column: over it its name (a 2 px rule as wide as the column, as a member's name is over its), its stack as small cards (a
// role each: UI, server, realtime, data, build, test, game; the libraries not on the list counted), its ways in marked (*Ways in*); under it its layers top to bottom, each a row of its parts (spec 89's
// cards; a row wraps after three), the layer's role named at the row's start (*Its face*, *Its doors*, *Its data*, *Its settings*). A part two containers use lies once, in a *Shared* column between the
// columns it serves, not in its own container's rows; a container left with no part of its own (a workspace whose code is all shared) lies after the others. Each link between two containers is the field's arrow in square steps through a lane over the columns (the shortest lowest, few and short), named on
// it (*HTTP: n routes · socket: n events*); a press on the name opens the link's routes and events in the right column (a tab of kind `link`, `LinkView`), a press again closes it. The cards are spec 87's
// 128 x 180, or 96 x 134 (5:7, the name in three lines, *Uses k · Used by m* in the title) when the table is crowded: more than four columns or more than twenty parts. Spec 89's reveal and marks apply to
// the parts inside the containers and the shared ones: the reveal is played once by `Lens` for both views, System and Feature modules (systemmap.js `Modules`); a container's parts gone since the last look
// lie in a last row of their own to crumble. `overview` null (a snapshot of a host from before spec 90): *Reading the project…*, and Feature modules still works.
// The whole is drawn at its natural size and scaled to the pane's width (sysfit.js: spec 107 §6; the arrows are measured in the unscaled box); *Fit* and *100 %* in its corner.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { command } from "../link.js";
import { lift, lifted, lower, linkKey } from "../frame/state.js";
import { ArrowLines } from "./arrows.js";
import { useScrollCue } from "../scrollcue.js";
import { FitButtons, useFit, usePan } from "./sysfit.js";
import { COULD_NOT, DONE, Modules, NOTHING, Part, READING, SysBar, dealsOf, liftedPart, openPart, orderOf, phaseOf, shownSys, useReveal } from "./systemmap.js";

// -- the words (spec 90 §0) ---------------------------------------------------------------------------------------------------------------------------------------------------
export const SHARED = "Shared";
export const WAYS_IN = "Ways in";
export const ROLE_WORDS = { face: "Its face", doors: "Its doors", data: "Its data", settings: "Its settings" };
export const WAY_WORDS = { page: "Page", main: "Main", bin: "Command", script: "Script", listen: "Listens" };
export const routesWords = (n) => `HTTP: ${n} ${n === 1 ? "route" : "routes"}`;
export const eventsWords = (n) => `socket: ${n} ${n === 1 ? "event" : "events"}`;
/** A link's name on its arrow: *HTTP: 6 routes · socket: 4 events* (a side with none left out). */
export const linkWords = (l) => [l.http?.length ? routesWords(l.http.length) : "", l.socket?.length ? eventsWords(l.socket.length) : ""].filter(Boolean).join(" · ");
export const moreWords = (n) => `+${n} more`;
const base = (p) => (p || "").split("/").pop() || p || "";

const PER = 3;                                           // a layer's row wraps after three cards
const CROWDED_COLS = 4, CROWDED_PARTS = 20;               // more than this: the smaller cards
const LANE = 40;                                         // a link's lane over the columns
const SLOT = 28;                                         // two ends of links at one container, this far apart
const HEAD = 9, HALF = 4;                                // the arrow head (arrows.js's)

/** The columns of the table, left to right: each container (its rows: its layers without the shared parts, then its parts gone since the last look), and after the first container a shared part serves
 *  (that is followed by another it serves) a *Shared* column of those parts. */
export function planOf(ov) {
  const containers = ov?.containers || [], ids = containers.map((c) => c.path);
  const shared = ov?.shared || [], common = new Set(shared.map((s) => s.path));
  const groups = new Map();
  for (const s of shared) {
    const at = (s.containers || []).map((p) => ids.indexOf(p)).filter((i) => i >= 0).sort((a, b) => a - b);
    const i = at.length > 1 ? at[0] : Math.max(0, ids.indexOf(s.container));
    const g = groups.get(i) || { serves: [], parts: [] };
    for (const p of s.containers || []) if (!g.serves.includes(p) && ids.includes(p)) g.serves.push(p);
    g.parts.push(s.path);
    groups.set(i, g);
  }
  const cols = [], bare = [];
  containers.forEach((c, i) => {
    const laid = new Set((c.layers || []).flatMap((l) => l.parts));
    const rows = (c.layers || []).map((l) => ({ role: l.role || "", parts: l.parts.filter((p) => !common.has(p)) }));
    const loose = (c.parts || []).filter((p) => !laid.has(p) && !common.has(p));
    if (loose.length) rows.push({ role: "", parts: loose });
    const gone = (c.gone || []).filter((p) => !common.has(p) && !laid.has(p));
    if (gone.length) rows.push({ role: "", parts: gone, gone: true });
    const col = { kind: "container", c, rows: rows.filter((r) => r.parts.length) };
    (col.rows.length || !containers.some((o) => o !== c && (o.parts || []).some((p) => !common.has(p))) ? cols : bare).push(col);
    const g = groups.get(i);
    if (g) cols.push({ kind: "shared", serves: g.serves, parts: g.parts });
  });
  return [...cols, ...bare];                                // a container with no part of its own (a workspace whose code is all shared) after the others: its name, stack and ways in
}

/** The links' arrows over the table `host`: each from the top of its `from` container's column up into its lane, across, down into the top of its `to`'s; the shortest span in the lowest lane. Each
 *  carries its name's place (`at`) on the middle of its lane. `scale`: the host is drawn scaled by it, so what is measured is divided by it. */
function arrowsOf(host, links, scale = 1) {
  if (!host || !links.length) return [];
  const origin = host.getBoundingClientRect();
  const box = (id) => {
    const el = host.querySelector(`.arch-col[data-container="${CSS.escape(id)}"]`);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: (r.left - origin.left) / scale, y: (r.top - origin.top) / scale, w: r.width / scale };
  };
  const items = links.map((l) => ({ l, a: box(l.from), b: box(l.to) })).filter((x) => x.a && x.b && x.l.from !== x.l.to);
  items.sort((p, q) => Math.abs(p.a.x - p.b.x) - Math.abs(q.a.x - q.b.x));
  const ends = new Map();                                 // the ends at each container, ordered by where the other end lies
  items.forEach((it) => {
    for (const [id, me, other, end] of [[it.l.from, it.a, it.b, "a"], [it.l.to, it.b, it.a, "b"]]) ends.set(id, [...(ends.get(id) || []), { it, me, other, end }]);
  });
  for (const list of ends.values()) {
    list.sort((p, q) => p.other.x - q.other.x);
    list.forEach((e, j) => { e.it[`x${e.end}`] = e.me.x + e.me.w / 2 + (j - (list.length - 1) / 2) * SLOT; });
  }
  const top = Math.min(...items.map((it) => Math.min(it.a.y, it.b.y)));
  const at = (x, y) => `${x.toFixed(1)},${y.toFixed(1)}`;
  return items.map((it, k) => {
    const xa = it.xa, xb = it.xb, ya = it.a.y - 2, yb = it.b.y - 2, lane = top - 4 - LANE * (k + 0.5);
    return { key: `${it.l.from}>${it.l.to}`, kind: "link", x1: xa, y1: ya, points: [at(xa, ya), at(xa, lane), at(xb, lane), at(xb, yb - (HEAD - 1))].join(" "),
      tip: { x: xb, y: yb }, head: `${at(xb, yb)} ${at(xb - HALF, yb - HEAD)} ${at(xb + HALF, yb - HEAD)}`, at: { x: (xa + xb) / 2, y: lane }, link: it.l };
  });
}

/** A container's name over its column: its stack as small cards, the libraries not on the list counted, its ways in marked. */
function Head({ c }) {
  const ways = c.ways_in || [];
  return html`<header class="arch-head">
    <span class="arena-member__nm arch-name" title=${c.path === "." ? c.name : c.path}>${c.name}</span>
    <span class="arch-rule" aria-hidden="true"></span>
    ${((c.stack || []).length > 0 || c.unknown > 0) && html`<ul class="arch-stack" aria-label=${`${c.name}: its stack`}>
      ${(c.stack || []).map((s) => html`<li key=${s.name} class="arch-lib" data-role=${s.role} title=${`${s.name} · ${s.role}`}><span class="arch-lib__nm">${s.name}</span><span class="arch-lib__role">${s.role}</span></li>`)}
      ${c.unknown > 0 && html`<li class="arch-lib is-more" title=${`${c.unknown} more not on the list of known libraries`}><span class="arch-lib__nm">${moreWords(c.unknown)}</span></li>`}
    </ul>`}
    ${ways.length > 0 && html`<div class="arch-ways"><span class="arch-ways__h">${WAYS_IN}</span>
      <ul class="arch-ways__list">${ways.map((w, i) => html`<li key=${i} class="arch-way" data-kind=${w.kind} title=${w.path || w.name}><${Icon} name="arrow-right" />
        <b>${WAY_WORDS[w.kind] || w.kind}</b> <span class="arch-way__what">${w.kind === "script" || w.kind === "bin" ? w.name || base(w.path) : base(w.path)}</span></li>`)}</ul></div>`}
  </header>`;
}

/** System: the containers as columns on the table, the shared parts between those they serve, the links as arrows named on them. */
export function Architecture({ doc, order, step, pick, party }) {
  const ov = doc.overview, host = useRef(), scroller = useRef(), [arrows, setArrows] = useState([]), [hover, setHover] = useState("");
  const shownPart = liftedPart(party), linkHead = `t:link:${party}:`, shownLink = lifted.value.startsWith(linkHead) ? lifted.value.slice(linkHead.length) : "";
  const cols = planOf(ov), links = ov.links || [];
  const parts = ov.parts || {};
  const count = cols.reduce((k, col) => k + (col.kind === "shared" ? col.parts.length : col.rows.reduce((j, r) => j + r.parts.length, 0)), 0);
  const small = cols.length > CROWDED_COLS || count > CROWDED_PARTS;
  const draw = (f = 1) => {
    const next = arrowsOf(host.current, links, f);
    setArrows((was) => (JSON.stringify(was.map((a) => a.points)) === JSON.stringify(next.map((a) => a.points)) ? was : next));
  };
  const there = (ov.containers || []).length > 0;
  const fit = useFit(scroller, host, draw, [ov, small, there]);
  useLayoutEffect(() => draw(fit.scale()), [ov, small]);
  useScrollCue(scroller);
  usePan(scroller, [there]);
  if (!(ov.containers || []).length) return html`<div class="sys-main"><div class="assets-none"><p class="assets-none__title">${NOTHING}</p></div></div>`;
  const goals = doc.goals || {}, gindex = new Map(order.map((o, i) => [o.goal, i])), deals = dealsOf(doc, order);
  const lit = new Set(hover ? [...(parts[hover]?.uses || []), ...(parts[hover]?.used_by || [])] : []);
  const names = Object.fromEntries((ov.containers || []).map((c) => [c.path, c.name]));
  const press = (c) => (shownPart === c.path ? lower() : openPart(c.path, party));
  const hovered = (path) => setHover(path);
  const card = (path, area) => {
    const c = parts[path] || { path, name: base(path), count: 0, uses: [], used_by: [], gone: false };
    const m = doc.changed?.[path], gi = m ? gindex.get(m.goal || "") : -1, phase = phaseOf(m, gi, step);
    return html`<${Part} key=${path} c=${{ ...c, area }} m=${m} goal=${m?.goal ? goals[m.goal] : null} phase=${phase} deal=${deals.get(path) || 0}
      dim=${!!pick && !!m && pick !== (m.goal || "@you")} on=${shownPart === path} lit=${hover === path ? "src" : lit.has(path) ? "use" : ""} onPress=${press} onHover=${hovered} />`;
  };
  const openLink = (l) => {
    const key = `${l.from}>${l.to}`;
    if (shownLink === key) lower();
    else lift(linkKey(party, key));
  };
  return html`<div class="sys-main">
    <div class="sys-scroll gui-scrolls" ref=${scroller}>
      <div class="arch-fit" style=${fit.w ? `width:${(fit.w * fit.f).toFixed(1)}px;height:${(fit.h * fit.f).toFixed(1)}px` : undefined}>
      <div class=${cls("arch", { "is-small": small })} ref=${host} data-size=${small ? "small" : "full"} data-scale=${fit.f.toFixed(3)} style=${fit.f < 1 ? `transform:scale(${fit.f})` : undefined}>
        <div class="arch-lanes" style=${`height:${links.length * LANE + 8}px`} aria-hidden="true"></div>
        <div class="arch-cols">
          ${cols.map((col) => (col.kind === "shared" ? html`<section key=${`shared:${col.serves.join(",")}`} class="arch-col arch-shared" data-shared=${col.serves.join(",")} aria-label=${SHARED}>
              <header class="arch-head"><span class="arena-member__nm arch-name">${SHARED}</span><span class="arch-rule" aria-hidden="true"></span>
                <span class="arena-cap arch-serves">${col.serves.map((p) => names[p] || p).join(" · ")}</span></header>
              <div class="arch-layer__parts">${col.parts.map((p) => card(p, SHARED))}</div>
            </section>`
            : html`<section key=${col.c.path} class=${cls("arch-col", { "is-bare": !col.rows.length })} data-container=${col.c.path} aria-label=${col.c.name}>
              <${Head} c=${col.c} />
              ${col.rows.length > 0 && html`<div class="arch-layers">${col.rows.map((r, i) => html`<div key=${i} class=${cls("arch-layer", { "is-gone": !!r.gone })} data-role=${r.role || undefined}>
                <span class="arch-layer__nm">${ROLE_WORDS[r.role] || ""}</span>
                <div class="arch-layer__parts">${r.parts.map((p) => card(p, col.c.name))}</div></div>`)}</div>`}
            </section>`))}
        </div>
        <${ArrowLines} lines=${arrows} />
        ${arrows.map((a) => html`<button type="button" key=${a.key} class="arch-link" data-link=${a.key} style=${`left:${a.at.x.toFixed(1)}px;top:${a.at.y.toFixed(1)}px`}
          aria-pressed=${String(shownLink === a.key)} aria-label=${`${names[a.link.from] || a.link.from} → ${names[a.link.to] || a.link.to}: ${linkWords(a.link)}`}
          onClick=${() => openLink(a.link)}>${linkWords(a.link)}</button>`)}
      </div>
      </div>
    </div>
    <${FitButtons} mode=${fit.mode} setMode=${fit.setMode} />
  </div>`;
}

// -- a link in the right column ------------------------------------------------------------------------------------------------------------------------------------------------

/** A link opened in the right column (a tab `{kind: "link", path: "<from>><to>", slug: <its party>}`): its routes (the method, the path, where it is called and answered) and its events (the event, which
 *  way, where it is sent and handled). Read from the System shown last, else asked of the host. */
export function LinkView({ p: tab }) {
  const party = tab.slug || "", sys = shownSys.value, [from, to] = (tab.path || "").split(">");
  const mine = sys && sys.party === party ? sys.doc?.overview : null;
  const [ov, setOv] = useState(mine), [err, setErr] = useState("");
  useEffect(() => {
    if (mine) { setOv(mine); return undefined; }
    let live = true;
    command("ideas.system", { party }, true).then((r) => {
      if (!live) return;
      if (!r || r.error || !r.overview) setErr(r?.error || COULD_NOT);
      else setOv(r.overview);
    }).catch((e) => { if (live) setErr(e.message || COULD_NOT); });
    return () => { live = false; };
  }, [tab.path, party, mine]);
  const link = (ov?.links || []).find((l) => l.from === from && l.to === to);
  const names = Object.fromEntries((ov?.containers || []).map((c) => [c.path, c.name])), A = names[from] || from, B = names[to] || to;
  const title = `${A} → ${B}`, way = { out: `${A} → ${B}`, back: `${B} → ${A}`, both: "both ways" };
  return html`<section class="sys-side arch-side" aria-label=${title} data-link=${tab.path}>
    <div class="sys-side__head"><b class="sys-side__name">${title}</b></div>
    ${err ? html`<p class="arena-cap">${err}</p>` : !ov ? html`<p class="arena-cap"><span class="ork-busy"></span></p>` : !link ? html`<p class="arena-cap">${A} and ${B} no longer talk</p>` : html`
      <p class="arena-cap">${linkWords(link)}</p>
      ${(link.http || []).length > 0 && html`<section class="sys-side__sec" data-sec="http"><h3 class="arena-sec">${routesWords(link.http.length)}</h3>
        <ul class="arch-side__list">${link.http.map((r, i) => html`<li key=${i} class="arch-route"><span class="arch-route__head"><b class="arch-route__m">${r.method}</b> <code class="arch-route__path">${r.path}</code></span>
          <span class="arch-route__where" title=${`${r.called_in} · ${r.answered_in}`}>Called in ${base(r.called_in) || "—"} · answered in ${base(r.answered_in) || "—"}</span></li>`)}</ul></section>`}
      ${(link.socket || []).length > 0 && html`<section class="sys-side__sec" data-sec="socket"><h3 class="arena-sec">${eventsWords(link.socket.length)}</h3>
        <ul class="arch-side__list">${link.socket.map((e, i) => html`<li key=${i} class="arch-event" data-way=${e.way}><span class="arch-route__head"><code class="arch-route__path">${e.event}</code> <span class="arch-event__way">${way[e.way] || e.way}</span></span>
          <span class="arch-route__where" title=${`${e.emitted_in} · ${e.handled_in}`}>Sent in ${base(e.emitted_in) || "—"} · handled in ${base(e.handled_in) || "—"}</span></li>`)}</ul></section>`}`}
  </section>`;
}

// -- the lens: both views over one bar, the reveal played once -------------------------------------------------------------------------------------------------------------------

/** The Tech lens's System or Feature modules (`tab`), with the bar over them. What was shown is seen when the lens is left (to Board, another party, or the page), not between its two views; the reveal
 *  plays once, on the first answer a view can show. `sys`: systemmap.js `useSystem`'s. */
export function Lens({ sys, party, tab }) {
  const { doc, err, look } = sys;
  const shows = !!doc && (tab === "modules" || !!doc.overview);
  const order = doc ? orderOf(doc) : [], step = useReveal(shows ? doc : null, order);
  const [pick, setPick] = useState("");
  useEffect(() => {                                        // the lens is left (or the page): what it showed is seen
    const save = () => sys.seen();
    addEventListener("pagehide", save);
    return () => { removeEventListener("pagehide", save); save(); };
  }, []);
  useEffect(() => { if (doc) shownSys.value = { doc, look, party }; }, [doc, look, party]);
  if (err && !doc) return html`<div class="sys" data-state="failed" data-view=${tab}><p class="arena-cap sys-note">${err}</p></div>`;
  if (!shows) return html`<div class="sys" data-state="reading" data-view=${tab}><p class="arena-cap sys-note"><span class="ork-busy"></span> ${READING}</p></div>`;
  const playing = step !== DONE;
  return html`<div class="sys" data-state="shown" data-view=${tab} data-reveal=${playing ? "playing" : "done"} data-step=${playing ? step : undefined}>
    <${SysBar} doc=${doc} look=${look} order=${order} pick=${pick} setPick=${setPick} rearrange=${tab === "modules" ? () => sys.rearrange() : null} />
    ${tab === "modules" ? html`<${Modules} doc=${doc} order=${order} step=${step} pick=${pick} party=${party} />`
      : html`<${Architecture} doc=${doc} order=${order} step=${step} pick=${pick} party=${party} />`}
  </div>`;
}
