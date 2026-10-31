// A goal's way on the phone's middle (docs/specs/117-the-phone-a-menu-of-the-leaders.md §5.1, docs/mockups/phone/sidebar.html A1, decisions §195.2): its header (its element big, its short name in the body face, its type's sign and *<Type> · at work in <Party>*, or its phase's word),
// its phases (`PHASES`: the past ones muted, its own in the ink; a press opens the goal's Talk or Spec page over the pane, as *Spec* under the card did), its route (the parties it passes in the route's order, each its leader's head and name: done with the check, the one at work
// turned, the next faint), why (its spec's *Why*, else the goal's own words, at most four lines) and *<Party>'s tasks* (the tasks of the step at work: `cascadeOf`, each its doer's head, its name and its stage's word, in the alert's frame when it asks or failed). A goal in line has its
// phases and why only, and the moon with its hour when it waits for the reset. Everything is read from what the page has (`ideas.map`, `ideas.board`) and the spec's page (`ideas.page`, as the Spec page reads it). Layout only (uplook.css).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { command } from "../link.js";
import { board } from "../board/store.js";
import { openOver } from "../frame/state.js";
import { PHASES, STAGES, cascadeOf, footWords, lineNow, nameOf, partiesAll, phaseOf, routeParties, stageOf, waitsWords } from "../table/data.js";
import { linesOf, partsOf } from "../table/specpage.js";

const phaseWord = (id) => (PHASES.find(([p]) => p === id) || [])[1] || "";
const partyBy = (slug) => partiesAll().find((g) => g.slug === slug) || null;

/** The parties a goal passes, in its route's order, each `{slug, name, head, state}`; `state` is `done`, `now` (at work: orkUI's work sign) or `next`. A goal with no planned route has its own party and those the Board says it touches. */
export function routeOf(n) {
  const phase = phaseOf(n.slug), legs = (n.route || []).filter((s) => s.step === "party" && s.party), seen = new Set(), out = [];
  const stateOf = (s) => (phase === "done" || s?.state === "done" ? "done" : phase === "work" && s && s.state !== "waiting" ? "now" : "next");
  for (const s of legs.length ? legs : [...routeParties(n.slug)].map((party, i) => ({ party, state: i === 0 ? "work" : "waiting" }))) {
    const g = partyBy(s.party);
    if (!g || seen.has(s.party)) continue;
    seen.add(s.party);
    out.push({ slug: g.slug, name: nameOf(g), head: g.leader?.head || null, state: stateOf(s) });
  }
  return out;
}

/** The goal's header: its element big, its short name, its type's sign and where it is. */
export function GoalHead({ n }) {
  const phase = phaseOf(n.slug), line = n.place === "deck", at = routeOf(n).find((r) => r.state === "now") || routeOf(n)[0];
  const where = line ? "In line" : phase === "work" ? `at work in ${at?.name || nameOf(partyBy(n.goal))}` : phaseWord(phase);
  return html`<header class="up-gh"><${Elem} name=${n.element || ""} big=${true} dim=${!n.element} />
    <div class="up-gh__txt"><h2 class="up-gh__name">${nameOf(n)}</h2><p class="up-gh__type">${n.type?.sign && html`<${Sign} name=${n.type.sign} />`}<span>${[n.type?.name, where].filter(Boolean).join(" · ")}</span></p></div></header>`;
}

/** The four phases as one button: its own phase in the ink, the past ones muted; a press opens the goal's page (Talk until it is decided, else Spec). */
export function Phases({ n }) {
  const phase = phaseOf(n.slug), at = PHASES.findIndex(([id]) => id === phase), talk = phase === "talk", page = talk ? "Talk" : "Spec";
  const open = () => openOver(talk ? "talk" : "spec", { idea: n.slug }, { title: "", key: "" }, page);
  const words = `${nameOf(n)}: ${phaseWord(phase) || "in line"}. Open its ${page}`;
  return html`<button type="button" class="up-phases" data-page=${talk ? "talk" : "spec"} aria-label=${words} title=${words} onClick=${open}>
    ${PHASES.map(([id, word], i) => html`<span key=${id} class=${cls("up-phase", { "is-past": at > i, "is-now": at === i })} data-phase=${id}>${word}</span>`)}</button>`;
}

