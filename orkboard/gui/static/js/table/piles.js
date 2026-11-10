// The Orkmaster's three piles (docs/specs/168-the-window-played-as-a-card-games-table.md B, decisions §283.11–§283.13; before: spec 147 B, decisions §251.3–§251.4): the goals of the project from the snapshot's nodes, by the stage each lies in (stages.js) —
// **Ideas** (read and routed by the Orkmaster, in Talk, an agreed decision's wait): the Orkmaster's hand, a fan of small backs turned like a hand's (fan.js), the goal being read lifted, a goal held or put off to a later hour at its end with a pause or a moon; **Specs** (its sections being written, the plan,
// the look's wait): a squared deck of small backs on their side, 78 x 56 (speccard.js), the front one's ring filling as the spec is written, a made spec's ring the wait gone, a goal that waits for the person with a still ring and a frame in the alert, the next to start named under the title with its time;
// **Implementation** (at work, its rune glowing and its leaders' heads at its foot; then put off: held after its spec, or to the night): standing cards, 144 x 202, read by their four corners (corners.js), the cards behind the front showing their foot, a thin edge or a sliver as the window leaves room
// (giveway.js, column.js); a goal held at work lies among them with a pause. Nothing counts what waits. A card hovered or focused slides out of its pile whole (column.css). The phone's menu keeps the earlier three piles (oldpiles.js): `legacy`.
// A back of Ideas cannot be picked (a press lifts the pile's list); a back of Specs or a standing card pressed picks its goal, one of Specs or a put-off one also lifts its choices (column.js).
// A potion hovered dims the cards whose goal does not wait for its tool, a card hovered hatches its next step off its tool's potion (spec 138 A.2, A.4, decisions §245.2; lit.js); a rune's glow and the ring's sweep run only on the goal that moves: the one picked, else the first at work (spec 140 C3, §247.8).
// This file draws the piles and their cards and says their words (`underOf`, `writingWords`, `nextWords`, `atWorkWords`, `sayOf`); the classification is stages.js (`kindOf`, `pilesOf`: pure, over a node); what a press does is passed in (`onPress`), so the piles hold no state of their own.
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { picked } from "../frame/state.js";
import { everBack } from "./backcard.js";
import { leftWords, shareOf } from "./backbody.js";
import { waitRuns } from "./data.js";
import { CornerFoot, CornerTop, muchOf } from "./corners.js";
import { CardWindow, lastMade, windowOf } from "./cardwindow.js";                       // the window where *now* was: what the work made, else the goal's picture (spec 148 B.2)
import { Fan } from "./fan.js";
import { SpecCard } from "./speccard.js";
import { backSpec, withPreview } from "./preview.js";
import { FOOT } from "./giveway.js";
import { litTool, hatched } from "../hand/state.js";
import { cardCost } from "../hand/cost.js";
import { defaultTool, movesOn, waitTool } from "./lit.js";
import { askedWords } from "./passing.js";
import { holdWords } from "./holdwords.js";
import { ACTIVE, AT_WORK, DECK_SHOWN, DECK_STEP, NEXT_AT, NEXT_IN, READING, WORK_SHOWN, WRITING, PILES, clock, failed, kindOf, lookAt, night, pilesOf, writing } from "./stages.js";
import { PILES_OLD, pilesOfOld } from "./oldpiles.js";

export { ACTIVE, AT_WORK, DECK_SHOWN, DECK_STEP, NEXT_AT, NEXT_IN, READING, WORK_SHOWN, WRITING, PILES, PILES_OLD, kindOf, lookAt, pilesOf, pilesOfOld, writing };
const LIVE_TASK = ["running", "testing", "picking", "failed"];


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

/** The line under Specs while a spec is being written: *writing: Round timer* (the goal in front, the Orkmaster's or its leaders'); "" when none is. */
export function writingWords(review) {
  const f = review[0]?.n;
  return f && writing(f) ? `${WRITING}: ${f.short || f.title}` : "";
}

/** The line under Implementation: *at work: Round timer*, the first goal at work (not one put off); "" when none is. */
export function atWorkWords(work) {
  const f = work.find((x) => !x.off)?.n;
  return f ? `${AT_WORK}: ${f.short || f.title}` : "";
}

