// A hearing (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §4, §6.7; decisions §198.6; the mockup docs/mockups/hearing/ 3): what the leaders of a goal's route disagree on, the goal's card in the middle and at most three sides around it —
// *Do it* at the right, *Drop it* or *After <goal>* at the left, *Do the smaller one* at the top — thrown by the person to the one they take. Two Needs you rows are a hearing: `{kind: "hearing", idea, moment: "talk", heading, sides, left_out, own, text}`
// (a goal's Talk, once a leader said no or doubted: realm/idea_objections.py) and a `fork` row, whose `hearing` holds its sides (realm/idea_hearing.py `of_fork`: two sections that disagree). A side is `{dir: right|left|up, kind: go|drop|smaller|later|side,
// leaders: [party], names, also, line, outcome, instead?, after?, after_title?, doubts?}`.
//   The face in the hand (the question sign, the first leader's head, the heading at its foot) is `way("hearing")` below; forkcard.js gives the fork's the same lifted card. Lifted on the desktop it opens over the pane (`openOver`, kind `choose`, source
//   `hearing`: `HearingPane`, with the goal's Spec under it for a fork); lifted on a phone it lies on the goal's top card in the middle (`HearingHere`, spec 117's middle).
//   The card in the middle is dragged or swiped (`setPointerCapture`, `touch-action: none` on the card alone; never from the screen's edge), tilts toward the side it nears, that side grows and its outcome is stamped on the card; let go past a third of the way
//   (or flung) it is thrown, short of it it comes back, down is no side. A press on a side throws it, → ← ↑ throw, Enter on the card (or *Or say it in your own words*) opens the field for the person's words. `ideas.throw {idea, moment, dir | text}`.
//   The toast says *Thrown to <Leader>: <outcome>*. Every throw of a Talk's hearing is sent at once and its toast says **Undo** for six seconds: `ideas.unthrow {idea, moment}` takes it back (a dropped goal returns, *Not now* is undone) unless it went on already,
//   which the host says in plain words (core/idea_objection.py `unthrow`); a fork's throw has no Undo, the leaders write their sections from it at once. Under reduced motion the card follows nothing and flies nowhere. Its sheet is hearing.css, linked as the hand's are.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { command, toast } from "../link.js";
import { board } from "../board/store.js";
import { mapData, act } from "../shell/store.js";
import { openOver, picked, tab } from "../frame/state.js";
import { uprightNow } from "../frame/upright.js";
import { mapName, nameOf, partiesAll } from "../table/data.js";
import { SpecPage, linesOf, partsOf } from "../table/specpage.js";
import { chooseFor } from "./choose.js";
import { momentOf } from "./hearingstate.js";
import { way } from "./ways.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as the hand's are linked
  const href = new URL("./hearing.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const FLY_MS = 360, UNDO_S = 6;               // the card's flight; the toast offers Undo this long
const LEAN = 16, EDGE = 20, MIN_WAY = 120, FLING = 0.5, HINT = "orkcraft.hearing.hint";       // px: where a side is nearer; the screen's edge a gesture never starts at; px/ms of a fling
const DIRS = ["right", "left", "up"];
const KEYS = { ArrowRight: "right", ArrowLeft: "left", ArrowUp: "up" };
const ARROW = { right: "→", left: "←", up: "↑" };
const SIGN = { go: "check", drop: "cross", smaller: "tidy", later: "moon" };
const OWN = "Or say it in your own words";
const reduced = () => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;
const partyBy = (slug) => partiesAll().find((g) => g.slug === slug) || null;
const headOfParty = (slug) => partyBy(slug)?.leader?.head || null;

/** The hearing a row holds, whichever kind it is: `{idea, moment, id, title, sides, own}`; a fork row with no `hearing` has its sides read from its own, in their order. */
export function hearingOf(row) {
  if (!row) return null;
  if (row.kind === "fork") {
    const h = row.hearing || {
      title: "", sides: (row.sides || []).slice(0, DIRS.length).map((s, i) => ({ dir: DIRS[i], kind: "side", party: s.party, leaders: [s.party], names: [s.leader || s.party], also: [], line: s.why || "", outcome: s.says || "" })) };
    return { idea: row.idea, moment: "fork", id: String(row.id || h.id || ""), title: h.title || row.about || "", sides: h.sides || [], own: true };
  }
  return { idea: row.idea, moment: row.moment || "talk", id: "", title: row.heading || row.text || "", sides: row.sides || [], own: row.own !== false };
}

/** The first leader's head of a hearing, as its face in the hand shows it. */
export const askerOf = (row) => headOfParty(hearingOf(row)?.sides?.find((s) => s.leaders?.length)?.leaders?.[0]) || null;

// -- the throw ----------------------------------------------------------------------------------------------------------------------

/** What the toast says of a throw: *Thrown to Sh.man: Do it* (no leader stood on the side: its outcome alone). */
const wordsOf = (side) => (side ? `${side.names?.[0] ? `Thrown to ${side.names[0]}: ` : ""}${side.outcome}` : "Said in your own words");

/** A throw: to `side`, or the person's `text`, sent at once. A Talk's throw is said with **Undo** for `UNDO_S` seconds (`ideas.unthrow`; `back()` takes the hearing up again when the host took it back, its refusal is toasted in its words);
 *  a fork's has none. `flight` is the card's flight in ms (the pane waits for it). Resolves true when the throw was taken, false when the host refused it (its words are toasted). */
export async function throwTo(h, pick, { back = null } = {}) {
  const side = pick.side || null, args = { idea: h.idea, moment: h.moment, ...(side ? { dir: side.dir } : { text: pick.text }) };
  try { localStorage.setItem(HINT, "1"); } catch { /* a convenience only */ }
  const got = await act("ideas.throw", args);
  if (!got) return false;
  if (h.moment !== "talk") { toast(wordsOf(side), "information", "", 5); return true; }
  const undo = async () => { if (await act("ideas.unthrow", { idea: h.idea, moment: h.moment })) back?.(); };
  toast(wordsOf(side), "information", "", UNDO_S, null, [{ label: "Undo", run: undo }]);
  return true;
}

// -- what the goal's card in the middle says -----------------------------------------------------------------------------------------

/** The lines of *Done when*, from the goal's page: its own section when it has one, else those of the parties' sections (at most four); the gist (or the goal's own words) when nothing is written yet. */
function wordsOfPage(page, node) {
  const secs = page?.sections || [], done = [];
  const own = secs.find((x) => String(x.name || "").trim().toLowerCase() === "done when");
  if (own) done.push(...linesOf(own.text));
  else for (const x of secs) { const p = partsOf(x.text), k = Object.keys(p).find((key) => key.toLowerCase() === "done when"); if (k) done.push(...linesOf(p[k])); }
  const gist = secs.find((x) => String(x.name || "").trim().toLowerCase() === "gist");
  return { done: done.slice(0, 4), gist: linesOf(gist?.text || "").join(" ") || (node?.title && node.title !== (node.short || "") ? node.title : "") };
}

/** The goal's page now and again when the Board changes; a page not read is no words. */
function useGoalWords(idea, node) {
  const [page, setPage] = useState(null), rev = board.value?.rev;
  useEffect(() => {
    let live = true;
    command("ideas.page", { slug: idea }, true).then((p) => { if (live) setPage(p && !p.error ? p : null); }).catch(() => { if (live) setPage((was) => was || null); });
    return () => { live = false; };
  }, [idea, rev]);
  return wordsOfPage(page, node);
}

// -- the sides ------------------------------------------------------------------------------------------------------------------------

/** An outcome in two parts: what the page says (*Do the smaller one: *, *After *: the button face) and what a leader said in it (the smaller goal, the goal waited for, a fork side's own words: the body face, never the pixel one). */
function outcomeParts(side) {
  const out = side.outcome || "", ends = (tail) => (tail && out.endsWith(tail) ? [out.slice(0, out.length - tail.length), tail] : null);
  if (side.kind === "smaller") return ends(side.instead) || [out, ""];
  if (side.kind === "later") return ends(side.after_title) || [out, ""];
  return side.kind === "side" ? ["", out] : [out, ""];
}

/** The outcome of a side as words. */
function Outcome({ side }) {
  const [fixed, said] = outcomeParts(side);
  return html`${fixed && html`<span class="hr-out__fix">${fixed}</span>`}${said && html`<span class="hr-out__said">${said}</span>`}`;
}

const joined = (names) => (names.length < 2 ? names[0] || "" : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`);

/** One side: its leaders' heads (the first at 28 px, the others at 16), its line in the body face, its outcome at its foot; the whole is a button. A line cut at three lines on a phone opens whole on *More*. */
function Side({ side, near, busy, onThrow }) {
  const said = useRef(), [open, setOpen] = useState(false), [cut, setCut] = useState(false);
  useLayoutEffect(() => {
    const el = said.current, measure = () => { if (el && !open) setCut(el.scrollHeight > el.clientHeight + 1); };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, [side.line, open]);
  const who = (side.names || []).length ? side.names : [], also = (side.also || []).length ? ` and ${joined(side.also)}` : "";
  const label = `${side.outcome}${who.length ? `, argued by ${joined(who)}` : ""}`;
  const line = side.line || (!side.leaders?.length ? "Nobody argued for it: the goal as you wrote it." : "");
  return html`<div class=${cls(`hr-side hr-side--${side.dir}`, { "is-near": near, "is-open": open })} data-dir=${side.dir} data-kind=${side.kind}>
    <button type="button" class="hr-side__btn" aria-label=${label} disabled=${busy} onClick=${() => onThrow(side)}>
      <span class="hr-who">${(side.leaders || []).map((slug, i) => {
        const head = headOfParty(slug);
        return head ? html`<span key=${slug} class=${cls("hr-head", { "is-first": i === 0 })}><${Head} race=${head.race} tier=${head.tier} /></span>` : null;
      })}<span class="hr-who__names">${who[0] || "No one"}${also}</span></span>
      <span class="hr-says" ref=${said}>${line}</span>
      ${(side.doubts || []).map((d) => html`<span key=${d.party} class="hr-doubt">${d.name} doubts: ${d.why}</span>`)}
      <span class="hr-out">${SIGN[side.kind] && html`<${Sign} name=${SIGN[side.kind]} />`}<span class="hr-out__words"><${Outcome} side=${side} /></span><span class="hr-key" aria-hidden="true">${ARROW[side.dir]}</span></span>
    </button>
    ${(cut || open) && html`<button type="button" class="ork-btn quiet hr-more" aria-expanded=${String(open)} onClick=${() => setOpen(!open)}>${open ? "Less" : "More"}</button>`}
  </div>`;
}

// -- the hearing ------------------------------------------------------------------------------------------------------------------------

const seenHint = () => { try { return localStorage.getItem(HINT) === "1"; } catch { return false; } };

/** The hearing: its title, the sides around the goal's card, the hint once a device. `reopen`: what Undo of a throw does to bring the hearing back; `onFly(true)`: told when the card is thrown, `onFly(false)` when it came back (the pane waits for the flight before it closes). */
export function Hearing({ row, reopen, onFly, close }) {
  const h = hearingOf(row), node = (mapData.value?.nodes || []).find((n) => n.slug === h.idea) || null, words = useGoalWords(h.idea, node);
  const root = useRef(), card = useRef(), field = useRef(), drag = useRef(null);
  const [near, setNear] = useState(""), [away, setAway] = useState(false), [typing, setTyping] = useState(false), [text, setText] = useState(""), [busy, setBusy] = useState(false), [hint] = useState(() => !seenHint());
  const by = Object.fromEntries(h.sides.map((s) => [s.dir, s]));
  useEffect(() => { card.current?.focus({ preventScroll: true }); }, [h.moment, h.id, h.idea]);
  useEffect(() => { if (typing) field.current?.focus({ preventScroll: true }); }, [typing]);

  const sideBox = (dir) => root.current?.querySelector(`.hr-side[data-dir="${dir}"] .hr-side__btn`)?.getBoundingClientRect() || null;
  /** How far a side lies from the card along its axis, in px (a third of it is the way a drag must go). */
  const wayTo = (dir) => {
    const s = sideBox(dir), c = card.current?.getBoundingClientRect();
    if (!s || !c) return MIN_WAY;
    return Math.max(MIN_WAY / 2, dir === "up" ? c.top + c.height / 2 - (s.top + s.height / 2) : Math.abs(s.left + s.width / 2 - (c.left + c.width / 2)));
  };
  const lean = (dx, dy) => (-dy > Math.abs(dx) && -dy > LEAN ? "up" : Math.abs(dx) >= Math.abs(dy) && dx > LEAN ? "right" : Math.abs(dx) >= Math.abs(dy) && dx < -LEAN ? "left" : "");
  const nearing = (dir) => { const d = by[dir] ? dir : ""; setNear((was) => (was === d ? was : d)); };

  const flyTo = (dir) => {                                                  // the card goes off to the side (none under reduced motion)
    setAway(true);
    onFly?.(true);
    const el = card.current, s = dir ? sideBox(dir) : null, c = el?.getBoundingClientRect();
    if (!el || reduced() || !s || !c) return;
    el.style.transform = `translate(${s.left + s.width / 2 - c.left - c.width / 2}px, ${s.top + s.height / 2 - c.top - c.height / 2}px) rotate(${dir === "left" ? -14 : dir === "right" ? 14 : 0}deg) scale(0.6)`;
  };
  const back = () => { setAway(false); setNear(""); onFly?.(false); if (card.current) card.current.style.transform = ""; };
  const send = async (pick) => {
    if (busy || away) return;
    setBusy(true);
    flyTo(pick.side?.dir || "");
    const ok = await throwTo(h, pick, { back: reopen });
    setBusy(false);
    if (!ok) back();
  };
  const throwSide = (side) => send({ side });
  const sendText = () => { const said = text.trim(); if (said) { setTyping(false); send({ text: said }); } };

  const down = (e) => {                                                     // a gesture starts on the card alone, never at the screen's edge
    if (busy || away || e.button > 0 || e.target.closest?.(".hr-own, .hr-field") || e.clientX < EDGE || e.clientX > window.innerWidth - EDGE) return;
    drag.current = { x: e.clientX, y: e.clientY, at: [[performance.now(), e.clientX, e.clientY]], dx: 0, dy: 0 };
    e.currentTarget.setPointerCapture?.(e.pointerId);
    card.current.classList.add("is-dragging");
  };
  const move = (e) => {
    const d = drag.current;
    if (!d) return;
    d.dx = e.clientX - d.x;
    d.dy = e.clientY - d.y > 0 ? (e.clientY - d.y) * 0.3 : e.clientY - d.y;           // down is no side: the card holds back
    d.at = [...d.at.slice(-3), [performance.now(), e.clientX, e.clientY]];
    if (!reduced()) card.current.style.transform = `translate(${d.dx}px, ${d.dy}px) rotate(${d.dx / 18}deg)`;
    nearing(lean(d.dx, d.dy));
  };
  const up = () => {
    const d = drag.current;
    if (!d) return;
    drag.current = null;
    card.current.classList.remove("is-dragging");
    const first = d.at[0], last = d.at[d.at.length - 1], ms = Math.max(1, last[0] - first[0]), vx = (last[1] - first[1]) / ms, vy = (last[2] - first[2]) / ms;
    const flung = Math.hypot(vx, vy) > FLING && ms < 200 ? lean(vx * 100, vy * 100) : "";
    const dir = lean(d.dx, d.dy), by_ = by[dir] ? dir : "", way = by_ ? Math.abs(by_ === "up" ? d.dy : d.dx) : 0;
    const to = by[flung] && Math.hypot(d.dx, d.dy) > LEAN ? flung : by_ && way >= Math.max(40, wayTo(by_) / 3) ? by_ : "";
    if (to) { send({ side: by[to] }); return; }
    card.current.classList.add("is-settling");                                 // short of a third: the card comes back
    setTimeout(() => card.current?.classList.remove("is-settling"), 300);
    back();
  };

  const key = (e) => {
    if (e.defaultPrevented || e.ctrlKey || e.metaKey || e.altKey || e.target.closest?.("textarea, input")) return;
    const dir = KEYS[e.key];
    if (dir) { if (by[dir]) { e.preventDefault(); throwSide(by[dir]); } return; }
    if (e.key === "Enter" && e.target === card.current && h.own) { e.preventDefault(); setTyping(true); }
  };
  const fieldKey = (e) => {
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setTyping(false); card.current?.focus({ preventScroll: true }); }
    else if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendText(); }
  };

  const name = nameOf(node) || node?.title || row.title || "", element = node?.element || "", hue = node?.hue || element, stamped = near ? by[near] || null : null;
  return html`<section ref=${root} class=${cls("ork-table hr", { "is-thrown": away })} data-kind="hearing" data-moment=${h.moment} data-goal=${h.idea} aria-label=${`${name}: ${h.title}`} onKeyDown=${key}>
    <h2 class="hr-title">${h.title}</h2>
    ${DIRS.map((dir) => by[dir] && html`<${Side} key=${`${h.moment}/${h.id}/${dir}`} side=${by[dir]} near=${near === dir} busy=${busy || away} onThrow=${throwSide} />`)}
    <div ref=${card} class=${cls(`ork-card hr-card${element ? ` el-${hue}` : ""}`, { "is-away": away })} tabindex="0" role="group" data-near=${near || undefined}
      aria-label=${`${name}: throw it to a side with the arrow keys${h.own ? ", or press Enter to say it in your own words" : ""}`}
      onPointerDown=${down} onPointerMove=${move} onPointerUp=${up} onPointerCancel=${up}>
      <span class="hr-card__head"><${Elem} name=${element} hue=${hue} dim=${!element} /><span class="hr-card__name">${name}</span></span>
      ${words.done.length > 0 ? html`<p class="ork-label hr-card__lab">Done when</p><ul class="hr-card__done">${words.done.map((l, i) => html`<li key=${i}>${l}</li>`)}</ul>`
        : words.gist && html`<p class="hr-card__gist">${words.gist}</p>`}
      ${h.own && !typing && html`<button type="button" class="hr-own" onClick=${() => setTyping(true)}>${OWN}</button>`}
      ${typing && html`<div class="hr-field" role="group" aria-label=${OWN}>
        <textarea ref=${field} class="ork-field hr-field__text" rows="3" aria-label="Your own words" value=${text} onInput=${(e) => setText(e.target.value)} onKeyDown=${fieldKey}></textarea>
        <div class="hr-field__acts"><button type="button" class="ork-btn quiet" onClick=${() => { setTyping(false); card.current?.focus({ preventScroll: true }); }}>Cancel</button>
          <button type="button" class="ork-btn primary" disabled=${!text.trim() || busy} onClick=${sendText}>Send</button></div></div>`}
      <span class="hr-stamp" aria-hidden="true" data-on=${stamped ? "1" : undefined}>${stamped && html`<${Outcome} side=${stamped} />`}</span>
    </div>
    ${hint && html`<p class="cap hr-hint">Swipe the card to the side you take, or press it</p>`}
    ${close && html`<button type="button" class="ork-btn quiet hr-back" onClick=${close}>Put it back</button>`}
  </section>`;
}

// -- over the pane (the desktop) and on the phone's middle ----------------------------------------------------------------------------

const rowOf = (idea) => (board.value?.needs_you || []).find((r) => (r.kind === "hearing" || r.kind === "fork") && r.idea === idea) || null;
const fromHere = () => ({ title: mapName(tab.value, partiesAll()), key: "" });

/** What the pane's `choose` draws for source `hearing` (`props.idea`): the hearing, and for a fork the goal's Spec with the sections of the sides lit under it. It goes back when the goal has no hearing left (thrown, answered meanwhile, or held for Undo);
 *  the next fork of the goal takes its place. The card's flight is waited for. */
function HearingPane({ props, close }) {
  const mine = rowOf(props.idea), last = useRef(null), [flying, setFlying] = useState(false);
  if (mine) { last.current = mine; }
  const row = mine || (flying ? last.current : null);
  useLayoutEffect(() => {
    if (mine) return undefined;
    if (!flying) { close(); return undefined; }
    const t = setTimeout(close, FLY_MS);
    return () => clearTimeout(t);
  }, [!mine, flying]);
  useEffect(() => { if (mine) setFlying(false); }, [mine?.id, mine?.kind]);
  if (!row) return null;
  const reopen = () => openOver("choose", { source: "hearing", idea: row.idea, moment: momentOf(row) }, fromHere(), row.title || "");
  return html`<div class="hr-pane" data-kind=${row.kind}>
    <${Hearing} key=${`${momentOf(row)}/${row.id || ""}`} row=${row} reopen=${reopen} onFly=${setFlying} close=${close} />
    ${row.kind === "fork" && html`<${SpecPage} props=${{ idea: row.idea }} />`}
  </div>`;
}
chooseFor("hearing", HearingPane);

/** The lifted card of a hearing on the desktop: it opens the hearing over the pane, in place of the aside (hand/questions.css hides it for the frame it takes). */
function HearingOpens({ s }) {
  useLayoutEffect(() => {
    openOver("choose", { source: "hearing", idea: s.row.idea, moment: momentOf(s.row) }, fromHere(), s.title || s.full);
  }, [s.key]);
  return html`<span class="q-opening" aria-hidden="true"></span>`;
}

/** The hearing on a phone: the goal's top card in the middle (spec 117), the sides around it. Thrown, the card goes from the hand and the next goal with a card is picked (upright.js); Undo of a drop picks the goal again. */
function HearingHere({ s }) {
  const reopen = () => { picked.value = s.row.idea; };
  return html`<${Hearing} key=${`${momentOf(s.row)}/${s.row.id || ""}`} row=${s.row} reopen=${reopen} />`;
}

/** The lifted card of a `hearing` row and of a `fork` row: upright on a touch phone it lies on the middle, else it opens over the pane. */
export function HearingLifted({ s }) {
  return uprightNow.value ? html`<${HearingHere} s=${s} />` : html`<${HearingOpens} s=${s} />`;
}

/** *Sh.man and the Dryad disagree*: the hearing's heading, as it is at the card's foot. */
export const headingOf = (row) => hearingOf(row)?.title || "";

// The face: the question sign, the first leader's head as its asker, the heading at its foot, no price.
way("hearing", { sign: "question", head: (s) => askerOf(s.row), foot: (s) => headingOf(s.row), price: () => null, Lifted: HearingLifted });
