// The Orkmaster's tables by the stage of the goal picked (docs/specs/168-the-window-played-as-a-card-games-table.md C3, decisions §283.16.1, .3, .5, .7; mockup docs/mockups/table-template/ shots 1 and 3): through the Orkmaster the table is a lane for each leader and
// what lies in it is the stage's:
//  - **The project** (nothing picked, `StageRows` over each lane of boardmap.js): the leader's goals in Talk as small cards (the verdict's sign face up once the leader has said it, a back while it assesses), then its goals' specs as small cards; the lane's
//    implementation is the cascade boardmap.js lays under them.
//  - **An idea** (a goal picked in Talk, `IdeaTable`): the route and its price on a plate with *Judge again now* (`ideas.judge_again`), under each leader of the route a small card with its verdict's sign (corners.js `Verdict`).
//  - **A spec** (a goal picked in its spec, `SpecTable`): a big card, 144 x 202, under each leader of the route, face up once its section is written, a back before.
//  The implementation (a goal picked at work) is planboard.js, which lays a later leader's step as a placeholder.
// A card pressed picks its goal and opens that leader's tab (`open`), where the leader's own table of that stage is (talkpage.js, specpage.js). Two card sizes only: 144 x 202 and the small 56 x 78 (smallcard.js). Layout is stageboard.css; this file reads the Board and draws.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { command } from "../link.js";
import { openTab, picked } from "../frame/state.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { costLine, partyName, routeWords } from "../hand/routecard.js";
import { nameOf, partiesAll, partiesNow, phaseOf } from "./data.js";
import { SmallCard } from "./smallcard.js";
import { CornerFoot, CornerTop, Verdict } from "./corners.js";
import { everBack } from "./backcard.js";
import { PILES } from "./stages.js";
import { backSpec, withPreview } from "./preview.js";
import { readSpec, usePage } from "./specpage.js";
import { Lanes } from "./stagelanes.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./stageboard.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const TALK = ["routed", "talk"], SPEC = ["decided", "sections"];

/** Which of the stages' tables a goal's state lies in: `idea` (Talk), `spec`, else "" (the plan, planboard.js). */
const STARTED = ["running", "testing", "picking", "review", "failed", "merged"];            // a task past waiting: the goal is at work, whatever its state says (its sections joined while its party works)
export const stageKind = (n) => (!n || (n.tasks || []).some((t) => STARTED.includes(t.state)) ? "" : phaseOf(n.slug) === "talk" ? "idea" : phaseOf(n.slug) === "spec" ? "spec" : "");

/** A card pressed: the goal is picked (never put down: a press is a look) and that leader's tab opens on it. */
export function open(slug, party) {
  picked.value = slug;
  openTab(party);
}

const rowOf = (slug) => (board.value?.needs_you || []).find((r) => r.kind === "route" && r.idea === slug) || null;

/** The leaders of a goal's route, by their parties' slugs, in the route's order: the steps the Board has (a step passed on from a party counts for that party), the route row that waits for the person, the leaders that have said something; the goal's own party
 *  when none of them says. Only the parties that stand in a lane now. */
export function leadersOf(n) {
  const out = [], add = (s) => { if (s && !out.includes(s)) out.push(s); };
  const asked = rowOf(n.slug)?.route || [];                                // the route as it waits for the person's Talk is the one being decided: it comes first
  (asked.length ? asked : n.route || []).forEach((s) => add(s.party));
  (n.say?.leaders || []).forEach((l) => add(l.party));
  if (!out.length) add(n.goal);
  const lanes = new Set(partiesNow().map((g) => g.slug));
  return out.filter((s) => lanes.has(s));
}

const partyOf = (slug) => partiesAll().find((g) => g.slug === slug) || null;
const sayOf = (n, party) => (n.say?.leaders || []).find((l) => l.party === party) || null;
const opens = (l) => (l?.needs || []).filter((x) => !x.state || x.state === "open").length;
const VERDICT = { go: "Go", doubt: "Doubt", no: "No" };

/** The words of a verdict on a card's caption: *Go*, *Doubt · 2 to answer*, *No*. */
export function verdictWords(l) {
  const open = opens(l);
  return `${VERDICT[l.verdict] || "Doubt"}${open ? ` · ${open} to answer` : ""}`;
}

