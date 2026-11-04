// The mana (docs/specs/104-the-mana-the-discard-on-the-table-a-lifted-card.md §3, decisions §175.2, §176.1–§176.2): the AI tools' limits as potions at the hand's right end, flush against the window's edge.
// One potion (orkUI's `.ork-potion`) a tool, in the order the chips had: above it the tool's mark in its own colour (the tool's initial in the body face with no mark), under it the share left, in the warn or the danger colour at
// those levels (`levelOf`).
// Two windows in one potion (docs/specs/114-the-mana-in-two-windows.md §3, decisions §192, hand/windows.js): the liquid is the tool's shortest window (the 5 hours: the now share), the bottle's size its longest (the week: large above 0.6,
// medium above 0.3, small above 0.1, else the vial: orkUI's `size-*`), every bottle standing on its floor in a slot of the large bottle's size, so the row never moves; the colour follows whichever runs out first (`levelOf` of the lower
// share); under the potion the now share alone (docs/specs/140 C1, decisions §247.3): *week 80%* muted under it only while the week is the window that runs out first (its share the lower), else only in the words, which say both and when each comes back;
// at the danger's level or empty the now share's place says *back 14:00* (spec 138 A.5, decisions §245.3: the lower window's reset in the machine's local time, *back Mon 09:00* when it is not today); on a crowded narrow width the share stays (mana.css). One to three tools lie in one row at the default size; four in two rows of two and five or six in two rows of three, small (decisions §177.8); more than six: the first five and a sixth place *+n* that opens all of them over the pane. At the narrow
// width (under 760 px, spec 94) every potion is small.
// A potion is a button, its words the chip's (*Claude Code: 62% of the week left*, `potionOf`); a press lifts its tool's card (toolcard.js, spec 130 B.3), on a host with no `tools` (Orkline's) it opens what used it over the pane, as the chip did.
// **The hand's tools, the empty slot** (spec 130 B.1, decisions §232.4–5): the potions are the tools in the hand in the person's order, the limits' rows and a tool with no limits read muted; dragging one changes the order (`tools.order`); the row ends with an empty slot, faint at rest, lit while the Orkmaster asks for a tool, gone at six; its press lifts the adding card (addtool.js). A tool whose limits were not read is its mark, muted, with no bottle, its words *Limits not read* (spec 140 C1).
// A card lifted that spends (`costOf`) hatches its share off its tool's top, and the share reads `62% −4%`. The words are said on the control, the potion itself is `aria-hidden` (orkUI's potion/README.md).
// The default (docs/specs/105-the-default-tool-moving-on-and-the-portal.md §4, decisions §177.1): the potion of the tool the open tab's work goes to carries a frame, a hotbar's chosen slot (orkUI's ink and edge, its notch, on the
// panel), and its words add *, the default*. On the project's tab it is the tool now (`town.mana.now`, else the Main tool, else the first); on a party's tab the tool the party is set to when it has one, else the same. One frame
// element slides between the places (a transform, `--ork-motion-base`; not under reduced motion); every potion keeps a transparent border of the frame's width, so nothing shifts. While going on paid holds (`town.mana.paid`)
// the tool billed by its API is a slot after the potions: its mark, orkUI's coins, *API* and the price under it, and the frame on it.
// A potion hovered or focused also lights the column's cards (spec 138 A, decisions §245.2): `litTool` is its provider, the column dims the cards whose goal does not wait for that tool (table/lit.js `waitTool`), the words add *Goals wait for its reset* when any does (never how many);
// a column card hovered hatches its next step's share off its tool's potion as a lifted card does (`hatched`, hand/cost.js `cardCost`).
// Who drinks from it (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §3.4, decisions §189.2): a potion hovered or focused marks its tool's marks on the tabs (`markedTool`, the tabs' second line: table/tabmarks.js, a 1 px outline), and its words add the parties
// that do and that check on it (*2 parties do on it, 1 party checks on it*; `usesWords`).
// The Play die lies at the potions' left (playdie.js, docs/specs/112-the-bars-marks-and-the-play-die.md §3.3, decisions §190.2): the same row, the same top edge; at the narrow width the two stand together at the row's end (mana.css).
// On a touch phone (docs/specs/117 §3, decisions §195.3) the potions are the top row's bottles (uptop.js): the same `potionOf` and `framedOf`, the same words, the bottle at its small scale, the default framed.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon, ORKUI } from "../orkui.js";
import { command, town } from "../link.js";
import { untilWords } from "../arena/arenawords.js";
import { MARKED, mapName, openTabOf, partiesAll } from "../table/data.js";
import { ORKMASTER, lift, lifted, lower, openOver, tab } from "../frame/state.js";
import { ADD_TOOL, TOOL, hatched, liftKey, litTool, markedDefault, markedTool } from "./state.js";
import { setupNow } from "./setupcards.js";
import { waitTool, defaultTool } from "../table/lit.js";
import { mapData } from "../shell/store.js";
import { windowWords, windowsOf } from "./windows.js";
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

