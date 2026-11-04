// The Orkmaster's column (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part B, decisions §206.2–§206.3; mockup docs/mockups/goal-card/): pinned at the window's left at the wide width (frame/frame.js), the table's height, the same on every tab, off the table on
// orkUI's room as the hand is. **Its head is the Orkmaster's tab** — the crown and *The Orkmaster*, `role="tab"`, open at first, underlined when open; pressed again, the open tab's head asks (ask.js `data-ask-head`) — and under it three piles of the project's goals (piles.js):
// *In analysis*, *To review*, *At work · later*. **What a press does**: a face-down card cannot be picked, its press lifts the pile's list over the pane in the Orkmaster's order (**Next** moves a goal before the first goal of its own party that waits its turn, with `ideas.move` as dragging does; **Remove** drops it, as the
// goal's menu does); a face-up card picks its goal (`picked`, as a stack does); a card of To review lifts **Start now** (`ideas.confirm`) and **Hold** (`ideas.ripe_hold`: the wait held, it starts when the person presses Start now), a put-off one **Start now** and
// **Back to review** (`ideas.ripe_back`). *Tonight* waits for a host command that puts an agreed goal off to the night (none yet). Esc or a press away puts the lifted thing away. The moves between piles are colmotion.js's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon } from "../orkui.js";
import { ORKMASTER, openOver, openTab, pick, picked, tab } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { act, mapData } from "../shell/store.js";
import { board } from "../board/store.js";
import { openTabOf, partiesAll, partiesNow, mapName, waitRuns } from "./data.js";
import { askOpen, closeAsk, desk, openAsk } from "./ask.js";
import { DropAsk, GoalMenu } from "./dropgoal.js";
import { liftDecision } from "../hand/state.js";
import { Said } from "../hand/sayonce.js";
import { ACTIVE, Pile, PILES, lookAt, nextWords, pilesOf, underOf } from "./piles.js";
import { useColumnMotion } from "./colmotion.js";
import { moodOf } from "./moods.js";
import { holdWords, waitsWords } from "./holdwords.js";
import { SetupBubble } from "../hand/setupcards.js";
import { laidNow } from "./laying.js";

const CROWN = { race: "peon", tier: "crown" };                   // the Orkmaster's head
export const columnPick = { slug: "" };                          // the goal the column picked last: the table does not move to its party's tab for it (table.js), the column is on every tab

/** The Orkmaster's tab: the column's head. Open at first; pressed again, it asks the Orkmaster (the bubble, ask.js). The project's ▾ beside it (*Switch project*). */
function Top({ parties, all }) {
  const open = openTabOf(tab.value, all) === ORKMASTER, name = currentProject.value?.name || "The project", ask = desk() && all.length > 0;
  const from = { title: mapName(openTabOf(tab.value, all), all), key: "" };
  const press = () => { if (!open) openTab(ORKMASTER); else if (ask) (askOpen.value === "" ? closeAsk() : openAsk(ORKMASTER)); };
  const keys = (e) => {
    if (e.key !== "ArrowRight" && e.key !== "End") return;
    const first = parties[0]?.slug;
    if (!first) return;
    e.preventDefault();
    openTab(first);
    requestAnimationFrame(() => document.getElementById(`tab-${first}`)?.focus());
  };
  return html`<div class="col-head" role="tablist" aria-label="The Orkmaster" onKeyDown=${keys}>
    <button type="button" class=${cls("ork-tab col-head__tab", { "is-open": open })} role="tab" id=${`tab-${ORKMASTER}`} data-tab=${ORKMASTER} data-ask-head=${open && ask ? ORKMASTER : undefined} aria-selected=${String(open)} aria-controls="table-pane"
      aria-haspopup=${ask ? "dialog" : undefined} aria-expanded=${ask && open ? String(askOpen.value === "") : undefined} aria-label=${`The Orkmaster · ${name}`}
      title=${open && ask ? `The Orkmaster: who does what. Press again to ask it (${name})` : `The Orkmaster: who does what (${name})`} onClick=${press}>
      <${Head} race=${CROWN.race} tier=${CROWN.tier} mood=${moodOf(null)} /><span class="col-head__nm">The Orkmaster</span>
    </button>
    ${currentProject.value && html`<button type="button" class="ork-btn quiet table-switch col-head__switch" aria-label="Switch project" title="Switch project" onClick=${() => openOver("projects", {}, from, "Projects")}><${Icon} name="chevron-down" /></button>`}
  </div>`;
}

/** **Remove** on a goal's row of the list: asks in place (*Drop this goal?*, dropgoal.js `DropAsk`) and drops it as the goal's menu does (the goal's work stops first). */
function Remove({ n }) {
  const [asking, setAsking] = useState(false);
  return asking ? html`<${DropAsk} slug=${n.slug} onKeep=${() => setAsking(false)} onDone=${() => setAsking(false)} />`
    : html`<button type="button" class="ork-btn quiet" data-remove=${n.slug} onClick=${() => setAsking(true)}>Remove</button>`;
}

