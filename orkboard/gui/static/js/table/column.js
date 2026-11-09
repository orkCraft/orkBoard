// The Orkmaster's column (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md part B, decisions §206.2–§206.3; mockup docs/mockups/goal-card/; as spec 156 B changed it, decisions §261.1, §261.5): pinned at the window's left at the wide width (frame/frame.js), the table's height, the same on every tab, off the table on
// orkUI's room as the hand is. **Its head is the Orkmaster's tab** — the crown and *The Orkmaster*, `role="tab"`, open at first, underlined when open; pressed again, the open tab's head asks (ask.js `data-ask-head`) — and under it three piles of the project's goals (piles.js):
// *In analysis*, *To review*, *At work · later*. **What a press does**: any card, face down too, picks its goal (`picked`, frame/state.js: one pick across the window), the same card pressed again puts the pick away, as Esc, a press on an empty place of the column and the browser's back do (state.js); a pile hovered or focused fans
// its backs, so each is reached. A picked card of To review lifts **Start now** (`ideas.confirm`) and **Hold** (`ideas.ripe_hold`: the wait held, it starts when the person presses Start now), a put-off one **Start now** and **Back to review** (`ideas.ripe_back`), an agreed decision's
// **Change…** and **Start now**, a held one's **Talk** — beside the column, not over the pane (part C draws them on the table through the Orkmaster); *Next* and *Remove* of a goal are in its menu (dropgoal.js). *Tonight* waits for a host command that puts an agreed goal off to the night (none yet). The moves between piles (and a goal's start) are colmotion.js's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon } from "../orkui.js";
import { ORKMASTER, openOver, openTab, pick, picked, tab } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { act, mapData } from "../shell/store.js";
import { board } from "../board/store.js";
import { openTabOf, partiesAll, partiesNow, mapName, waitRuns } from "./data.js";
import { askOpen, closeAsk, desk, openAsk } from "./ask.js";
import { GoalMenu } from "./dropgoal.js";
import { liftDecision } from "../hand/state.js";
import { Said } from "../hand/sayonce.js";
import { Pile, PILES, WORK_SHOWN, atWorkWords, lookAt, nextWords, pilesOf, underOf, writing, writingWords } from "./piles.js";
import { giveWay } from "./giveway.js";
import { useColumnMotion } from "./colmotion.js";
import { moodOf } from "./moods.js";
import { holdWords, offWords, waitsWords } from "./holdwords.js";
import { SetupBubble } from "../hand/setupcards.js";
import { laidNow } from "./laying.js";
import { Passing, askedWords } from "./passing.js";
import { ProjectLine, useProjectNow } from "./projectdeal.js";

const CROWN = { race: "peon", tier: "crown" };                   // the Orkmaster's head

