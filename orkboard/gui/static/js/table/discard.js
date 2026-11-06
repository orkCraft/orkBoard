// The discard (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §4, decisions §176.3, §185.3; docs/specs/101 §4.4, decisions §145.4, §159, §167.7): it lies on the table, at the foot of its last column (the one right of
// the lanes), the hand card's size, with the word *Discard* above it, on every tab. It was the hand's (hand/discard.js); the hand imports nothing of it. Its sheet is discard.css (the card's anatomy and sizes are the hand's, hand.css).
// The last goal done lies face up on a card's face (spec 147 A.3, decisions §251: the rune and the done sign at the top, its name in four lines, the heads that did it and the time it took at the foot; *N tasks, in main since HH:MM* where the snapshot says it) with the backs of the others under it; while dev holds goals main lacks (the gate), its
// window carries the lich's head and its foot *n goals ready for main*; with nothing done to see, that line alone is on its back. Pressed, it opens over the pane (`discard`): the goals done and not yet seen (a goal pressed opens
// its Result and tells the host it was seen, `ideas.seen`, and it leaves the discard), and *Ready for main*: each goal ready is a card (table/portal.js, spec 105 F: pressed or dragged it is chosen for the portal in the ring over the pile, which sends that goal alone to main) and **To main** (spec 149 G.1: the goal chosen, or the first ready, goes the portal's way with its checks; dev whole by code only for commits that belong to no goal). No act on main lies on the pile (§160.5): the pile only shows and opens.
// A goal done in the night (`ideas.night`, hand/nightcard.js) wears a small moon on its card and its row until its result is seen, and on the first look after the night the night's goals are dealt into the pile one by one (docs/specs/128 C.3, decisions §206.9).
// The ring in it also holds the road's two corners, Release and Live, and the gate of skeletons while a goal's way into main is checked (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4, portal.js, road.js).
// With no gate (dev and main one branch, or no main: `gateData.same`, docs/specs/113-a-project-with-no-preview-or-no-gate.md §4, decisions §191.2) the end is the label and the pile's place or the pile alone: no ring, no portal, no corners.
// The end is laid for what it holds (decisions §247.1, spec 140 A1; before, at the wide width, always: docs/specs/110 §3.2, decisions §185, §186): **the discard is drawn from its first goal done** (the label *Discard* and the pile); with nothing done and nothing
// ready for main nothing lies there, no frame (no `.ork-card-place`) and no word. The portal's ring over it is drawn only while a goal is ready for main or its checks run, else the road's two corners alone (portal.js); with none of these
// the end is not laid at all and the table gains its width (discard.css). At the narrow width, as before, no part with nothing done and nothing ready for main.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { act, mapData } from "../shell/store.js";
import { mergeGate } from "../arena/gate.js";
import { closeOver, openOver, over, picked } from "../frame/state.js";
import { drawn } from "../frame/kinds.js";
import { doneOf, readyOf, readyWords } from "../hand/data.js";
import { DEAL_MS, leans } from "../hand/motion.js";
import { nightFirst, nightMoons } from "../hand/nightcard.js";
import { Portal, ReadyCards, chosenSlug, toMain } from "./portal.js";
import { noGate } from "./data.js";
import { CornerTop, CornerFoot, muchOf, secondsBetween, IN_MAIN } from "./corners.js";             // the card is read by its four corners (spec 147 A.3, decisions §251)
import { CardWindow, lastMade, windowOf } from "./cardwindow.js";

const LICH = { race: "lich", tier: "elder" };
const EDGES = 3;
const GAP_MS = 380;                                       // the night's goals are dealt into the pile this far apart (on the first look after the night: spec 128 C.3)

/** The goals done and not yet seen that the pile shows: the night's goals still to be dealt (nightcard.js `nightFirst`) lie out of it until their turn. */
function shownDone() {
  const first = nightFirst.value, held = first ? new Set(first.goals.slice(first.n)) : null;
  return held?.size ? doneOf().filter((g) => !held.has(g.slug)) : doneOf();
}

/** Deals the night's goals into the pile one by one, a gap apart, from the first look (`nightFirst`); `n` is kept on the record, so a pile drawn again does not deal them again. Returns the slug just dealt while its card flies, else "". */
function useNightDeal() {
  const first = nightFirst.value, [, tick] = useState(0);
  useEffect(() => {
    if (!first || first.n >= first.goals.length) return undefined;
    const t = setInterval(() => {
      first.n += 1;
      first.at = Date.now();
      tick((x) => x + 1);
      setTimeout(() => tick((x) => x + 1), DEAL_MS + 50);                           // the card has landed
      if (first.n >= first.goals.length) clearInterval(t);
    }, GAP_MS);
    return () => clearInterval(t);
  }, [first]);
  return first && first.n > 0 && Date.now() - first.at < DEAL_MS ? first.goals[first.n - 1] : "";
}