/** What a card says of its state, for a screen reader and its title: *its spec is ready; it starts by itself in 4 min*. */
export function sayOf(n, pile, off, first) {
  if (pile === "analysis") {
    if (n.held_for === "hold") return "held: nothing starts it until you press Talk";
    if (kindOf(n)?.mark === "later") return `put off: ${holdWords(n)}`;
    if (waitRuns(n)) return `its decision is agreed; its spec starts by itself at ${clock(n.back.ripe.left_s)}`;
    if (n.state === "decided") return "its decision waits for your word";
    if (waitsYou(n)) return "waits for your answer";
    if (n.state === "talk") return "its leaders are talking it over";
    if (n.state === "sketch" || n.state === "sections") return "its leaders are writing its spec";
    return n.state === "reading" || n.state === "planning" ? "the Orkmaster is writing its spec" : "waits for the Orkmaster";
  }
  if (pile === "review") {
    if (n.proposed) return "proposed by a leader in the night: Take or Drop it in your hand";
    if (writing(n)) return n.state === "planning" ? "the Orkmaster is writing its spec" : "its leaders are writing its spec";
    if (n.changing) return "Held while its leaders rewrite";                      // a change to its spec is open (spec 144 D.1): nothing starts it until the person answers
    if (lookAt(n)) return `Starts by itself at ${lookAt(n)}`;
    const r = n.back?.ripe;
    return r && !r.by && !r.held ? `its spec is ready; it ${first ? `starts by itself in ${leftWords(r.left_s)}` : `starts by itself about ${clock(r.left_s)}`}` : "its spec is ready; it waits for your word to start";
  }
  if (!off && !failed(n) && kindOf(n)?.mark === "hold") return "at work: held";
  return off === "held" ? "put off: held until you start it" : off === "night" ? `put off to tonight, ${night()}` : (n.tasks || []).some((t) => t.state === "failed") || n.state === "failed" ? "at work: a task failed" : "at work";
}



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
function nowOf(n, off, mark = "") {
  const asked = askedWords(n.slug), live = liveTasks(n)[0];
  if (off === "held" || (!off && mark === "hold" && !failed(n))) return { sign: "pause", text: "Held" };
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
  return html`<button type="button" class=${cls("ork-card col-card col-card--down col-card--deck", { "ork-picked": on, asks, "is-dim": own.dim })} ...${withPreview(own.hatch, backSpec(n.title, sayOf(n, "review", "", first), n))} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="review" data-down="1" data-changing=${n.changing ? "1" : undefined} data-look=${lookAt(n) || undefined} style=${`--i:${i}`}
    aria-pressed=${String(on)} aria-label=${`${n.title}: ${sayOf(n, "review", "", first)}`} onClick=${() => onPress(n, "review", "")}>
    <span class="ork-card-back col-deck__back" aria-hidden="true"></span>
    <span class=${cls(`ork-sigil table-back-sigil col-sigil is-waiting${el && !asks ? ` is-${hue}` : ""}`, { "col-stopped": asks })} style=${`--ork-sigil-share:${share}`} data-share=${share} aria-hidden="true"><span class="ork-sigil__seal"><${Elem} name=${el} hue=${hue} dim=${!el} /></span></span>
  </button>`;
}

/** A card of At work · later, standing (144 x 202), read by its four corners (spec 147 A): its goal's rune and kind at the top, its name in up to four lines, what it does now (two lines), the wait's bar where it waits, and at the foot the leaders at work and how much (the time left, *asks you* while it waits for the
 *  person). The foot row is 26 px with the card's padding, so a card behind the front shows exactly it. `y` and `x`: where giveWay puts it (px below and right of the front card). */
