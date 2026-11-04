// The quick question as the open leader's bubble (docs/specs/123-the-leaders-at-the-table.md §6, which changes docs/specs/106-a-quick-question.md §3 and docs/specs/121-the-day-the-morning-and-the-night.md §6; decisions §181, §201):
// the person presses the open leader's head (tabs.js draws it as a button carrying `data-ask-head="<tab>"`, and opens the bubble with `openAsk(tab)`), and a bubble stands under it on orkUI's raised panel, its tail under the head's centre, at most 440 px
// wide and kept inside the window. Its states are the line's that was: **asking** (the field focused; Enter sends `ideas.ask {party, q}`, party "" on the Orkmaster's tab; the field is kept when the bubble is closed), **reading** (the question
// muted, *The <Leader> is reading the map* with orkUI's `ork-think`), **answered** (the question muted, the answer in the body face with its line breaks — plain text, never Markdown —, up to four sources as small chips, **Make it a goal**,
// *Ask more*), **failed** (its error). The answer is the host's (`town.ask`, one for the project): it stays until it is put away (× on an answer: `ideas.ask_clear`), a bubble closed with the answer in it shows nothing more on the head, and
// opening it shows the answer. **Make it a goal** tells the host (`ideas.ask_goal`) and opens the new goal's field with that line written (the field is the hand's, addressed to the open tab as it always is), and the bubble gives way to it.
// The evening line (`Since`, concerns.js) is drawn at the bubble's top whenever the party's record has it; the bubble opens by itself once a day for a party, when its tab is open and the person has not seen the line today (a `localStorage` key a party a day,
// a convenience only: without it, once while the page lasts). The foot (a party's, not the Orkmaster's): *Its seat: <tool> · <tier>* and **Change**, which opens the leader's seat's popover (seatpop.js).
// Esc, × or a press outside closes it; the head keeps the focus. The desktop only: under 760 px wide and on a touch screen (§181.8) no head opens a bubble. Nothing over an open page: opening one puts the bubble away.
// **What it is about** (spec 128 E, decisions §206.5): under the head row (and the evening line) a chip says what is picked, the goal's rune and name or *The whole project*, and, when `openAsk(tab, part)` carried one (a part of a goal's change, pressed on a leader's tab),
// a chip of the part with × that takes it off. The answer stays a read. Under an answer: **Make it a goal** when nothing, or a goal done, is picked; **Make it a change** when a goal that is agreed or at work is picked on a leader's tab (never the Orkmaster's): it sends
// `ideas.change {idea, party, part?, text}` with the person's question as the words, the answer is put away, and the leader's decision comes to the hand (hand/changecard.js: *Now* and *Proposed*, or Design's three looks).
// Typing here never opens the new goal's field: the hand opens it on a key typed with nothing focused (hand/hand.js), and this field has the focus.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { Elem, Head, Icon, TIER_WORDS } from "../orkui.js";
import { command, toast, town } from "../link.js";
import { spendWords } from "../hand/costline.js";
import { mapData } from "../shell/store.js";
import { ORKMASTER, over, picked } from "../frame/state.js";
import { fieldText } from "../hand/state.js";
import { openField } from "../hand/pluscard.js";
import { WHOLE, groupsOf, mapName, toolOf, wide } from "./data.js";
import { Since, lookOf } from "./concerns.js";
import { SeatPop } from "./seatpop.js";
import { Linked } from "./asklinks.js";
import { ToolMark } from "./header.js";

const Q_CHARS = 500;                                                  // as realm/board_ask.py Q_CHARS
const CROWN = { race: "peon", tier: "crown" };                        // the Orkmaster's head, as the tabs and the notice draw it
const WIDTH = 440, EDGE = 16, TAIL = 28;                              // the bubble's widest, its distance from the window's edge, its tail's usual place from its left

/** The tab whose bubble is open: a party's slug, "" for the Orkmaster's, null while none is. */
export const askOpen = signal(null);
const keyOf = (tab) => (!tab || tab === ORKMASTER ? "" : tab);
/** The part of a goal's change the bubble is about: `{id, name}`, null for none. */
export const askPart = signal(null);
/** The states of a goal that is agreed or at work: *Make it a change* may be asked of a leader about it (as realm/leader_change.py `CHANGE_STATES`). */
export const AGREED = ["decided", "sketch", "sections", "planning", "plan", "working"];

/** Opens the bubble of a tab (`ORKMASTER`, "" or a party's slug); the head that carries `data-ask-head` is what it stands under. `part`: a part of a goal's change it is about (its name, or `{id, name}`), a chip with ×;
 *  `words`: what the field starts with (*Talk more* gives the words it was asked with back). Exported so another part (a part of a change pressed, a decision card's *Talk more*) can open it. */
