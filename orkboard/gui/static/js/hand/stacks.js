// The stacks (docs/specs/101 §4.3, decisions §167.7; docs/specs/98-the-table-and-the-hand.md §4.2, decisions §121.2): one a goal and a lane that has Needs you rows, under the lane of who asks (data.js `laneOf`), its most
// urgent card face up and the cards under it face down (orkUI's backs laid as a fan, five edges at most, never a number), the stacks in the order of their top cards' urgency (data.js `stacksOf`). Two goals under one lane fan within its
// width: the urgent in front at the lane's right, those behind it to the left, showing their edge and their element only, each rising whole on hover, on focus or on a tap (hand.css); the + card lies whole at the first lane's left end, not in its fan. A stack pressed picks its goal and lifts its top card (stopcard.js), answered one a press; a picked goal's stacks are lit alike (`.ork-picked`). A card that comes is dealt, from the card of the task that asks or failed (a failure is thrown from its lane's card, which leaves a place: table/flight.js `useThrown`; hand.js), a card that goes crumbles where it lay
// (an answered one flies back into its goal's card), none of it under reduced motion (motion.js).
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { lift, lower, lifted, pick, picked } from "../frame/state.js";
import { nameOf, partiesNow } from "../table/data.js";
import { StopCard, askerOf, handsWords, whoOf } from "./stopcard.js";
import { goalOfStop, lieBehind } from "./data.js";
import { mapData } from "../shell/store.js";
import { Shards, fromWhere, useGone, useHanded } from "./motion.js";
import { liftKey } from "./state.js";

const EDGES = 5;                                  // the backs under a stack's top that show (the stack's depth, never a number)
/** The fan (docs/specs/101 §7.1, decisions §168.4): a card's place behind the front one (1 the next) fixes its step aside in px and its turn in degrees, by turns right and left, never random (a redraw shakes nothing).
 *  The first two are cards seen, the rest hint at more by their edge. hand.css reads them as `--dx` and `--rot`, unitless. */
const FAN = [null, [7, 3], [-7, -3], [10, 4], [-10, -4], [9, 2]];

/** A stack's cards under its top, face down, laid as a fan. (Only a stack's top card is handed: the cards under it lie as edges, so a stack that grows plays one flight.) */
function Edges({ n }) {
  return Array.from({ length: n }, (_, k) => n - k).map((i) => html`<i key=${i} class="ork-card-back edge hand-back" style=${`--ork-deck-i:${i};--dx:${FAN[i][0]};--rot:${FAN[i][1]}`} aria-hidden="true"></i>`);
}

/** Who plays a stop and where it comes from and goes back to (`whoOf`, and its task: the card of the task that asks or failed is the origin, not the first card of its goal: spec 128 C). */
const whereOf = (s) => ({ ...whoOf(s), task: s.task?.id || s.row?.task || "" });

/** Where an answered card goes back to, the element of its origin; none for a card whose goal is gone (a dropped one crumbles where it lay: flying back means *answered*, crumbling *gone*) and for one with no origin in view (spec 120 §6.10). */
function backTo(s) {
  const goal = goalOfStop(s);
  if (goal && !(mapData.value?.nodes || []).some((n) => n.slug === goal)) return null;
  return fromWhere(whereOf(s))?.el || null;
}

