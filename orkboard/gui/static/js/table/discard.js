// The discard (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §4, decisions §176.3; docs/specs/101 §4.4, decisions §145.4, §159, §167.7): it lies on the table, at the foot of its last column (the one right of
// the lanes), the hand card's size, with the word *Discard* above it, on every tab. It was the hand's (hand/discard.js); the hand imports nothing of it. Its sheet is discard.css (the card's anatomy and sizes are the hand's, hand.css).
// The last goal done lies face up on a card's face (its element and name in the header, the check in the window, *Done* in the label row) with the backs of the others under it; while dev holds goals main lacks (the gate), its
// window carries the lich's head and its foot *n goals ready for main*; with nothing done to see, that line alone is on its back. Pressed, it opens over the pane (`discard`): the goals done and not yet seen (a goal pressed opens
// its Result and tells the host it was seen, `ideas.seen`, and it leaves the discard), and *Ready for main*: each goal ready is a card (table/portal.js, spec 105 F: pressed or dragged it opens the portal over the pile, which sends that goal alone to main) and **To main** (dev whole, for a person's own commits, by code). No act on main lies on the pile (§160.5): the pile only shows and opens.
// No part with nothing done and nothing ready for main.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { act, mapData } from "../shell/store.js";
import { mergeGate } from "../arena/gate.js";
import { closeOver, openOver, over } from "../frame/state.js";
import { drawn } from "../frame/kinds.js";
import { doneOf, readyOf, readyWords } from "../hand/data.js";
import { leans } from "../hand/motion.js";
import { Portal, ReadyCards } from "./portal.js";

const LICH = { race: "lich", tier: "elder" };
const EDGES = 3;

/** The Release leader's head, the lich's (decisions §158); the lich elder with no such party. */
export function lichOf() {
  const g = (mapData.value?.goals || []).find((x) => x.leader?.head?.race === "lich");
  return g?.leader?.head || LICH;
}

/** A goal done and not yet seen is opened as its Result, then it is seen and leaves the discard. */
export async function seeResult(g) {
  openOver("result", { idea: g.slug }, null, g.full || g.title);
  await act("ideas.seen", { idea: g.slug });
}

/** Whether there is a pile: a goal done, or goals ready for main. */
export const hasDiscard = () => doneOf().length > 0 || !!readyOf();

/** The pile: the last goal done, the backs under it, the lich's head and what is ready for main. */
export function Discard() {
  const done = doneOf(), ready = readyOf();
  if (!done.length && !ready) return null;
  const top = done[0], under = Math.min(EDGES, Math.max(0, done.length - 1)), words = readyWords(ready), lit = over.value?.kind === "discard";
  const press = () => { if (lit) closeOver(); else openOver("discard", {}, null, "Done"); };
  const label = `Done${top ? `: ${top.full}` : ""}${words ? `. ${words}` : ""}`;
  const lich = lichOf();
  return html`<div class="ork-deck table-discard" data-n=${under} title="Done">
    ${Array.from({ length: under }, (_, k) => under - k).map((i) => html`<i key=${i} class="ork-card-back edge hand-back" style=${`--ork-deck-i:${i}`} aria-hidden="true"></i>`)}
    ${top ? html`<button type="button" class=${cls(`ork-card ork-leans hand-card hand-card--stop hand-done${top.element ? ` el-${top.element}` : ""}`, { "is-on": lit })} aria-label=${label} aria-expanded=${lit ? "true" : "false"} onClick=${press} ...${leans}>
        <span class="hand-card__head"><${Elem} name=${top.element} dim=${!top.element} /><span class="hand-card__name">${top.title}</span></span>
        <span class="hand-card__window"><span class="hand-card__act"><span class="hand-mark is-ok"><${Sign} name="check" big=${true} label="Done" /></span></span>
          ${words && html`<span class="hand-card__asker"><${Head} race=${lich.race} tier=${lich.tier} /></span>`}</span>
        <span class="hand-card__label"><span class="hand-card__party">Done</span></span>
        <span class="hand-card__foot">${words}</span>
      </button>`
      : html`<button type="button" class=${cls("ork-card-back hand-back hand-done", { "is-on": lit })} aria-label=${label} aria-expanded=${lit ? "true" : "false"} onClick=${press}>
        <span class="hand-back__ready"><${Head} race=${lich.race} tier=${lich.tier} /><span class="cap">${words}</span></span></button>`}
  </div>`;
}

/** *Done, not yet seen* and *Ready for main*, over the pane. */
export function DiscardView() {
  const done = doneOf(), ready = readyOf(), [busy, setBusy] = useState(false);
  const merge = async (e) => { setBusy(true); await mergeGate(e); setBusy(false); };
  return html`<div class="hand-discardview">
    ${!done.length && !ready && html`<p class="ok-tone-muted">Nothing is done and waiting, and nothing waits for main.</p>`}
    ${done.length > 0 && html`<section class="hand-part" aria-label="Done, not yet seen">
      <h2 class="ork-label">Done, not yet seen</h2>
      <ul class="hand-rows">${done.map((g) => html`<li key=${g.slug}><button type="button" class="ork-row hand-drow" data-slug=${g.slug} onClick=${() => seeResult(g)}>
        <${Elem} name=${g.element} dim=${!g.element} /><span class="hand-drow__text"><span class="body">${g.full}</span></span>
        ${g.type?.sign && html`<span class="hand-drow__type" title=${g.type.name}><${Sign} name=${g.type.sign} /></span>`}
        <span class="cap hand-drow__place">Result<i class="ork-chev right" aria-hidden="true"></i></span></button></li>`)}</ul></section>`}
    ${ready && html`<section class="hand-part" aria-label="Ready for main">
      <div class="hand-part__head"><${Head} race=${lichOf().race} tier=${lichOf().tier} /><h2 class="ork-label hand-part__title">Ready for ${ready.main}</h2>
        <button type="button" class="ork-btn primary" disabled=${busy} title=${`Merges ${ready.into} into ${ready.main}: nothing reaches ${ready.main} without you`} onClick=${merge}>To ${ready.main}</button></div>
      ${ready.goals.length > 0 ? html`<${ReadyCards} goals=${ready.goals} main=${ready.main} />`
        : html`<p class="cap">${readyWords(ready)}: commits that belong to no goal.</p>`}
      <p class="cap">Nothing reaches ${ready.main} without you.</p></section>`}
  </div>`;
}

/** The pile's place on the table: the last column's foot, the word *Discard* above the pile (discard.css); nothing with nothing done and nothing ready for main. */
export function DiscardEnd() {
  if (!hasDiscard()) return null;
  return html`<div class="table-end" data-end="discard"><${Portal} /><span class="table-end__label">Discard</span><${Discard} /></div>`;
}

drawn("discard", DiscardView);
