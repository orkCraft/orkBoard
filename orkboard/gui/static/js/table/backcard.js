// A goal's own card face down (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.3–§6.5, decisions §198.8): while its leaders talk it over (`talk`) and while its wait runs (`wait`) or is held (`held`), the goal's card in the Orkmaster's lane is its back — the
// + card's seal with its own rune lit (glowing while the leaders talk), its short name at the foot, never the + card's green — and under it its route's heads, small, faint until `back.heard` names them. No verdict, no tick, no count is drawn (§145.3): the ring of
// the seal is the wait (backbody.js), the words under the card *Starts by itself in 4 min*. Hovered, it only lifts (orkUI's `.ork-leans`); pressed (or Enter), it turns to its face (`BackFace`, drawn over the card where it lies like any lifted card: its words, the route
// edited here with the route card's `RouteLifted`, what each leader that has said said, its cost; at the wait *All the leaders agreed* and **Hold**, held **Start**) and *Turn it back* turns it down again. The turn is orkUI's `.ork-turn` (0.28.0), in place (`Turning`).
// `back` is the node's (realm/board_back.py). `everBack` remembers the goals this page has seen face down, for the turn up at the wait's end and the flight to the lane (flight.js).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { reduced, tokenMs } from "../hand/motion.js";
import { lift, lower, lifted, picked } from "../frame/state.js";
import { act } from "../shell/store.js";
import { board } from "../board/store.js";
import { CostLine, RouteLifted, costLine, partyName, routeWords } from "../hand/routecard.js";
import { bodyOf } from "../hand/decisioncard.js";
import { BackBody, leftWords, shareOf } from "./backbody.js";
import { GoalMenu } from "./dropgoal.js";
import { PickGoal, Sec, aboutTokens, leans, litKey, ownKey } from "./card.js";

/** The goals this page has seen face down (their turn up and their flight to a lane are played once, never for what changed unseen). */
export const everBack = new Set();

/** Which back a goal wears, `"talk"` · `"wait"` · `"held"`, "" for none (a face-up card): its leaders are talking it over; all agreed and its wait runs; all agreed and the wait is held (by the person, a stop or a spent window). */
export function backKind(n) {
  const b = n?.back;
  if (!b) return "";
  if (n.state === "talk") return "talk";
  if (n.state === "decided" && b.ripe && b.ripe.by !== "leaders") return b.ripe.held ? "held" : "wait";
  return "";
}

const shares = new Map();                       // the last share of a wait seen, by goal: a held wait stands where it was (the host keeps no share of a held one)
const HELD = "Held: start it when you are ready";

/** A Needs you row of kind `kind` (or one of `kinds`) of the goal: the hand's cards the goal waits on. */
const rowOf = (slug, ...kinds) => (board.value?.needs_you || []).find((r) => r.idea === slug && kinds.includes(r.kind)) || null;

/** The words under a back: the wait's time, or *Held: …*; none while the leaders talk. */
export function underWords(kind, ripe) {
  return kind === "wait" ? `Starts by itself in ${leftWords(ripe?.left_s)}` : kind === "held" ? HELD : "";
}

/** What the back says of the goal now (kind, the wait's share, its label), kept by `Turning` while the card turns up. */
function backOf(n, kind) {
  const b = n.back, route = b.route || [], heard = new Set(b.heard || []), said = route.filter((s) => heard.has(s.party)).length;
  let share = null;
  if (kind === "wait") { share = shareOf(b.ripe); shares.set(n.slug, share); } else if (kind === "held") share = shares.get(n.slug) ?? 0;
  const under = underWords(kind, b.ripe);
  const label = kind === "talk" ? `${n.title}: the leaders are talking it over${route.length ? ` · ${said} of ${route.length} leaders have said` : ""}`
    : kind === "wait" ? `${n.title}: all the leaders agreed. ${under}` : `${n.title}: ${HELD}`;
  return { kind, route, heard, said, share, under, label, asked: !!rowOf(n.slug, "talk", "hearing", "cause") };
}

/** The goal's card face down: the back itself, a button. */
function BackButton({ n, back, on, live }) {
  const key = ownKey(n);
  return html`<button type="button" class=${cls("ork-card ork-leans table-card table-card--back", { "is-lifted": on, "is-lit": litKey.value === key, "ork-picked": picked.value === n.slug })} data-lkey=${key} data-goal=${n.slug} data-state=${n.state} data-back=${back.kind}
      data-about=${aboutTokens(n)} aria-pressed=${String(on)} aria-label=${back.label} tabindex=${live ? undefined : -1} onClick=${() => lift(on ? "" : key)} ...${leans}>
    <${BackBody} element=${n.element} hue=${n.hue} name=${n.short || n.title} glowing=${back.kind === "talk" && !back.asked} waiting=${back.share} />
  </button>`;
}

