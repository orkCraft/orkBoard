// The stacks (docs/specs/101 §4.3, decisions §167.7; docs/specs/98-the-table-and-the-hand.md §4.2, decisions §121.2): one a goal and a lane that has Needs you rows, under the lane of who asks (data.js `laneOf`), its most
// urgent card face up and the cards under it face down (orkUI's backs laid as a fan, five edges at most, never a number), the stacks in the order of their top cards' urgency (data.js `stacksOf`). Two goals under one lane fan within its
// width: the urgent in front at the lane's right, those behind it to the left, showing their edge and their element only, each rising whole on hover, on focus or on a tap (hand.css); the first lane's last card is the +
// card. A stack pressed picks its goal and lifts its top card (stopcard.js), answered one a press; a picked goal's stacks are lit alike (`.ork-picked`). A card that comes is dealt, a card that goes crumbles where it lay,
// none of it under reduced motion (motion.js).
import { html, cls } from "../html.js";
import { lift, lower, lifted, pick, picked } from "../frame/state.js";
import { nameOf, partiesNow } from "../table/data.js";
import { StopCard } from "./stopcard.js";
import { Shards, useDealt, useGone } from "./motion.js";
import { liftKey } from "./state.js";

const EDGES = 5;                                  // the backs under a stack's top that show (the stack's depth, never a number)
/** The fan (docs/specs/101 §7.1, decisions §168.4): a card's place behind the front one (1 the next) fixes its step aside in px and its turn in degrees, by turns right and left, never random (a redraw shakes nothing).
 *  The first two are cards seen, the rest hint at more by their edge. hand.css reads them as `--dx` and `--rot`, unitless. */
const FAN = [null, [7, 3], [-7, -3], [10, 4], [-10, -4], [9, 2]];

/** A stack's cards under its top, face down, laid as a fan. */
function Edges({ n }) {
  return Array.from({ length: n }, (_, k) => n - k).map((i) => html`<i key=${i} class="ork-card-back edge hand-back" style=${`--ork-deck-i:${i};--dx:${FAN[i][0]};--rot:${FAN[i][1]}`} aria-hidden="true"></i>`);
}

function Stack({ stack, dealt, ghost = false }) {
  const cards = useGone(stack.cards, (s) => s.key), live = cards.filter((c) => !c.gone), on = lifted.value;
  const goal = stack.goal && !stack.goal.startsWith("party:") ? stack.goal : "";
  const press = (s) => () => {
    if (ghost) return;
    if (goal && picked.value !== goal) pick(goal);                     // a stack picks its goal (§5.1); the same goal pressed again is taken off by the picked thing, not here
    if (on === liftKey(s.key)) lower(); else lift(liftKey(s.key));
  };
  if (ghost) {                                                          // the last card of the stack was answered: it crumbles where it lay
    return html`<div class="ork-deck hand-stack is-gone" data-stack=${stack.key} data-n="0"><${StopCard} s=${stack.cards[0]} gone=${true}><${Shards} /><//></div>`;
  }
  const top = live[0]?.item, under = Math.min(EDGES, Math.max(0, live.length - 1)), lit = !!goal && picked.value === goal;
  if (!top) return null;
  return html`<div class=${cls("ork-deck hand-stack", { "is-picked": lit })} data-stack=${stack.key} data-goal=${goal} data-n=${under} data-cards=${stack.cards.length}>
    <${Edges} n=${under} />
    <${StopCard} s=${top} top=${true} lit=${lit} slot=${on === liftKey(top.key)} dealt=${dealt[top.key] ?? null} onPress=${press(top)} />
    ${cards.filter((c) => c.gone).map(({ item: s }) => html`<${StopCard} key=${s.key} s=${s} gone=${true}><${Shards} /><//>`)}
  </div>`;
}

/** One place along a lane's fan (hand.css reads `--at`, the place from the lane's left, 0 the back of the fan, and `--of`, the last place: the front is at the lane's right) */
function Slot({ at, of, z, behind = false, plus = false, children }) {
  return html`<div class=${cls("hand-slot", { "is-behind": behind, "is-plus": plus })} style=${`--at:${at};--of:${of};--z:${z}`} data-at=${at}>${children}</div>`;
}

/** The lanes of the hand, one under each tab of the Board (the first the project's), each a fan of its stacks (the most urgent in front); `plus`: the + card, last of the first lane's fan. */
export function Stacks({ stacks, plus }) {
  const parties = partiesNow(), count = parties.length + 1, items = useGone(stacks, (st) => st.key), dealt = useDealt(stacks.flatMap((st) => st.cards.map((s) => s.key)));
  const lanes = Array.from({ length: count }, () => []);
  for (const it of items) lanes[Math.min(it.item.lane || 0, count - 1)].push(it);
  return lanes.map((list, i) => {
    const extra = i === 0 && plus ? 1 : 0, m = list.length + extra, solo = m === 1;
    const place = (k) => ({ at: solo ? 1 : m - 1 - k, of: solo ? 2 : m - 1, z: m - k, behind: !solo && k > 0 });
    return html`<div key=${i} class="hand-lane" data-lane=${i} role="group" aria-label=${i === 0 ? "The project’s lane" : `${nameOf(parties[i - 1])}’s lane`}>
      ${list.map(({ item: st, gone }, k) => html`<${Slot} key=${st.key} ...${place(k)}><${Stack} stack=${st} dealt=${dealt} ghost=${gone} /><//>`)}
      ${extra ? html`<${Slot} key="plus" plus=${true} ...${place(list.length)}>${plus}<//>` : null}
    </div>`;
  });
}
