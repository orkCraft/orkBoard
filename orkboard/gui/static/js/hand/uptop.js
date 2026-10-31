// The phone's top row (docs/specs/117-the-phone-a-menu-of-the-leaders.md §3, docs/mockups/phone/sidebar.html, decisions §195.3): at the left **the crown** (upmenu.js `Crown`: the Orkmaster's crowned head, 44 px; it opens the menu of the leaders),
// then **the potions as bottles** (the desktop's own: mana.js `potionOf`, `framedOf`, the bottle by §192's four sizes at the small scale, its liquid the 5 hours, the default framed, its mark small at its corner and its share under it, each a 44 px
// target; at most four places, a fifth or the paid slot makes *+n*), at the right **the die** (orkUI's, small; on a phone Play runs on the computer, so a press says so and throws nothing) and **the discard** (its top card small; a press opens the
// goals done over the pane, as the table's pile does; none while there is nothing done and nothing ready for main). Layout only (upright.css); every colour, face and corner is orkUI's.
import { html, cls } from "../html.js";
import { Head, Icon, Sign } from "../orkui.js";
import { town, toast } from "../link.js";
import { ORKMASTER, closeOver, openOver, over } from "../frame/state.js";
import { lichOf, hasDiscard } from "../table/discard.js";
import { doneOf, readyOf, readyWords } from "./data.js";
import { Who, framedOf, paidWordsOf, potionOf } from "./mana.js";
import { DieCube, asleepNow } from "./playdie.js";
import { Crown } from "./upmenu.js";

const PLACES_UP = 4;                                    // the potions' places on a phone (the desktop's six, two rows of three, do not fit a row of the top)
export const PLAY_UP = "Play it on the computer";       // the die's line on a phone

/** One tool as a bottle: its mark small at the corner, the bottle in a slot of the large one's size, its now share under it, in the warn or the danger colour as it runs low. A press opens what used it over the pane. */
function Bottle({ l, from, framed }) {
  const p = potionOf(l, null, framed);
  return html`<button type="button" class=${cls(`up-pot is-${p.level}`, { "is-default": framed })} data-provider=${l.provider} data-level=${p.level} data-size=${p.size} data-default=${framed ? "1" : undefined}
      title=${p.words} aria-label=${p.words} onClick=${() => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`)}>
    <${Who} l=${l} />
    <span class="up-pot__slot"><span class=${cls("ork-potion small", { [`size-${p.size}`]: p.size !== "large", "is-warn": p.level === "warn", "is-danger": p.level === "danger" })} style=${`--ork-potion-left:${p.liquid}`} aria-hidden="true"></span></span>
    <span class="up-pot__share">${p.share}</span>
  </button>`;
}

/** The paid slot: the tool billed by its API has no limit to pour, so the coins stand where the bottle would, *API* under them. */
function PaidBottle({ paid, from, framed }) {
  const words = paidWordsOf(paid, framed);
  return html`<button type="button" class=${cls("up-pot up-pot--paid", { "is-default": framed })} data-provider=${paid.tool} data-paid="1" data-default=${framed ? "1" : undefined} title=${words} aria-label=${words}
      onClick=${() => openOver("limits", { provider: paid.tool }, from, `${paid.name}: what used it`)}>
    <${Who} l=${{ provider: paid.tool, name: paid.name }} /><span class="up-pot__slot"><${Icon} name="coins" /></span><span class="up-pot__share">API</span>
  </button>`;
}

/** The tools' bottles, the default framed. */
function Bottles() {
  const limits = town.value?.limits || [], mana = town.value?.mana || null, paid = mana?.paid || null;
  const slots = PLACES_UP - (paid ? 1 : 0), over = limits.length > slots, shown = over ? limits.slice(0, slots - 1) : limits, more = limits.length - shown.length;
  const key = framedOf({ limits, mana, open: ORKMASTER, parties: [], shown }), from = { title: "", key: "" };         // the Board is not reached upright: the opened place says its own title
  if (!limits.length && !paid) return html`<div class="up-pots"></div>`;
  return html`<div class="up-pots" role="group" aria-label="What is left of your AI tools" data-n=${shown.length + (over ? 1 : 0) + (paid ? 1 : 0)} data-default=${key || undefined}>
    ${shown.map((l) => html`<${Bottle} key=${l.provider} l=${l} from=${from} framed=${key === l.provider} />`)}
    ${over && html`<button type="button" class="up-pot up-pot--more" title=${`${more} more tools: what is left of them`} aria-label=${`${more} more tools: what is left of them`}
      onClick=${() => openOver("limits", {}, from, "What is left of your AI tools")}><span class="up-pot__initial" aria-hidden="true">+${more}</span></button>`}
    ${paid && html`<${PaidBottle} key="paid" paid=${paid} from=${from} framed=${key === "paid"} />`}
  </div>`;
}

/** The die: orkUI's, small. On a phone Play runs on the computer, so a press says so in a line and throws nothing. */
function Die() {
  return html`<button type="button" class=${cls("up-die", { "is-asleep": asleepNow() })} aria-label=${PLAY_UP} title=${PLAY_UP} onClick=${() => toast(PLAY_UP, "information")}>
    <span class="ork-die face-5" aria-hidden="true"><${DieCube} /></span></button>`;
}

/** The discard: the last goal done face up on a small card with the backs of the others under it (its words are the table's pile's); a press opens the goals done over the pane, and again closes them. */
function Pile() {
  if (!hasDiscard()) return null;
  const top = doneOf()[0], words = readyWords(readyOf()), lit = over.value?.kind === "discard", lich = lichOf();
  const press = () => { if (lit) closeOver(); else openOver("discard", {}, null, "Done"); };
  return html`<button type="button" class=${cls("up-pile", { "is-on": lit })} aria-label=${`Done${top ? `: ${top.full}` : ""}${words ? `. ${words}` : ""}`} aria-expanded=${lit ? "true" : "false"} onClick=${press}>
    <span class="ork-card-back" aria-hidden="true"></span>
    ${top ? html`<span class="ork-card up-pile__top" aria-hidden="true"><${Sign} name="check" /></span>` : html`<span class="ork-card-back up-pile__top" aria-hidden="true"><${Head} race=${lich.race} tier=${lich.tier} /></span>`}
  </button>`;
}

/** The top row. */
export function Top() {
  return html`<div class="up-top"><${Crown} /><${Bottles} /><${Die} /><${Pile} /></div>`;
}