/** The seconds a goal took: from its first task started to its last finished; NaN when the tasks carry no such times. */
function tookOf(tasks = []) {
  const from = Math.min(...tasks.map((t) => Date.parse(t.started || "")).filter(Number.isFinite)), to = Math.max(...tasks.map((t) => Date.parse(t.finished || "")).filter(Number.isFinite));
  return Number.isFinite(from) && Number.isFinite(to) ? secondsBetween(new Date(from).toISOString(), new Date(to).toISOString()) : NaN;
}

/** The heads that did a goal: its tasks' seats, each race and tier once, three at most. */
function headsOf(tasks = []) {
  const seen = new Set(), heads = [];
  for (const t of tasks) {
    const h = t.head, id = h && `${h.race}/${h.tier}`;
    if (h && !seen.has(id)) { seen.add(id); heads.push(h); }
  }
  return heads.slice(0, 3);
}

/** *3 tasks, in main since 11:40*: only where the snapshot says when the goal reached main (`in_main`, an ISO time of the host); "" otherwise — nothing is made up. */
function mainLine(g) {
  const at = String((mapData.value?.nodes || []).find((n) => n.slug === g.slug)?.in_main || "").slice(11, 16), n = g.tasks.length;
  return at && n ? `${n} ${n === 1 ? "task" : "tasks"}, ${IN_MAIN} ${at}` : "";
}

/** The Release leader's head, the lich's (decisions §158); the lich elder with no such party. */
export function lichOf() {
  const g = (mapData.value?.goals || []).find((x) => x.leader?.head?.race === "lich");
  return g?.leader?.head || LICH;
}

/** A goal done and not yet seen is opened as its Result, then it is seen and leaves the discard. **It is also the goal picked** (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.3): when the Result is put away, each leader's tab shows
 *  what the goal changed against what its spec promised (goalview.js), and the Play die wears its rune. */
export async function seeResult(g) {
  picked.value = g.slug;
  openOver("result", { idea: g.slug }, null, g.full || g.title);
  await act("ideas.seen", { idea: g.slug });
}

/** Whether there is a pile: a goal done, or goals ready for main. */
export const hasDiscard = () => shownDone().length > 0 || !!readyOf();

/** The pile: the last goal done, the backs under it, the lich's head and what is ready for main. */
export function Discard({ dealing = "" }) {
  const done = shownDone(), ready = readyOf(), moons = nightMoons();
  if (!done.length && !ready) return null;
  const top = done[0], moon = !!top && moons.has(top.slug), under = Math.min(EDGES, Math.max(0, done.length - 1)), words = readyWords(ready), lit = over.value?.kind === "discard";
  const press = () => { if (lit) closeOver(); else openOver("discard", {}, null, "Done"); };
  const label = `Done${top ? `: ${top.full}` : ""}${words ? `. ${words}` : ""}`;
  const lich = lichOf(), line = top ? words || mainLine(top) : "";
  const made = top ? lastMade(top.tasks) : null, windowed = !!top && windowOf({ made, picture: top.picture }).kind !== "none";       // its window between the name and the foot: the last made, else the goal's picture, else its line (spec 148 B.3)
  return html`<div class="ork-deck table-discard" data-n=${under} title="Done">
    ${Array.from({ length: under }, (_, k) => under - k).map((i) => html`<i key=${i} class="ork-card-back edge hand-back" style=${`--ork-deck-i:${i}`} aria-hidden="true"></i>`)}
    ${top ? html`<button key=${dealing ? top.slug : "top"} type="button" class=${cls(`ork-card ork-leans hand-card hand-card--stop hand-card--corners hand-done${top.element ? ` el-${top.hue || top.element}` : ""}`, { "is-on": lit, "ork-deal": !!dealing })} data-slug=${top.slug} data-moon=${moon ? "1" : undefined} data-dealt=${dealing || undefined}
        aria-label=${label} aria-expanded=${lit ? "true" : "false"} onClick=${press} ...${leans}>
        <${CornerTop} rune=${{ name: top.element, hue: top.hue, dim: !top.element }} kind="check" signal="success" />
        <span class="hand-done__name" title=${top.title}>${top.title}</span>
        ${windowed ? html`<${CardWindow} of=${{ made, picture: top.picture, name: top.title }} />` : line && html`<span class="hand-done__line" title=${line}>${line}</span>`}
        ${moon && html`<span class="hand-done__moon" title="Done in the night"><${Sign} name="moon" label="Done in the night" /></span>`}
        <${CornerFoot} who=${{ heads: headsOf(top.tasks) }} much=${muchOf({ done: true, took: tookOf(top.tasks) })} />
      </button>`
      : html`<button type="button" class=${cls("ork-card-back hand-back hand-done", { "is-on": lit })} aria-label=${label} aria-expanded=${lit ? "true" : "false"} onClick=${press}>
        <span class="hand-back__ready"><${Head} race=${lich.race} tier=${lich.tier} /><span class="cap" title=${words || undefined}>${words}</span></span></button>`}
  </div>`;
}

