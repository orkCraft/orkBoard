// The route card (docs/specs/100-a-goals-way-as-cards.md §1, part A; docs/specs/99-a-goals-way.md §4; decisions §133.1, §136.2, §140.2–§140.3, §147.4, §156.6, §158.2): a goal's first card, dealt as soon as the
// Orkmaster has routed it. Its face is the card of spec 101 (stopcard.js): the goal's element and name, the route's sign in its window with the Orkmaster's crowned head in its corner, the gem of its cost in the
// label row. Lifted (`RouteLifted`, in place of the plain answers): the route as the leaders' heads in order, each with a small × (a press on the head opens its seat popover as the table's does), a **+** offering
// the project's parties but Release (those the goal's marks touch first), the route in words, the cost (the gem and its words, said again from the answer of an edit), its place in line, and its one act: **Talk**
// (with **Later, by itself** only when the limits run low). A bug is Tech alone: *finding the cause* with **Talk**, or, when its report holds a failing test, **Start** with *The long way* beside it; another short goal (the row's `type`: a clean-up, a balance pass) says *<Party> alone* and its own line, with **Talk**.
// Registers itself with ways.js (`route`); startcard.js (the `start` row) reads the same helpers. The sheet is way.css, linked as hand.css is (frame/frame.js).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { command, toast } from "../link.js";
import { act, mapData } from "../shell/store.js";
import { SeatPop } from "../table/seatpop.js";
import { GoalMenu } from "../table/dropgoal.js";
import { groupsOf, nameOf, partiesAll } from "../table/data.js";
import { Gem, costOf } from "./cost.js";
import { way } from "./ways.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./way.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** Release's leader (realm/library.py): its party is never a step of a route (decisions §137.1, §140.3). */
const RELEASE = "release-manager";

// -- what an edit answered ----------------------------------------------------------------------------------------------------

/** The route, its cost and what depends on them, as `ideas.route_set` answered them, by goal: `{base, fields}`. `base` is the row as it was when the edit was made: while the Board still shows that row, the answer
 *  is said (the cost again at once); once the Board has the new row, the row is. */
const edits = signal({});

const sigOf = (row) => JSON.stringify([(row?.route || []).map((x) => x.party), row?.cost || null, !!row?.short, !!row?.reproduces, row?.offer || []]);

/** The row of a route card as it stands now: the host's row, or the answer of the last edit made on it while the Board has not yet caught up. */
export function viewOf(s) {
  const row = s.row || {}, e = edits.value[row.idea];
  return e && e.base === sigOf(row) ? { ...row, ...e.fields } : row;
}

// -- words ----------------------------------------------------------------------------------------------------------------------

/** *1st*, *2nd*, *3rd*, *4th*, *11th*, *22nd*. */
export function ordinal(n) {
  const t = n % 100, end = t >= 11 && t <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" })[n % 10] || "th";
  return `${n}${end}`;
}

const partyBy = (slug) => partiesAll().find((g) => g.slug === slug) || null;
/** A party's name as the Board says it (its slug while the map has not got it). */
export const partyName = (slug) => nameOf(partyBy(slug)) || slug;

/** The route in words: *Game design, then Art, then Tech*. */
export const routeWords = (steps) => steps.map((x) => partyName(x.party)).join(", then ");

/** The Orkmaster's head, crowned: the asker of every card here (it routes, the leaders answer later). */
export function orkHead() {
  const ork = mapData.value?.project?.orkmaster || null;
  return { race: ork?.race || "peon", tier: ork?.tier || "crown" };
}

const priceFrom = (c) => (c && Number.isFinite(Number(c.usd_low)) ? { low: Number(c.usd_low), high: Number(c.usd_high ?? c.usd_low) } : null);

/** A cost as the face says it: `{gem, words}`, *about 6 calls, about 4% of Claude's week*; null for a cost of nothing. The gem and the share come from cost.js. */
export function costLine(cost) {
  if (!cost) return null;
  const spend = costOf({ kind: "route", row: { cost } }), calls = Number(cost.calls) || 0;
  const words = [calls ? `about ${calls} ${calls === 1 ? "call" : "calls"}` : "", spend?.words || ""].filter(Boolean).join(", ");
  return words || spend ? { spend, words } : null;
}

/** The gem with the cost's words, on the lifted card. */
export function CostLine({ cost }) {
  const c = costLine(cost);
  if (!c) return null;
  return html`<div class="hand-spend hand-way__cost" data-cost=${c.spend?.gem || ""}><${Gem} cost=${c.spend} /><span class="hand-spend__words">${c.words}</span></div>`;
}

// -- the lifted card ----------------------------------------------------------------------------------------------------------------