/** The goal in line waits for its turn; the moon and its hour when it waits for the reset. */
export function Waits({ n }) {
  const g = lineNow().find((x) => x.slug === n.slug);
  return g ? html`<p class="up-wait">${g.reset && html`<${Sign} name="moon" />`}<span>${waitsWords(g)}</span></p>` : null;
}

/** The route: the parties in order with an arrow between them. */
export function Route({ n }) {
  const steps = routeOf(n);
  if (!steps.length) return null;
  const word = { done: "done", now: "at work", next: "next" };
  return html`<div class="up-route" role="list" aria-label="Its route">${steps.map((s, i) => html`${i > 0 && html`<${Icon} name="arrow-right" />`}
    <span key=${s.slug} role="listitem" class=${cls("up-step", { [`is-${s.state}`]: true })} data-party=${s.slug} aria-label=${`${s.name}: ${word[s.state]}`} title=${`${s.name}: ${word[s.state]}`}>
      ${s.head && html`<${Head} race=${s.head.race} tier=${s.head.tier} />`}<span>${s.name}</span>${s.state === "done" && html`<${Sign} name="check" />`}${s.state === "now" && html`<${Sign} name="work" />`}</span>`)}</div>`;
}

/** The goal's own words when its spec has no *Why*: its full title when the short name is shorter. */
const describeOf = (n) => (n.title && n.title !== (n.short || "") ? n.title : "");

/** The spec's *Why* (its old section, else a party section's `### Why`), else the goal's own words; read from the goal's page now and again when the Board changes. */
function useWhy(n) {
  const [page, setPage] = useState(null), rev = board.value?.rev;
  useEffect(() => {
    let live = true;
    command("ideas.page", { slug: n.slug }, true).then((p) => { if (live) setPage(p && !p.error ? p : null); }).catch(() => { if (live) setPage((was) => was || null); });
    return () => { live = false; };
  }, [n.slug, rev]);
  const secs = page?.sections || [];
  let why = secs.find((x) => String(x.name || "").trim().toLowerCase() === "why")?.text || "";
  for (const x of why ? [] : secs) {
    const p = partsOf(x.text), k = Object.keys(p).find((key) => key.toLowerCase() === "why");
    if (k && p[k]) { why = p[k]; break; }
  }
  return linesOf(why).join(" ") || describeOf(n);
}

/** Why, at most four lines. */
export function Why({ n }) {
  const why = useWhy(n);
  return why ? html`<p class="up-why">${why}</p>` : null;
}

/** *<Party>'s tasks*: the tasks of the step at work, each its doer's head (its stage's sign with none), its name and its stage's word; a task that asks or failed in the alert's frame. */
export function Tasks({ n }) {
  const tasks = cascadeOf(n);
  if (!tasks.length) return null;
  const at = routeOf(n).find((r) => r.state === "now") || routeOf(n)[0], name = at?.name || nameOf(partyBy(n.goal));
  return html`<section class="up-sec" aria-label=${`${name}'s tasks`}><p class="up-lab">${name}'s tasks</p>
    <ul class="up-tasks">${tasks.map((t) => html`<li key=${t.id} class=${cls("up-task", { asks: t.state === "failed" || t.state === "picking" })} data-task=${t.id} data-state=${t.state}>
      ${t.head ? html`<${Head} race=${t.head.race} tier=${t.head.tier} />` : html`<${Sign} name=${STAGES[stageOf(t)].sign} />`}<span class="up-task__name">${t.short || t.title}</span><span class="up-task__stage">${footWords(t)}</span></li>`)}</ul></section>`;
}
