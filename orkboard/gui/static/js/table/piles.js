// The Orkmaster's three piles (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part B.3–B.6, decisions §206.3; mockup docs/mockups/goal-card/): the goals of the project from the snapshot's nodes, by where each lies in its life —
// **In analysis** (the idea, Talk, the decision and the spec being written: decisions §224), its cards face down and sideways with no name; **To review** (the spec is made and waits for its work, which starts by itself): face up, still, its wait a bar in eighths and a time;
// **At work · later** (at work, its rune glowing and its leaders' heads at its foot; then put off: held, or to the night). A pile shows its front card whole (112 x 157) and the 20 px foot of each card under it (at most three), then thin edges, never a count; a card hovered or
// focused slides out of its pile whole (column.css). A face-down card cannot be picked (a press lifts the pile's list); a face-up card pressed picks its goal, a card of To review or a put-off one also lifts its choices (column.js).
// This file classifies (`kindOf`, `pilesOf`: pure, over a node) and draws the piles and their cards; what a press does is passed in (`onPress`), so the piles hold no state of their own.
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { picked } from "../frame/state.js";
import { board } from "../board/store.js";
import { everBack } from "./backcard.js";
import { leftWords, shareOf } from "./backbody.js";
import { waitRuns } from "./data.js";
import { MidHeads, Play, middleOf } from "./downmid.js";

export const ANALYSIS = ["raw", "reading", "asks", "routed", "talk", "decided", "sketch", "sections"];     // the idea, Talk, the decision and the spec being written (decisions §224); `ready`, `planning` and `plan` are the spec made: To review
const SPEC_MADE = ["ready", "planning", "plan"];                                                       // the Orkmaster's draft is `planning` (face down: it is being written); once `agreed` (a decision confirmed, the leaders wrote the spec) they are To review
const WORKING = ["working", "failed"];
const PAST_WAITING = ["running", "testing", "picking", "review", "failed"];                            // a task past waiting: its goal is at work
export const ACTIVE = ["reading", "planning", "talk", "sketch", "sections"];                                                  // the Orkmaster or its leaders are on it: its ring runs
const LIVE_TASK = ["running", "testing", "picking", "failed"];
const PEEK = 20, EDGES = 6, SHOWN = 4;                                                                // a card's foot under the one above it, the thin edges' height, the cards drawn of a pile (the front and three under it)

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
  const left = (x) => (Number.isFinite(Number(x.n.back?.ripe?.left_s)) && !x.n.back?.ripe?.by ? Number(x.n.back.ripe.left_s) : Infinity);
  out.review = out.review.map((x, i) => ({ ...x, i })).sort((a, b) => left(a) - left(b) || a.i - b.i);
  const rank = { "": 0, held: 1, night: 2 };
  out.work = out.work.map((x, i) => ({ ...x, i })).sort((a, b) => rank[a.off] - rank[b.off] || a.i - b.i);
  return out;
}

const waitsYou = (n) => !waitRuns(n) && (!!n.asks_you || n.state === "asks");                                              // a question or the decision to confirm waits for the person (`goal_place`: `asks_you`)

/** The goal the pile's title says the Orkmaster is on: *writing: <short>*, *talked over: <short>* in Talk, *waits for you* while it asks; "" when none is. */
export function underOf(analysis) {
  const f = analysis[0]?.n;
  if (!f) return "";
  if (waitsYou(f)) return "waits for you";
  if (waitRuns(f)) return `decided: ${f.short || f.title} · starts its spec at ${clock(f.back.ripe.left_s)}`;
  if (f.state === "talk") return `talked over: ${f.short || f.title}`;
  return ACTIVE.includes(f.state) ? `writing: ${f.short || f.title}` : "";
}

/** The wait of To review's first card in words, *next in 4 min*; "" when none runs. */
export function nextWords(review) {
  const r = review[0]?.n.back?.ripe;
  return r && !r.by && !r.held && Number.isFinite(Number(r.left_s)) ? `next in ${leftWords(r.left_s)}` : "";
}

