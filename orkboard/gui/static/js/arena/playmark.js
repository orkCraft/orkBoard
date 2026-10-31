// Mark on the live product (docs/specs/115-the-live-product-under-each-leaders-eyes.md §6.4–§6.5, mockup docs/mockups/play-lenses/ states 4–8): the live product's own picking, as a party's map is picked (spec 102 §6).
// The bar's **Mark** (or the key `M`, or **Make it a goal** on a hint) lays a still layer over the frame — the product takes no press; the bar says *Draw a box or press a part* · *Cancel*, Esc cancels: a drag draws the box (dashed, in
// the ink), a press takes the rectangle of the first element under it (the probe's `under`; with no probe, a small box around the press). The field opens beside the box, inside the pane: the line; the kinds as radio chips (*Bug*,
// *Looks wrong*, *Missing*, *Confusing*); *→ <Party> ×* (the open tab's party; none on the project's tab, where the Orkmaster routes it); *With:* and the chips of what goes with it, each with its × (*the screen: <name>*, *the part: <part>*,
// *<n> errors*, *<n> failed requests*, *the server's last lines*, *the game's state* when the probe has one); *Add to "<goal>"* when the host offers one (`ideas.play_mark_offer`: ticked); **Send**. Send asks the probe for the picture and the
// state, then `ideas.play_mark`. Sent: the box stays about 1.2 s on the frame in the goal's element's colour (a stepped fade; none under reduced motion), the bar says *Sent to <Party>: <title>*, Play stays open and the goal is in the first lane.
// A canvas under the box: the chips gain *the game's state*, and under Game design's tab the field asks *At which step?* with the loop's steps (`ideas.loop`) as chips; the chosen step goes in the text.
// The box is kept in pixels of the frame (the probe's); the host takes it in shares (0 to 1) of the frame.
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Sign } from "../orkui.js";
import { command } from "../link.js";
import { refreshShell } from "../shell/store.js";
import { pathOf, tally } from "./playlens.js";

export const MARK = "Mark", CANCEL = "Cancel", DRAW = "Draw a box or press a part", SEND = "Send", STEP_ASK = "At which step?";
export const KINDS = [["bug", "Bug"], ["looks", "Looks wrong"], ["missing", "Missing"], ["confusing", "Confusing"]];
export const sentWords = (party, title) => `Sent to ${party}: ${title}`;

const FIELD_W = 380, MIN_DRAG = 6, SENT_MS = 1200, PRESS_BOX = { w: 64, h: 40 };
const typing = (el) => !!el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || el.isContentEditable);
const clamp = (n, lo, hi) => Math.max(lo, Math.min(n, Math.max(lo, hi)));
const share = (n, of) => (of > 0 ? Math.round((n / of) * 10000) / 10000 : 0);

/** The mark's state and what it does (see the head). `stage`: the frame's box (a ref); `probe`: playlens.js `useProbe`; `where`: the place (`useLens`); `lens`: the open tab's lens or null; `g`: the open tab's party or null; `said`: puts words in the bar;
 *  `enabled`: Play shows its frame; `made(hint)`: a hint was made into a goal (it is not shown again in this play). */