/** Under the back: its route's heads, small, faint until the leader has said, and the wait's words. */
function BackFoot({ back }) {
  return html`<span class="table-back-heads" data-heard=${back.said} aria-hidden="true">${back.route.map((s) => html`<span key=${s.party} class=${cls("table-back-head", { "is-said": back.heard.has(s.party) })} data-party=${s.party}>${s.head && html`<${Head} race=${s.head.race} tier=${s.head.tier} title=${partyName(s.party)} />`}</span>`)}</span>
  ${back.under && html`<span class="table-back-under" data-wait=${back.kind}>${back.under}</span>`}`;
}

/** A goal's own card that wears a back at some time on this page (spec 120 §6.3–§6.5, §6.11): orkUI's `.ork-turn`, its back the goal face down and its face (`children`) the card face up, **in place**. It is face down while the goal's leaders talk it over and its wait runs
 *  (`kind`), and face up otherwise; a press on the back turns it to its face (the lifted card draws its details over it) and *Turn it back* turns it down; when the wait ends the back turns up where it lies. The back is kept while it turns, then taken away. Under reduced motion
 *  orkUI swaps the two sides at once. Its heads and its wait's words lie under it while it is a back. */
export function Turning({ n, kind, children }) {
  const key = ownKey(n), on = lifted.value === key, root = useRef(), kept = useRef(null), [held, setHeld] = useState(!!kind);
  everBack.add(n.slug);
  if (kind) kept.current = backOf(n, kind);
  useEffect(() => {
    if (kind) { setHeld(true); return undefined; }
    const t = setTimeout(() => setHeld(false), reduced() ? 0 : tokenMs("--ork-motion-play", 400) + 100);          // the back stays while it turns away
    return () => clearTimeout(t);
  }, [kind]);
  const up = !kind || on, back = kept.current && (kind || held) ? kept.current : null, was = useRef(up);
  useEffect(() => {                                                                  // the side the focus was on turns away: the focus goes to the side that shows
    if (was.current === up) return;
    was.current = up;
    const el = root.current, at = document.activeElement;
    if (el && at && el.contains(at)) requestAnimationFrame(() => el.querySelector(`.ork-turn__${up ? "face" : "back"} > .table-card`)?.focus({ preventScroll: true }));
  }, [up]);
  return html`<div ref=${root} class=${cls("ork-turn table-turn", { "is-up": up })} data-turn=${up ? "face" : "back"}>
      ${back && html`<div class="ork-turn__back"><${BackButton} n=${n} back=${back} on=${on} live=${!!kind} /></div>`}
      <div class="ork-turn__face">${children}</div>
    </div>
    ${kind && back && html`<${BackFoot} back=${back} />`}`;
}

/** The goal's card turned to its face, over the card where it lies (card.js `Lifted`). */
export function BackFace({ n }) {
  const kind = backKind(n), b = n.back, [busy, setBusy] = useState(false), idea = n.slug;
  const run = async (name) => { setBusy(true); try { if (await act(name, { idea })) lower(); } finally { setBusy(false); } };
  const row = rowOf(idea, "decision"), why = row ? bodyOf(row.text)?.why : "";
  const caption = kind === "talk" ? "The leaders are talking it over." : kind === "wait" ? "All the leaders agreed" : HELD;
  const said = b.stances || [], steps = b.route || [];
  return html`<h3 class="table-back__nm table-back__goal">${n.title}</h3>
    <p class="table-back__cap" data-caption=${kind}>${caption}</p>
    ${kind === "talk" ? html`<${RouteLifted} s=${{ row: { idea, goal: n.goal, route: steps, cost: b.cost || null, short: !!b.short, reproduces: false, offer: b.offer || [], low: false, type: "" } }} close=${lower} edit=${true} />`
      : html`<${Sec} label="Route"><span>${routeWords(steps)}</span></${Sec}>${costLine(b.cost) && html`<${CostLine} cost=${b.cost} />`}`}
    ${said.length > 0 && html`<${Sec} label="What the leaders said"><ul class="table-back__stances">${said.map((s) => html`<li key=${s.party} data-party=${s.party}><b>${partyName(s.party)}</b> ${s.stance}</li>`)}</ul></${Sec}>`}
    ${why && html`<${Sec} label="Why"><span class="table-back__text">${why}</span></${Sec}>`}
    ${kind !== "talk" && html`<p class="table-back__cap" data-under=${kind}>${underWords(kind, b.ripe)}</p>`}
    <div class="table-back__acts">
      ${kind === "wait" && html`<button type="button" class="ork-btn table-back__hold" disabled=${busy} title="Stop the wait: it starts when you press Start" onClick=${() => run("ideas.ripe_hold")}>Hold</button>`}
      ${kind === "held" && html`<button type="button" class="ork-btn primary table-back__start" disabled=${busy} title="The decision is written and the leaders write their sections" onClick=${() => run("ideas.confirm")}>Start</button>`}
      <button type="button" class="ork-btn quiet table-back__turn" onClick=${() => lower()}>Turn it back</button>
      <${PickGoal} n=${n} /><${GoalMenu} slug=${n.slug} where="inline" />
    </div>`;
}
