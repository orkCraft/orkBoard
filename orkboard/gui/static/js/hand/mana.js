// The mana (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §3, decisions §175.2, §176.1–§176.2): the AI tools' limits as potions at the hand's right end, flush against the window's edge.
// One potion (orkUI's `.ork-potion`) a tool, in the order the chips had: above it the tool's mark in its own colour (the tool's initial in the body face with no mark), under it the share left, in the warn or the danger colour at
// those levels (`levelOf`). One to three tools lie in one row at the default size; four in two rows of two and five or six in two rows of three, small (decisions §177.8); more than six: the first five and a sixth place *+n* that opens all of them over the pane. At the narrow
// width (under 760 px, spec 94) every potion is small.
// A potion is a button, its words the chip's (*Claude Code: 62% of the week left*, `windowOf`); a press opens what used it over the pane, as the chip did. A tool whose limits were not read is an empty potion with *?*.
// A card lifted that spends (`costOf`) hatches its share off its tool's top, and the share reads `62% −4%`. The words are said on the control, the potion itself is `aria-hidden` (orkUI's potion/README.md).
// The default (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §4, decisions §177.1): the potion of the tool the open tab's work goes to carries a frame, a hotbar's chosen slot (orkUI's ink and edge, its notch, on the
// panel), and its words add *, the default*. On the project's tab it is the tool now (`town.mana.now`, else the Main tool, else the first); on a party's tab the tool the party is set to when it has one, else the same. One frame
// element slides between the places (a transform, `--ork-motion-base`; not under reduced motion); every potion keeps a transparent border of the frame's width, so nothing shifts. While going on paid holds (`town.mana.paid`)
// the tool billed by its API is a slot after the potions: its mark, orkUI's coins, *API* and the price under it, and the frame on it.
// Who drinks from it (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.4, decisions §189.2): a potion hovered or focused marks its tool's marks on the tabs (`markedTool`, the tabs' second line: table/tabmarks.js, a 1 px outline), and its words add the parties
// that do and that check on it (*2 parties do on it, 1 party checks on it*; `usesWords`).
// The Play die lies at the potions' left (playdie.js, docs/specs/112-the-bars-marks-and-the-play-die.md §3.3, decisions §190.2): the same row, the same top edge; at the narrow width the two stand together at the row's end (mana.css).
// Upright on a touch phone (docs/specs/103 §1.2.5, decisions §179.1) the tools are `Tools`: each its coloured mark with its share under it, no bottle, a 44 px target, in one row no taller than the …; the default framed (on the hand's screen
// the tool now, else the Main tool: §178.3), its words the potion's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon, ORKUI } from "../orkui.js";
import { town } from "../link.js";
import { levelOf, windowOf } from "../arena/limits.js";
import { untilWords } from "../arena/arenawords.js";
import { MARKED, mapName, openTabOf, partiesAll } from "../table/data.js";
import { ORKMASTER, openOver, tab } from "../frame/state.js";
import { markedTool } from "./state.js";
import { costOf } from "./cost.js";
import { priceWords } from "./paidcard.js";

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

/** The parties that do and that check on a tool, in words (decisions §189.2): *2 parties do on it, 1 party checks on it*; "" when none does either. A Lean party does but has no separate check. */
export function usesWords(provider, parties = []) {
  const does = parties.filter((g) => g.does_tool === provider).length, checks = parties.filter((g) => !g.lean && g.checks_tool === provider).length;
  const said = [does && `${does} ${does === 1 ? "party does" : "parties do"} on it`, checks && `${checks} ${checks === 1 ? "party checks" : "parties check"} on it`].filter(Boolean);
  return said.join(", ");
}

/** What a tool's potion says: `{read, share, level, took, words}`; `cost` (from `costOf`) is the lifted card's, when it takes from this tool; `framed` adds *, the default*; `uses` (from `usesWords`) the parties that do and check on it. */
export function potionOf(l, cost = null, framed = false, uses = "") {
  const read = typeof l.left === "number", win = read ? windowWords(windowOf(l)) : "";
  const share = read ? `${Math.round(l.left * 100)}%` : "?", level = read ? levelOf(l.left) : "unread";
  const took = read && cost?.spend ? cost.taken : "";
  const said = read ? `${l.name}: ${share} ${win ? `of ${win} ` : ""}left` : `${l.name}: limits not read yet`, left = framed ? `${said}, the default` : said;
  const spent = took ? `${left}. This card takes about ${took} of it` : left;
  return { read, share, level, took, words: uses ? `${spent}. ${uses.charAt(0).toUpperCase()}${uses.slice(1)}` : spent };
}