export function useMark({ stage, probe, where, lens, g, said, enabled, made }) {
  const [m, setM] = useState({ mode: "off" }), [drag, setDrag] = useState(null), pointer = useRef(null), alive = useRef(true), pk = pathOf(probe.place);
  useEffect(() => () => { alive.current = false; }, []);
  const patch = useCallback((p) => setM((o) => ({ ...o, ...p })), []);
  const kindHere = lens?.mapId === "screens" || lens?.mapId === "art" ? "looks" : "bug";
  const start = useCallback((seed = {}) => {
    if (!enabled) return;
    setM({ mode: seed.box ? "field" : "draw", box: null, under: [], text: "", kind: kindHere, off: [], add: true, party: true, step: "", state: null, offer: null, steps: null, busy: false, error: "", ...seed });
    said("");
  }, [enabled, kindHere]);
  const cancel = useCallback(() => { setM({ mode: "off" }); setDrag(null); pointer.current = null; }, []);
  const now = useRef({});
  now.current = { mode: m.mode, enabled, start, cancel };                             // what the key's listener reads: always this render's, never one a render behind
  useEffect(() => {                                                                    // Esc cancels (before the pane's own Esc, which would close Play); M starts
    const key = (e) => {
      const { mode, enabled: on, start: begin, cancel: stop } = now.current;
      if (e.key === "Escape" && (mode === "draw" || mode === "field")) { e.preventDefault(); e.stopPropagation(); stop(); return; }
      if ((e.key === "m" || e.key === "M") && !e.ctrlKey && !e.metaKey && !e.altKey && mode === "off" && on && !typing(e.target)) { e.preventDefault(); begin(); }
    };
    addEventListener("keydown", key, true);
    return () => removeEventListener("keydown", key, true);
  }, []);
  useEffect(() => { if (!enabled && m.mode !== "off") cancel(); }, [enabled]);
  const field = m.mode === "field";
  useEffect(() => {                                                                    // the game's state, if the page tells one
    if (!field || !probe.probing) return undefined;
    let live = true;
    probe.ask("state").then((r) => { if (live) patch({ state: r && !r.none && r.state != null ? r.state : null }); });
    return () => { live = false; };
  }, [field, probe.probing]);
  useEffect(() => {                                                                    // a goal not started with a mark of this kind here, by code
    if (!field) return undefined;
    let live = true;
    command("ideas.play_mark_offer", { path: pk, kind: m.kind }, true).then((r) => { if (live) patch({ offer: r?.goal || null }); }).catch(() => { if (live) patch({ offer: null }); });
    return () => { live = false; };
  }, [field, m.kind, pk]);
  const canvas = (m.under || []).some((u) => u.role === "canvas" || /^canvas\b/.test(u.selector || "")), asksStep = field && canvas && lens?.mapId === "game-design";
  useEffect(() => {                                                                    // the loop's steps, since no code knows which one this is
    if (!asksStep || m.steps) return;
    command("ideas.loop", {}, true).then((r) => { if (alive.current) patch({ steps: [...new Set((r?.loops || []).flatMap((l) => (l.steps || []).map((s) => s.name)).filter(Boolean))].slice(0, 12) }); }).catch(() => patch({ steps: [] }));
  }, [asksStep]);

  const rel = (e) => { const r = stage.current.getBoundingClientRect(); return { x: clamp(e.clientX - r.left, 0, r.width), y: clamp(e.clientY - r.top, 0, r.height) }; };
  const fit = (r) => {                                                                 // a rectangle inside the frame, at least 8 px
    const W = stage.current.clientWidth, H = stage.current.clientHeight, x = clamp(r.x, 0, W - 8), y = clamp(r.y, 0, H - 8);
    return { x, y, w: clamp(r.w, 8, W - x), h: clamp(r.h, 8, H - y) };
  };
  const down = (e) => {
    if (e.button) return;
    e.currentTarget.setPointerCapture?.(e.pointerId);
    pointer.current = rel(e);
    setDrag({ from: pointer.current, to: pointer.current });
  };
  const move = (e) => { if (pointer.current) setDrag({ from: pointer.current, to: rel(e) }); };
  const up = async (e) => {
    const from = pointer.current;
    pointer.current = null;
    setDrag(null);
    if (!from) return;
    const to = rel(e), w = Math.abs(to.x - from.x), h = Math.abs(to.y - from.y);
    if (w >= MIN_DRAG || h >= MIN_DRAG) {                                              // a drag draws the box; the elements under it come when the probe answers
      const box = fit({ x: Math.min(from.x, to.x), y: Math.min(from.y, to.y), w, h });
      setM((o) => ({ ...o, mode: "field", box, under: [] }));
      const r = await probe.ask("under", { box });
      if (alive.current && r?.elements) patch({ under: r.elements });
    } else {                                                                           // a press takes the first element under it
      const r = await probe.ask("under", { box: { x: to.x, y: to.y, w: 0, h: 0 } }), els = r?.elements || [];
      if (!alive.current) return;
      setM((o) => ({ ...o, mode: "field", under: els, box: els[0]?.rect ? fit(els[0].rect) : fit({ x: to.x - PRESS_BOX.w / 2, y: to.y - PRESS_BOX.h / 2, ...PRESS_BOX }) }));
    }
  };

  const chips = chipsOf(m, { where, lens, probe });
  const send = async () => {
    const el = stage.current, W = el.clientWidth, H = el.clientHeight, keep = chips.filter((c) => !m.off.includes(c.key)).map((c) => c.key), by = !!(m.party && g);
    patch({ busy: true, error: "" });
    let picture, state;
    if (probe.probing && keep.includes("screen")) { const p = await probe.ask("picture", {}, 6000); if (p?.html) picture = { html: p.html, w: p.w, h: p.h }; }
    if (probe.probing && keep.includes("state")) { const s = await probe.ask("state"); if (s && !s.none && s.state != null) state = s.state; }
    const text = m.step ? `${m.text.trim()}\n\nAt the step: ${m.step}` : m.text.trim(), box = m.box;
    try {
      const r = await command("ideas.play_mark", { text, kind: m.kind, path: pk, box: { x: share(box.x, W), y: share(box.y, H), w: share(box.w, W), h: share(box.h, H) }, viewport: { w: W, h: H }, with: keep,
        under: (m.under || []).slice(0, 3), ...(picture ? { picture } : {}), ...(state !== undefined ? { state } : {}), ...(by ? { party: g.slug } : {}), ...(m.offer && m.add ? { add_to: m.offer.slug } : {}) }, true);
      if (!alive.current) return;
      setM({ mode: "sent", box, element: r?.element || "dust" });
      if (m.hint) made?.(m.hint);
      said(sentWords(r?.party_title || (by ? g.short || g.title : "") || "the Orkmaster", r?.title || r?.slug || ""));
      refreshShell();
      setTimeout(() => { if (alive.current) setM((o) => (o.mode === "sent" ? { mode: "off" } : o)); }, SENT_MS);
    } catch (e) {
      if (alive.current) patch({ busy: false, error: e?.message || "It did not send" });
    }
  };
  return { m, patch, start, cancel, send, chips, canvas, drag, place: probe.place, handlers: { onPointerDown: down, onPointerMove: move, onPointerUp: up, onPointerCancel: () => { pointer.current = null; setDrag(null); } } };
}