/** The Orkmaster's tab: the column's head, its first line the project's name, its second the project's kind and stage (projectdeal.js; spec 161 J). *The Orkmaster* is in its `aria-label` and `title` only. Open at first; pressed again, it asks the Orkmaster (the bubble, ask.js). The project's ▾ beside it (*Switch project*). */
function Top({ parties, all }) {
  const open = openTabOf(tab.value, all) === ORKMASTER, name = currentProject.value?.name || "The project", ask = desk() && all.length > 0;
  const from = { title: mapName(openTabOf(tab.value, all), all), key: "" }, now = useProjectNow(currentProject.value?.path || "");
  const press = () => { if (!open) openTab(ORKMASTER); else if (ask) (askOpen.value === "" ? closeAsk() : openAsk(ORKMASTER)); };
  const keys = (e) => {
    if (e.key !== "ArrowRight" && e.key !== "End") return;
    const first = parties[0]?.slug;
    if (!first) return;
    e.preventDefault();
    openTab(first);
    requestAnimationFrame(() => document.getElementById(`tab-${first}`)?.focus());
  };
  return html`<div class="col-head" role="tablist" aria-label="The Orkmaster" data-race="orkmaster" onKeyDown=${keys}>
    <span class=${cls("ork-pennant small", { "is-open": open })} data-party="orkmaster" aria-hidden="true"></span>
    <button type="button" class=${cls("ork-tab col-head__tab", { "is-open": open })} role="tab" id=${`tab-${ORKMASTER}`} data-tab=${ORKMASTER} data-ask-head=${open && ask ? ORKMASTER : undefined} aria-selected=${String(open)} aria-controls="table-pane"
      aria-haspopup=${ask ? "dialog" : undefined} aria-expanded=${ask && open ? String(askOpen.value === "") : undefined} aria-label=${`The Orkmaster · ${name}`}
      title=${open && ask ? `The Orkmaster: who does what. Press again to ask it (${name})` : `The Orkmaster: who does what (${name})`} onClick=${press}>
      <${Head} race=${CROWN.race} tier=${CROWN.tier} mood=${moodOf(null)} /><span class="col-head__nm" title=${name}>${name}</span>
    </button>
    <${ProjectLine} now=${now} />
    ${currentProject.value && html`<button type="button" class="ork-btn quiet table-switch col-head__switch" aria-label="Switch project" title="Switch project" onClick=${() => openOver("projects", {}, from, "Projects")}><${Icon} name="chevron-down" /></button>`}
  </div>`;
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

/** A card's choices, beside it: **Start now** and **Hold** on a card of To review, **Start now** and **Back to review** on a put-off one. The commands are the wait's own (`ideas.confirm`, `ideas.ripe_hold`, `ideas.ripe_back`). */
function Acts({ n, off, pile, place, close }) {
  const [busy, setBusy] = useState(false);
  const look = lookAt(n);                                                  // a spec made waits for its look (spec 144 B.2): Start now passes its plan (`ideas.start_now`), and there is no Hold of a decision's wait
  const run = (name, args) => async () => { setBusy(true); try { if (await act(name, args || { idea: n.slug })) close(); } finally { setBusy(false); } };
  const ripe = n.back?.ripe && !n.back.ripe.by, title = n.title || n.short || "";           // a lifted card says its title once (docs/specs/140 A4, decisions §247.6): its heading is the whole title, a line that repeats it is not drawn, what it says is one sentence and the rest is behind its …
  if (pile === "analysis") {                                                  // a face-down card: an agreed decision's Change… and Start now, a goal held's Talk, the words of its wait, and the goal's menu (Next, Drop this goal…)
    return html`<div class="ork-frame col-lift col-acts" role="dialog" aria-label=${`${n.title}: what waits`} data-lift="acts" data-goal=${n.slug} style=${place}>
      <h3 class="col-lift__t"><${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} />${title}</h3>
      ${!holdWords(n) && !offWords(n) && html`<p class="col-lift__cap">Face down: its spec is not written yet.</p>`}${holdWords(n) && html`<p class="col-lift__cap" data-hold=${n.slug}>${holdWords(n)}</p>`}${offWords(n) && html`<p class="col-lift__cap" data-off=${n.slug}>${offWords(n)}</p>`}
      <div class="col-lift__acts">${waitRuns(n) && html`<${Agreed} n=${n} close=${close} />`}${n.held_for === "hold" && html`<${Talk} n=${n} close=${close} />`}<${GoalMenu} slug=${n.slug} where="inline" /></div>
    </div>`;
  }
  if (pile === "review" && writing(n)) {                                      // its spec is being written (Specs): nothing to start or hold yet, only its menu
    return html`<div class="ork-frame col-lift col-acts" role="dialog" aria-label=${`${n.title}: its spec`} data-lift="acts" data-goal=${n.slug} style=${place}>
      <h3 class="col-lift__t"><${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} />${title}</h3>
      <p class="col-lift__cap" data-writing=${n.slug}>${n.state === "planning" ? "The Orkmaster is writing its spec." : "Its leaders are writing its spec."}</p>
      <div class="col-lift__acts"><${GoalMenu} slug=${n.slug} where="inline" /></div>
    </div>`;
  }
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

/** *At work · later* gives way to the window and the column never scrolls (spec 147 B.5, decisions §251.4): the room the pile may take is measured (its box is whatever the fan and the deck leave under their own, never what the pile holds), and `giveWay` (giveway.js) says how far each card behind
 *  lies below the front one, or that the pile sinks under the hand's rim. Measured again whenever the box changes (a resized window, a goal moved from one pile to another). `laid`: the piles are drawn. */
function useGiveWay(root, count, laid) {
  const [way, setWay] = useState(null);
  useLayoutEffect(() => {
    const room = laid ? root.current?.querySelector(".col-room") : null;
    if (!room) { setWay(null); return undefined; }
    const measure = () => {
      const next = giveWay({ room: room.clientHeight, front: room.querySelector(".col-card--up")?.offsetHeight || 202, behind: Math.max(0, Math.min(count, WORK_SHOWN) - 1) });
      setWay((was) => (was && was.sunk === next.sunk && was.push === next.push && was.steps.join() === next.steps.join() ? was : next));
    };
    measure();
    const watch = new ResizeObserver(measure);
    watch.observe(room);
    return () => watch.disconnect();
  }, [count, laid]);
  return way;
}

export function Column() {
  const root = useRef(), nodes = mapData.value?.nodes || [], piles = pilesOf(nodes), parties = partiesNow(), all = partiesAll(), [lift, setLift] = useState(null);
  useColumnMotion(root);
  const laid = laidNow(), way = useGiveWay(root, piles.work.length, laid);
  const gone = lift?.kind === "acts" && (!nodes.some((n) => n.slug === lift.slug) || picked.value !== lift.slug);                 // the choices go with the pick
  useEffect(() => { if (gone) setLift(null); });
  useEffect(() => {                                                                    // Esc or a press away puts the lifted thing away
    if (!lift) return undefined;
    const key = (e) => { if (e.key === "Escape" && !e.defaultPrevented && !e.target.closest?.(".table-drop")) { e.preventDefault(); setLift(null); if (lift.kind === "acts" && picked.peek() === lift.slug) pick(""); } };      // the card's choices go with its pick: one Esc puts both away (spec 156 Done when 1)
    const away = (e) => { if (!e.target.closest?.(".col-lift, .col-card")) setLift(null); };
    addEventListener("keydown", key, true);                                             // first: what the column lifted is the topmost thing (a question asked in it takes its own Esc first)
    document.addEventListener("pointerdown", away, true);
    return () => { removeEventListener("keydown", key, true); document.removeEventListener("pointerdown", away, true); };
  }, [lift?.kind, lift?.slug]);
  const press = (n, pile, off) => {                                                                          // any card picks its goal, face down too; the same card again puts the pick away (state.js)
    const was = picked.value === n.slug, acts = !(pile === "work" && !off);                                 // a card at work has no choices; every other picked card has its choices (and its menu) beside it
    setLift(!was && acts ? { kind: "acts", slug: n.slug, off, pile } : null);
    pick(n.slug);
  };
  useEffect(() => {                                                                                          // a press on an empty place of the column puts the pick away
    const away = (e) => { if (picked.value && e.target.matches?.(".col, .col-scroll, .col-sec, .col-room, .col-pile, .col-plab, .col-under")) pick(picked.value); };
    const host = root.current;
    host?.addEventListener("click", away);
    return () => host?.removeEventListener("click", away);
  }, []);
  const place = useBeside(root, `${lift?.kind}:${lift?.slug}`, `.col-card[data-goal="${lift?.slug}"]`);
  const behind = piles.analysis.find(({ n }) => askedWords(n.slug));                                          // a goal asked of another leader: its line is the pile's (a back of the hand has no room to say it)
  const wrote = writingWords(piles.review), next = nextWords(piles.review);                                  // Specs: what is being written, then (a second line) the next to start by itself
  const under = { analysis: underOf(piles.analysis) || waitsWords(piles.analysis.map((x) => x.n)), review: wrote || next, work: atWorkWords(piles.work) }, item = lift?.kind === "acts" ? nodes.find((n) => n.slug === lift.slug) : null;
  return html`<div class="col" ref=${root} data-col="1">
    <${Top} parties=${parties} all=${all} />
    <${SetupBubble} />
    ${laid && html`<div class="col-scroll">${PILES.map(([id, title]) => html`<${Pile} key=${id} id=${id} title=${title} items=${piles[id]} under=${under[id]} asked=${id === "analysis" && behind ? askedWords(behind.n.slug) : id === "review" && wrote ? next : ""} onPress=${press} way=${id === "work" ? way : null} />`)}</div>`}
    <${Passing} />
    ${item && !gone && html`<${Acts} n=${item} off=${lift.off} pile=${lift.pile} place=${place} close=${() => setLift(null)} />`}
  </div>`;
}