function WorkCard({ n, i, off, mark, y, x, onPress }) {
  const el = n.element || "", hue = n.hue || el, on = picked.value === n.slug, work = !off, glow = work && movesOn(n.slug), own = lit(n), ripe = n.back?.ripe, bad = failed(n), asks = !!n.asks_you && !bad;
  const tasks = work ? tasksCount(n) : null, now = nowOf(n, off, mark), lefts = liveTasks(n).map((t) => Number(t.left)).filter((s) => Number.isFinite(s));
  const much = muchOf({ left: lefts.length ? Math.max(...lefts) : NaN, cost: cardCost(n)?.gem || "" }), name = n.title || n.short || "";
  const kind = bad ? "alert" : asks || now.asked ? "question" : n.type?.sign || "", signal = bad ? "danger" : asks ? "alert" : "";
  const made = lastMade(n.tasks), windowed = windowOf({ made, picture: n.picture }).kind !== "none";                // the window where *now* was (spec 148 B.2): what the work made, else the goal's picture, else what it does now
  const bar = off && ripe && Number(ripe.seconds) > 0 ? shareOf(ripe) : null;                                // a card put off waits: its bar in eighths where its wait is known, quiet where it is not
  return html`<button type="button" class=${cls("ork-card col-card col-card--up", { [`el-${n.hue || n.element}`]: !!(n.hue || n.element), "ork-picked": on, asks, fails: bad, "is-off": !!off, "is-dim": own.dim })} ...${own.hatch} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="work" data-off=${off || undefined} style=${`--i:${i};--y:${y}px;--x:${x}px`}
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

const SPEC_STEP = 4;                                                                                           // the cards of the Specs deck lie 4 px apart

/** What a card of the Specs deck draws of its goal (speccard.js): its words, the ring's share and whether it asks. A spec being written has its ring filling by the share of its sections written (`back.written`: `{done, total}`, nothing before the host says), a spec made the share of its wait gone; a goal that
 *  waits for the person has the ring full, still and in the alert. */
function specFace(n, first) {
  const asks = waitsYou(n) || (!!n.asks_you && !failed(n)), ripe = n.back?.ripe, w = n.back?.written, wr = writing(n);
  const running = !wr && !!ripe && !ripe.by && !ripe.held && !n.changing && !lookAt(n), share = asks ? 1 : wr ? (Number(w?.total) > 0 ? Math.min(8, Math.round((Number(w.done) / Number(w.total)) * 8)) / 8 : 0) : running ? shareOf(ripe) : 0;
  everBack.add(n.slug);
  return { say: sayOf(n, "review", "", first), proposed: !!n.proposed, share, asks, writing: wr, look: lookAt(n), glow: wr && movesOn(n.slug), bad: failed(n) };
}

/** One pile: its title and, under it, what it says (*reading: Round timer*, *next in 2 min: Round timer*), then its cards — the fan of In analysis (every goal a back), the deck of To review (the front and four behind, 3 px apart), the standing cards of At work (the front and five behind; `way`: giveway.js, how far each
 *  lies below the front one, or sunk). **A pile's heading appears with its first card**, never empty (spec 130 C.6). */
export function Pile({ id, title, items, under = "", asked = "", onPress, way = null, legacy = false }) {
  if (!items.length) return null;
  const head = html`<div class="col-plab"><span class="col-plab__t ork-plaque">${title}</span></div>
    <${Under} id=${id} text=${under} asks=${under === "waits for you"} />${asked && html`<${Under} id=${id} text=${asked} extra=${true} />`}`;
  if (id === "analysis") {
    const reads = ACTIVE.includes(items[0].n.state), said = (n) => `${n.title}: ${sayOf(n, "analysis")}`;
    return html`<section class="col-sec" data-pile=${id} aria-label=${title}>${head}<${Fan} items=${items} reads=${reads} said=${said} line=${(n) => sayOf(n, "analysis")} legacy=${legacy} own=${lit} waits=${waitsYou} picked=${picked.value} onPress=${onPress} /></section>`;
  }
  if (id === "review" && !legacy) {                                                                              // Specs: a squared deck of small backs on their side, 78 x 56
    const shown = items.slice(0, DECK_SHOWN);
    return html`<section class="col-sec" data-pile=${id} aria-label=${title}>${head}
      <div class="col-pile is-down is-specs" style=${`--h:${56 + (shown.length - 1) * SPEC_STEP}px;--step:${SPEC_STEP}px`} data-count=${items.length}>${shown.map(({ n }, i) => html`<${SpecCard} key=${n.slug} n=${n} i=${i} ...${specFace(n, i === 0)} own=${lit(n)} on=${picked.value === n.slug} onPress=${onPress} />`)}</div>
    </section>`;
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
      ${shown.map(({ n, off, mark }, i) => html`<${WorkCard} key=${n.slug} n=${n} i=${i} off=${off} mark=${mark} y=${ys[i]} x=${sunk ? i * DECK_STEP : 0} onPress=${onPress} />`)}
    </div></div>
  </section>`;
}
