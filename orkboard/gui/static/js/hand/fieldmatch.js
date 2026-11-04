// The new-goal field's line when the goal sent looks like part of one lying face down (docs/specs/135-a-new-goal-matched-against-the-face-down-pile.md §A.5; decisions §242.1–§242.2): `ideas.add {match: true}` answers
// `{slug: "", match: {idea, title, party, state, score, why, shared, adds, reworded, cost: {calls, usd_high} | null}}` and adds nothing; the field (pluscard.js) stays open, its words, its rune and its files kept, and says under the
// text one line, *Looks like part of: <title>*, with two buttons: **Add to it** (`ideas.add_to_goal`, its cost under it when the goal's decision is worded again: *about <n>% of Claude's week*, cost.js) and **Keep apart** (the goal
// is sent as it is, with `apart`). Neither closes the field but by doing its work. The phone's field is this one (updeck.js). No toast, no count, no card of its own.
import { html } from "../html.js";
import { costOf } from "./cost.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as changecard.js links its own
  const href = new URL("./fieldmatch.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** What *Add to it* costs, in words (*about 4% of Claude's week*), "" when it costs nothing (the goal has no decision worded yet). */
export function addCostWords(match) {
  const usd = Number(match?.cost?.usd_high);
  if (!(usd > 0)) return "";
  return costOf({ kind: "plan", node: { plan_estimate: { usd_low: usd, usd_high: usd } } })?.words || "";
}

/** The line and its two buttons. `match`: the host's; `onAdd`, `onApart`: the two answers; `busy`: one is going. */
export function MatchLine({ match, busy, onAdd, onApart }) {
  const cost = addCostWords(match);
  return html`<div class="hand-field__match" role="group" aria-label="Looks like part of another goal" data-match=${match.idea}>
    <p class="body hand-field__looks" data-part="looks">Looks like part of: <b>${match.title}</b></p>
    <div class="hand-field__match-acts">
      <span class="hand-field__match-add"><button type="button" class="ork-btn primary" data-act="add-to-it" disabled=${busy} title="The words join that goal" onClick=${onAdd}>Add to it</button>
        ${cost && html`<span class="cap" data-part="cost">${cost}</span>`}</span>
      <button type="button" class="ork-btn" data-act="keep-apart" disabled=${busy} title="It goes on as a goal of its own" onClick=${onApart}>Keep apart</button>
    </div>
  </div>`;
}
