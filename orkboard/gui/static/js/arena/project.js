// The project's level (docs/specs/70-orkmaster-and-the-project.md §2–§3, decisions §85): a press on the Orkmaster in the project's line shows the whole of the project in place of one party —
// a column for each party in the Board's order (Operations is not one), its head (the leader's head, its name, *k/n*; a press opens that party) on the canvas, under the heads the table
// (orkUI's `.ork-table`, as the party's field: docs/specs/78-the-project-on-the-table.md) with each party's goals as the field's cards (5:7: the goal's element, its type's sign, its type, its title,
// its state's words) grouped *Planning*, *At work*, *Waits for main*, then *Flags (n)* folded. A press on a card opens the goal's screen in the drawer.
// Wider than the field the columns scroll sideways and the heads stay. Hovering or focusing a deck draws, with arrows.js, a link to each deck its route names in another column (the pitch it came from,
// the release it went into); nothing at rest. Above the columns the Orkmaster's head and *New party* (its deck: projectdeal.js), below them *New goal* (projectdeal.js, a goal's party from the Orkmaster).
// The code's goal is a party; its idea is a goal; its deck is a goal drawn small, never a word a person reads.
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Chev, Elem, Head, Sign } from "../orkui.js";
import { PROJECT, goalList } from "../board/store.js";
import { showIdea, showPlan } from "../shell/store.js";
import { countTip, countWords, goalsOf, nodesOf } from "./arenawords.js";
import { elementOf, goalMark } from "./goalwords.js";
import { pitchMark } from "./pitchwords.js";
import { typeSign } from "./stacks.js";
import { ArrowLines, segment } from "./arrows.js";
import { reducedMotion } from "./motion.js";
import { PartyList, show } from "./partylist.js";
import { NewGoalPile, NewPartyPile } from "./projectdeal.js";
import { orkLinks } from "./collidewords.js";
import { GROUPS, PARTIES_WORDS, THE_PROJECT, deckCount, decksOf, emptyWords, linksOf } from "./projectwords.js";

const TONES = { danger: "is-danger", alert: "is-alert" };

/** The classes a goal's card wears (as the field's Planning card, field.js `PlanCard`): at work, failed, waiting for you; a Planning goal not at work dashed; a done one muted. */
const deckCls = (key, mark) => ({ "is-run": mark.sign === "work", "is-fail": mark.tone === "danger", "is-stop": mark.sign === "alert",
  "is-wait": key === "planning" && mark.sign !== "work" && mark.sign !== "alert", "is-later": key === "waits" || key === "flags" });

/** One goal as a card on the table (spec 78 §2), the field's card: its element, its state's sign, its type's sign top right; its type's name, its title (two lines), its state's words.
 *  A press opens its screen (its plan when the plan waits). */
function Deck({ d, group, party, lit, setLit }) {
  const n = d.n, el = elementOf(n), mark = n.pitch ? pitchMark(n) : goalMark(n);
  const open = () => (n.needs_you === "plan" ? showPlan(n.slug, "", { via: "map" }) : showIdea(n.slug, { via: "map" }));
  const on = () => setLit(n.slug), off = () => setLit((now) => (now === n.slug ? "" : now));
  return html`<div class="arena-stk"><button type="button" class=${cls("arena-task arena-pdeck", deckCls(group, mark), { "is-lit": lit === n.slug })} data-slug=${n.slug} data-party=${party}
      title=${`${n.title} · ${d.words}`} aria-label=${`${n.title}, ${d.words}`} onClick=${open} onMouseEnter=${on} onMouseLeave=${off} onFocus=${on} onBlur=${off}>
    <span class="arena-task__top"><${Elem} name=${el.name} dim=${el.dim} />
      ${mark.sign && html`<span class=${cls("arena-pdeck__mark", TONES[mark.tone])} title=${mark.label || undefined}><${Sign} name=${mark.sign} /></span>`}${typeSign(n)}</span>
    <span class="arena-task__goal">${n.type?.name || (n.pitch ? "Pitch" : "Goal")}</span>
    <span class="arena-task__name arena-pdeck__title">${n.short || n.title}</span>
    <span class="arena-task__foot arena-pdeck__line">${d.words}</span>
  </button></div>`;
}