/** The parties a **+** offers: the project's, but those on the route and Release (and Ideation, which judges pitches); the ones the goal's marks touch first. */
export function offered(v) {
  const on = new Set((v.route || []).map((x) => x.party)), touches = new Set(v.offer || []);
  return partiesAll().filter((g) => !on.has(g.slug) && g.leader?.slug !== RELEASE && !g.ideation)
    .sort((a, b) => Number(touches.has(b.slug)) - Number(touches.has(a.slug))).map((g) => ({ g, touches: touches.has(g.slug) }));
}

const hasSeat = (g, slug) => !!g && groupsOf(g).some((x) => x.seats.some((m) => m.slug === slug));

function Steps({ s, v, busy, send }) {
  const [seat, setSeat] = useState(""), [menu, setMenu] = useState(false), plus = useRef(), was = useRef(null);
  const steps = v.route || [], more = offered(v);
  useLayoutEffect(() => {                                               // (a layout effect: the Esc that follows the close at once is the card's) Esc closes the popover or the menu first, not the card; a press away closes the menu
    if (!seat && !menu) return undefined;
    const esc = (e) => {
      if (e.key !== "Escape") return;
      e.stopPropagation();
      e.preventDefault();
      if (menu) plus.current?.focus();
      setSeat("");
      setMenu(false);
    };
    const away = (e) => { if (menu && !e.target.closest?.(".hand-route__menu, .hand-route__add")) setMenu(false); };
    window.addEventListener("keydown", esc, true);
    document.addEventListener("pointerdown", away, true);
    return () => { window.removeEventListener("keydown", esc, true); document.removeEventListener("pointerdown", away, true); };
  }, [seat, menu]);
  const press = (slug) => {                                             // the popover closes itself on a press away: a press on the head that opened it must not open it again
    const open = was.current ?? seat;
    was.current = null;
    setMenu(false);
    setSeat(open === slug ? "" : slug);
  };
  const off = (slug) => send(steps.map((x) => x.party).filter((p) => p !== slug));
  const add = (slug) => { setMenu(false); send([...steps.map((x) => x.party), slug]); };
  const seatOf = seat && partyBy(seat), step = steps.find((x) => x.party === seat);
  return html`<div class="hand-route">
    <ol class="hand-route__steps" aria-label="The route">${steps.map((x) => {
      const g = partyBy(x.party), name = partyName(x.party), live = hasSeat(g, x.leader);
      return html`<li key=${x.party} class="hand-route__step" data-party=${x.party}>
        ${live ? html`<button type="button" class=${cls("hand-route__head", { "is-on": seat === x.party })} aria-haspopup="dialog" aria-expanded=${String(seat === x.party)} aria-label=${`${name}’s leader`} title=${name}
            onPointerDown=${() => { was.current = seat; }} onClick=${() => press(x.party)}>${x.head && html`<${Head} race=${x.head.race} tier=${x.head.tier} size="mid" />`}</button>`
          : html`<span class="hand-route__head" title=${name}>${x.head && html`<${Head} race=${x.head.race} tier=${x.head.tier} size="mid" />`}</span>`}
        <button type="button" class="ork-btn quiet hand-route__off" disabled=${busy || steps.length < 2} aria-label=${`Take ${name} off the route`}
          title=${steps.length < 2 ? "A route needs a party" : `Take ${name} off the route`} onClick=${() => off(x.party)}><${Icon} name="close" /></button>
      </li>`;
    })}
      ${more.length > 0 && html`<li class="hand-route__step is-add"><button type="button" ref=${plus} class="ork-btn hand-route__add" disabled=${busy} aria-haspopup="menu" aria-expanded=${String(menu)} aria-label="Add a party to the route"
        title="Add a party to the route" onClick=${() => { setSeat(""); setMenu(!menu); }}><${Icon} name="plus" /></button></li>`}
    </ol>
    ${menu && html`<div class="hand-route__menu" role="menu" aria-label="Add a party to the route">${more.map(({ g, touches }) => html`<button type="button" key=${g.slug} role="menuitem" class="ork-btn hand-route__pick"
        data-party=${g.slug} data-touches=${touches ? "1" : undefined} onClick=${() => add(g.slug)}>
        ${g.leader?.head && html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} />`}<span class="hand-route__pick-name">${nameOf(g)}</span>${touches && html`<span class="hand-route__touches">touches its map</span>`}</button>`)}</div>`}
    ${seat && seatOf && step && html`<div class="hand-route__pop"><${SeatPop} g=${seatOf} slug=${step.leader} from=${null} onClose=${() => setSeat("")} /></div>`}
  </div>`;
}

/** What a short goal that is no bug is, in a few plain words, by its type (`type`: the goal type's id): *Tech alone: a small clean-up*. */
const SMALL = { tidy: "a small clean-up", balance: "a small change to the numbers" };

/** A bug is the goal type `bug`; a route row of an older host has no `type` and is read as before (a short goal is a bug). */
const isBug = (v) => v.type === undefined || v.type === "bug";

/** A short goal in words: *Tech alone: finding the cause*, *Tech alone: the report has a failing test*, *Tech alone: a small clean-up*. */
function aloneWords(v) {
  const who = `${partyName(v.route?.[0]?.party || "")} alone`;
  return `${who}: ${isBug(v) ? (v.reproduces ? "the report has a failing test" : "finding the cause") : SMALL[v.type] || "a small change"}`;
}

/** The craft whose map is the opportunity tree (spec 102 §8.3). */
const PRODUCT = "product";

/** *Serves: <job>* (spec 102 §8.3, decisions §172.2): for a goal of a party whose craft is product, the jobs of Product's opportunity tree to choose from (`ideas.tree`); the choice is kept at once
 *  (`ideas.tree_attach {job, goal}`, an empty job takes it off), none chosen none attached. With no job kept, nothing is offered. */
function Serves({ idea, busy }) {
  const [tree, setTree] = useState(null), [job, setJob] = useState(""), [wait, setWait] = useState(false);
  useEffect(() => {
    let live = true;
    command("ideas.tree", {}, true).then((r) => {
      if (!live || !r) return;
      setTree(r);
      setJob((r.serves || []).find((x) => x.goal === idea)?.job || "");
    }).catch(() => {});
    return () => { live = false; };
  }, [idea]);
  const jobs = tree?.jobs || [];
  if (!jobs.length) return null;
  const choose = async (e) => {
    const next = e.currentTarget.value, was = job;
    setJob(next);
    setWait(true);
    const got = await act("ideas.tree_attach", { job: next, goal: idea });
    setWait(false);
    if (!got) setJob(was);                                              // refused: the host said why in a toast, the choice stays as it was
  };
  return html`<label class="hand-way__serves">
    <span class="cap">Serves:</span>
    <span class="ork-select"><select class="ork-field" name="serves" aria-label="Serves" value=${job} disabled=${busy || wait} onChange=${choose}>
      <option value="" selected=${!job}>No job</option>
      ${jobs.map((j) => html`<option key=${j.id} value=${j.id} selected=${j.id === job}>${j.want}</option>`)}
    </select></span>
  </label>`;
}

/** The route card lifted (in place of the plain answers; stopcard.js adds *Put it back*). */
export function RouteLifted({ s, close }) {
  const v = viewOf(s), idea = s.row.idea, [busy, setBusy] = useState(false), steps = v.route || [];
  const run = async (name, args, then) => {
    setBusy(true);
    try { return await act(name, { idea, ...args }); } finally { setBusy(false); then?.(); }
  };
  const send = async (route) => {                                       // an edit: no call; the answer says the route and its cost again
    const base = sigOf(s.row), got = await run("ideas.route_set", { route });
    if (got?.route) edits.value = { ...edits.value, [idea]: { base, fields: { route: got.route, cost: got.cost, short: !!got.short, reproduces: !!got.reproduces, offer: got.offer || [] } } };
  };
  const talk = async () => { if (await run("ideas.talk", {})) close?.(); };
  const start = async () => { if (await run("ideas.route_start", {})) close?.(); };
  const later = async () => {
    if (await run("ideas.route_later", {})) { toast("In line: it talks by itself after the limits reset."); close?.(); }
  };
  const short = !!v.short && steps.length === 1, report = short && isBug(v) && !!v.reproduces;
  return html`<div class="hand-way hand-way--route" data-short=${short ? "1" : undefined}>
    <${Steps} s=${s} v=${v} busy=${busy} send=${send} />
    ${short ? html`<p class="body hand-way__words">${aloneWords(v)}</p>`
      : html`<p class="body hand-way__words">${routeWords(steps)}</p>`}
    ${partyBy(s.row.goal)?.party_craft === PRODUCT && html`<${Serves} idea=${idea} busy=${busy} />`}
    <${CostLine} cost=${v.cost} />
    ${v.place > 0 && html`<p class="cap hand-way__place">${ordinal(v.place)} in line</p>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      ${report ? html`<button type="button" class="ork-btn primary" disabled=${busy} title="The report has its failing test: the work starts, with no Talk" onClick=${start}>Start</button>
          <button type="button" class="ork-btn quiet" disabled=${busy} title="Talk first, then the decision and the sections" onClick=${talk}>The long way</button>`
        : html`<button type="button" class="ork-btn primary" disabled=${busy} title="The leaders answer in short; nothing is made yet" onClick=${talk}>Talk</button>
          ${v.low && html`<button type="button" class="ork-btn" disabled=${busy} title="The limits run low: it waits in line and talks by itself after they reset" onClick=${later}>Later, by itself</button>`}`}
    </div>
    <div class="hand-way__more"><${GoalMenu} slug=${idea} where="inline" /></div>
  </div>`;
}

// What the face reads: the route's sign (a way onward) in its window, the Orkmaster's head over its corner (stopcard.js `headOf`), the cost's gem in its label row (cost.js `priceOf`).
way("route", { sign: "after", head: orkHead, price: (s) => priceFrom(viewOf(s).cost), Lifted: RouteLifted });
