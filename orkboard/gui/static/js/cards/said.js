// A leader's words at the head of what its mat opened (decisions §297.4): who said it, when, what and why, over the table or the
// spread, so nothing of the post is lost when a mat opens as a table instead of an L of words.
import { html } from "../html.js";
import { HeadOf, KINDS, when, whoOf } from "../table/post.js";

export function Said({ p }) {
  const w = whoOf(p.leader);
  return html`<div class="cards-said" data-race=${w.race || "orkmaster"} role="note" aria-label=${`${w.name} said`}>
    <span class="cards-said__av"><${HeadOf} w=${w} size="mid" /></span>
    <span class="cards-said__t"><b>${w.name}</b><small>${[KINDS[p.kind] || KINDS.news, when(p.at)].filter(Boolean).join(" · ")}</small></span>
    <p class="cards-said__words">${p.text}${p.why ? html`<small>${p.why}</small>` : ""}</p></div>`;
}