/** A party's head over its column, on the canvas above the table: its leader's head, its name, *k/n*; a press opens the party. */
function ColumnHead({ g, nodes }) {
  const name = g.short || g.title;
  return html`<button type="button" class="arena-pcol__head" data-goal=${g.slug} title=${`Open ${name}`} onClick=${() => show(g.slug, PROJECT)}>
    <span class="arena-plist__head">${g.leader?.head ? html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} />` : null}</span>
    <span class="arena-pcol__name" title=${g.title}>${name}</span>
    <span class="arena-phead__count" title=${countTip(g, nodes)}>${countWords(g, nodes)}</span>
  </button>`;
}

/** A party's column on the table: its groups of cards, its Flags folded. */
function Column({ g, nodes, lit, setLit }) {
  const [flags, setFlags] = useState(false), d = decksOf(g, nodes), name = g.short || g.title;
  const decks = (key, list) => html`<div class="arena-phase">${list.map((x) => html`<${Deck} key=${x.n.slug} d=${x} group=${key} party=${g.slug} lit=${lit} setLit=${setLit} />`)}</div>`;
  return html`<section class="arena-pcol" data-goal=${g.slug} aria-label=${name}>
    ${deckCount(d) === 0 && html`<p class="arena-cap arena-pcol__empty">${emptyWords(name)}</p>`}
    ${GROUPS.map(([key, label]) => d[key].length > 0 && html`<div key=${key} class="arena-pgroup" data-group=${key}><h3 class="arena-sec">${label}</h3>${decks(key, d[key])}</div>`)}
    ${d.flags.length > 0 && html`<div class="arena-pgroup" data-group="flags">
      <button type="button" class="ork-btn quiet arena-fold" aria-expanded=${flags} onClick=${() => setFlags(!flags)}><${Chev} dir=${flags ? "down" : "right"} /> Flags (${d.flags.length})</button>
      ${flags && decks("flags", d.flags)}</div>`}
  </section>`;
}

const LEAVE_MS = 420;                                         // a collision that was answered crumbles this long (arena.css `arena-crumble`)
const seen = () => !reducedMotion() && !document.hidden;      // motion plays only while the page is seen and the person has not asked for none

/** The links on the level, in the host's coordinates: the Orkmaster's (spec 71 §6: a collision, in the signal's colour, between its two decks while its stop is open; a wait, an arrow from the goal waited for), always;
 *  and the lit deck's route (the two decks' boxes joined by an arrow, from the earlier step to the later). `collisions`: `project.collisions`. */
function useLinks(host, nodes, lit, collisions) {
  const [lines, setLines] = useState([]);
  const [size, setSize] = useState(0);
  useLayoutEffect(() => {
    const el = host.current;
    if (!el || typeof ResizeObserver !== "function") return undefined;
    const watch = new ResizeObserver(() => setSize(Math.round(el.getBoundingClientRect().width)));
    watch.observe(el);
    return () => watch.disconnect();
  }, []);
  const was = useRef([]);                                     // the lines drawn last: a collision that went is kept as they were
  useLayoutEffect(() => {
    const el = host.current, mine = [...orkLinks(collisions, nodes), ...(lit ? linksOf(nodes).filter((l) => l.from === lit || l.to === lit) : [])];
    const base = el?.getBoundingClientRect(), box = (slug) => {
      const x = el.querySelector(`.arena-pdeck[data-slug="${CSS.escape(slug)}"]`);
      if (!x) return null;
      const r = x.getBoundingClientRect();
      return { x: r.left - base.left, y: r.top - base.top, w: r.width, h: r.height };
    };
    const next = !el ? [] : mine.map((l) => [l, box(l.from), box(l.to)]).filter(([, a, b]) => a && b).map(([l, a, b]) => { const g = segment(l.key, a, b); return { ...g, ...(l.kind === "collide" ? { x2: g.tip.x, y2: g.tip.y } : {}), kind: l.kind || "" }; });          // a collision has no head: its line goes to the deck
    const open = new Set((collisions || []).map((c) => `collide:${c.id}`)), now = Date.now();
    const out = was.current.filter((l) => l.leaving && l.until > now);              // a collision answered or withdrawn while the page is seen crumbles for LEAVE_MS (spec 74 §3); one the filter hid, or the first read, never
    if (seen()) for (const l of was.current) if (l.kind === "collide" && !l.leaving && !open.has(l.key) && !next.some((x) => x.key === l.key)) out.push({ ...l, leaving: true, until: now + LEAVE_MS });
    const all = [...next, ...out.filter((l) => !next.some((x) => x.key === l.key))];
    was.current = all;
    setLines((cur) => (!cur.length && !all.length ? cur : all));
    if (out.length) setTimeout(() => { was.current = was.current.filter((l) => !l.leaving || l.until > Date.now()); setLines((cur) => cur.filter((l) => !l.leaving || l.until > Date.now())); }, LEAVE_MS + 30);
  }, [lit, nodes, collisions, size]);
  return lines;
}

/** The project's level: the field in place of a party's. `stops`: the one hand's, as Operations' field has it. */
export function Project({ m, stops }) {
  const parties = goalsOf(m, goalList().map((x) => x.slug)), [lit, setLit] = useState(""), host = useRef();
  const lines = useLinks(host, m.nodes || [], lit, m.project?.collisions);
  const ork = m.project?.orkmaster;
  return html`<div class="arena arena-project" data-goal=${PROJECT}>
    <${PartyList} />
    <div class="arena-ops__main arena-project__main">
      <div class="arena-pjtop">${ork && html`<${Head} race=${ork.race || "peon"} tier=${ork.tier || "crown"} />`}<h2 class="arena-pjtop__title">${THE_PROJECT}</h2>
        <span class="arena-cap">${PARTIES_WORDS}</span></div>
      <${NewPartyPile} deal=${m.project?.deal || []} />
      <section class="arena-project__body" aria-label=${THE_PROJECT}>
        <div class="arena-project__grid">
          <div class="arena-project__heads">${parties.map((g) => html`<${ColumnHead} key=${g.slug} g=${g} nodes=${nodesOf(m, g.slug)} />`)}</div>
          <div class="arena-project__cols ork-table" ref=${host}>
            ${parties.map((g) => html`<${Column} key=${g.slug} g=${g} nodes=${nodesOf(m, g.slug)} lit=${lit} setLit=${setLit} />`)}
            <${ArrowLines} lines=${lines} />
          </div>
        </div>
      </section>
      <${NewGoalPile} goals=${parties} />
      ${stops}
    </div>
  </div>`;
}