/** **Change…** and **Start now** on the row of an agreed decision whose wait runs (decisions §240.2): *Start now* confirms it (`ideas.confirm`, as *Start now* of To review does); *Change…* holds the wait (`ideas.ripe_hold`), which
 *  makes the decision the person's move again: its card is dealt into the hand (data.js `stopsOfProject`) and lifted (hand.js, `liftDecision`); the goal lies put off in At work · later while it is held. */
function Agreed({ n, close }) {
  const [busy, setBusy] = useState(false);
  const run = (name, then) => async () => { setBusy(true); try { if (await act(name, { idea: n.slug })) { then?.(); close(); } } finally { setBusy(false); } };
  return html`<button type="button" class="ork-btn quiet" data-change=${n.slug} disabled=${busy} title="Hold its wait and open its decision in the hand" onClick=${run("ideas.ripe_hold", () => { liftDecision.value = n.slug; })}>Change…</button>
    <button type="button" class="ork-btn quiet" data-start=${n.slug} disabled=${busy} title="Confirm the decision now: its leaders write the spec" onClick=${run("ideas.confirm")}>Start now</button>`;
}

/** **Talk** on the row of a goal the person holds (spec 130 E.3): the route card left the hand, so its way back is here. */
function Talk({ n, close }) {
  const [busy, setBusy] = useState(false);
  const run = async () => { setBusy(true); try { if (await act("ideas.talk", { idea: n.slug })) close(); } finally { setBusy(false); } };
  return html`<button type="button" class="ork-btn quiet" data-talk=${n.slug} disabled=${busy} title="The leaders answer in short; nothing is made yet" onClick=${run}>Talk</button>`;
}

/** In analysis, read out over the pane in the Orkmaster's order: each goal's rune and whole title; the one being written says so, a goal put off says **not before 14:05** (holdwords.js, spec 138 B.5), a goal held says **Held** and has **Talk** (spec 130 E.3), the others have **Next** (after the front one) and **Remove**. */
function List({ items, place, close }) {
  const before = (i) => items.slice(0, i).find(({ n }) => n.goal === items[i].n.goal && !ACTIVE.includes(n.state))?.n.slug;           // *Next*: before the first goal of its own party still waiting its turn (the Board moves a goal among its party's, `ideas.move`)
  return html`<div class="ork-frame col-lift col-list" role="dialog" aria-label="In analysis, in order" data-lift="list" style=${place}>
    <h3 class="col-lift__t">In analysis</h3>
    <p class="col-lift__cap">Face down: their specs are not written yet, so their names are on their other side. In the Orkmaster's order:</p>
    <ol class="col-list__rows">${items.map(({ n }, i) => {
      const writing = i === 0 && ACTIVE.includes(n.state) && !n.asks_you;
      return html`<li key=${n.slug} class="col-list__row" data-goal=${n.slug}><${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} /><span class="col-list__nm">${n.title}</span>
        ${writing ? html`<span class="col-lift__cap">${n.state === "talk" ? "talked over" : "writing"}</span>`
          : html`${holdWords(n) && html`<span class="col-lift__cap col-list__hold" data-hold=${n.slug}>${holdWords(n)}</span>`}<span class="col-list__acts">${waitRuns(n) && html`<${Agreed} n=${n} close=${close} />`}${n.held_for === "hold" && html`<${Talk} n=${n} close=${close} />`}${before(i) && html`<button type="button" class="ork-btn quiet" data-next=${n.slug} aria-label=${`Next: ${n.title}`} onClick=${() => act("ideas.move", { slug: n.slug, before: before(i) })}>Next</button>`}<${Remove} n=${n} /></span>`}</li>`;
    })}</ol>
    <div class="col-lift__acts"><button type="button" class="ork-btn quiet" onClick=${close}>Close</button></div>
  </div>`;
}