/** The parties that do and that check on a tool, in words (decisions §189.2): *2 parties do on it, 1 party checks on it*; "" when none does either. A Lean party does but has no separate check. */
export function usesWords(provider, parties = []) {
  const does = parties.filter((g) => g.does_tool === provider).length, checks = parties.filter((g) => !g.lean && g.checks_tool === provider).length;
  const said = [does && `${does} ${does === 1 ? "party does" : "parties do"} on it`, checks && `${checks} ${checks === 1 ? "party checks" : "parties check"} on it`].filter(Boolean);
  return said.join(", ");
}

const until = (reset) => { const at = untilWords(reset); return at ? `, until ${at}` : ""; };
const sentence = (text) => `${text.charAt(0).toUpperCase()}${text.slice(1)}`;

/** What a tool's potion says: `{read, share, week, of, size, liquid, level, dry, took, words}`; `cost` (from `costOf`) is the lifted card's, when it takes from this tool; `framed` adds *, the default*; `uses` (from `usesWords`) the parties that do and check on it.
 *  `share` is the now share (the shortest window's), `back` (*14:00*, said after *back*, "" above the danger's level) what stands in its place at the danger's level or empty, `week` what stands muted under it only while the week runs out first, `{name, share}` (*week 82%*) and, for a tool with one window named so, `of` (*of the month*); the words say both: *Claude Code: 30% of the 5 hours left, until 18:40; 82% of the week, until Thu 09:00*. */
export function potionOf(l, cost = null, framed = false, uses = "", waiting = false) {
  const wait = waiting ? ". Goals wait for its reset" : "";
  const w = windowsOf(l), took = w.read && cost?.spend ? cost.taken : "";
  if (!w.read) return { read: false, share: "", back: "", week: null, of: "", size: "large", liquid: 0, level: "unread", dry: false, took: "", words: `${l.name}: Limits not read${framed ? ", the default" : ""}${uses ? `. ${sentence(uses)}` : ""}${wait}` };
  const nowWin = windowWords(w.now.window), weekWin = w.week ? windowWords(w.week.window) : "";
  const first = `${l.name}: ${w.now.share} ${nowWin ? `of ${nowWin} ` : ""}left${until(w.now.reset)}`;
  const said = w.week ? `${first}; ${w.week.share} ${weekWin ? `of ${weekWin}` : "left"}${until(w.week.reset)}` : first;
  const left = framed ? `${said}, the default` : said, spent = took ? `${left}. This card takes about ${took} of it` : left;
  const back = w.level === "danger" && w.lowReset ? untilWords(w.lowReset) : "";                                       // the hour a tool at the danger's level or empty comes back (spec 138 A.5)
  const week = w.week && w.weekFirst ? { name: weekWin.replace(/^the /, "") || "week", share: w.week.share } : null, of = !w.week && nowWin ? `of ${nowWin}` : "";
  return { read: true, share: w.now.share, back, week, of, size: w.size, liquid: w.liquid, level: w.level, dry: w.dry, took, words: `${uses ? `${spent}. ${sentence(uses)}` : spent}${wait}` };
}

