// What the past (chronicle.js) is drawn of: a call to the host, the open tab's party, and the cards it deals (docs/specs/150 E2.2, decisions §254.7; docs/specs/134 part B). A goal that went through the portal is a card (its rune, the sign `check`, its name,
// its day, the version it went out in at its bottom right); a decision of no goal is a card of its own (the sign `page`, *§<n>*); the decision a goal carries is a small link beside its card (§238.4: it does not stand in the deal twice).
// A card is pressed to be lifted: the goal as it was or the decision's entry (chroniclerows.js). Colours and corners are orkUI's (chronicle.css).
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { command } from "../link.js";
import { ORKMASTER, tab } from "../frame/state.js";
import { nameOf, partiesAll } from "./data.js";
import { dayWord } from "./chroniclewords.js";

export const COULD_NOT = "The past could not be read";

/** One call to the host, its refusal in words: `[data, err]`. */
export async function ask(name, args) {
  try {
    const r = await command(name, args, true);
    return r && !r.error ? [r, ""] : [null, r?.error || COULD_NOT];
  } catch (e) { return [null, e?.message && e.message !== "offline" ? e.message : COULD_NOT]; }
}

/** The past is read through the open tab: `{party, name}`, the party's slug and its name (*Design*), both "" on the Orkmaster's tab. Read in a component, it follows the tab. */
export function whose() {
  const t = tab.value, g = t && t !== ORKMASTER ? partiesAll().find((x) => x.slug === t) : null;
  return g ? { party: g.slug, name: nameOf(g) } : { party: "", name: "" };
}

const IN = { title: "its name", spec: "its spec", decision: "its decision" };

/** A card of the deal. `item`: `{type: "goal" | "decision", id, title, element, hue, day, decision, in}`, `version`: the deck it lies in (its bottom right). `lit`: the card a pick marks. */
export function Card({ item, version = "", found = false, lit = false, onOpen, onDecision }) {
  const goal = item.type === "goal", mark = goal ? { "data-goal": item.id } : { "data-decision-row": item.id };
  return html`<li class=${cls("chr-card-wrap", { "is-lit": lit })} data-lit=${lit ? "1" : undefined} ...${mark}>
    <button type="button" class="ork-card chr-card" onClick=${() => onOpen(item)} aria-label=${goal ? item.title : `§${item.id} ${item.title}`}>
      <span class="corner corner--top"><span class="corner__rune"><${Elem} name=${item.element || ""} hue=${item.hue || ""} dim=${!item.element} /></span><span class="corner__kind"><${Sign} name=${goal ? "check" : "page"} /></span></span>
      <span class="chr-card__nm">${goal ? "" : html`<span class="chr-card__num">§${item.id}</span> `}${item.title}</span>
      <span class="chr-card__day">${found && item.in?.length ? `in ${item.in.map((k) => IN[k] || k).join(", ")}` : dayWord(item.day)}</span>
      <span class="corner corner--foot"><span class="corner__who"></span>${version && html`<span class="corner__much" data-much="version">${version}</span>`}</span>
    </button>
    ${goal && item.decision > 0 && html`<button type="button" class="ork-btn quiet chr-card__dec" data-decision=${item.decision} aria-label=${`Decision ${item.decision}`} onClick=${() => onDecision(item.decision)}>§${item.decision}</button>`}
  </li>`;
}

/** A deck: a version's (or the week's, or the unreleased) pile, its name and its day; pressed it deals its cards, pressed again it is put away. `dim`: a search found nothing in it. */
export function Deck({ deck, on = false, dim = false, onPress }) {
  return html`<button type="button" class=${cls("chr-deck", { "is-on": on, "is-dim": dim })} data-deck=${deck.id} aria-pressed=${String(on)} onClick=${onPress}>
    <b class="chr-deck__nm">${deck.name}</b><small class="chr-deck__day">${deck.day}</small></button>`;
}
