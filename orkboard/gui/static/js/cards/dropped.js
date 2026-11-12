// The discard's third pile, Dropped (decisions §298.8): the goals dropped lie face down under their plate, thickness only and no number; pressed, the pile spreads them face up
// (S cards with their last tokens), each with *Take back*, which sends `ideas.take_back {slug}` and brings the goal back to the hand (the host answers it: gui/ideas_mats.py, a Drop's Undo).
// The host keeps no list of the goals dropped, so the pile holds this page's own drops. A goal dropped on this page (the hand's *Drop*, hand/turncards.js)
// lies here at once, kept in a signal; one taken back is out of the pile and its turn is back in the hand. Dropping a goal stays the person's: nothing here drops one.
import { useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { command } from "../link.js";
import { CardS } from "./card.js";
import { nodeOf } from "./feed.js";

export const droppedNow = signal([]);           // the goals dropped on this page, the last one first
export const takenBack = signal([]);            // the goals taken back out of the pile (the host's own list may still name them)

/** The goals in the pile, the last dropped first: this page's, then the host's. */
export const droppedSlugs = () => [...new Set(droppedNow.value)].filter((s) => !takenBack.value.includes(s));
export const dropGoal = (slug) => { droppedNow.value = [slug, ...droppedNow.value.filter((s) => s !== slug)]; takenBack.value = takenBack.value.filter((s) => s !== slug); };
export const takeBackGoal = (slug) => { droppedNow.value = droppedNow.value.filter((s) => s !== slug); takenBack.value = [...takenBack.value.filter((s) => s !== slug), slug]; };

const nodeIn = (slug) => nodeOf(slug) || null;

function One({ slug }) {
  const n = nodeIn(slug) || { slug, title: slug }, card = { slug, title: n.short || n.title || slug, element: n.element, hue: n.hue, sign: n.type?.sign || "check", leader: n.goal };
  const back = () => Promise.resolve(command("ideas.take_back", { slug })).then(() => takeBackGoal(slug)).catch(() => {});
  return html`<div class="cards-dropped__one" data-dropped=${slug}><${CardS} n=${card} line="dropped" />
    <button type="button" class="ork-btn" data-act="take_back" onClick=${back}><span>Take back</span></button></div>`;
}

/** The pile under the *dev* pile: its plate, its backs; pressed, its goals face up. Nothing when no goal was dropped. */
export function Dropped() {
  const slugs = droppedSlugs(), [open, setOpen] = useState(false);
  if (!slugs.length) return null;
  return html`<section class="discard-pile cards-dropped" data-pile="dropped" aria-label="Dropped">
    <button type="button" class="ork-plaque discard-plate" data-plate="dropped" aria-expanded=${open ? "true" : "false"} title=${open ? "Put the goals face down" : "Spread the goals dropped"} onClick=${() => setOpen(!open)}><span>Dropped</span></button>
    <p class="discard-pile__words">goals dropped, face down</p>
    ${open ? html`<div class="cards-row is-wrap" role="group" aria-label="Goals dropped">${slugs.map((s) => html`<${One} key=${s} slug=${s} />`)}</div>`
      : html`<button type="button" class="cards-dropped__pile" data-act="spread" aria-label="Goals dropped, face down. Press to spread them." onClick=${() => setOpen(true)}>
        ${Array.from({ length: Math.min(slugs.length, 5) }, (_, i) => html`<span key=${i} aria-hidden="true" style=${`--dx:${i * 2}px;--dy:${-i * 2}px`}></span>`)}</button>`}
  </section>`;
}
