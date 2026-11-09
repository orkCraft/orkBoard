// The table by the picked goal's phase (docs/specs/156-one-pick-and-the-release-column.md part C, decisions §261.4 — it changes §126.4): with a goal picked, the table itself shows its phase at the open tab.
// Through the Orkmaster: while the goal is not yet talked, its route and what it costs (the route card's words, hand/routecard.js, read only: its acts stay the card's in the hand); from Talk on, its plan in the lanes as today (§206.4).
// Through a leader on its route (spec 168 C4): **Talk**, that party's say as one row of three groups of cards (sayrow.js; its stance as kept, talkpage.js `PartyTalk`, until it has said any); **Spec**, the steps' header, the parts now and as they will be and its section (specsteps.js);
// **Work**, the lanes by its seats (seatlanes.js) over what it will change (goalview.js); **Done**, what it changed against what was promised
// (goalview.js) and, under it, the quality record (qualitypage.js). Under the table, once the goal is past Talk, one folded line *Earlier: Talk · Spec*: a phase pressed unfolds what it said at this tab in place, pressed again folds it.
// Nothing opens over the pane. The pages themselves (talkpage.js, specpage.js, qualitypage.js) are reused, never their data code. The word *Earlier* is the lexicon's `phase_earlier`.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head } from "../orkui.js";
import { board } from "../board/store.js";
import { CostLine, partyName, routeWords } from "../hand/routecard.js";
import { phaseOf, PHASES } from "./data.js";
import { viewable } from "./goalmap.js";
import { GoalView } from "./goalview.js";
import { PartyTalk, TalkPage } from "./talkpage.js";
import { PartySection, SpecPage } from "./specpage.js";
import { SayRow, sayOf } from "./sayrow.js";
import { SpecTable } from "./specsteps.js";
import { SeatLanes, lanesOf } from "./seatlanes.js";
import { QualityPage } from "./qualitypage.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./phaseview.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** The route row of a goal that waits for its Talk, null for none. */
const routeRowOf = (slug) => (board.value?.needs_you || []).find((r) => r.kind === "route" && r.idea === slug) || null;

/** What the table shows for the goal `n` at the tab of `g` (null: the Orkmaster's): `route` (the Orkmaster, not talked yet), `talk`, `spec`, `work`, `done` (a leader), "" for the table as before (the Orkmaster's lanes, a leader's map). */
export function phaseKind(g, n) {
  if (!n) return "";
  if (!g) return n.state === "routed" || routeRowOf(n.slug) ? "route" : "";
  const phase = phaseOf(n.slug);
  if (phase === "talk" || phase === "spec") return phase;
  return (phase === "work" || phase === "done") && viewable(n) ? phase : "";
}

/** The Orkmaster's body while the goal is not yet talked: the route, in words and as the leaders' heads, and its cost; read only. */
export function RouteView({ n }) {
  const row = routeRowOf(n.slug), steps = row?.route?.length ? row.route : (n.route || []).filter((s) => s.party);
  return html`<section class="phase-route" data-view="route" data-goal=${n.slug} aria-label=${`${n.title}: its route and cost`}>
    <header class="gv-title"><${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} big=${true} /><div><b>${n.title}</b><span>Its route and what it costs</span></div></header>
    ${steps.length ? html`<ol class="phase-route__steps" aria-label="The route">${steps.map((x) => html`<li key=${x.party} class="phase-route__step" data-party=${x.party}>
        ${x.head && html`<${Head} race=${x.head.race} tier=${x.head.tier} size="mid" />`}<span>${partyName(x.party)}</span></li>`)}</ol>
      <p class="body phase-route__words">${routeWords(steps)}</p>`
      : html`<p class="table-over__muted" data-state="none">It is not routed yet.</p>`}
    ${row?.cost && html`<${CostLine} cost=${row.cost} />`}
    ${row?.place > 0 && html`<p class="cap">${row.place === 1 ? "First" : `Number ${row.place}`} in line</p>`}
  </section>`;
}

/** A leader's body for the phase `kind`. */
export function PhaseView({ g, n, kind }) {
  if (kind === "talk") return sayOf(n, g.slug) ? html`<${SayRow} n=${n} g=${g} />` : html`<div class="phase-view" data-view="talk"><${PartyTalk} idea=${n.slug} party=${g.slug} /></div>`;      // its say as cards (spec 168 C4) once it has spoken in cards, else its stance as kept
  if (kind === "spec") return html`<${SpecTable} n=${n} g=${g} />`;
  const lanes = kind === "work" ? lanesOf(n, g) : null, seats = lanes && lanes.make.length + lanes.check.length + lanes.back.length > 0;
  return html`${seats && html`<${SeatLanes} n=${n} g=${g} />`}<${GoalView} key=${`${g.slug}:${n.slug}`} g=${g} n=${n} />${kind === "done" && html`<div class="phase-quality" data-view="quality"><${QualityPage} props=${{ idea: n.slug }} /></div>`}`;
}

const SAID = [["talk", "Talk"], ["spec", "Spec"]];            // the phases that say something to unfold

/** *Earlier: Talk · Spec*: the phases gone by, folded under the table; a phase pressed unfolds what it said at this tab (the same parts as above), pressed again folds it. `g`: the open tab's party, null for the Orkmaster's. */
export function Earlier({ g, n }) {
  const [open, setOpen] = useState({}), at = PHASES.findIndex(([id]) => id === phaseOf(n.slug));
  const gone = SAID.filter(([id]) => PHASES.findIndex(([x]) => x === id) < at);
  if (!gone.length) return null;
  const body = (id) => (g ? id === "talk" ? html`<${PartyTalk} idea=${n.slug} party=${g.slug} />` : html`<${PartySection} idea=${n.slug} party=${g.slug} />`
    : id === "talk" ? html`<${TalkPage} props=${{ idea: n.slug }} close=${() => {}} />` : html`<${SpecPage} props=${{ idea: n.slug }} />`);
  return html`<section class="phase-earlier" aria-label="Earlier" data-goal=${n.slug}>
    <p class="phase-earlier__line"><span class="ork-label">Earlier:</span>${gone.map(([id, word], i) => html`<span key=${id}>${i > 0 && " · "}<button type="button" class=${cls("ork-btn quiet phase-earlier__one", { "is-open": !!open[id] })} data-earlier=${id}
        aria-expanded=${String(!!open[id])} title=${`${word}: ${open[id] ? "fold it" : "what it said at this tab"}`} onClick=${() => setOpen({ ...open, [id]: !open[id] })}>${word}</button></span>`)}</p>
    ${gone.filter(([id]) => open[id]).map(([id]) => html`<div key=${id} class="phase-earlier__body" data-earlier-body=${id}>${body(id)}</div>`)}
  </section>`;
}
