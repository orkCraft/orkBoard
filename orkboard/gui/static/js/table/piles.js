// The Orkmaster's three piles (docs/specs/147-one-card-four-corners.md part B, decisions §251.3–§251.4; before: spec 128 part B.3–B.6, decisions §206.3; mockup docs/mockups/card-ratio/): the goals of the project from the snapshot's nodes, by where each lies in its life —
// **In analysis** (the idea, Talk, the decision and the spec being written: decisions §224): the Orkmaster's hand, a near-straight fan of small backs (fan.js), the goal being read lifted; **To review** (the spec is made and waits for its work, which starts by itself): a squared deck of backs on their side,
// each back's ring filling in eighths as its start comes, a goal that waits for the person with a still ring and a frame in the alert, the next to start named under the title with its time; **At work · later** (at work, its rune glowing and its leaders' heads at its foot; then put off: held, or to the night):
// standing cards, 144 x 202, read by their four corners (corners.js), the cards behind the front showing their foot, a thin edge or a sliver as the window leaves room (giveway.js, column.js). Nothing counts what waits. A card hovered or focused slides out of its pile whole (column.css).
// A back of In analysis cannot be picked (a press lifts the pile's list); a back of To review or a standing card pressed picks its goal, one of To review or a put-off one also lifts its choices (column.js).
// A potion hovered dims the cards whose goal does not wait for its tool, a card hovered hatches its next step off its tool's potion (spec 138 A.2, A.4, decisions §245.2; lit.js); a rune's glow and the ring's sweep run only on the goal that moves: the one picked, else the first at work (spec 140 C3, §247.8).
// This file classifies (`kindOf`, `pilesOf`: pure, over a node) and draws the piles and their cards; what a press does is passed in (`onPress`), so the piles hold no state of their own.
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { picked } from "../frame/state.js";
import { board } from "../board/store.js";
import { everBack } from "./backcard.js";
import { leftWords, shareOf } from "./backbody.js";
import { waitRuns } from "./data.js";
import { CornerFoot, CornerTop, muchOf } from "./corners.js";
import { CardWindow, lastMade, windowOf } from "./cardwindow.js";                       // the window where *now* was: what the work made, else the goal's picture (spec 148 B.2)
import { Fan } from "./fan.js";
import { FOOT } from "./giveway.js";
import { litTool, hatched } from "../hand/state.js";
import { cardCost } from "../hand/cost.js";
import { defaultTool, movesOn, waitTool } from "./lit.js";
import { askedWords } from "./passing.js";

// the words under a pile's title, as realm/lexicon.py says them (column_*; tests/test_column_browser.py keeps them so)
export const READING = "reading", NEXT_IN = "next in", NEXT_AT = "next at";

export const ANALYSIS = ["raw", "reading", "asks", "routed", "talk", "decided", "sketch", "sections"];     // the idea, Talk, the decision and the spec being written (decisions §224); `ready`, `planning` and `plan` are the spec made: To review
const SPEC_MADE = ["ready", "planning", "plan"];                                                       // the Orkmaster's draft is `planning` (face down: it is being written); once `agreed` (a decision confirmed, the leaders wrote the spec) they are To review
const WORKING = ["working", "failed"];
const PAST_WAITING = ["running", "testing", "picking", "review", "failed"];                            // a task past waiting: its goal is at work
export const ACTIVE = ["reading", "planning", "talk", "sketch", "sections"];                                                  // the Orkmaster or its leaders are on it: its ring runs
const LIVE_TASK = ["running", "testing", "picking", "failed"];
export const DECK_SHOWN = 5, WORK_SHOWN = 6, DECK_STEP = 3;                                       // the cards drawn of the deck (the front and four behind, 3 px apart) and of At work (the front and five behind); the rest wait their turn, never counted

export const PILES = [["analysis", "In analysis"], ["review", "To review"], ["work", "At work · later"]];

