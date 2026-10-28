// The stacks (docs/specs/98-the-table-and-the-hand.md §4.2, decisions §121.2): one a goal that has Needs you rows, its most urgent card face up and the cards under it
// face down (orkUI's backs, three edges at most), the stacks in the order of their top cards' urgency (data.js `stacksOf`). A stack pressed picks its goal and, with
// more than one card, fans out in place (orkUI's `.ork-fan`); a card pressed is lifted (stopcard.js) and its stack keeps its place, a dashed slot where it lay. A card
// that comes is dealt, a card that goes crumbles where it lay, none of it under reduced motion (motion.js). A stop of no goal (a sign-in) is a stack of its own.
import { useLayoutEffect, useRef } from "preact/hooks";
import { html, cls } from "../html.js";
import { lift, lower, lifted, pick, picked } from "../frame/state.js";
import { StopCard } from "./stopcard.js";
import { Shards, useDealt, useFan, useGone } from "./motion.js";
import { fanned, liftKey } from "./state.js";

const EDGES = 3;                                  // the backs under a stack's top that show (the stack's depth, never a number)

/** A stack's cards under its top, face down. */
function Edges({ n }) {
  return Array.from({ length: n }, (_, k) => n - k).map((i) => html`<i key=${i} class="ork-card-back edge hand-back" style=${`--ork-deck-i:${i}`} aria-hidden="true"></i>`);
}

function Stack({ stack, dealt, ghost = false }) {
  const open = fanned.value === stack.key && !ghost && stack.cards.length > 1, fan = useFan(open);
  const cards = useGone(stack.cards, (s) => s.key), live = cards.filter((c) => !c.gone), on = lifted.value;
  const goal = stack.goal && !stack.goal.startsWith("party:") ? stack.goal : "";
  const press = (s) => () => {
    if (ghost) return;
    if (goal && picked.value !== goal) pick(goal);                     // a stack picks its goal (§5.1); the same goal pressed again is taken off by the picked thing, not here
    if (stack.cards.length > 1 && fanned.value !== stack.key) { fanned.value = stack.key; lower(); return; }
    if (on === liftKey(s.key)) lower(); else lift(liftKey(s.key));
  };
  const lit = !!goal && picked.value === goal;
  if (fan.shown) {
    const mid = (cards.length - 1) / 2;
    return html`<div class=${cls("hand-stack ork-fan is-fanned", { closing: fan.closing })} data-stack=${stack.key} data-goal=${goal} role="group" aria-label=${`${stack.cards.length} cards of one goal`}>
      ${cards.map(({ item: s, gone }, i) => html`<div key=${s.key} class="hand-fan__card" style=${`--ork-fan-i:${i};--ork-fan-mid:${mid}`}>
        <${StopCard} s=${s} lit=${lit} slot=${on === liftKey(s.key)} gone=${gone} onPress=${press(s)} dealt=${dealt[s.key] ?? null}>${gone && html`<${Shards} />`}<//></div>`)}
    </div>`;
  }
  if (ghost) {                                                          // the last card of the stack was answered: it crumbles where it lay
    return html`<div class="ork-deck hand-stack is-gone" data-stack=${stack.key} data-n="0"><${StopCard} s=${stack.cards[0]} gone=${true}><${Shards} /><//></div>`;
  }
  const top = live[0]?.item, under = Math.min(EDGES, Math.max(0, live.length - 1));
  if (!top) return null;
  return html`<div class="ork-deck hand-stack" data-stack=${stack.key} data-goal=${goal} data-n=${under} data-cards=${stack.cards.length}>
    <${Edges} n=${under} />
    <${StopCard} s=${top} top=${true} lit=${lit} slot=${on === liftKey(top.key)} dealt=${dealt[top.key] ?? null} onPress=${press(top)} />
    ${cards.filter((c) => c.gone).map(({ item: s }) => html`<${StopCard} key=${s.key} s=${s} gone=${true}><${Shards} /><//>`)}
  </div>`;
}

/** The hand's middle: every stack, the most urgent first. Nothing when nothing waits. */
export function Stacks({ stacks }) {
  const items = useGone(stacks, (st) => st.key), dealt = useDealt(stacks.flatMap((st) => st.cards.map((s) => s.key))), box = useRef(), came = Object.keys(dealt).join("|");
  useLayoutEffect(() => {                                                    // a card is dealt from the deck: orkUI's deal starts it where the deck lies
    const deck = document.querySelector(".hand-deckback")?.getBoundingClientRect();
    if (!deck || !box.current) return;
    for (const el of box.current.querySelectorAll(".ork-deal")) {
      const r = el.getBoundingClientRect();
      el.style.setProperty("--ork-deal-x", `${deck.left - r.left}px`);
      el.style.setProperty("--ork-deal-y", `${deck.top - r.top}px`);
    }
  }, [came]);
  return html`<div ref=${box} class="hand-stacks" role="group" aria-label="The stacks">
    ${items.map(({ item: st, gone }) => html`<${Stack} key=${st.key} stack=${st} dealt=${dealt} ghost=${gone} />`)}
  </div>`;
}