const night = () => String(board.value?.night || "01:00-07:00").split("-")[0];
const clock = (left_s) => { const d = new Date(Date.now() + Math.max(0, Number(left_s) || 0) * 1000); return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`; };

/** What a card says of its state, for a screen reader and its title: *its spec is ready; it starts by itself in 4 min*. */
export function sayOf(n, pile, off, first) {
  if (pile === "analysis") {
    if (waitRuns(n)) return `its decision is agreed; its spec starts by itself at ${clock(n.back.ripe.left_s)}`;
    if (n.state === "decided") return "its decision waits for your word";
    if (waitsYou(n)) return "waits for your answer";
    if (n.state === "talk") return "its leaders are talking it over";
    if (n.state === "sketch" || n.state === "sections") return "its leaders are writing its spec";
    return n.state === "reading" || n.state === "planning" ? "the Orkmaster is writing its spec" : "waits for the Orkmaster";
  }
  if (pile === "review") {
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

/** The sign of a card's state on its foot: yellow `question` while it waits for the person (the faint one will be for a question passed on to another leader, part D), `alert` in danger while a task failed. */
function Mark({ n }) {
  if (failed(n)) return html`<span class="col-mark is-failed" title="A task failed"><${Sign} name="alert" /></span>`;
  if (n.asks_you) return html`<span class="col-mark is-asks" title="Waits for you"><${Sign} name="question" /></span>`;
  return null;
}

/** The leaders' heads at a card's foot: the parties whose tasks of this goal are at work, one head each. */
function Heads({ n }) {
  const seen = new Set(), heads = [];
  for (const t of n.tasks || []) {
    const h = t.head;
    if (!h || !LIVE_TASK.includes(t.state)) continue;
    const key = `${h.race}-${h.tier}`;
    if (!seen.has(key)) { seen.add(key); heads.push(h); }
  }
  return html`<span class="col-heads">${heads.map((h) => html`<${Head} key=${`${h.race}-${h.tier}`} race=${h.race} tier=${h.tier} />`)}</span>`;
}

/** A card face down, sideways (157 x 112): the seal with its rune at the seal's top, upright; **no name** (it is on the card's other side, and in its label). The front one's ring runs while the Orkmaster or its leaders are on it; yellow and still while it waits for the person. */
function DownCard({ n, i, front, onPress, open }) {
  const asks = front && waitsYou(n), wait = front && waitRuns(n), mid = front ? middleOf(n) : null, filling = mid?.fill != null, busy = front && !asks && !wait && !filling && ACTIVE.includes(n.state), el = n.element || "", hue = n.hue || el;
  const share = wait ? mid.wait : filling ? mid.fill : null;                                              // the ring as a share (orkUI's `.is-waiting`, in eighths): what is left of the wait, or what is written of the spec
  everBack.add(n.slug);                                                                                  // seen face down: its turn up and its flight to a lane are played once (backcard.js)
  const card = html`<button type="button" class=${cls("ork-card col-card col-card--down", { asks })} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile="analysis" data-down="1" style=${`--i:${i}`}
    tabindex=${front ? undefined : -1} aria-hidden=${front ? undefined : "true"} aria-haspopup=${front ? "dialog" : undefined} aria-expanded=${front ? String(open) : undefined}
    aria-label=${front ? `${n.title}: ${sayOf(n, "analysis")}; press for the list in order` : undefined} onClick=${() => onPress(n, "analysis")}>
    <span class=${cls(`ork-sigil table-back-sigil col-sigil${el ? ` is-${hue}` : ""}`, { "col-busy": busy, "col-stopped": asks, "is-waiting": share != null })} style=${share != null ? `--ork-sigil-share:${share}` : undefined} data-share=${share != null ? share : undefined} aria-hidden="true"><span class="ork-sigil__seal"><${Elem} name=${el} hue=${hue} dim=${!el} glowing=${busy} /></span>${mid && !wait && html`<${MidHeads} heads=${mid.heads} />`}</span>
  </button>`;
  return wait ? html`${card}<${Play} n=${n} />` : card;
}

/** A card face up (112 px wide, its height its content's: decisions §249.1, spec 142 A): **no window**; its rune and its whole name at its top (three lines at most, `line-clamp: 3`; the short name only where the title is missing), and its foot (20 px: the rune, the tasks done, then its time or its leaders' heads, the sign of its state; **no name in it**, spec 140 A2: the whole name is in the foot's `title` and `aria-label`). `first`: the front of To review shows the wait as a bar in eighths and its time left. */
function UpCard({ n, i, pile, off, first, onPress }) {
  const el = n.element || "", hue = n.hue || el, on = picked.value === n.slug, work = pile === "work" && !off, ripe = n.back?.ripe, running = pile === "review" && ripe && !ripe.by && !ripe.held;
  if (pile === "review") everBack.add(n.slug);
  const moon = off === "night", name = n.title || n.short || "", tasks = work ? tasksCount(n) : null;                    // a goal at work says its tasks done of all at its foot (spec 129 H2.3)
  const extra = pile === "review" ? (running ? (first ? html`<span class="col-when">${leftWords(ripe.left_s)}</span>` : html`<span class="col-when">~${clock(ripe.left_s)}</span>`) : null)
    : off === "held" ? html`<span class="col-when"><${Sign} name="pause" />Held</span>` : moon ? html`<span class="col-when"><${Sign} name="moon" />${night()}</span>` : html`<${Heads} n=${n} />`;
  return html`<button type="button" class=${cls("ork-card col-card col-card--up", { "ork-picked": on, asks: !!n.asks_you && !failed(n), fails: failed(n), "is-off": !!off })} data-goal=${n.slug} data-about=${`idea:${n.slug}`} data-state=${n.state} data-pile=${pile} data-off=${off || undefined} style=${`--i:${i}`}
    aria-pressed=${String(on)} aria-label=${`${n.title}: ${sayOf(n, pile, off, first)}${tasks ? `, ${tasks.done} of ${tasks.total} tasks finished` : ""}`} onClick=${() => onPress(n, pile, off)}>
    <span class="col-hd"><${Elem} name=${el} hue=${hue} dim=${!el} glowing=${work} /><span class="col-nm">${name}</span></span>
    <span class=${cls("col-foot", `col-c-${hue || "dust"}`)} title=${name} aria-label=${name}><${Elem} name=${el} hue=${hue} dim=${!el} glowing=${work} />${tasks && html`<span class="col-count" data-count=${`${tasks.done}/${tasks.total}`} title=${`${tasks.done} of ${tasks.total} tasks finished`}>${tasks.done}/${tasks.total}</span>`}${extra}<${Mark} n=${n} />
      ${first && running && html`<span class="col-wbar" style=${`--s:${shareOf(ripe)}`} aria-hidden="true"><i></i></span>`}</span>
  </button>`;
}

/** One pile: its title and, under it, what it says (*writing: Round timer*), its cards stacked by `--i` (the foot of each under the one above it), the thin edges when more lie under them. Empty: *Nothing here*. */
export function Pile({ id, title, items, under = "", onPress, open = false }) {
  const shown = items.slice(0, SHOWN), down = id === "analysis", peek = down ? 4 : PEEK, tall = down ? 112 : 157, edges = items.length > SHOWN;
  const beneath = (shown.length - 1) * peek + (edges ? EDGES : 0), height = tall + beneath;      // face up the height is the cards' own: only what lies under the front is known (`--under`)
  return html`<section class="col-sec" data-pile=${id} aria-label=${title}>
    <div class="col-plab"><span class="col-plab__t">${title}</span><span class=${cls("col-under", { "is-asks": under === "waits for you" })} data-under=${id}>${under}</span></div>
    ${shown.length ? html`<div class=${cls("col-pile", { "is-down": down, "is-up": !down })} style=${down ? `--h:${height}px;--peek:${peek}px` : `--under:${beneath}px;--peek:${peek}px`} data-count=${items.length}>
      ${shown.map(({ n, off }, i) => (down ? html`<${DownCard} key=${n.slug} n=${n} i=${i} front=${i === 0} onPress=${onPress} open=${open} />` : html`<${UpCard} key=${n.slug} n=${n} i=${i} pile=${id} off=${off} first=${i === 0} onPress=${onPress} />`))}
      ${edges && html`<span class="col-edges" style=${down ? `top:${height - (edges ? EDGES : 0)}px` : undefined} aria-hidden="true"></span>`}
    </div>` : html`<p class="col-none">Nothing here</p>`}
  </section>`;
}