/** One tool's mark in its own colour (orkUI's `marks/harness-<id>.png`, not the ink one); its initial in the body face with no mark. */
function Who({ l }) {
  return MARKED.includes(l.provider)
    ? html`<img class="ork-mark" src=${`${ORKUI}/marks/harness-${l.provider}.png`} srcset=${`${ORKUI}/marks/harness-${l.provider}@2x.png 2x`} alt="" draggable="false" />`
    : html`<span class="hand-pot__initial" aria-hidden="true">${(l.name || l.provider || "?").charAt(0).toUpperCase()}</span>`;
}

function Pot({ l, cost, small, from, framed, parties = [] }) {
  const p = potionOf(l, cost && cost.tool === l.provider ? cost : null, framed, usesWords(l.provider, parties));
  const style = `--ork-potion-left:${p.read ? l.left : 0}${p.took ? `;--ork-potion-spend:${cost.spend}` : ""}`;
  return html`<button type="button" class=${cls("hand-pot", `is-${p.level}`, { "is-default": framed })} data-provider=${l.provider} data-level=${p.level} data-default=${framed ? "1" : undefined}
      title=${p.words} aria-label=${p.words} onClick=${() => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`)}
      onPointerEnter=${() => { markedTool.value = l.provider; }} onPointerLeave=${() => { if (markedTool.value === l.provider) markedTool.value = ""; }}
      onFocus=${() => { markedTool.value = l.provider; }} onBlur=${() => { if (markedTool.value === l.provider) markedTool.value = ""; }}>
    <${Who} l=${l} />
    <span class=${cls("ork-potion", { small, "is-warn": p.level === "warn", "is-danger": p.level === "danger" })} style=${style} aria-hidden="true"></span>
    <span class="hand-pot__share">${p.share}${p.took && html` <span class="hand-pot__took">−${p.took}</span>`}</span>
  </button>`;
}

/** What the paid slot says: the tool, billed per task by its API, has no limit to pour; its price a task, and until when the yes holds. */
export function paidWordsOf(paid, framed = false) {
  const price = priceWords(paid), until = untilWords(paid.until);
  return `${paid.name} paid by its API: no limit, ${price ? `about ${price} a task` : "its cost is not known yet"}${until ? `, going on until ${until}` : ""}${framed ? ", the default" : ""}`;
}

/** The slot after the potions while going on paid holds: the tool's mark, orkUI's coins where a potion would stand, *API* and the price under it. */
function PaidPot({ paid, from, framed }) {
  const words = paidWordsOf(paid, framed), price = priceWords(paid);
  return html`<button type="button" class=${cls("hand-pot hand-pot--paid", { "is-default": framed })} data-provider=${paid.tool} data-paid="1" data-default=${framed ? "1" : undefined} title=${words} aria-label=${words}
      onClick=${() => openOver("limits", { provider: paid.tool }, from, `${paid.name}: what used it`)}>
    <${Who} l=${{ provider: paid.tool, name: paid.name }} />
    <span class="hand-pot__coins" aria-hidden="true"><${Icon} name="coins" /></span>
    <span class="hand-pot__share">API</span>
    ${price && html`<span class="hand-pot__sub">≈${price}</span>`}
  </button>`;
}

/** Which place the frame is on, from what the page knows: `"paid"`, a shown potion's provider, or "" (no frame). `open` is the open tab, `parties` the project's parties (a party's `tool` is the one it is set to, "" follows). */
export function framedOf({ limits, mana, open, parties, shown = limits }) {
  const party = open !== ORKMASTER ? parties.find((g) => g.slug === open) : null, pinned = party?.tool || "";
  const wanted = pinned || mana?.now || mana?.main || limits[0]?.provider || "", paid = mana?.paid;
  if (paid && wanted === paid.tool && !pinned) return "paid";
  if (shown.some((l) => l.provider === wanted)) return wanted;
  return paid && wanted === paid.tool ? "paid" : "";
}

/** The frame: one element moved to the framed place with a transform (its slide) and sized to it; hidden with no place. The first place is taken without a slide. */
function useFrame(box, frame, key, deps) {
  useLayoutEffect(() => {
    const el = frame.current, wrap = box.current;
    if (!el || !wrap) return undefined;
    const place = () => {
      const on = wrap.querySelector('[data-default="1"]');
      el.hidden = !on;
      if (!on) return;
      el.style.width = `${on.offsetWidth}px`;
      el.style.height = `${on.offsetHeight}px`;
      el.style.transform = `translate(${on.offsetLeft}px, ${on.offsetTop}px)`;
    };
    place();
    if (!el.dataset.placed) requestAnimationFrame(() => requestAnimationFrame(() => { el.dataset.placed = "1"; }));
    if (typeof ResizeObserver !== "function") return undefined;
    const ro = new ResizeObserver(place);
    ro.observe(wrap);
    wrap.querySelectorAll(".hand-pot").forEach((p) => ro.observe(p));
    return () => ro.disconnect();
  }, [key, ...deps]);
}

/** One tool upright on a touch phone: its mark with its share under it (the share in the warn or the danger colour as it runs low), no bottle; its words are the potion's. */
function Tool({ l, from, framed }) {
  const p = potionOf(l, null, framed);
  return html`<button type="button" class=${cls("hand-pot hand-pot--tool", `is-${p.level}`, { "is-default": framed })} data-provider=${l.provider} data-level=${p.level} data-default=${framed ? "1" : undefined}
      title=${p.words} aria-label=${p.words} onClick=${() => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`)}>
    <${Who} l=${l} /><span class="hand-pot__share">${p.share}</span>
  </button>`;
}