/** One tool's mark in its own colour (orkUI's `marks/harness-<id>.png`, not the ink one); its initial in the body face with no mark. */
export function Who({ l }) {
  return MARKED.includes(l.provider)
    ? html`<img class="ork-mark" src=${`${ORKUI}/marks/harness-${l.provider}.png`} srcset=${`${ORKUI}/marks/harness-${l.provider}@2x.png 2x`} alt="" draggable="false" />`
    : html`<span class="hand-pot__initial" aria-hidden="true">${(l.name || l.provider || "?").charAt(0).toUpperCase()}</span>`;
}

/** The potions in the hand's order (spec 130 B.1): a tool in the hand with no limits read is a muted potion; a tool not in the hand has none. A host with no `tools` (Orkline's): the limits as they come. */
export function potionsOf(limits, tools) {
  if (!tools) return limits;
  const by = new Map(limits.map((l) => [l.provider, l]));
  return (tools.hand || []).map((t) => by.get(t.id) || { provider: t.id, name: t.title });
}

const toggleLift = (key) => { const k = liftKey(key); if (lifted.peek() === k) lower(); else lift(k); };

/** Dragging a potion changes the order the work moves on in (`tools.order`): dropped on another, it takes that one's place. */
function useDragOrder(tools) {
  const from = useRef("");
  if (!tools || (tools.order || []).length < 2) return () => ({});
  return (id) => ({
    draggable: true,
    onDragStart: (e) => { from.current = id; e.dataTransfer.effectAllowed = "move"; e.dataTransfer.setData("text/plain", id); },
    onDragOver: (e) => { if (from.current && from.current !== id) e.preventDefault(); },
    onDrop: (e) => {
      e.preventDefault();
      const was = from.current;
      from.current = "";
      if (!was || was === id) return;
      const order = tools.order.filter((t) => t !== was);
      order.splice(tools.order.indexOf(id), 0, was);
      command("tools.order", { order }, true).catch(() => {});
    },
    onDragEnd: () => { from.current = ""; },
  });
}

/** The empty slot: a potion's place in pixel dashes with a +. orkUI first: `.ork-potion.is-empty`. */
function EmptySlot({ lit, small }) {
  return html`<button type="button" class=${cls("hand-pot hand-pot--empty", { "is-lit": lit })} data-empty-slot="1" aria-label="Add an AI tool" title="Add an AI tool" onClick=${() => toggleLift(ADD_TOOL)}>
    <span class=${cls("hand-pot__slot", { "is-small": small })}><span class="hand-pot__dashes" aria-hidden="true"><${Icon} name="plus" /></span></span></button>`;
}

