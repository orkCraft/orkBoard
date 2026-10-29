// A goal ready for main as a card of the phone's hand (docs/decisions.md §180.2, docs/specs/105 F): Release's card, the lich asks. Its context says what is done and that the checks are green; on its body lie the line (portal.js `lineOf`),
// the portal (orkUI's `.ork-portal`, the button that sends the goal to main: portal.js `play`, `ideas.to_main`), the pixel-face word *Main* and *Later*, which only puts the card back for this session's view (the goal stays ready in
// the discard). The plan (`ideas.to_main_plan`) is asked once when the card comes on top (portal.js `choose`); a goal the gate holds is `is-sealed`, its reason under the portal in the danger colour, a press says it again and sends
// nothing; the first time the portal shimmers (`is-new`) and says how. On success the card goes with the goal and the next entry comes on top.
import { useEffect } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Sign } from "../orkui.js";
import { gateData } from "../shell/store.js";
import { choose, close, echo, first, joined, labelOf, lineOf, namesOf, plan, play, reasonOf } from "../table/portal.js";
import { later } from "./entries.js";

/** What the context of a ready card says: *Lobby and Reconnect are done and their checks are green*, *Lobby is done and its checks are green*. */
export function readyWhy(slug) {
  const p = plan.value?.slug === slug ? plan.value : null, names = namesOf(p, slug);
  return names.length > 1 ? `${joined(names)} are done and their checks are green` : `${names[0]} is done and its checks are green`;
}

/** The stop the context reads for a ready entry (kind `ready`): Release's lich, the goal's node, the why. */
export function readyStop(e) {
  return { key: e.key, kind: "ready", node: e.node, title: e.ready.title, full: e.ready.title, party: { name: "Release", head: e.head }, why: readyWhy(e.ready.slug), text: "", label: "Ready for main" };
}

/** The card: the goal's element and *<Goal> is ready for main*, the check in its window with the lich's head, the portal on its body. */
export function ReadyCard({ e }) {
  const slug = e.ready.slug, main = gateData.value?.main || "main", p = plan.value?.slug === slug ? plan.value : null;
  useEffect(() => { choose(slug); return close; }, [slug]);                                     // the plan is asked once, when the card comes on top
  const sealed = p?.state === "fail" || !!p?.sealed, reason = reasonOf(p), name = `${e.name} is ready for ${main}`;
  const line = p?.state === "ok" ? lineOf(p, slug, main) : p?.state === "fail" ? `Into ${main}: ${e.name}` : `Checking ${e.name}…`;
  const state = p?.state === "ok" ? (sealed ? "sealed" : "open") : p?.state || "wait";
  return html`<aside class=${cls(`ork-card hand-card hand-card--stop hand-card--big hand-lifted hand-lifted--up hand-ready${e.element ? ` el-${e.element}` : ""}`, { "is-new": first.value })}
      role="group" tabindex="-1" aria-label=${name} data-key=${e.key} data-kind="ready" data-portal=${state}>
    <span class="hand-card__head"><${Elem} name=${e.element} dim=${!e.element} /><span class="hand-card__name hand-lifted__title">${name}</span></span>
    <span class="hand-card__window"><span class="hand-card__fig"><span class="hand-card__act"><span class="hand-mark is-ok"><${Sign} name="check" big=${true} /></span></span><span class="hand-card__asker"><${Head} race=${e.head.race} tier=${e.head.tier} /></span></span></span>
    <span class="hand-card__label"><span class="hand-card__party">Release</span></span>
    <div class="hand-lifted__body hand-ready__body">
      <p class="body hand-ready__line">${line}</p>
      <button type="button" class=${cls("ork-portal", { "is-sealed": sealed, "is-new": first.value })} aria-label=${labelOf(p, slug, main)} aria-disabled=${p?.state === "wait" ? "true" : undefined} onClick=${play}></button>
      <span class="hand-ready__label">${main === "main" ? "Main" : main}</span>
      ${first.value && !sealed && html`<p class="cap hand-ready__hint">Tap the portal to send it to main</p>`}
      <p class="cap hand-ready__sealed" role="status" aria-live="polite">${sealed && html`<span key=${echo.value}>Sealed: ${reason}</span>`}</p>
      <button type="button" class="ork-btn quiet hand-ready__later" onClick=${() => { later.value = [...later.value, slug]; }}>Later</button>
    </div>
    <span class="hand-card__foot hand-lifted__kind">Ready for ${main}</span>
  </aside>`;
}