/** The small back of a leader that has not said its verdict yet (56 x 78): orkUI's small back with the goal's rune on its seal; a press is the same as the face's. */
export function SmallBack({ n, g, onPress, extra = {} }) {
  const el = n.element || "", hue = n.hue || el;
  everBack.add(n.slug);
  const props = withPreview({ class: "ork-card sb-back", "data-goal": n.slug, "data-party": g.slug, "data-assessing": "1", "aria-label": `${n.title}: assessing`, ...extra }, backSpec(n.title, "Assessing…", n));
  return html`<button type="button" ...${props} onClick=${onPress}><span class="ork-card-back small" aria-hidden="true"><span class="ork-card-back__seal"><${Elem} name=${el} hue=${hue} dim=${!el} /></span></span></button>`;
}

/** One leader's card of a goal in Talk: its verdict's sign face up once it has said it (a question that waits for the person is the card's alert frame), else a back while it assesses. `dots`: the route's parties for the face's dots. */
export function SaidCard({ n, g, dots }) {
  const l = sayOf(n, g.slug), parties = dots.map(partyOf).filter(Boolean), done = (n.say?.leaders || []).map((x) => x.party);
  const press = () => open(n.slug, g.slug);
  if (!l) return html`<${SmallBack} n=${n} g=${g} onPress=${press} />`;
  const waits = opens(l) > 0;
  return html`<${SmallCard} n=${n} parties=${parties} done=${done} signal=${waits ? "alert" : ""} picture=${html`<${Verdict} verdict=${l.verdict} label=${verdictWords(l)} />`} onPress=${press}
    extra=${{ "data-party": g.slug, "data-verdict": l.verdict, "data-leader": l.leader || undefined }} />`;
}

/** The goals of the Board that lie at a stage (`TALK` or `SPEC` states) with this leader on their route, in the Board's order. */
const goalsAt = (states, g) => (mapData.value?.nodes || []).filter((n) => states.includes(n.state) && n.place === "table" && !n.folded && leadersOf(n).includes(g.slug));

/** Whether the leader has a goal in Talk or in its spec to lay as a row. */
export const hasRows = (g) => goalsAt(TALK, g).length + goalsAt(SPEC, g).length > 0;

/** The project's lane over the cascade: the leader's goals in Talk as small cards, then its goals' specs as small cards (each a face once it writes, as the Orkmaster's column's). Nothing when it has none. */
export function StageRows({ g }) {
  const talk = goalsAt(TALK, g), spec = goalsAt(SPEC, g);
  if (!talk.length && !spec.length) return null;
  return html`<div class="sb-rows" data-rows=${g.slug}>
    ${talk.length > 0 && html`<section class="sb-row" data-row="ideas" aria-label=${PILES[0][1]}><span class="ork-label sb-row__label">${PILES[0][1]}</span>
      <div class="sb-row__cards">${talk.map((n) => html`<${SaidCard} key=${n.slug} n=${n} g=${g} dots=${leadersOf(n)} />`)}</div></section>`}
    ${spec.length > 0 && html`<section class="sb-row" data-row="specs" aria-label=${PILES[1][1]}><span class="ork-label sb-row__label">${PILES[1][1]}</span>
      <div class="sb-row__cards">${spec.map((n) => html`<${SmallCard} key=${n.slug} n=${n} parties=${leadersOf(n).map(partyOf).filter(Boolean)} signal=${n.asks_you ? "alert" : ""} onPress=${() => open(n.slug, g.slug)}
        extra=${{ "data-party": g.slug, "data-spec": "1" }} />`)}</div></section>`}
  </div>`;
}

// -- an idea ---------------------------------------------------------------------------------------------------------------------

/** The route's price: the route row's while it waits for Talk, else the goal's estimate. */
const priceOf = (n) => rowOf(n.slug)?.cost || n.estimate || n.plan_estimate || null;

/** The plate: the route as the leaders' heads and in words, its price, and *Judge again now* (the leaders that doubted, said no, were turned down or were touched judge it again: `ideas.judge_again`; a refusal is the page's toast). */
function Plate({ n, leaders }) {
  const [busy, setBusy] = useState(false), steps = leaders.map((s) => ({ party: s, head: partyOf(s)?.leader?.head })), price = costLine(priceOf(n)), said = !!n.say;
  const judge = () => { setBusy(true); command("ideas.judge_again", { idea: n.slug }).catch(() => {}).finally(() => setBusy(false)); };
  return html`<section class="sb-plate ork-plate" data-view="route" data-goal=${n.slug} aria-label=${`${n.title}: its route and cost`}>
    <ol class="sb-plate__steps" aria-label="The route">${steps.map((x) => html`<li key=${x.party} class="phase-route__step" data-party=${x.party} title=${partyName(x.party)}>${x.head && html`<${Head} race=${x.head.race} tier=${x.head.tier} />`}</li>`)}</ol>
    <span class="body phase-route__words">Route: ${routeWords(steps)}</span>
    ${price && html`<span class="sb-plate__cost hand-way__cost" data-cost=${price.spend?.gem || ""}>${price.words}</span>`}
    <span class="table-grow"></span>
    <button type="button" class="ork-btn quiet sb-plate__judge" data-judge="1" disabled=${busy || !said} title=${said ? "The leaders that doubted, said no, were turned down or were touched judge it again" : "No leader has said its verdict yet"} onClick=${judge}>Judge again now</button>
  </section>`;
}