function Stack({ stack, dealt, ghost = false }) {
  const cards = useGone(stack.cards, (s) => s.key), live = cards.filter((c) => !c.gone), on = lifted.value;
  const goal = stack.goal && !stack.goal.startsWith("party:") ? stack.goal : "";
  const press = (s) => () => {
    if (ghost) return;
    if (goal && picked.value !== goal) pick(goal);                     // a card lifted picks its goal, never toggling it off (spec 155 B.4); its lowering leaves the pick, which the same card of the column, Esc, an empty press or the back put away
    if (on === liftKey(s.key)) lower(); else lift(liftKey(s.key));
  };
  if (ghost) {                                                          // the last card of the stack was answered: it crumbles where it lay
    const to = backTo(stack.cards[0]);
    return html`<div class="ork-deck hand-stack is-gone" data-stack=${stack.key} data-n="0"><${StopCard} s=${stack.cards[0]} gone=${true} back=${to}>${!to && html`<${Shards} />`}<//></div>`;
  }
  const top = live[0]?.item, under = Math.min(EDGES, Math.max(0, live.length - 1)), lit = !!goal && picked.value === goal;
  if (!top) return null;
  return html`<div class=${cls("ork-deck hand-stack", { "is-picked": lit })} data-stack=${stack.key} data-goal=${goal} data-n=${under} data-cards=${stack.cards.length}>
    <${Edges} n=${under} />
    <${StopCard} s=${top} top=${true} lit=${lit} slot=${on === liftKey(top.key)} dealt=${dealt[top.key] ?? null} onPress=${press(top)} />
    ${cards.filter((c) => c.gone).map(({ item: s }) => { const to = backTo(s); return html`<${StopCard} key=${s.key} s=${s} gone=${true} back=${to}>${!to && html`<${Shards} />`}<//>`; })}
  </div>`;
}

/** One place along a lane's fan (hand.css reads `--at`, the place from the lane's left, 0 the back of the fan, and `--of`, the last place: the front is at the lane's right) */
function Slot({ at, of, z, behind = false, plus = false, children }) {
  return html`<div class=${cls("hand-slot", { "is-behind": behind, "is-plus": plus })} style=${`--at:${at};--of:${of};--z:${z}`} data-at=${at}>${children}</div>`;
}

/** The leader of a lane, for the narrow hand laid by leader (spec 147 C.4): a 22 px separator with the leader's 16 px head before the lane's cards, the Orkmaster's crowned head for the first lane (the column's). It is not drawn at the wide width, where the lane is the leader's. */
export const laneHead = (lane, party) => (lane === 0 ? { race: "peon", tier: "crown" } : party?.leader?.head || null);      // the head before a lane's cards on the narrow page and the phone (the phone's row: uprow.js)
function Sep({ lane, party }) {
  const h = laneHead(lane, party);
  return html`<span class="hand-sep" data-lane=${lane} aria-hidden="true">${h && html`<${Head} race=${h.race} tier=${h.tier} />`}</span>`;
}

/** The lanes of the hand, one under each tab of the Board (the first the project's), each a fan of its stacks (the most urgent in front); `plus`: the + card, which lies whole at the first lane's left end, never in its fan
 *  (spec 107 §13.2, decisions §182.4): the first lane's stacks fan to its right (hand.css gives the lane the room when it has any). */
export function Stacks({ stacks, plus }) {
  const parties = partiesNow(), count = parties.length + 1, items = useGone(stacks, (st) => st.key),
    dealt = useHanded(stacks.flatMap((st) => st.cards.map((s, at) => ({ key: s.key, top: at === 0, ...whereOf(s), name: askerOf(s), words: handsWords(s) }))));
  const lanes = Array.from({ length: count }, () => []);
  for (const it of items) lanes[Math.min(it.item.lane || 0, count - 1)].push(it);
  const last = lanes[count - 1];
  for (const l of lanes) l.sort((a, b) => Number(lieBehind(a.item)) - Number(lieBehind(b.item)));         // a goal's own stack in front of a party's question that blocks nothing (spec 143 E.2); what blocks keeps its urgency's place
  last.sort((a, b) => Number(lieBehind(a.item)) - Number(lieBehind(b.item)) || Number(!!b.item.road) - Number(!!a.item.road));                 // Release's and Live's stacks (no lane of their own at the wide width) lie at the last lane's right end, in front (spec 111 §4.1)
  return lanes.map((list, i) => {
    const m = list.length, solo = m === 1;
    const place = (k) => ({ at: solo ? 1 : m - 1 - k, of: solo ? 2 : m - 1, z: m - k, behind: !solo && k > 0 });
    return html`<div key=${i} class="hand-lane" data-lane=${i} role="group" aria-label=${i === 0 ? "The project’s lane" : `${nameOf(parties[i - 1])}’s lane`}>
      ${i === 0 && plus ? html`<${Slot} key="plus" plus=${true} at=${0} of=${1} z=${m + 2}>${plus}<//>` : null}
      ${m ? html`<${Sep} key="sep" lane=${i} party=${parties[i - 1]} />` : null}
      ${list.map(({ item: st, gone }, k) => html`<${Slot} key=${st.key} ...${place(k)}><${Stack} stack=${st} dealt=${dealt} ghost=${gone} /><//>`)}
    </div>`;
  });
}
