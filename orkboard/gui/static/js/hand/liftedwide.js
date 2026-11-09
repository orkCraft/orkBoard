// Any other card lifted on the desktop (docs/specs/168 D1, decisions §283.19, §286): no card of 404 x 566 is left. A card that is no question or failure (a plan, a decision, a pick, a result, a goal's way's card, a conflict) rises as the others do: the 144 x 202 hand card at the table's foot at its left,
// its goal picked and its asker's tab opened; what it says and its answers lie in the hand's place beside it, a body as large as the hand (hand.css `is-play`, handplace.js): its words and its way's own body (stopcard.js `Body`, a way's `Lifted`) at the left, its answers, its cost and *Put it back* at the right.
// The rest of the hand sinks as for the ways. The narrow page and the phone keep the inline card (stopcard.js `Lifted`).
import { useEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { CornerFoot, CornerTop, muchOf } from "../table/corners.js";
import { lower } from "../frame/state.js";
import { Answers } from "./answers.js";
import { costOf, Spend } from "./cost.js";
import { OWN_LINES, WayLine } from "./wayline.js";
import { Body, actionOf, footOf, headOf, labelOf, signalOf } from "./stopcard.js";
import { StopWindow, hasWindow } from "./handwindow.js";
import { usePlay } from "./answercards.js";
import { usePlace } from "./handplace.js";
import { useAbout } from "./about.js";
import { wayOf } from "./ways.js";
import { SketchLifted, isSketch } from "./sketchcard.js";
import { footCost } from "./waycost.js";

/** The lifted card of any kind that is not a question or a failure, on the desktop: the card at the table's foot at its left and a body as large as the hand in the hand's place. */
export function LiftedWide({ s }) {
  const box = useRef(), cost = costOf(s), head = headOf(s), element = s.node?.element || "", hue = s.node?.hue || element;
  useAbout(s);
  usePlay(s);
  const at = usePlace(box, null, [s.key]);
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, [s.key]);
  const tone = s.tone === "danger" ? "danger" : s.tone === "alert" ? "alert" : "", Way = wayOf(s.kind)?.Lifted || (isSketch(s) ? SketchLifted : null), shown = footCost(s.key, cost);
  return html`<aside ref=${box} class=${cls(`ork-card hand-card hand-card--stop hand-card--face hand-lifted hand-lifted--asked is-play has-body${element ? ` el-${hue}` : ""}${tone ? ` ${tone}` : ""}`, { asks: ["asks", "goal", "pick", "collide", "conflict"].includes(s.kind), fails: s.kind === "failed" })}
      role="dialog" tabindex="-1" aria-label=${`Lifted: ${labelOf(s)}`} data-key=${s.key} data-kind=${s.kind} style=${at ? `left:${at.left}px` : undefined}>
    <${CornerTop} rune=${{ name: element, hue, dim: !element }} kind=${actionOf(s).sign} signal=${signalOf(s)} />
    <span class="hand-card__name" title=${s.full || s.title}>${s.title || s.full}</span>
    <span class="hand-card__foot">${footOf(s) === s.label ? "" : footOf(s)}</span>
    <${CornerFoot} who=${head ? { heads: [head], word: "" } : null} much=${shown ? { ...muchOf({ cost: shown.gem }), share: !!shown.share } : null} />
  <div class=${cls("hand-body is-play", { "has-way": !!Way })} role="group" aria-label=${labelOf(s)} style=${at ? `left:0;width:${at.width}px;height:${at.height}px` : undefined}>
    <div class="hand-lifted__body">

      ${hasWindow(s) && html`<div class="hand-lifted__win"><${StopWindow} s=${s} h=${72} /></div>`}
      <span class="ork-label hand-lifted__kind">${s.label}</span>
      ${Way ? html`<${Way} s=${s} close=${lower} />` : html`<${Body} s=${s} />`}
    </div>
    <div class="hand-lifted__acts">
      ${!Way && html`<div class="hand-answers" role="group" aria-label="Answers"><${Answers} s=${s} /></div>`}
      ${s.row?.level && s.row?.pulls && !OWN_LINES.has(s.kind) ? html`<${WayLine} row=${s.row} own=${cost?.words || ""} />` : html`<${Spend} cost=${cost} />`}
      ${!wayOf(s.kind)?.puts && html`<button type="button" class="ork-btn hand-put" onClick=${lower}>Put it back</button>`}
    </div>
  </div></aside>`;
}
