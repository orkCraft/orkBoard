// The mana (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §3, decisions §175.2, §176.1–§176.2): the AI tools' limits as potions at the hand's right end, flush against the window's edge.
// One potion (orkUI's `.ork-potion`) a tool, in the order the chips had: above it the tool's mark in its own colour (the tool's initial in the body face with no mark), under it the share left, in the warn or the danger colour at
// those levels (`levelOf`). One to three tools lie in one row at the default size; four to six in two rows of three, small; more than six: the first five and a sixth place *+n* that opens all of them over the pane. At the narrow
// width (under 760 px, spec 94) every potion is small.
// A potion is a button, its words the chip's (*Claude Code: 62% of the week left*, `windowOf`); a press opens what used it over the pane, as the chip did. A tool whose limits were not read is an empty potion with *?*.
// A card lifted that spends (`costOf`) hatches its share off its tool's top, and the share reads `62% −4%`. The words are said on the control, the potion itself is `aria-hidden` (orkUI's potion/README.md).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { ORKUI } from "../orkui.js";
import { town } from "../link.js";
import { levelOf, windowOf } from "../arena/limits.js";
import { MARKED, mapName, partiesNow } from "../table/data.js";
import { openOver, tab } from "../frame/state.js";
import { costOf } from "./cost.js";

export const PLACES = 6;                              // the potions' places: two rows of three
const NARROW = "(max-width: 759px)";                  // spec 94: the phone's width is the narrow one

function useNarrow() {
  const [narrow, set] = useState(() => typeof matchMedia === "function" && matchMedia(NARROW).matches);
  useEffect(() => {
    if (typeof matchMedia !== "function") return undefined;
    const m = matchMedia(NARROW), on = () => set(m.matches);
    m.addEventListener("change", on);
    on();
    return () => m.removeEventListener("change", on);
  }, []);
  return narrow;
}

/** The window a tool's share is of, in words: *the week*, *the 5-hour window*, *the day*. */
export function windowWords(win) {
  return { week: "the week", "5h": "the 5-hour window", daily: "the day", day: "the day" }[win] || (win ? `the ${win} window` : "");
}

/** What a tool's potion says: `{read, share, level, took, words}`; `cost` (from `costOf`) is the lifted card's, when it takes from this tool. */
export function potionOf(l, cost = null) {
  const read = typeof l.left === "number", win = read ? windowWords(windowOf(l)) : "";
  const share = read ? `${Math.round(l.left * 100)}%` : "?", level = read ? levelOf(l.left) : "unread";
  const took = read && cost?.spend ? cost.taken : "";
  const left = read ? `${l.name}: ${share} ${win ? `of ${win} ` : ""}left` : `${l.name}: limits not read yet`;
  return { read, share, level, took, words: took ? `${left}. This card takes about ${took} of it` : left };
}

/** One tool's mark in its own colour (orkUI's `marks/harness-<id>.png`, not the ink one); its initial in the body face with no mark. */
function Who({ l }) {
  return MARKED.includes(l.provider)
    ? html`<img class="ork-mark" src=${`${ORKUI}/marks/harness-${l.provider}.png`} srcset=${`${ORKUI}/marks/harness-${l.provider}@2x.png 2x`} alt="" draggable="false" />`
    : html`<span class="hand-pot__initial" aria-hidden="true">${(l.name || l.provider || "?").charAt(0).toUpperCase()}</span>`;
}

function Pot({ l, cost, small, from }) {
  const p = potionOf(l, cost && cost.tool === l.provider ? cost : null);
  const style = `--ork-potion-left:${p.read ? l.left : 0}${p.took ? `;--ork-potion-spend:${cost.spend}` : ""}`;
  return html`<button type="button" class=${cls("hand-pot", `is-${p.level}`)} data-provider=${l.provider} data-level=${p.level} title=${p.words} aria-label=${p.words}
      onClick=${() => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`)}>
    <${Who} l=${l} />
    <span class=${cls("ork-potion", { small, "is-warn": p.level === "warn", "is-danger": p.level === "danger" })} style=${style} aria-hidden="true"></span>
    <span class="hand-pot__share">${p.share}${p.took && html` <span class="hand-pot__took">−${p.took}</span>`}</span>
  </button>`;
}

/** The potions. `lifted`: the stop now lifted in the hand, whose cost names the tool it takes from. */
export function Mana({ lifted = null }) {
  const narrow = useNarrow(), limits = town.value?.limits || [];
  if (!limits.length) return null;
  const cost = lifted ? costOf(lifted) : null, from = { title: mapName(tab.value, partiesNow()), key: "" };
  const over = limits.length > PLACES, shown = over ? limits.slice(0, PLACES - 1) : limits, rows = limits.length > 3 ? 2 : 1, small = narrow || rows === 2, more = limits.length - shown.length;
  return html`<div class="hand-mana" role="group" aria-label="What is left of your AI tools" data-rows=${rows} data-n=${limits.length}>
    ${shown.map((l) => html`<${Pot} key=${l.provider} l=${l} cost=${cost} small=${small} from=${from} />`)}
    ${over && html`<button type="button" class="hand-pot hand-pot--more" title=${`${more} more tools: what is left of them`} aria-label=${`${more} more tools: what is left of them`}
      onClick=${() => openOver("limits", {}, from, "What is left of your AI tools")}><span class="hand-pot__initial" aria-hidden="true">+${more}</span></button>`}
  </div>`;
}