function Pot({ l, cost, small, from, framed, parties = [], onPress = null, drag = null }) {
  const dflt = defaultTool(), waiting = (mapData.value?.nodes || []).some((n) => waitTool(n, dflt) === l.provider);                  // a goal waits for this tool's reset: said, never how many (spec 138 A.3, decisions §67)
  const p = potionOf(l, cost && cost.tool === l.provider ? cost : null, framed, usesWords(l.provider, parties), waiting);
  const style = `--ork-potion-left:${p.liquid}${p.took ? `;--ork-potion-spend:${cost.spend}` : ""}`;
  const mark = () => { markedTool.value = l.provider; markedDefault.value = framed; litTool.value = l.provider; }, unmark = () => { if (markedTool.value === l.provider) { markedTool.value = ""; markedDefault.value = false; } if (litTool.value === l.provider) litTool.value = ""; };
  return html`<button type="button" class=${cls("hand-pot", `is-${p.level}`, { "is-default": framed, "is-dry": p.dry })} data-provider=${l.provider} data-level=${p.level} data-size=${p.size} data-default=${framed ? "1" : undefined}
      title=${p.words} aria-label=${p.words} onClick=${onPress || (() => openOver("limits", { provider: l.provider }, from, `${l.name}: what used it`))} ...${drag || {}}
      onPointerEnter=${mark} onPointerLeave=${unmark} onFocus=${mark} onBlur=${unmark}>
    <${Who} l=${l} />
    <span class=${cls("hand-pot__slot", { "is-small": small })}>${p.read && html`<span class=${cls("ork-potion", { [`size-${p.size}`]: p.size !== "large", small, "is-warn": p.level === "warn", "is-danger": p.level === "danger" })} style=${style} aria-hidden="true"></span>`}</span>
    <span class="hand-pot__shares"><span class="hand-pot__share">${p.back ? html`<span class="hand-pot__back">back ${p.back}</span><span class="hand-pot__pct">${p.share}</span>` : p.share}${p.took && html` <span class="hand-pot__took">−${p.took}</span>`}</span>
    ${p.week && html`<span class="hand-pot__week"><span class="hand-pot__week-name">${p.week.name} </span>${p.week.share}</span>`}
    ${p.of && html`<span class="hand-pot__week hand-pot__week--of">${p.of}</span>`}</span>
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

/** The potions. `lifted`: the stop now lifted in the hand, whose cost names the tool it takes from. */
export function Mana({ lifted = null }) {
  const narrow = useNarrow(), box = useRef(), frame = useRef(), tools = town.value?.tools || null, limits = potionsOf(town.value?.limits || [], tools), mana = town.value?.mana || null, paid = mana?.paid || null, empty = !!tools && !tools.full, drag = useDragOrder(tools);
  const parties = partiesAll(), open = openTabOf(tab.value, parties);
  const slots = PLACES - (paid ? 1 : 0), over = limits.length > slots, shown = over ? limits.slice(0, slots - 1) : limits, more = limits.length - shown.length;
  const places = shown.length + (over ? 1 : 0) + (paid ? 1 : 0) + (empty ? 1 : 0), rows = places > 3 ? 2 : 1, small = narrow || rows === 2;
  const key = framedOf({ limits, mana, open, parties, shown });
  useFrame(box, frame, key, [narrow, places, lifted ? 1 : 0, paid?.usd_task ?? ""]);
  if (!limits.length && !paid && !empty) return null;
  const cost = lifted ? costOf(lifted) : hatched.value, from = { title: mapName(tab.value, parties), key: "" };
  return html`<div class="hand-mana" ref=${box} role="group" aria-label="What is left of your AI tools" data-rows=${rows} data-n=${places} data-paid=${paid ? "1" : undefined} data-default=${key || undefined}>
    <span class="hand-mana__frame" ref=${frame} aria-hidden="true" hidden></span>
    ${shown.map((l) => html`<${Pot} key=${l.provider} l=${l} cost=${cost} small=${small} from=${from} framed=${key === l.provider} parties=${parties} onPress=${tools ? () => toggleLift(`${TOOL}${l.provider}`) : null} drag=${tools ? drag(l.provider) : null} />`)}
    ${over && html`<button type="button" class="hand-pot hand-pot--more" title=${`${more} more tools: what is left of them`} aria-label=${`${more} more tools: what is left of them`}
      onClick=${() => openOver("limits", {}, from, "What is left of your AI tools")}><span class="hand-pot__initial" aria-hidden="true">+${more}</span></button>`}
    ${paid && html`<${PaidPot} key="paid" paid=${paid} from=${from} framed=${key === "paid"} />`}
    ${empty && html`<${EmptySlot} key="empty" lit=${setupNow.value?.step === "tools"} small=${small} />`}
  </div>`;
}
