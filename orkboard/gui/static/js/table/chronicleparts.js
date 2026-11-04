// What the chronicle (chronicle.js) is drawn of: a call to the host, a goal's row and a decision's row (docs/specs/134 part B). A goal's row is pressed to open the goal as it was; the decision it carries is a small link beside it
// (§238.4: a decision a goal carries stands under its goal's row, not in the list); a decision of no goal is a row of its own. Colours and corners are orkUI's (chronicle.css).
import { html } from "../html.js";
import { Elem } from "../orkui.js";
import { command } from "../link.js";
import { dayWord } from "./chroniclewords.js";

export const COULD_NOT = "The chronicle could not be read";

/** One call to the host, its refusal in words: `[data, err]`. */
export async function ask(name, args) {
  try {
    const r = await command(name, args, true);
    return r && !r.error ? [r, ""] : [null, r?.error || COULD_NOT];
  } catch (e) { return [null, e?.message && e.message !== "offline" ? e.message : COULD_NOT]; }
}

const IN = { title: "its name", spec: "its spec", decision: "its decision" };

/** A goal that went through the portal: its rune, name and day; `found` (a search's find) says where the words were; `g.decision` the number of the decision it carries. */
export function GoalRow({ g, found = false, onGoal, onDecision }) {
  return html`<li class="chr-row" data-goal=${g.idea}>
    <button type="button" class="ork-row chr-row__btn" onClick=${() => onGoal(g.idea)}>
      <${Elem} name=${g.element || ""} hue=${g.hue || ""} dim=${!g.element} /><span class="chr-row__nm">${g.title}</span>
      ${found && g.in?.length ? html`<span class="chr-row__in">in ${g.in.map((k) => IN[k] || k).join(", ")}</span>` : html`<span class="chr-row__day">${dayWord(g.day)}</span>`}</button>
    ${g.decision > 0 && html`<button type="button" class="ork-btn quiet chr-row__dec" data-decision=${g.decision} aria-label=${`Decision ${g.decision}`} onClick=${() => onDecision(g.decision)}>§${g.decision}</button>`}
  </li>`;
}

/** A decision of no goal (a hypothesis's verdict, a cascade): its number, title and day. */
export function DecisionRow({ d, onDecision }) {
  return html`<li class="chr-row" data-decision-row=${d.number}>
    <button type="button" class="ork-row chr-row__btn" onClick=${() => onDecision(d.number)}>
      <span class="chr-row__num">§${d.number}</span><span class="chr-row__nm">${d.title}</span><span class="chr-row__day">${dayWord(d.day)}</span></button>
  </li>`;
}
