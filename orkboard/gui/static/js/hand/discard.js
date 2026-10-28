// The discard (docs/specs/98-the-table-and-the-hand.md §4.3, decisions §145.4, §159): the last goal done lies face up (*done*, its element, its name) with the backs of the others under it;
// while dev holds goals main lacks (the gate), its top card carries the lich's head and *n goals ready for main*; with nothing done to see, that line alone is on its back. Pressed, it opens
// over the pane (`discard`): the goals done and not yet seen (a goal pressed opens its Result and tells the host it was seen, `ideas.seen`, and it leaves the discard), and *Ready for main*
// with **To main** (today's merge into main, by code). No act on main lies on the pile (§160.5): the pile only shows and opens. No part with nothing done and nothing ready for main.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { act, mapData } from "../shell/store.js";
import { mergeGate } from "../arena/gate.js";
import { closeOver, openOver, over } from "../frame/state.js";
import { doneOf, readyOf, readyWords } from "./data.js";
import { leans } from "./motion.js";

const LICH = { race: "lich", tier: "elder" };
const EDGES = 3;

/** The Release leader's head, the lich's (decisions §158); the lich elder with no such party. */
function lichOf() {
  const g = (mapData.value?.goals || []).find((x) => x.leader?.head?.race === "lich");
  return g?.leader?.head || LICH;
}

/** A goal done and not yet seen is opened as its Result, then it is seen and leaves the discard. */
export async function seeResult(g) {
  openOver("result", { idea: g.slug }, null, g.full || g.title);
  await act("ideas.seen", { idea: g.slug });
}

/** The pile at the hand's right end. */
export function Discard() {
  const done = doneOf(), ready = readyOf();
  if (!done.length && !ready) return null;
  const top = done[0], under = Math.min(EDGES, Math.max(0, done.length - 1)), words = readyWords(ready), lit = over.value?.kind === "discard";
  const press = () => { if (lit) closeOver(); else openOver("discard", {}, null, "Done"); };
  const label = `Done${top ? `: ${top.full}` : ""}${words ? `. ${words}` : ""}`;
  return html`<div class="ork-deck hand-deck hand-discard" data-n=${under} title="Done">
    ${Array.from({ length: under }, (_, k) => under - k).map((i) => html`<i key=${i} class="ork-card-back edge hand-back" style=${`--ork-deck-i:${i}`} aria-hidden="true"></i>`)}
    ${top ? html`<button type="button" class=${cls("ork-card ork-leans hand-card hand-done", { "is-on": lit })} aria-label=${label} aria-expanded=${lit ? "true" : "false"} onClick=${press} ...${leans}>
        <span class="hand-card__top"><${Elem} name=${top.element} dim=${!top.element} /><span class="is-ok"><${Sign} name="check" label="Done" /></span></span>
        <span class="hand-card__name">${top.title}</span>
        <span class="hand-card__foot">${words && html`<${Head} race=${lichOf().race} tier=${lichOf().tier} size="mid" /><span class="cap hand-card__ready">${words}</span>`}</span>
      </button>`
      : html`<button type="button" class=${cls("ork-card-back hand-back hand-deckback hand-done", { "is-on": lit })} aria-label=${label} aria-expanded=${lit ? "true" : "false"} onClick=${press}>
        <span class="hand-back__ready"><${Head} race=${lichOf().race} tier=${lichOf().tier} size="mid" /><span class="cap">${words}</span></span></button>`}
  </div>`;
}

/** *Done, not yet seen* and *Ready for main*, over the pane. */
export function DiscardView() {
  const done = doneOf(), ready = readyOf(), [busy, setBusy] = useState(false);
  const nodes = Object.fromEntries((mapData.value?.nodes || []).map((n) => [n.slug, n]));
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
      ${ready.goals.length > 0 ? html`<ul class="hand-rows">${ready.goals.map((i) => html`<li key=${i.slug} class="ork-row hand-drow"><span class="hand-tick" aria-label="Ticked"><${Sign} name="check" /></span>
        <${Elem} name=${nodes[i.slug]?.element || ""} dim=${!nodes[i.slug]?.element} /><span class="hand-drow__text"><span class="body">${i.title}</span></span>
        ${nodes[i.slug]?.type?.sign && html`<span class="hand-drow__type" title=${nodes[i.slug].type.name}><${Sign} name=${nodes[i.slug].type.sign} /></span>`}</li>`)}</ul>`
        : html`<p class="cap">${readyWords(ready)}: commits that belong to no goal.</p>`}
      <p class="cap">Nothing reaches ${ready.main} without you.</p></section>`}
  </div>`;
}
