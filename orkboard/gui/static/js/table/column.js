// The Orkmaster's column (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part B, decisions §206.2–§206.3; mockup docs/mockups/goal-card/): pinned at the window's left at the wide width (frame/frame.js), the table's height, the same on every tab, off the table on
// orkUI's room as the hand is. **Its head is the Orkmaster's tab** — the crown and *The Orkmaster*, `role="tab"`, open at first, underlined when open; pressed again, the open tab's head asks (ask.js `data-ask-head`) — and under it three piles of the project's goals (piles.js):
// *In analysis*, *To review*, *At work · later*. **What a press does**: a face-down card cannot be picked, its press lifts the pile's list over the pane in the Orkmaster's order (**Next** moves a goal before the first goal of its own party that waits its turn, with `ideas.move` as dragging does; **Remove** drops it, as the
// goal's menu does); a face-up card picks its goal (`picked`, as a stack does); a card of To review lifts **Start now** (`ideas.confirm`) and **Later today** (`ideas.ripe_hold`: the wait held, it starts when the person presses Start now), a put-off one **Start now** and
// **Back to review** (`ideas.ripe_back`). *Tonight* waits for a host command that puts an agreed goal off to the night (none yet). Esc or a press away puts the lifted thing away. The moves between piles are colmotion.js's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon } from "../orkui.js";
import { ORKMASTER, openOver, openTab, pick, picked, tab } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { act, mapData } from "../shell/store.js";
import { openTabOf, partiesAll, partiesNow, mapName } from "./data.js";
import { askOpen, closeAsk, desk, openAsk } from "./ask.js";
import { DropAsk, GoalMenu } from "./dropgoal.js";
import { ACTIVE, Pile, PILES, nextWords, pilesOf, underOf } from "./piles.js";
import { useColumnMotion } from "./colmotion.js";
import { moodOf } from "./moods.js";

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
    <button type="button" class="ork-btn quiet table-switch col-head__switch" aria-label="Switch project" title="Switch project" onClick=${() => openOver("projects", {}, from, "Projects")}><${Icon} name="chevron-down" /></button>
  </div>`;
}

/** **Remove** on a goal's row of the list: asks in place (*Drop this goal?*, dropgoal.js `DropAsk`) and drops it as the goal's menu does (the goal's work stops first). */
function Remove({ n }) {
  const [asking, setAsking] = useState(false);
  return asking ? html`<${DropAsk} slug=${n.slug} onKeep=${() => setAsking(false)} onDone=${() => setAsking(false)} />`
    : html`<button type="button" class="ork-btn quiet" data-remove=${n.slug} onClick=${() => setAsking(true)}>Remove</button>`;
}

/** In analysis, read out over the pane in the Orkmaster's order: each goal's rune and whole title; the one being written says so, the others have **Next** (after the front one) and **Remove**. */
function List({ items, place, close }) {
  const before = (i) => items.slice(0, i).find(({ n }) => n.goal === items[i].n.goal && !ACTIVE.includes(n.state))?.n.slug;           // *Next*: before the first goal of its own party still waiting its turn (the Board moves a goal among its party's, `ideas.move`)
  return html`<div class="ork-frame col-lift col-list" role="dialog" aria-label="In analysis, in order" data-lift="list" style=${place}>
    <h3 class="col-lift__t">In analysis</h3>
    <p class="col-lift__cap">Face down: their specs are not written yet, so their names are on their other side. In the Orkmaster's order:</p>
    <ol class="col-list__rows">${items.map(({ n }, i) => {
      const writing = i === 0 && (n.state === "reading" || n.state === "planning" || n.state === "talk") && !n.asks_you;
      return html`<li key=${n.slug} class="col-list__row" data-goal=${n.slug}><${Elem} name=${n.element} dim=${!n.element} /><span class="col-list__nm">${n.title}</span>
        ${writing ? html`<span class="col-lift__cap">${n.state === "talk" ? "talked over" : "writing"}</span>`
          : html`<span class="col-list__acts">${before(i) && html`<button type="button" class="ork-btn quiet" data-next=${n.slug} aria-label=${`Next: ${n.title}`} onClick=${() => act("ideas.move", { slug: n.slug, before: before(i) })}>Next</button>`}<${Remove} n=${n} /></span>`}</li>`;
    })}</ol>
    <div class="col-lift__acts"><button type="button" class="ork-btn quiet" onClick=${close}>Close</button></div>
  </div>`;
}

/** A card's choices, beside it: **Start now** and **Later today** on a card of To review, **Start now** and **Back to review** on a put-off one. The commands are the wait's own (`ideas.confirm`, `ideas.ripe_hold`, `ideas.ripe_back`). */
function Acts({ n, off, place, close }) {
  const [busy, setBusy] = useState(false);
  const run = (name) => async () => { setBusy(true); try { if (await act(name, { idea: n.slug })) close(); } finally { setBusy(false); } };
  const cap = off === "held" ? "Held: nothing starts it until you press Start now." : off === "night" ? "Put off to the night's window." : n.back?.ripe && !n.back.ripe.by ? "Its spec is ready. It starts by itself in its turn; read it on the tabs, and ask a leader there to change it." : "Its spec is ready. It waits for your word to start.";
  return html`<div class="ork-frame col-lift col-acts" role="dialog" aria-label=${`${n.title}: when it starts`} data-lift="acts" data-goal=${n.slug} style=${place}>
    <h3 class="col-lift__t"><${Elem} name=${n.element} dim=${!n.element} />${n.short || n.title}</h3>
    <p class="col-lift__cap">${n.title}</p>
    <p class="col-lift__cap">${cap}</p>
    <div class="col-lift__acts">
      <button type="button" class="ork-btn primary" data-now=${n.slug} disabled=${busy} title="Its sections are written now" onClick=${run("ideas.confirm")}>Start now</button>
      ${off ? (off === "held" && html`<button type="button" class="ork-btn" data-back=${n.slug} disabled=${busy} title="Its wait begins again" onClick=${run("ideas.ripe_back")}>Back to review</button>`)
        : html`<button type="button" class="ork-btn" data-later=${n.slug} disabled=${busy} title="Hold it: nothing starts it until you press Start now" onClick=${run("ideas.ripe_hold")}>Later today</button>`}
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
  const under = { analysis: underOf(piles.analysis), review: nextWords(piles.review), work: "" }, item = lift?.kind === "acts" ? nodes.find((n) => n.slug === lift.slug) : null;
  return html`<div class="col" ref=${root} data-col="1">
    <${Top} parties=${parties} all=${all} />
    <div class="col-scroll">${PILES.map(([id, title]) => html`<${Pile} key=${id} id=${id} title=${title} items=${piles[id]} under=${under[id]} onPress=${press} open=${lift?.kind === "list"} />`)}</div>
    ${lift?.kind === "list" && html`<${List} items=${piles.analysis} place=${place} close=${() => setLift(null)} />`}
    ${item && !gone && html`<${Acts} n=${item} off=${lift.off} place=${place} close=${() => setLift(null)} />`}
  </div>`;
}