export function openAsk(tab, part = null, words = "") {
  const p = typeof part === "string" ? { id: part, name: part } : part && (part.id || part.name) ? { id: String(part.id ?? part.name), name: String(part.name || part.id) } : null;
  askPart.value = p;
  if (words) drafts[keyOf(tab)] = String(words);
  askOpen.value = keyOf(tab);
}
export const closeAsk = () => { askOpen.value = null; askPart.value = null; };

/** What the field kept when its bubble was closed, a party's (the Orkmaster's under ""). */
const drafts = {};

const headOf = (tab) => (typeof document === "undefined" ? null : document.querySelector(`[data-ask-head="${CSS.escape(tab)}"]`));
/** Whether a head may open a bubble: the wide width and a pointer that is not a finger. */
export const desk = () => wide.value && !(typeof matchMedia === "function" && matchMedia("(pointer: coarse)").matches);

// -- the evening line, seen once a day a party ------------------------------------------------------------------------------------------------------------------------------------------
const seenNow = new Set();
const dayKey = (party) => { const d = new Date(); return `orkboard.ask.evening.${party}.${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`; };
function seen(party) {
  const k = dayKey(party);
  if (seenNow.has(k)) return true;
  try { return localStorage.getItem(k) === "1"; } catch { return false; }
}
function seeing(party) {
  const k = dayKey(party);
  seenNow.add(k);
  try { localStorage.setItem(k, "1"); } catch { /* a convenience only */ }
}

/** Who answers on a tab: `{name, head}`, the Orkmaster, or the party's leader seat (*the leader* when it has none). `party` "" is the Orkmaster's. */
export function askerOf(party, parties) {
  if (!party) return { name: "Orkmaster", head: CROWN };
  const g = parties.find((x) => x.slug === party), seat = g ? groupsOf(g).find((x) => x.band === "lead")?.seats[0] : null;
  return { name: seat?.name || "leader", head: seat?.head || null, seat };
}

/** The leader's name and role as the bubble's head row says them: *Grukk, the Architect*, *the Architect* with no name of its own, *the Orkmaster*. */
function whoWords(party, g, here) {
  if (!party) return "the Orkmaster";
  const own = String(g?.leader?.name || "").trim();
  return own && own.toLowerCase() !== here.name.toLowerCase() ? `${own}, the ${here.name}` : `the ${here.name}`;
}

