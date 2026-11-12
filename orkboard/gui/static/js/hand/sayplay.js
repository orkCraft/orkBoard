// A card in play whose ways are not a question's (docs/specs/168 D1, C4; decisions §283.16.4, §283.19, §286): a leader's risk, conflict, better or the open fork of the say (table/sayask.js), and a decision's conflict (conflictcard.js), rise at the table's foot at their left as the 144 x 202 card
// they were; their goal is picked and their asker's tab opened (frame/state.js `playAt`); their ways are the hand's row from the same left edge, cut by the rim and rising when hovered (answercards.js `WayCard`, `data-way-kind` of each: the way's kind, J1); a card with its own words (a conflict's *Other…*)
// lays the Pen, a field as large as the hand (penfield.js). `PlayWays` draws a descriptor `{title, foot, sign, element, hue, head, tab, ways, leave, pen}` (a way is `{id, name, line, pick, kind, run}`; `pen`: `{name, line?, who, send(text), ask?, at?}`, drawn as a way of its own (before the way at index `at`, else last), `ask` the field's own words: penfield.js; `whole`: the ways lie wholly inside the hand, none cut by its rim; `acts`: `[{id, name, line, run}]`, the card's menu, quiet buttons beside *Put it back*: spec 168 F2). The commands are the callers': C4's
// `ideas.take_way {idea, id, way}`, `ideas.leave_say {idea, id}`, `ideas.take_better {idea, id}`, `ideas.say_fork {idea, pick}`, and `ideas.conflict {idea, number, choice, text?}`; a refusal is the keeper's plain words (a toast) and the card stays; answered, the card goes back. Wide only: the narrow page keeps the choice over the pane.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { CornerFoot, CornerTop } from "../table/corners.js";
import { lower, playAt, playing } from "../frame/state.js";
import { sayCard } from "../table/sayask.js";
import { OWN_LINE, WayCard, useRing } from "./answercards.js";
import { PenField } from "./penfield.js";
import { usePlace } from "./handplace.js";

/** The say's card in play, for `playing.value`. */
export function SayLifted() {
  const props = playing.value, card = props ? sayCard(props, lower) : null;
  return html`<${PlayWays} card=${card} id=${`say:${props?.idea}:${props?.id}`} idea=${props?.idea || ""} kind="say" />`;
}

/** A descriptor's card and its ways (see the top); `card` null: it is answered and the card goes back. `id`: its key (`data-key`), `idea`: the goal it is about (ringed in the column), `kind`: its `data-kind`. */
export function PlayWays({ card: c, id, idea, kind }) {
  const box = useRef(), row = useRef(), penBtn = useRef(), wasPen = useRef(false), [pen, setPen] = useState(false);
  useLayoutEffect(() => { if (!c) lower(); }, [!c]);                          // answered (here or elsewhere): the card goes back
  useEffect(() => { if (c) playAt(c.tab, idea); }, [id]);
  useEffect(() => { setPen(false); }, [id]);
  useEffect(() => { if (wasPen.current && !pen) penBtn.current?.focus({ preventScroll: true }); wasPen.current = pen; }, [pen]);
  useRing(idea, "asks");
  const at = usePlace(box, row, [id], pen);
  useEffect(() => { box.current?.focus({ preventScroll: true }); }, [id]);
  if (!c) return null;
  const rune = { name: c.element, hue: c.hue || c.element, dim: !c.element }, s = { full: c.title };
  const own = c.pen && html`<${WayCard} key="own" w=${{ id: "own", name: c.pen.name, line: c.pen.line || OWN_LINE, sign: "text", pick: false, cost: null, run: () => setPen(!pen) }} s=${s} head=${c.head} rune=${rune} btn=${penBtn} on=${pen} />`;
  return html`<aside ref=${box} class=${`ork-card hand-card hand-card--stop hand-card--face hand-lifted hand-lifted--asked is-play asks${c.element ? ` el-${c.hue || c.element}` : ""}`} role="dialog" tabindex="-1" aria-label=${`Lifted: ${c.title}`}
      data-key=${id} data-kind=${kind} style=${at ? `left:${at.left}px` : undefined}>
    <${CornerTop} rune=${rune} kind=${c.sign} signal="alert" />
    <span class="hand-card__name" title=${c.title}>${c.title}</span>
    <span class="hand-card__foot">${c.foot}</span>
    <${CornerFoot} who=${c.head ? { heads: [c.head], word: "" } : null} />
  </aside>
  <div ref=${row} class=${`hand-ways-row is-play${pen ? " is-writing" : ""}${c.whole ? " is-whole" : ""}`} role="group" aria-label="Answers">
    <div class="hand-ways-cards">
      ${c.ways.flatMap((w, i) => [c.pen && c.pen.at === i ? own : null, html`<${WayCard} key=${w.id} w=${w} s=${s} head=${c.head} rune=${rune} />`])}
      ${c.pen && !(c.pen.at >= 0 && c.pen.at < c.ways.length) ? own : null}
    </div>
    <div class="hand-ways-acts">
      ${c.leave && html`<button type="button" class="ork-btn quiet" data-act="leave" onClick=${c.leave}>Leave it</button>`}
      ${(c.acts || []).map((a) => html`<button key=${a.id} type="button" class="ork-btn quiet" data-act=${a.id} title=${a.line || undefined} onClick=${a.run}>${a.name}</button>`)}
      <button type="button" class="ork-btn hand-put" data-act="put" onClick=${lower}>Put it back</button>
    </div>
  </div>
  ${pen && c.pen && html`<${PenField} at=${at} who=${c.pen.who} close=${() => setPen(false)} send=${c.pen.send} ask=${c.pen.ask} />`}`;
}