/** Where a goal lies in the column: `{pile: "analysis" | "review" | "work", off: "" | "held" | "night"}`, null for a goal the column does not hold (done, a pitch, one folded away). `off`: put off, in At work · later after the ones at work. */
export function kindOf(n) {
  const s = n.state, ripe = n.back?.ripe || null;
  if (s === "done" || n.folded) return null;
  if (s === "decided") return ripe?.held ? { pile: "work", off: "held" } : { pile: "analysis", off: "" };   // the decision worded waits for the person's word, face down; held: put off until the person starts it
  if (n.start_at === "night" || n.waits?.kind === "night") return { pile: "work", off: "night" };      // put off to the night's window
  if (WORKING.includes(s) || (n.tasks || []).some((t) => PAST_WAITING.includes(t.state))) return { pile: "work", off: "" };
  if (SPEC_MADE.includes(s)) return s === "planning" && !n.agreed ? { pile: "analysis", off: "" } : { pile: "review", off: "" };   // the Orkmaster's own draft is still being written; a spec made waits in To review for its work (decisions §224)
  if (ANALYSIS.includes(s)) return { pile: "analysis", off: "" };
  return null;
}

/** The three piles in their order: `{analysis, review, work}`, each a list of `{n, off}`. In analysis the goal being worked on is first (the Orkmaster reads, routes or talks it over), the others in the Orkmaster's order; To review by the time left of its wait (the one that
 *  starts first in front); At work the ones at work, then held, then the night's. */
export function pilesOf(nodes) {
  const out = { analysis: [], review: [], work: [] };
  (nodes || []).forEach((n) => { const k = kindOf(n); if (k) out[k.pile].push({ n, off: k.off }); });
  out.analysis = out.analysis.map((x, i) => ({ ...x, i })).sort((a, b) => Number(ACTIVE.includes(b.n.state)) - Number(ACTIVE.includes(a.n.state)) || a.i - b.i);
  const left = (x) => (lookAt(x.n) ? Number(x.n.look_until) - Date.now() / 1000 : Number.isFinite(Number(x.n.back?.ripe?.left_s)) && !x.n.back?.ripe?.by ? Number(x.n.back.ripe.left_s) : Infinity);
  out.review = out.review.map((x, i) => ({ ...x, i })).sort((a, b) => left(a) - left(b) || a.i - b.i);
  const rank = { "": 0, held: 1, night: 2 };
  out.work = out.work.map((x, i) => ({ ...x, i })).sort((a, b) => rank[a.off] - rank[b.off] || a.i - b.i);
  return out;
}

/** The card's dim and its hatch (spec 138 A.2, A.4): while a potion is hovered (`litTool`) a card whose goal does not wait for that tool is dimmed (`.is-dim`, never hidden); a card hovered or focused hatches its next step's share off its tool's potion (`hatched`). */
const lit = (n) => ({ dim: !!litTool.value && waitTool(n, defaultTool()) !== litTool.value,
  hatch: { onPointerEnter: () => { hatched.value = cardCost(n); }, onPointerLeave: () => { hatched.value = null; }, onFocus: () => { hatched.value = cardCost(n); }, onBlur: () => { hatched.value = null; } } });

const waitsYou = (n) => !waitRuns(n) && (!!n.asks_you || n.state === "asks");                                              // a question or the decision to confirm waits for the person (`goal_place`: `asks_you`)

/** The goal the pile's title says the Orkmaster is on: *reading: <short>*, *talked over: <short>* in Talk, *waits for you* while it asks; "" when none is. */
export function underOf(analysis) {
  const f = analysis[0]?.n;
  if (!f) return "";
  if (waitsYou(f)) return "waits for you";
  if (waitRuns(f)) return `decided: ${f.short || f.title} · starts its spec at ${clock(f.back.ripe.left_s)}`;
  if (f.state === "talk") return `talked over: ${f.short || f.title}`;
  return ACTIVE.includes(f.state) ? `${READING}: ${f.short || f.title}` : "";
}