/** A card's choices, beside it: **Start now** and **Hold** on a card of To review, **Start now** and **Back to review** on a put-off one. The commands are the wait's own (`ideas.confirm`, `ideas.ripe_hold`, `ideas.ripe_back`). */
function Acts({ n, off, place, close }) {
  const [busy, setBusy] = useState(false);
  const look = lookAt(n);                                                  // a spec made waits for its look (spec 144 B.2): Start now passes its plan (`ideas.start_now`), and there is no Hold of a decision's wait
  const run = (name, args) => async () => { setBusy(true); try { if (await act(name, args || { idea: n.slug })) close(); } finally { setBusy(false); } };
  const ripe = n.back?.ripe && !n.back.ripe.by, title = n.title || n.short || "";           // a lifted card says its title once (docs/specs/140 A4, decisions §247.6): its heading is the whole title, a line that repeats it is not drawn, what it says is one sentence and the rest is behind its …
  const cap = off === "held" ? "Held: nothing starts it until you press Start now." : off === "night" ? `Later, tonight ${String(board.value?.night || "01:00-07:00").split("-")[0]}: it starts by itself in the night's window.`
    : look ? `Starts by itself at ${look}. Read it on the tabs, and ask the Orkmaster to change it.`
    : ripe ? "Its spec is ready; it starts by itself in its turn. Read it on the tabs, and ask a leader there to change it." : "Its spec is ready; it waits for your word to start.";
  return html`<div class="ork-frame col-lift col-acts" role="dialog" aria-label=${`${n.title}: when it starts`} data-lift="acts" data-goal=${n.slug} style=${place}>
    <h3 class="col-lift__t"><${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} />${title}</h3>
    <${Said} key=${n.slug} title=${[n.title, n.short]} lines=${[cap]} tag="col-lift__cap" />
    <div class="col-lift__acts">
      <button type="button" class="ork-btn primary" data-now=${n.slug} disabled=${busy} title="Its sections are written now" onClick=${look ? run("ideas.start_now", { slug: n.slug }) : run("ideas.confirm")}>Start now</button>
      ${look ? null : off ? (off === "held" && html`<button type="button" class="ork-btn" data-back=${n.slug} disabled=${busy} title="Its wait begins again" onClick=${run("ideas.ripe_back")}>Back to review</button>`)
        : html`<button type="button" class="ork-btn" data-later=${n.slug} disabled=${busy} title="Nothing starts it until you press Start now" onClick=${run("ideas.ripe_hold")}>Hold</button>`}
      <${GoalMenu} slug=${n.slug} where="inline" />
    </div>
  </div>`;
}

/** Where a lifted thing stands: beside the column, at the height of the card (or of the pile's title), kept inside the window. */
function useBeside(root, key, sel) {
  const [at, setAt] = useState("");
  useLayoutEffect(() => {
    const host = root.current, el = host?.querySelector(sel);
    if (!host || !el) return;
    const h = host.getBoundingClientRect(), r = el.getBoundingClientRect();
    setAt(`left:${Math.round(h.width + 8)}px;top:${Math.max(0, Math.round(Math.min(r.top - h.top, h.height - 160)))}px`);
  }, [key]);
  return at;
}

export function Column() {
  const root = useRef(), nodes = mapData.value?.nodes || [], piles = pilesOf(nodes), parties = partiesNow(), all = partiesAll(), [lift, setLift] = useState(null);
  useColumnMotion(root, piles.work);
  const gone = lift?.kind === "acts" && !nodes.some((n) => n.slug === lift.slug);
  useEffect(() => { if (gone || (lift?.kind === "list" && !piles.analysis.length)) setLift(null); });
  useEffect(() => {                                                                    // Esc or a press away puts the lifted thing away
    if (!lift) return undefined;
    const key = (e) => { if (e.key === "Escape" && !e.defaultPrevented && !e.target.closest?.(".table-drop")) { e.preventDefault(); setLift(null); } };
    const away = (e) => { if (!e.target.closest?.(".col-lift, .col-card")) setLift(null); };
    addEventListener("keydown", key, true);                                             // first: what the column lifted is the topmost thing (a question asked in it takes its own Esc first)
    document.addEventListener("pointerdown", away, true);
    return () => { removeEventListener("keydown", key, true); document.removeEventListener("pointerdown", away, true); };
  }, [lift?.kind, lift?.slug]);
  const press = (n, pile, off) => {
    if (pile === "analysis") { setLift(lift?.kind === "list" ? null : { kind: "list" }); return; }              // face down: it cannot be picked, its press lifts the pile's list
    columnPick.slug = picked.value === n.slug ? "" : n.slug;
    if (pile === "work" && !off) { setLift(null); pick(n.slug); return; }                                      // at work: picked, as a stack is
    if (lift?.kind === "acts" && lift.slug === n.slug) { setLift(null); if (picked.value === n.slug) pick(n.slug); return; }
    setLift({ kind: "acts", slug: n.slug, off });
    if (picked.value !== n.slug) pick(n.slug);
  };
  const place = useBeside(root, `${lift?.kind}:${lift?.slug}`, lift?.kind === "acts" ? `.col-card[data-goal="${lift.slug}"]` : '.col-sec[data-pile="analysis"]');
  const under = { analysis: underOf(piles.analysis) || waitsWords(piles.analysis.map((x) => x.n)), review: nextWords(piles.review), work: "" }, item = lift?.kind === "acts" ? nodes.find((n) => n.slug === lift.slug) : null;
  return html`<div class="col" ref=${root} data-col="1">
    <${Top} parties=${parties} all=${all} />
    <${SetupBubble} />
    ${laidNow() && html`<div class="col-scroll">${PILES.map(([id, title]) => html`<${Pile} key=${id} id=${id} title=${title} items=${piles[id]} under=${under[id]} onPress=${press} open=${lift?.kind === "list"} />`)}</div>`}
    ${lift?.kind === "list" && html`<${List} items=${piles.analysis} place=${place} close=${() => setLift(null)} />`}
    ${item && !gone && html`<${Acts} n=${item} off=${lift.off} place=${place} close=${() => setLift(null)} />`}
  </div>`;
}