/** The paid slot upright: the tool's mark with *API* under it (its words say the price and until when). */
function PaidTool({ paid, from, framed }) {
  const words = paidWordsOf(paid, framed);
  return html`<button type="button" class=${cls("hand-pot hand-pot--tool hand-pot--paid", { "is-default": framed })} data-provider=${paid.tool} data-paid="1" data-default=${framed ? "1" : undefined} title=${words} aria-label=${words}
      onClick=${() => openOver("limits", { provider: paid.tool }, from, `${paid.name}: what used it`)}><${Who} l=${{ provider: paid.tool, name: paid.name }} /><span class="hand-pot__share">API</span></button>`;
}

/** The AI tools' row upright on a touch phone (spec 103 §1.2.5): a mark and a share each, the default framed (the frame slides as on the desktop). A press opens what used it over the pane. */
export function Tools() {
  const box = useRef(), frame = useRef(), limits = town.value?.limits || [], mana = town.value?.mana || null, paid = mana?.paid || null;
  const slots = PLACES - (paid ? 1 : 0), over = limits.length > slots, shown = over ? limits.slice(0, slots - 1) : limits, more = limits.length - shown.length;
  const key = framedOf({ limits, mana, open: ORKMASTER, parties: [], shown }), places = shown.length + (over ? 1 : 0) + (paid ? 1 : 0);
  useFrame(box, frame, key, [places]);
  if (!limits.length && !paid) return null;
  const from = { title: "", key: "" };                                                  // the Board is not reached upright: the opened place says its own title
  return html`<div class="hand-mana hand-mana--tools" ref=${box} role="group" aria-label="What is left of your AI tools" data-n=${places} data-default=${key || undefined}>
    <span class="hand-mana__frame" ref=${frame} aria-hidden="true" hidden></span>
    ${shown.map((l) => html`<${Tool} key=${l.provider} l=${l} from=${from} framed=${key === l.provider} />`)}
    ${over && html`<button type="button" class="hand-pot hand-pot--more" title=${`${more} more tools: what is left of them`} aria-label=${`${more} more tools: what is left of them`}
      onClick=${() => openOver("limits", {}, from, "What is left of your AI tools")}><span class="hand-pot__initial" aria-hidden="true">+${more}</span></button>`}
    ${paid && html`<${PaidTool} key="paid" paid=${paid} from=${from} framed=${key === "paid"} />`}
  </div>`;
}

/** The potions. `lifted`: the stop now lifted in the hand, whose cost names the tool it takes from. */
export function Mana({ lifted = null }) {
  const narrow = useNarrow(), box = useRef(), frame = useRef(), limits = town.value?.limits || [], mana = town.value?.mana || null, paid = mana?.paid || null;
  const parties = partiesAll(), open = openTabOf(tab.value, parties);
  const slots = PLACES - (paid ? 1 : 0), over = limits.length > slots, shown = over ? limits.slice(0, slots - 1) : limits, more = limits.length - shown.length;
  const places = shown.length + (over ? 1 : 0) + (paid ? 1 : 0), rows = places > 3 ? 2 : 1, small = narrow || rows === 2;
  const key = framedOf({ limits, mana, open, parties, shown });
  useFrame(box, frame, key, [narrow, places, lifted ? 1 : 0, paid?.usd_task ?? ""]);
  if (!limits.length && !paid) return null;
  const cost = lifted ? costOf(lifted) : null, from = { title: mapName(tab.value, parties), key: "" };
  return html`<div class="hand-mana" ref=${box} role="group" aria-label="What is left of your AI tools" data-rows=${rows} data-n=${places} data-paid=${paid ? "1" : undefined} data-default=${key || undefined}>
    <span class="hand-mana__frame" ref=${frame} aria-hidden="true" hidden></span>
    ${shown.map((l) => html`<${Pot} key=${l.provider} l=${l} cost=${cost} small=${small} from=${from} framed=${key === l.provider} parties=${parties} />`)}
    ${over && html`<button type="button" class="hand-pot hand-pot--more" title=${`${more} more tools: what is left of them`} aria-label=${`${more} more tools: what is left of them`}
      onClick=${() => openOver("limits", {}, from, "What is left of your AI tools")}><span class="hand-pot__initial" aria-hidden="true">+${more}</span></button>`}
    ${paid && html`<${PaidPot} key="paid" paid=${paid} from=${from} framed=${key === "paid"} />`}
  </div>`;
}