/** The clock time a spec made starts by itself at (spec 144 B.2; the look's wait, `look_until` in the future): *13:40*, with the weekday when it is not today's; "" for a card with no look running. Never a countdown. */
export function lookAt(n) {
  if (!(Number(n?.look_until) > Date.now() / 1000)) return "";
  const d = new Date(Number(n.look_until) * 1000), hm = `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
  return d.toDateString() === new Date().toDateString() ? hm : `${d.toLocaleDateString("en-GB", { weekday: "short" })} ${hm}`;
}

/** The next to start by itself in To review, in words: *next in 4 min: Round timer* (a decision's wait) or *next at 13:40: Round timer* (a spec's look); "" when none runs. A goal held, changing or waiting for the person is never the next (spec 147 B.3). */
export function nextWords(review) {
  for (const { n } of review) {
    const r = n.back?.ripe, goal = n.title || n.short || "";
    if (n.changing || waitsYou(n) || n.asks_you) continue;
    if (lookAt(n)) return `${NEXT_AT} ${lookAt(n)}: ${goal}`;
    if (r && !r.by && !r.held && Number.isFinite(Number(r.left_s))) return `${NEXT_IN} ${leftWords(r.left_s)}: ${goal}`;
  }
  return "";
}

const night = () => String(board.value?.night || "01:00-07:00").split("-")[0];
const clock = (left_s) => { const d = new Date(Date.now() + Math.max(0, Number(left_s) || 0) * 1000); return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; };

/** What a card says of its state, for a screen reader and its title: *its spec is ready; it starts by itself in 4 min*. */
export function sayOf(n, pile, off, first) {
  if (pile === "analysis") {
    if (n.held_for === "hold") return "held: nothing starts it until you press Talk";
    if (waitRuns(n)) return `its decision is agreed; its spec starts by itself at ${clock(n.back.ripe.left_s)}`;
    if (n.state === "decided") return "its decision waits for your word";
    if (waitsYou(n)) return "waits for your answer";
    if (n.state === "talk") return "its leaders are talking it over";
    if (n.state === "sketch" || n.state === "sections") return "its leaders are writing its spec";
    return n.state === "reading" || n.state === "planning" ? "the Orkmaster is writing its spec" : "waits for the Orkmaster";
  }
  if (pile === "review") {
    if (n.changing) return "Held while its leaders rewrite";                      // a change to its spec is open (spec 144 D.1): nothing starts it until the person answers
    if (lookAt(n)) return `Starts by itself at ${lookAt(n)}`;
    const r = n.back?.ripe;
    return r && !r.by && !r.held ? `its spec is ready; it ${first ? `starts by itself in ${leftWords(r.left_s)}` : `starts by itself about ${clock(r.left_s)}`}` : "its spec is ready; it waits for your word to start";
  }
  return off === "held" ? "put off: held until you start it" : off === "night" ? `put off to tonight, ${night()}` : (n.tasks || []).some((t) => t.state === "failed") || n.state === "failed" ? "at work: a task failed" : "at work";
}


const failed = (n) => n.state === "failed" || (n.tasks || []).some((t) => t.state === "failed");

/** A goal at work's tasks done of all (spec 129 H2.3): `{done, total}` over its tasks that were not dropped (done: merged), null when it has none yet. */
export function tasksCount(n) {
  const all = (n.tasks || []).filter((t) => t.state !== "dropped");
  return all.length ? { done: all.filter((t) => t.state === "merged").length, total: all.length } : null;
}

/** The tasks of a goal that are at work now, and the leaders' heads of them, one head each. */
const liveTasks = (n) => (n.tasks || []).filter((t) => LIVE_TASK.includes(t.state));
function headsOf(n) {
  const seen = new Set();
  return liveTasks(n).map((t) => t.head).filter((h) => h && !seen.has(`${h.race}-${h.tier}`) && seen.add(`${h.race}-${h.tier}`));
}

/** What the middle of a standing card says it does now, with the small sign before it: held, put off to the night, a task failed, waiting for the person, a question passed on, the task at work, else *At work*. */
function nowOf(n, off) {
  const asked = askedWords(n.slug), live = liveTasks(n)[0];
  if (off === "held") return { sign: "pause", text: "Held" };
  if (off === "night") return { sign: "moon", text: `Tonight ${night()}` };
  if (failed(n)) return { sign: "alert", text: "A task failed" };
  if (n.asks_you) return { sign: "question", text: "Waits for you" };
  if (asked) return { sign: "question", text: asked, asked: true };
  return { sign: "", text: live ? `Now: ${live.short || live.title}` : "At work" };
}

/** The line under a pile's title: the words up to the first *: * and then the goal, in the ink (*next in 2 min: **Round timer***). */
function Under({ id, text, asks = false, extra = false }) {
  const at = text.indexOf(": ");
  return html`<span class=${cls("col-under", { "is-asks": asks, "col-under--asked": extra })} data-under=${extra ? undefined : id} data-under-asked=${extra ? id : undefined} title=${text}>${at < 0 ? text : html`${text.slice(0, at + 2)}<b>${text.slice(at + 2)}</b>`}</span>`;
}

/** A back of To review (157 x 112, on its side, a squared deck): orkUI's back with the goal's seal in the part that shows, its rune at the seal's top; **no corners**, the seal is the rune. The ring is the wait: orkUI's `.is-waiting` filled in eighths by the share of its wait gone (`shareOf`) in the goal's
 *  colour; a goal that waits for the person has the ring full, still and in the alert, and its frame in the alert. */
function DeckCard({ n, i, first, onPress }) {
  const el = n.element || "", hue = n.hue || el, on = picked.value === n.slug, asks = waitsYou(n) || (!!n.asks_you && !failed(n)), ripe = n.back?.ripe, running = !!ripe && !ripe.by && !ripe.held && !n.changing && !lookAt(n), own = lit(n);
  everBack.add(n.slug);
  const share = asks ? 1 : running ? shareOf(ripe) : 0;
  return html`<button type="button" class=${cls("ork-card col-card col-card--down col-card--deck", { "ork-picked": on, asks, "is-dim": own.dim })} ...${own.hatch} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="review" data-down="1" data-changing=${n.changing ? "1" : undefined} data-look=${lookAt(n) || undefined} style=${`--i:${i}`}
    aria-pressed=${String(on)} aria-label=${`${n.title}: ${sayOf(n, "review", "", first)}`} title=${n.title} onClick=${() => onPress(n, "review", "")}>
    <span class="ork-card-back col-deck__back" aria-hidden="true"></span>
    <span class=${cls(`ork-sigil table-back-sigil col-sigil is-waiting${el && !asks ? ` is-${hue}` : ""}`, { "col-stopped": asks })} style=${`--ork-sigil-share:${share}`} data-share=${share} aria-hidden="true"><span class="ork-sigil__seal"><${Elem} name=${el} hue=${hue} dim=${!el} /></span></span>
  </button>`;
}

/** A card of At work · later, standing (144 x 202), read by its four corners (spec 147 A): its goal's rune and kind at the top, its name in up to four lines, what it does now (two lines), the wait's bar where it waits, and at the foot the leaders at work and how much (the time left, *asks you* while it waits for the
 *  person). The foot row is 26 px with the card's padding, so a card behind the front shows exactly it. `y` and `x`: where giveWay puts it (px below and right of the front card). */
function WorkCard({ n, i, off, y, x, onPress }) {
  const el = n.element || "", hue = n.hue || el, on = picked.value === n.slug, work = !off, glow = work && movesOn(n.slug), own = lit(n), ripe = n.back?.ripe, bad = failed(n), asks = !!n.asks_you && !bad;
  const tasks = work ? tasksCount(n) : null, now = nowOf(n, off), lefts = liveTasks(n).map((t) => Number(t.left)).filter((s) => Number.isFinite(s));
  const much = muchOf({ left: lefts.length ? Math.max(...lefts) : NaN, cost: cardCost(n)?.gem || "" }), name = n.title || n.short || "";
  const kind = bad ? "alert" : asks || now.asked ? "question" : n.type?.sign || "", signal = bad ? "danger" : asks ? "alert" : "";
  const made = lastMade(n.tasks), windowed = windowOf({ made, picture: n.picture }).kind !== "none";                // the window where *now* was (spec 148 B.2): what the work made, else the goal's picture, else what it does now
  const bar = off && ripe && Number(ripe.seconds) > 0 ? shareOf(ripe) : null;                                // a card put off waits: its bar in eighths where its wait is known, quiet where it is not
  return html`<button type="button" class=${cls("ork-card col-card col-card--up", { "ork-picked": on, asks, fails: bad, "is-off": !!off, "is-dim": own.dim })} ...${own.hatch} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="work" data-off=${off || undefined} style=${`--i:${i};--y:${y}px;--x:${x}px`}
    aria-pressed=${String(on)} aria-label=${`${name}: ${sayOf(n, "work", off)}${tasks ? `, ${tasks.done} of ${tasks.total} tasks finished` : ""}`} onClick=${() => onPress(n, "work", off)}>
    <${CornerTop} rune=${{ name: el, hue, dim: !el, glowing: glow, still: false }} kind=${kind} signal=${signal} />
    <span class="col-nm" title=${name}>${name}</span>
    ${windowed && html`<${CardWindow} of=${{ made, picture: n.picture, name }} />`}
    <span class=${cls("col-foot", `col-c-${hue || "dust"}`)}>
      ${!windowed && html`<span class="col-now" data-asked=${now.asked ? n.slug : undefined}>${now.sign && html`<${Sign} name=${now.sign} />`}<span class="col-now__t">${now.text}</span>${tasks && html`<span class="col-count" data-count=${`${tasks.done}/${tasks.total}`} title=${`${tasks.done} of ${tasks.total} tasks finished`}>${tasks.done}/${tasks.total}</span>`}</span>`}
      ${off && html`<span class=${cls("col-wbar", { "is-quiet": bar == null })} style=${bar != null ? `--s:${bar}` : undefined} aria-hidden="true"><i></i></span>`}
      <${CornerFoot} who=${{ heads: headsOf(n) }} much=${much} ask=${asks} />
    </span>
  </button>`;
}

/** One pile: its title and, under it, what it says (*reading: Round timer*, *next in 2 min: Round timer*), then its cards — the fan of In analysis (every goal a back), the deck of To review (the front and four behind, 3 px apart), the standing cards of At work (the front and five behind; `way`: giveway.js, how far each
 *  lies below the front one, or sunk). **A pile's heading appears with its first card**, never empty (spec 130 C.6). */
export function Pile({ id, title, items, under = "", asked = "", onPress, way = null }) {
  if (!items.length) return null;
  const head = html`<div class="col-plab"><span class="col-plab__t ork-plaque">${title}</span></div>
    <${Under} id=${id} text=${under} asks=${under === "waits for you"} />${asked && html`<${Under} id=${id} text=${asked} extra=${true} />`}`;
  if (id === "analysis") {
    const reads = ACTIVE.includes(items[0].n.state), said = (n) => `${n.title}: ${sayOf(n, "analysis")}`;
    return html`<section class="col-sec" data-pile=${id} aria-label=${title}>${head}<${Fan} items=${items} reads=${reads} said=${said} own=${lit} waits=${waitsYou} picked=${picked.value} onPress=${onPress} /></section>`;
  }
  if (id === "review") {
    const shown = items.slice(0, DECK_SHOWN);
    return html`<section class="col-sec" data-pile=${id} aria-label=${title}>${head}
      <div class="col-pile is-down" style=${`--h:${112 + (shown.length - 1) * DECK_STEP}px;--step:${DECK_STEP}px`} data-count=${items.length}>${shown.map(({ n }, i) => html`<${DeckCard} key=${n.slug} n=${n} i=${i} first=${i === 0} onPress=${onPress} />`)}</div>
    </section>`;
  }
  const shown = items.slice(0, WORK_SHOWN), sunk = (way?.sunk || 0) > 0, steps = shown.slice(1).map((_, k) => way?.steps?.[k] ?? FOOT);
  const ys = [0];
  steps.forEach((s) => ys.push(ys[ys.length - 1] + (sunk ? 0 : s)));
  return html`<section class="col-sec col-sec--work" data-pile=${id} aria-label=${title}>${head}
    <div class="col-room"><div class=${cls("col-pile is-up", { "is-sunk": sunk })} style=${`--behind:${ys[ys.length - 1]}px;margin-top:${way?.push || 0}px`} data-count=${items.length}>
      ${shown.map(({ n, off }, i) => html`<${WorkCard} key=${n.slug} n=${n} i=${i} off=${off} y=${ys[i]} x=${sunk ? i * DECK_STEP : 0} onPress=${onPress} />`)}
    </div></div>
  </section>`;
}