/** The chips of what goes with a mark (`with`'s keys), the ones this place has: see the head. */
function chipsOf(m, { where, lens, probe }) {
  const out = [], path = probe.place?.path || "/", under = (m.under || [])[0];
  out.push({ key: "screen", label: where.screen ? `the screen: ${where.screen.name}` : `the page: ${path}` });
  const part = lens?.parts?.[0]?.name || (under ? (under.role === "canvas" ? "the canvas" : under.selector) : "");
  if (part) out.push({ key: "part", label: `the part: ${part}` });
  const t = tally(probe.events, path);
  if (t.errors) out.push({ key: "errors", label: `${t.errors} ${t.errors === 1 ? "error" : "errors"}` });
  if (t.requests) out.push({ key: "requests", label: `${t.requests} failed ${t.requests === 1 ? "request" : "requests"}` });
  out.push({ key: "lines", label: "the server's last lines" });
  if (m.state != null) out.push({ key: "state", label: "the game's state" });
  return out;
}

const boxStyle = (b) => `left:${b.x}px;top:${b.y}px;width:${b.w}px;height:${b.h}px`;

function Kinds({ kind, set }) {
  const keys = (e) => {
    const at = KINDS.findIndex(([id]) => id === kind), to = { ArrowRight: at + 1, ArrowDown: at + 1, ArrowLeft: at - 1, ArrowUp: at - 1 }[e.key];
    if (to === undefined) return;
    e.preventDefault();
    const next = KINDS[(to + KINDS.length) % KINDS.length][0];
    set(next);
    e.currentTarget.querySelector(`[data-kind="${next}"]`)?.focus();
  };
  return html`<div class="play-field__row" role="radiogroup" aria-label="Kind" onKeyDown=${keys}><span class="play-field__cap">Kind</span>
    ${KINDS.map(([id, word]) => html`<button type="button" key=${id} role="radio" class="ork-chip play-kind" data-kind=${id} aria-checked=${String(kind === id)} tabIndex=${kind === id ? 0 : -1} onClick=${() => set(id)}>${word}</button>`)}</div>`;
}

