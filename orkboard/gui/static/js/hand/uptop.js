// The phone's top row, the header (docs/specs/117-the-phone-a-menu-of-the-leaders.md §3, decisions §195.3, §292.3; goal 169 H after docs/mockups/phone/feed.html v3, screens 7 and 8): at the left **the crown** (upmenu.js `Crown`: the Orkmaster's crowned head, 44 px; it opens
// the menu of the leaders), **the project's name** (pressed: *Switch project*, as the menu's), **Settings** and **Stop all** (`halt`, door.js, as the menu's, which stays: no confirm, in the danger's colour), then **the potions as bottles** (the desktop's own: mana.js `potionOf`, `framedOf`, the bottle by
// §192's four sizes at the small scale, its liquid the 5 hours, the default framed, its mark small at its corner and its share under it, each a 44 px target; at most four places, a fifth or the paid slot makes *+n*), **the lamp's chain** hung from the header beside the bottles (orkUI's
// cartoon chain, short at rest, pulled while away, its word *Here* or *Away* at its bead: table/presence.js `PresenceChain` with `pic`; none from a host that does not say) and **the discard** (its top card small; a press opens the goals done over the pane, as the table's pile does;
// none while there is nothing done and nothing ready for main). The die and the backpack left it for the round button at the foot's right (upround.js, §292.1). Where the row is short of room the project's name, then Settings, give way first (the menu keeps both).
// **Scrolled** (§291.5, §292.3), the middle's heads go with the feed and the row folds to one thin row of the bottles, Stop all and the chain (`is-thin`); back near the top it unfolds. The row stands above the middle, never over it, and the middle's `scroll-padding-top` is the thin
// row's height: a block the focus moves to is never under the header (WCAG 2.4.11). Layout only (upright.css); every colour, face and corner is orkUI's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head, Icon, Sign } from "../orkui.js";
import { town } from "../link.js";
import { ORKMASTER, closeOver, openOver, over } from "../frame/state.js";
import { lichOf, hasDiscard } from "../table/discard.js";
import { halt } from "../table/door.js";
import { currentProject } from "../shell/projects.js";
import { doneOf, readyOf, readyWords } from "./data.js";
import { Who, framedOf, paidWordsOf, potionOf } from "./mana.js";
import { STOP_WORDS } from "./playdie.js";
import { Crown, menuOpen } from "./upmenu.js";
import { PresenceChain } from "../table/presence.js";

export { PLAY_UP } from "./upround.js";
const PLACES_UP = 4;                                    // the potions' places on a phone (the desktop's six, two rows of three, do not fit a row of the top)
export const FOLD_AT = 48, FOLD_BACK = 8;               // the middle scrolled past 48 px folds the row; back within 8 px of its top it unfolds
const ROOM = 64;                                        // the least the project's name is drawn at

/** One tool as a bottle: its mark small at the corner, the bottle in a slot of the large one's size, its now share (at the danger's level *back 14:00*, spec 138 A.5; an unread tool no bottle, spec 140 C1) under it, in the warn or the danger colour as it runs low. A press opens what used it over the pane. */
function Bottle({ l, from, framed }) {
  const p = potionOf(l, null, framed);
  return html`<button type="button" class=${cls(`up-pot is-${p.level}`, { "is-default": framed })} data-provider=${l.provider} data-level=${p.level} data-size=${p.size} data-default=${framed ? "1" : undefined}
      title=${p.words} aria-label=${p.words} onClick=${() => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`)}>
    <${Who} l=${l} />
    <span class="up-pot__slot">${p.read && html`<span class=${cls("ork-potion small", { [`size-${p.size}`]: p.size !== "large", "is-warn": p.level === "warn", "is-danger": p.level === "danger" })} style=${`--ork-potion-left:${p.liquid}`} aria-hidden="true"></span>`}</span>
    <span class="up-pot__share">${p.back ? `back ${p.back}` : p.share}</span>
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

/** Whether the middle is scrolled past the fold: the middle (`.up-look`, the feed or a goal) is read on every scroll and whenever the row is drawn again (a new middle starts at its top). */
function useFold(row) {
  const [thin, setThin] = useState(false);
  useEffect(() => {
    const hand = row.current?.closest(".hand-up");
    if (!hand) return undefined;
    const on = (e) => { const t = e.target; if (t instanceof Element && t.classList.contains("up-look")) setThin((was) => (was ? t.scrollTop > FOLD_BACK : t.scrollTop > FOLD_AT)); };
    hand.addEventListener("scroll", on, true);
    return () => hand.removeEventListener("scroll", on, true);
  }, []);
  useLayoutEffect(() => {
    const look = row.current?.closest(".hand-up")?.querySelector(".up-look");
    if (thin && (!look || look.scrollTop <= FOLD_BACK)) setThin(false);
  });
  return thin;
}

/** What the row has room for: all, or Settings given way (`name`), or the name too (`none`); read from the drawn row, again when its width changes. */
function useRoom(row) {
  useLayoutEffect(() => {
    const el = row.current;
    if (!el) return undefined;
    const fit = () => {
      el.dataset.fit = "all";
      const name = () => el.querySelector(".up-name")?.getBoundingClientRect().width ?? ROOM;
      if (name() < ROOM) { el.dataset.fit = "name"; if (name() < ROOM) el.dataset.fit = "none"; }
    };
    fit();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(fit) : null;
    ro?.observe(el);
    return () => ro?.disconnect();
  });
}

/** The top row. */
export function Top() {
  const row = useRef(), thin = useFold(row), project = currentProject.value?.name || "The project", from = { title: "", key: "" }, inert = menuOpen.value;
  useRoom(row);
  return html`<div ref=${row} class=${cls("up-top", { "is-thin": thin })} data-thin=${thin ? "1" : undefined}>
    <${Crown} />
    <button type="button" class="up-name" inert=${inert || undefined} aria-hidden=${inert ? "true" : undefined} aria-label=${`Switch project: ${project}`} title="Switch project" onClick=${() => openOver("projects", {}, from, "Projects")}><span>${project}</span></button>
    <button type="button" class="up-ico up-set" inert=${inert || undefined} aria-hidden=${inert ? "true" : undefined} aria-label="Settings" title="Settings" onClick=${() => openOver("settings", {}, from, "Settings")}><${Icon} name="sliders" /></button>
    <button type="button" class="up-ico up-stop" inert=${inert || undefined} aria-hidden=${inert ? "true" : undefined} aria-label="Stop all" title=${STOP_WORDS} onClick=${() => halt()}><${Icon} name="boarded" /></button>
    <${Bottles} /><${PresenceChain} pic=${true} /><${Pile} />
  </div>`;
}