/** The bubble itself, open: positioned under the head, its content by the state of the question. */
function Bubble({ tab, party, g, parties, look }) {
  const box = useRef(), field = useRef(), pop = useRef();
  const [q, setQ] = useState(drafts[party] || ""), [sending, setSending] = useState(false), [more, setMore] = useState(false), [seat, setSeat] = useState(false);
  const ask = town.value?.ask || null, here = askerOf(party, parties);
  const reading = ask?.status === "asking", readBy = reading ? askerOf(ask.party || "", parties) : null, mine = !!ask && (ask.party || "") === party;
  const state = reading && mine ? "reading" : mine && !reading && !more ? (ask.status === "failed" ? "failed" : "answered") : "asking";
  const goalNode = picked.value ? (mapData.value?.nodes || []).find((x) => x.slug === picked.value) || null : null, part = askPart.value;
  const aboutGoal = goalNode ? goalNode.short || goalNode.title || WHOLE : WHOLE, canChange = !!goalNode && !!party && AGREED.includes(goalNode.state), canGoal = !goalNode || goalNode.state === "done";
  const words = `Ask the ${here.name}`, seatOf = g ? here.seat : null, from = { title: mapName(tab, parties), key: "" };

  const place = () => {                                              // under the head, the tail under its centre, inside the window
    const el = box.current, head = headOf(tab);
    if (!el || !head) return;
    const r = head.getBoundingClientRect(), vw = document.documentElement.clientWidth, vh = document.documentElement.clientHeight;
    const width = Math.min(WIDTH, vw - 2 * EDGE), cx = r.left + r.width / 2, left = Math.max(EDGE, Math.min(cx - TAIL, vw - width - EDGE)), top = r.bottom + 14;
    Object.assign(el.style, { width: `${width}px`, left: `${left}px`, top: `${top}px` });
    const tail = el.querySelector(".table-ask__tail"), inner = el.querySelector(".table-ask__in");
    if (tail) tail.style.left = `${Math.max(12, Math.min(cx - left - 8, width - 20))}px`;                // the tail's left corner: its middle is 8 px on
    if (inner) inner.style.maxHeight = `${Math.max(120, vh - top - 2 * EDGE)}px`;
    if (pop.current) Object.assign(pop.current.style, { left: `${left}px`, top: `${el.getBoundingClientRect().bottom + 6}px`, width: `${width}px` });
  };
  useLayoutEffect(place);
  useEffect(() => {
    addEventListener("resize", place);
    addEventListener("scroll", place, true);
    return () => { removeEventListener("resize", place); removeEventListener("scroll", place, true); };
  }, [tab]);

  const close = (back = true) => { closeAsk(); if (back) headOf(tab)?.focus?.(); };
  const wasSeat = useRef(false);
  wasSeat.current = seat;
  useLayoutEffect(() => {                                            // Esc and a press outside put it away (the seat's popover first, on its own Esc); listening from the first frame it is drawn
    const esc = (e) => { if (e.key === "Escape" && !wasSeat.current && !e.defaultPrevented) { e.preventDefault(); e.stopPropagation(); close(true); } };
    const away = (e) => {
      const t = e.target;
      if (box.current?.contains(t) || t.closest?.("[data-ask-head], .table-ask__pop, .table-seatpop")) return;
      close(false);
      setTimeout(() => { if (document.activeElement === document.body) headOf(tab)?.focus?.(); }, 0);
    };
    addEventListener("keydown", esc, true);
    document.addEventListener("pointerdown", away, true);
    return () => { removeEventListener("keydown", esc, true); document.removeEventListener("pointerdown", away, true); };
  }, [tab]);
  useLayoutEffect(() => { (field.current || box.current?.querySelector("button"))?.focus(); }, [state]);       // the field takes the focus in the press that opened it; an answer, its first button
  useEffect(() => { if (reading) setMore(false); }, [reading]);

  const send = async (e) => {
    e.preventDefault();
    const text = q.trim();
    if (!text || sending || reading) return;
    setSending(true);
    try { await command("ideas.ask", { party, q: text }); setQ(""); drafts[party] = ""; } catch { /* refused: the host's words are in a toast, the question stays */ }
    setSending(false);
  };
  const away = () => {                                               // × on an answer puts it away; on the rest it only closes
    if (state === "answered" || state === "failed") command("ideas.ask_clear", {}).catch(() => {});
    close(true);
  };
  const change = async () => {                                      // the person's words become a decision in the hand: the leader replans its part (ideas.change); the answer is put away
    if (sending) return;
    setSending(true);
    try { await command("ideas.change", { idea: goalNode.slug, party, ...(part ? { part: part.id } : {}), text: ask.q }); } catch { setSending(false); return; }       // refused: the host's words are in a toast, the answer stays
    setSending(false);
    command("ideas.ask_clear", {}).catch(() => {});
    close(false);
  };
  const analysis = state === "answered" && ask?.goal_in_analysis ? (mapData.value?.nodes || []).find((x) => x.slug === ask.goal_in_analysis) || { slug: ask.goal_in_analysis } : null;
  const addTo = async () => {                                        // the person's words kept as written in the goal's Asked, and its decision worded again when it is worded already (ideas.add_to_goal, spec 132 A)
    if (sending || !analysis) return;
    setSending(true);
    let got = null;
    try { got = await command("ideas.add_to_goal", { idea: analysis.slug, text: ask.q, via: "bubble" }); } catch { setSending(false); return; }      // refused: the host's words are in a toast, the answer stays
    setSending(false);
    const price = got?.reworded && got.cost ? spendWords(got.cost.usd_high) : "";
    toast(got?.reworded ? `Added to the goal; the Orkmaster words its decision again${price ? `: ${price}` : ""}` : "Added to the goal");
    command("ideas.ask_clear", {}).catch(() => {});
    close(false);
  };
  const goal = () => {
    command("ideas.ask_goal", {}).catch(() => {});
    fieldText.value = ask.goal;
    close(false);
    openField();
  };
  const sources = state === "answered" && Array.isArray(ask.sources) ? ask.sources : [];
  const tool = seatOf ? toolOf(g, seatOf) : null, tier = TIER_WORDS[seatOf?.head?.tier];
  return html`<section class="table-ask__bubble" role="dialog" aria-label=${words} data-ask=${tab} data-state=${state} ref=${box}>
      <i class="table-ask__tail" aria-hidden="true"></i>
      <div class="table-ask__in">
        <div class="table-ask__who">${here.head && html`<${Head} race=${here.head.race} tier=${here.head.tier} />`}<span class="table-ask__name">${whoWords(party, g, here)}</span><span class="table-ask__grow"></span>
          <button type="button" class="ork-btn quiet table-ask__x" aria-label="Put away" title="Put away" onClick=${away}><${Icon} name="close" /></button></div>
        ${look?.since && html`<${Since} rec=${look} />`}
        <div class="table-ask__about" aria-label="What it is about">
          <span class="ork-chip table-ask__chip" data-about=${goalNode ? "goal" : "project"}>${goalNode && html`<${Elem} name=${goalNode.element || ""} hue=${goalNode.hue || ""} />`}<span>${aboutGoal}</span></span>
          ${part && html`<span class="ork-chip table-ask__chip" data-about="part" title="A part of its change"><${Icon} name="map" /><span>${part.name}</span>
            <button type="button" class="table-ask__unpart" aria-label="Take the part off" title="Take the part off" onClick=${() => { askPart.value = null; }}><${Icon} name="close" /></button></span>`}
        </div>
        ${state === "asking" && html`<form class="table-ask__form" onSubmit=${send}>
          <input type="text" class="ork-field table-ask__field" ref=${field} aria-label=${words} placeholder=${part ? `What about ${part.name}?` : goalNode ? `What about ${aboutGoal}?` : `${words}…`} maxlength=${Q_CHARS} autocomplete="off" enterkeyhint="send"
            value=${q} disabled=${reading} onInput=${(e) => { setQ(e.currentTarget.value); drafts[party] = e.currentTarget.value; }} />
        </form>`}
        ${state === "asking" && reading && html`<p class="table-ask__reading ork-think" role="status">The ${readBy.name} is reading the map</p>`}
        ${state === "reading" && html`<p class="table-ask__q">${ask.q}</p><p class="table-ask__reading ork-think" role="status">The ${here.name} is reading the map</p>`}
        ${state === "answered" && html`<p class="table-ask__q">${ask.q}</p>
          <p class="table-ask__text"><${Linked} text=${ask.answer} /></p>
          ${sources.length > 0 && html`<ul class="table-ask__srcs" aria-label="Where it is said">${sources.map((s) => html`<li key=${s} class="ork-chip table-ask__src"><${Linked} text=${s} /></li>`)}</ul>`}
          <div class="table-ask__acts">${analysis && html`<button type="button" class="ork-btn primary" data-act="add" disabled=${sending} title=${`Your words are kept as written in ${analysis.short || analysis.title || "the goal"}; if its decision is worded already, the Orkmaster words it again`} onClick=${addTo}>Add to the goal</button>`}${canChange && html`<button type="button" class="ork-btn primary" disabled=${sending} title=${`${here.name} replans its part of ${aboutGoal} from your words; you decide in the hand`} onClick=${change}>Make it a change</button>`}
            ${canGoal && ask.goal && html`<button type="button" class="ork-btn primary" title=${ask.goal} onClick=${goal}>Make it a goal</button>`}<span class="table-ask__grow"></span>
            <button type="button" class="ork-btn quiet" onClick=${() => setMore(true)}>Ask more</button></div>`}
        ${state === "failed" && html`<p class="table-ask__q">${ask.q}</p><p class="table-ask__err" role="alert">${ask.error || "No answer came: ask again"}</p>
          <div class="table-ask__acts"><span class="table-ask__grow"></span><button type="button" class="ork-btn quiet" onClick=${() => setMore(true)}>Ask again</button></div>`}
        ${seatOf && tool && html`<div class="table-ask__seat"><span>Its seat:</span><${ToolMark} id=${tool.id} /><span>${[tool.name, tier].filter(Boolean).join(" · ")}</span>
          <button type="button" class="ork-btn quiet" aria-haspopup="dialog" onClick=${() => setSeat(true)}>Change</button></div>`}
      </div>
    </section>
    ${seat && seatOf && html`<div class="table-ask__pop" ref=${pop}><${SeatPop} g=${g} slug=${seatOf.slug} from=${from} onClose=${() => setSeat(false)} /></div>`}
`;
}

/** What the tabs draw once: the bubble of the open tab when it is open. `tab`: the open tab (`ORKMASTER` or a party's slug); `parties`: the Board's. Also opens it once a day for the evening line. */
export function AskBubble({ tab, parties }) {
  const key = keyOf(tab), g = key ? parties.find((x) => x.slug === key) : null, ok = desk() && (key ? !!g : parties.length > 0) && !over.value;
  const look = key ? lookOf(key) : null, line = String(look?.since?.line || "").trim(), open = askOpen.value;
  useEffect(() => { if (open !== null && (open !== key || !ok)) closeAsk(); }, [key, ok, open]);        // another tab, a page over the pane, a window too narrow: put away
  useEffect(() => {                                                  // the evening line: open once a day a party, when its tab is open
    if (!key || !line || !ok || askOpen.peek() !== null || !headOf(tab) || seen(key)) return;
    seeing(key);
    openAsk(tab);
  }, [key, line, ok]);
  if (!ok || open !== key || !headOf(tab)) return null;
  return html`<${Bubble} key=${key} tab=${tab} party=${key} g=${g} parties=${parties} look=${look} />`;
}
