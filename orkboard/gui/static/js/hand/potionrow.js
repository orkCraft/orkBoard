// The potions in a row (docs/specs/168-the-window-played-as-a-card-games-table.md A4, decisions §285.1, §284.3; before it the drum, §261.13, §262.1): at 760 px and up, at the left of the right column's head (table/lane.js), **three bottles at most** whose tops stand on one line
// (`align-items: flex-start`): the tool the open tab's work goes to (the picked goal at work's tool, else the open tab's: `activeTool`), then any tool at the warn or the danger level, then the others in the person's order (`tools.order`). **Nothing the person does reorders the row.**
// Each bottle is orkUI's `.ork-potion.small` (2 px a cell) in its week's size (`size-medium|small|vial`, spec 114), its 5 hours' share under it (*62%*, *out* while a window is at 0); **under a bottle smaller than the large the week's share too** (*week*, *30%*): its size is
// the week's, said where it has shrunk and nowhere else. The tool the work goes to has its share in the ink, a tool at warn or danger in that level's colour (decisions §262.1); a press lifts the tool's card (as the unrolled row's); a bottle hovered or focused lights the column's cards and
// outlines its marks on the tabs (`litTool`, `markedTool`); a card lifted or hovered that spends hatches its share (`liftedStop`, `hatched`).
// **Hovered or focused, the row unrolls** (`data-open`, Esc or the pointer leaving folds it): `.pots__all` (always drawn, hidden until then) under the head lists every tool as `Pot` (its mark, its size, *back 14:00* at the danger's level, a drag in it changes `tools.order`), the paid slot and the empty slot at its end. Layout: potions.css.
import { useEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { town } from "../link.js";
import { mapName, openTabOf, partiesAll } from "../table/data.js";
import { tab, openOver } from "../frame/state.js";
import { TOOL, hatched, litTool, markedDefault, markedTool } from "./state.js";
import { setupNow } from "./setupcards.js";
import { costOf } from "./cost.js";
import { EmptySlot, PaidPot, Pot, Who, activeTool, paidWordsOf, potionOf, potionsOf, toggleLift, useDragOrder, usesWords } from "./mana.js";

if (typeof document !== "undefined") {
  const href = new URL("./potions.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const ROW_MAX = 3;
export const ALERT_LEVELS = ["warn", "danger"];
export const liftedStop = signal(null);          // the stop lifted in the hand (hand.js sets it): the row's potion of the tool it takes from hatches that share

/** Which tools stand in the row, in order: `wanted` (the tool the work goes to) first, then the tools at the warn or the danger level, then the person's order (`limits` as given), `max` at most. Pure: `levelOf` says a tool's level. */
export function rowOf(limits, wanted, levelOf, max = ROW_MAX) {
  const first = limits.filter((l) => l.provider === wanted), rest = limits.filter((l) => l.provider !== wanted);
  const alert = rest.filter((l) => ALERT_LEVELS.includes(levelOf(l))), calm = rest.filter((l) => !ALERT_LEVELS.includes(levelOf(l)));
  return [...first, ...alert, ...calm].slice(0, max);
}

/** The 5 hours' share a bottle says under it: *out* while a window is at 0, else the share. */
export const fiveOf = (p) => (p.dry ? "out" : p.share);

/** One bottle of the row: orkUI's small potion in its size, its shares under it (the week's too under a bottle smaller than the large). */
function Bottle({ l, p, front, from, tools }) {
  const small = p.size !== "large" && p.weekShare, style = `--ork-potion-left:${p.liquid}${p.took ? `;--ork-potion-spend:${p.spend}` : ""}`;
  const mark = () => { markedTool.value = l.provider; markedDefault.value = front; litTool.value = l.provider; };
  const unmark = () => { if (markedTool.value === l.provider) { markedTool.value = ""; markedDefault.value = false; } if (litTool.value === l.provider) litTool.value = ""; };
  return html`<button type="button" class=${cls(`pot-s is-${p.level}`, { "is-front": front, "is-dry": p.dry })} data-provider=${l.provider} data-level=${p.level} data-size=${p.size} data-front=${front ? "1" : undefined}
      title=${p.words} aria-label=${p.words} onClick=${tools ? () => toggleLift(`${TOOL}${l.provider}`) : () => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`)}
      onPointerEnter=${mark} onPointerLeave=${unmark} onFocus=${mark} onBlur=${unmark}>
    ${p.read ? html`<span class=${cls("ork-potion small", { [`size-${p.size}`]: p.size !== "large", "is-warn": p.level === "warn", "is-danger": p.level === "danger" })} style=${style} aria-hidden="true"></span>`
      : html`<span class="pot-s__none" aria-hidden="true"><${Who} l=${l} /></span>`}
    <span class="pot-s__cap"><b class="pot-s__five">${p.read ? fiveOf(p) : ""}</b>${small && html`<span class="pot-s__week">week</span><span class="pot-s__week">${p.weekShare}</span>`}</span>
  </button>`;
}

/** The paid slot in the row: the coins where a bottle would stand, *API* under it. */
function PaidBottle({ paid, from, front }) {
  const words = paidWordsOf(paid);
  return html`<button type="button" class=${cls("pot-s is-paid", { "is-front": front })} data-provider=${paid.tool} data-paid="1" title=${words} aria-label=${words} onClick=${() => openOver("limits", { provider: paid.tool }, from, `${paid.name}: what used it`)}>
    <span class="pot-s__none" aria-hidden="true"><${Who} l=${{ provider: paid.tool, name: paid.name }} /></span><span class="pot-s__cap"><b class="pot-s__five">API</b></span></button>`;
}

/** The row, and the whole list unrolled under it. `above`: the list unrolls upward (the row has no room under it: the hand's, before the table is laid). */
export function PotionRow({ above = false }) {
  const box = useRef(), [out, setOut] = useState(false), tools = town.value?.tools || null, limits = potionsOf(town.value?.limits || [], tools), mana = town.value?.mana || null, paid = mana?.paid || null, empty = !!tools && !tools.full, drag = useDragOrder(tools);
  const parties = partiesAll(), open = openTabOf(tab.value, parties), lifted = liftedStop.value;
  useEffect(() => {                                                                                       // Esc folds the list, the pointer leaving it too (below)
    if (!out) return undefined;
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented) { setOut(false); e.preventDefault(); if (box.current?.contains(document.activeElement)) document.activeElement.blur(); } };
    document.addEventListener("keydown", esc, true);
    return () => document.removeEventListener("keydown", esc, true);
  }, [out]);
  if (!limits.length && !paid && !empty) return null;
  const cost = lifted ? costOf(lifted) : hatched.value, from = { title: mapName(tab.value, parties), key: "" };
  const by = new Map(limits.map((l) => { const hit = cost && cost.tool === l.provider; return [l.provider, { ...potionOf(l, hit ? cost : null, false, usesWords(l.provider, parties)), spend: hit ? cost.spend : 0 }]; }));
  const members = paid && !limits.some((l) => l.provider === paid.tool) ? [...limits, { provider: paid.tool, name: paid.name, paid: true }] : limits;
  const wanted = activeTool({ limits, mana, open, parties }), shown = rowOf(members, wanted, (l) => (l.paid ? "ok" : by.get(l.provider).level));
  const fold = (e) => { if (!e.relatedTarget || !box.current?.contains(e.relatedTarget)) setOut(false); };
  return html`<div class="pots" ref=${box} role="group" aria-label="What is left of your AI tools" data-open=${out ? "1" : undefined} data-above=${above ? "1" : undefined}
      onPointerEnter=${(e) => { if (e.pointerType !== "touch") setOut(true); }} onPointerLeave=${() => { if (!drag.busy()) setOut(false); }} onFocusIn=${() => setOut(true)} onFocusOut=${fold}>
    <div class="pots__row">
      ${shown.map((l) => (l.paid ? html`<${PaidBottle} key=${l.provider} paid=${paid} from=${from} front=${l.provider === wanted} />` : html`<${Bottle} key=${l.provider} l=${l} p=${by.get(l.provider)} front=${l.provider === wanted} from=${from} tools=${tools} />`))}
      ${!members.length && empty && html`<${EmptySlot} key="empty" lit=${setupNow.value?.step === "tools"} small=${true} />`}
    </div>
    <div class="pots__all" role="group" aria-label="Every AI tool">
      ${limits.map((l) => html`<${Pot} key=${l.provider} l=${l} cost=${cost} small=${false} from=${from} framed=${false} front=${l.provider === wanted} parties=${parties} onPress=${tools ? () => toggleLift(`${TOOL}${l.provider}`) : null} drag=${tools ? drag(l.provider) : null} />`)}
      ${paid && html`<${PaidPot} key="paid" paid=${paid} from=${from} framed=${false} />`}
      ${empty && members.length > 0 && html`<${EmptySlot} key="empty" lit=${setupNow.value?.step === "tools"} small=${false} />`}
    </div>
  </div>`;
}
