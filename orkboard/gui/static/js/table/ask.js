// The quick question as the open leader's bubble (docs/specs/123-the-leaders-at-the-table.md §6, which changes docs/specs/106-a-quick-question.md §3 and docs/specs/121-the-day-the-morning-and-the-night.md §6; decisions §181, §201):
// the person presses the open leader's head (tabs.js draws it as a button carrying `data-ask-head="<tab>"`, and opens the bubble with `openAsk(tab)`), and a bubble stands under it on orkUI's raised panel, its tail under the head's centre, at most 440 px
// wide and kept inside the window. Its states are the line's that was: **asking** (the field focused; Enter sends `ideas.ask {party, q}`, party "" on the Orkmaster's tab; the field is kept when the bubble is closed), **reading** (the question
// muted, *The <Leader> is reading the map* with orkUI's `ork-think`), **answered** (the question muted, the answer in the body face with its line breaks — plain text, never Markdown —, up to four sources as small chips, **Make it a goal**,
// *Ask more*), **failed** (its error). The answer is the host's (`town.ask`, one for the project): it stays until it is put away (× on an answer: `ideas.ask_clear`), a bubble closed with the answer in it shows nothing more on the head, and
// opening it shows the answer. **Make it a goal** tells the host (`ideas.ask_goal`) and opens the new goal's field with that line written (the field is the hand's, addressed to the open tab as it always is), and the bubble gives way to it.
// The evening line (`Since`, concerns.js) is drawn at the bubble's top whenever the party's record has it; the bubble opens by itself once a day for a party, when its tab is open and the person has not seen the line today (a `localStorage` key a party a day,
// a convenience only: without it, once while the page lasts). The foot (a party's, not the Orkmaster's): *Its seat: <tool> · <tier>* and **Change**, which opens the leader's seat's popover (seatpop.js).
// Esc, × or a press outside closes it; the head keeps the focus. The desktop only: under 760 px wide and on a touch screen (§181.8) no head opens a bubble. Nothing over an open page: opening one puts the bubble away.
// Typing here never opens the new goal's field: the hand opens it on a key typed with nothing focused (hand/hand.js), and this field has the focus.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html } from "../html.js";
import { Head, Icon, TIER_WORDS } from "../orkui.js";
import { command, town } from "../link.js";
import { ORKMASTER, over } from "../frame/state.js";
import { fieldText } from "../hand/state.js";
import { openField } from "../hand/pluscard.js";
import { groupsOf, mapName, toolOf, wide } from "./data.js";
import { Since, lookOf } from "./concerns.js";
import { SeatPop } from "./seatpop.js";
import { ToolMark } from "./header.js";

const Q_CHARS = 500;                                                  // as realm/board_ask.py Q_CHARS
const CROWN = { race: "peon", tier: "crown" };                        // the Orkmaster's head, as the tabs and the notice draw it
const WIDTH = 440, EDGE = 16, TAIL = 28;                              // the bubble's widest, its distance from the window's edge, its tail's usual place from its left

/** The tab whose bubble is open: a party's slug, "" for the Orkmaster's, null while none is. */
export const askOpen = signal(null);
const keyOf = (tab) => (!tab || tab === ORKMASTER ? "" : tab);
/** Opens the bubble of a tab (`ORKMASTER`, "" or a party's slug); the head that carries `data-ask-head` is what it stands under. */
export const openAsk = (tab) => { askOpen.value = keyOf(tab); };
export const closeAsk = () => { askOpen.value = null; };

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

  const close = (back = true) => { askOpen.value = null; if (back) headOf(tab)?.focus?.(); };
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
        ${state === "asking" && html`<form class="table-ask__form" onSubmit=${send}>
          <input type="text" class="ork-field table-ask__field" ref=${field} aria-label=${words} placeholder=${`${words}…`} maxlength=${Q_CHARS} autocomplete="off" enterkeyhint="send"
            value=${q} disabled=${reading} onInput=${(e) => { setQ(e.currentTarget.value); drafts[party] = e.currentTarget.value; }} />
        </form>`}
        ${state === "asking" && reading && html`<p class="table-ask__reading ork-think" role="status">The ${readBy.name} is reading the map</p>`}
        ${state === "reading" && html`<p class="table-ask__q">${ask.q}</p><p class="table-ask__reading ork-think" role="status">The ${here.name} is reading the map</p>`}
        ${state === "answered" && html`<p class="table-ask__q">${ask.q}</p>
          <p class="table-ask__text">${ask.answer}</p>
          ${sources.length > 0 && html`<ul class="table-ask__srcs" aria-label="Where it is said">${sources.map((s) => html`<li key=${s} class="ork-chip table-ask__src">${s}</li>`)}</ul>`}
          <div class="table-ask__acts">${ask.goal && html`<button type="button" class="ork-btn primary" title=${ask.goal} onClick=${goal}>Make it a goal</button>`}<span class="table-ask__grow"></span>
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
  useEffect(() => { if (open !== null && (open !== key || !ok)) askOpen.value = null; }, [key, ok, open]);        // another tab, a page over the pane, a window too narrow: put away
  useEffect(() => {                                                  // the evening line: open once a day a party, when its tab is open
    if (!key || !line || !ok || askOpen.peek() !== null || !headOf(tab) || seen(key)) return;
    seeing(key);
    openAsk(tab);
  }, [key, line, ok]);
  if (!ok || open !== key || !headOf(tab)) return null;
  return html`<${Bubble} key=${key} tab=${tab} party=${key} g=${g} parties=${parties} look=${look} />`;
}