/** The field beside the box (see the head). */
function Field({ mk, g, size, where }) {
  const { m, patch, chips, canvas } = mk, ref = useRef(), text = useRef(), [h, setH] = useState(320);
  useLayoutEffect(() => { if (ref.current) setH(ref.current.offsetHeight); });
  useEffect(() => { text.current?.focus(); }, []);
  const b = m.box, w = Math.min(FIELD_W, Math.max(0, size.w - 16)), right = b.x + b.w + 12, left = right + w <= size.w - 8 ? right : b.x - w - 12 >= 8 ? b.x - w - 12 : size.w - w - 8;
  const top = clamp(b.y, 8, size.h - h - 8), on = (k) => !m.off.includes(k), toggle = (k) => patch({ off: on(k) ? [...m.off, k] : m.off.filter((x) => x !== k) });
  const name = g ? g.short || g.title || g.slug : "", ready = m.text.trim() && !m.busy, failure = chips.some((c) => (c.key === "errors" || c.key === "requests") && on(c.key)) && m.kind === "bug";
  const where_ = where.screen ? where.screen.name : "the page";
  return html`<div ref=${ref} class="ork-card play-field" role="dialog" aria-label=${`Mark on ${where_}`} style=${`left:${left}px;top:${top}px;width:${w}px`}
      onKeyDown=${(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && ready) { e.preventDefault(); mk.send(); } }}>
    <div class="play-field__head"><${Sign} name="target" />Mark on ${where_}<span class="play-field__path">${pathOf(mk.place)}</span></div>
    <textarea ref=${text} class="ork-field play-field__text" aria-label="What is wrong here" value=${m.text} onInput=${(e) => patch({ text: e.currentTarget.value })}></textarea>
    <${Kinds} kind=${m.kind} set=${(kind) => patch({ kind })} />
    ${canvas && m.steps && m.steps.length > 0 && html`<div class="play-field__row" role="radiogroup" aria-label=${STEP_ASK}><span class="play-field__cap">${STEP_ASK}</span>
      ${m.steps.map((s) => html`<button type="button" key=${s} role="radio" class="ork-chip play-kind" data-step=${s} aria-checked=${String(m.step === s)} onClick=${() => patch({ step: m.step === s ? "" : s })}>${s}</button>`)}</div>`}
    ${g ? html`<div class="play-field__row"><span class="play-field__cap">To</span>${m.party
        ? html`<span class="ork-chip play-to" data-to=${g.slug}>→ ${g.leader?.head && html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} />`}${name}
            <button type="button" class="play-x" aria-label=${`Do not send it to ${name}`} onClick=${() => patch({ party: false })}>×</button></span>`
        : html`<span class="play-field__quiet">The Orkmaster routes it</span><button type="button" class="ork-btn quiet" onClick=${() => patch({ party: true })}>→ ${name}</button>`}</div>`
      : html`<div class="play-field__row"><span class="play-field__cap">To</span><span class="play-field__quiet">The Orkmaster routes it</span></div>`}
    <div class="play-field__row" role="group" aria-label="With"><span class="play-field__cap">With</span>
      ${chips.map((c) => html`<button type="button" key=${c.key} class=${cls("ork-chip play-with", { "is-off": !on(c.key) })} data-with=${c.key} aria-pressed=${String(on(c.key))} title=${on(c.key) ? "Leave it out" : "Put it back"}
        onClick=${() => toggle(c.key)}>${c.label}<span class="play-x" aria-hidden="true">×</span></button>`)}</div>
    ${m.offer && html`<label class="play-addto"><input type="checkbox" checked=${m.add} onChange=${(e) => patch({ add: e.currentTarget.checked })} />
      <span>Add to "${m.offer.title}"<small>Not started yet; it has a mark of this kind here.</small></span></label>`}
    ${failure && html`<p class="play-field__route">It reproduces: the failure goes with it, so no diagnosis call.</p>`}
    ${m.error && html`<p class="play-field__error" role="alert">${m.error}</p>`}
    <div class="play-field__acts"><button type="button" class="ork-btn quiet" onClick=${mk.cancel}>${CANCEL}</button>
      <button type="button" class="ork-btn primary" disabled=${!ready} onClick=${mk.send}>${SEND}</button></div>
  </div>`;
}

/** What lies over the frame while a mark is made and after it is sent (inside the frame's box, `position: relative`): the still layer, the box, the field; the sent box. */
export function MarkLayer({ mk, g, size, where }) {
  const { m, drag } = mk;
  if (m.mode === "sent") return html`<div class="play-sent" data-elem=${m.element} style=${boxStyle(m.box)} aria-hidden="true"></div>`;
  if (m.mode !== "draw" && m.mode !== "field") return null;
  const dragged = drag && { x: Math.min(drag.from.x, drag.to.x), y: Math.min(drag.from.y, drag.to.y), w: Math.abs(drag.to.x - drag.from.x), h: Math.abs(drag.to.y - drag.from.y) };
  return html`<div class="play-still" data-mark=${m.mode} ...${mk.handlers}></div>
    ${(dragged || m.box) && html`<div class="ork-box play-box" data-box="" style=${boxStyle(dragged || m.box)}></div>`}
    ${m.mode === "field" && m.box && !drag && html`<${Field} mk=${mk} g=${g} size=${size} where=${where} />`}`;
}