/** A goal in Talk, through the Orkmaster: the plate, and under each leader of the route its card. A leader off the route has none. */
export function IdeaTable({ n }) {
  const leaders = leadersOf(n);
  return html`<div class="sb sb--idea" data-stage="idea" data-goal=${n.slug}>
    <${Plate} n=${n} leaders=${leaders} />
    <${Lanes} n=${n} stage="idea" leaders=${leaders}>${(g) => {
      const l = sayOf(n, g.slug);
      return html`<div class="sb-said" data-leader=${g.slug}><${SaidCard} n=${n} g=${g} dots=${leaders} />
        <div class="sb-said__words"><b class="sb-said__verdict">${l ? verdictWords(l) : "Assessing…"}</b>${l?.why && html`<span class="sb-said__why">${l.why}</span>`}</div></div>`;
    }}<//>
  </div>`;
}

// -- a spec ------------------------------------------------------------------------------------------------------------------------

/** A leader's section as a big card (144 x 202): its part's name, what it promises (its *Done when* lines) in the window, its leader's head at the foot; face up once written. */
function SpecFace({ n, g, sec }) {
  const kind = n.type?.sign || "", lines = (sec.done || []).slice(0, 3);
  return html`<button type="button" class=${cls("ork-card ork-leans table-card sb-spec", { [`el-${n.hue || n.element}`]: !!(n.hue || n.element) })} data-spec-card=${g.slug} data-state="written" data-goal=${n.slug} aria-label=${`${nameOf(g)}: its section is written`} onClick=${() => open(n.slug, g.slug)}>
    <${CornerTop} rune=${{ name: n.element, hue: n.hue, dim: !n.element, still: true }} kind=${kind} />
    <span class="table-card__head"><span class="table-card__nm">${nameOf(g)}'s part</span></span>
    <span class="table-card__win is-window sb-spec__win">${lines.length ? html`<span class="body sb-spec__lines">${lines.join(" · ")}</span>` : html`<${Sign} name=${kind || "page"} big=${true} />`}</span>
    <${CornerFoot} who=${g.leader?.head ? { heads: [g.leader.head] } : null} />
  </button>`;
}

/** A leader's section not written yet: orkUI's back, the goal's rune on its seal, *writing* under it. */
function SpecBack({ n, g }) {
  const el = n.element || "", hue = n.hue || el;
  everBack.add(n.slug);
  const props = withPreview({ class: "sb-spec sb-spec--back", "data-spec-card": g.slug, "data-state": "writing", "data-goal": n.slug, "aria-label": `${nameOf(g)}: its section is being written` }, backSpec(n.title, "writing", n));
  return html`<button type="button" ...${props} onClick=${() => open(n.slug, g.slug)}><span class="ork-card-back" aria-hidden="true"><span class="ork-card-back__seal"><${Elem} name=${el} hue=${hue} dim=${!el} /></span></span><span class="sb-spec__say">writing</span></button>`;
}

/** A goal in its spec, through the Orkmaster: a big card under each leader of the route, face up once its section is written (the page's, `ideas.page`), a back before. */
export function SpecTable({ n }) {
  const page = usePage(n.slug), leaders = leadersOf(n), parties = partiesAll(), home = parties.find((g) => g.slug === n.goal) || null;
  const written = page ? readSpec(page, parties, home).sections : [];
  return html`<div class="sb sb--spec" data-stage="spec" data-goal=${n.slug}>
    <${Lanes} n=${n} stage="spec" leaders=${leaders}>${(g) => {
      const sec = written.find((x) => x.party?.slug === g.slug);
      return html`<div class="sb-slot">${sec ? html`<${SpecFace} n=${n} g=${g} sec=${sec} />` : html`<${SpecBack} n=${n} g=${g} />`}</div>`;
    }}<//>
  </div>`;
}