/** *Done, not yet seen* and *Ready for main*, over the pane. */
export function DiscardView() {
  const done = shownDone(), ready = readyOf(), moons = nightMoons(), [busy, setBusy] = useState(false);
  const merge = async (e) => {                                                          // a goal ready goes the portal's way, its checks in it (spec 149 G.1); dev whole is for commits of no goal
    setBusy(true);
    try { if (ready?.goals.length) await toMain(chosenSlug() || ready.goals[0].slug); else await mergeGate(e); } finally { setBusy(false); }
  };
  return html`<div class="hand-discardview">
    ${!done.length && !ready && html`<p class="ok-tone-muted">Nothing is done and waiting, and nothing waits for main.</p>`}
    ${ready && html`<section class="hand-part" aria-label="Ready for main">
      <div class="hand-part__head"><${Head} race=${lichOf().race} tier=${lichOf().tier} /><h2 class="ork-label hand-part__title">Ready for ${ready.main}</h2>
        <button type="button" class="ork-btn primary" data-to-main disabled=${busy}
          title=${ready.goals.length > 0 ? `Sends the goal chosen, or the first one ready, through the portal to ${ready.main}: its checks run first, nothing reaches ${ready.main} without you` : `Merges ${ready.into} into ${ready.main}: nothing reaches ${ready.main} without you`} onClick=${merge}>To ${ready.main}</button></div>
      ${ready.goals.length > 0 ? html`<${ReadyCards} goals=${ready.goals} main=${ready.main} />`
        : html`<p class="cap">${readyWords(ready)}: commits that belong to no goal.</p>`}
      <p class="cap">Nothing reaches ${ready.main} without you.</p></section>`}
    ${done.length > 0 && html`<section class="hand-part" aria-label="Done, not yet seen">
      <h2 class="ork-label">Done, not yet seen</h2>
      <ul class="hand-rows">${done.map((g) => html`<li key=${g.slug}><button type="button" class="ork-row hand-drow" data-slug=${g.slug} onClick=${() => seeResult(g)}>
        <${Elem} name=${g.element} hue=${g.hue} dim=${!g.element} /><span class="hand-drow__text"><span class="body">${g.full}</span></span>
        ${moons.has(g.slug) && html`<span class="hand-drow__moon" data-moon="1" title="Done in the night"><${Sign} name="moon" label="Done in the night" /></span>`}
        ${g.type?.sign && html`<span class="hand-drow__type" title=${g.type.name}><${Sign} name=${g.type.sign} /></span>`}
        <span class="cap hand-drow__place">Result<i class="ork-chev right" aria-hidden="true"></i></span></button></li>`)}</ul></section>`}
  </div>`;
}

/** The table's end: the portal's place, the word *Discard* and the pile (discard.css), each only when it holds something (decisions §247.1): the pile and its word from the first goal done, the portal's place while a goal is ready for main or the road has a corner; else nothing. */
export function DiscardEnd() {
  const dealing = useNightDeal(), pile = hasDiscard();
  if (!pile) return null;
  return html`<div class="table-end" data-end="discard">${!noGate() && html`<${Portal} />`}<span class="table-end__label">Discard</span><${Discard} dealing=${dealing} /></div>`;
}

/** The discard in the table's edge at the wide width (spec 150 D.2, frame/edge.js): the word and the pile, the pile cut from its foot when the window is short. Nothing while nothing is done or ready. */
export function EdgeDiscard() {
  const dealing = useNightDeal();
  return hasDiscard() ? html`<div class="edge-discard" data-end="discard"><span class="table-end__label">Discard</span><${Discard} dealing=${dealing} /></div>` : null;
}

drawn("discard", DiscardView);
