// The parties in the left column (docs/specs/69-parties-in-the-column.md, decisions §84; it was the party's deck, spec 52 §3, and the parties' spread): from the top the
// project switcher (shell/projects.js, as wide as the column), then a heading for each party in the Board's order — its leader's head, its whole name (two lines, then cut,
// the title whole), *k/n*, the work sign while it is at work and, on a closed party, one sign for the stops that wait in it where they cannot be seen (! , ✗ when one failed:
// §65.2) —, Operations when the project has them, then *+ New party*. One party is open, the one the board shows, with its body under its heading (`body`: goals.js `Left`); the open heading
// is its leader's (spec 73 §2): the leader's head, the party's name and *<leader> leads* under it, the work sign and *k/n*, no row of the leader's in the body. The project's line also holds the **+** of New goal (newgoal.js).
// a press on a closed heading shows that party (the party switch: the board redraws in place, the party kept per device), a press on the open one shows only its leader's work, or everyone's again (the leader's row did, spec 73 §2). ↑ and ↓ move between
// the headings. A switch says `ideas.shown` (spec 68 §7.9). A new party saved gathers its seats' heads onto its heading's head (spec 63 §3, goaltabs.js `gatherInto`). The column scrolls under the project's line.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { track, OPS, PROJECT } from "../board/store.js";
import { keepGoal } from "../board/tracks.js";
import { mapData } from "../shell/store.js";
import { command } from "../link.js";
import { dialog, openDialog } from "../shell/modals.js";
import { ProjectSwitcher } from "../shell/projects.js";
import { clearPicks, dropGather, gather, leaveParty, picks, solo } from "./arenastate.js";
import { reducedMotion } from "./motion.js";
import { countTip, countWords, plural } from "./arenawords.js";
import { gatherInto, partiesOf, shownOf } from "./goaltabs.js";
import { NewGoalPlus } from "./newgoal.js";
import { THE_PROJECT } from "./projectwords.js";

let scrolled = 0;                                       // the column's scroll, kept across the redraw a switch makes (the party is keyed, the list is drawn again)

/** Shows another party (or Operations, or the project's level): what was hovered or opened on the last one goes, the picks stay with their party. */
export function show(slug, want) {
  if (slug === want) return;
  leaveParty();
  track.value = slug;
  if (slug !== OPS && want && want !== OPS) command("ideas.shown", { party: slug, from: want }).catch(() => {});      // counted by the host (spec 68 §4, §7.9): fire and forget, never waited for, never a toast of its own
}

/** What waits in a closed party, as one sign: ✗ in the danger colour when one failed, else !; its title says how many. */
function WaitSign({ n, failed, name }) {
  if (!n) return null;
  return html`<span class=${cls("arena-phead__stop", failed ? "is-danger" : "is-alert")} title=${`${plural(n, "waits", "wait")} in ${name}`}><${Sign} name=${failed ? "cross" : "alert"} /></span>`;
}

/** Who leads a party, by name (Ideation's is the Investor). */
const leaderOf = (g) => g.leader?.name || (g.party || []).find((m) => m.band === "lead")?.name || (g.ideation ? "Investor" : "Taskmaster");

/** A party's heading: one button, its leader's head, its name (the open one's has *<leader> leads* under it), the work sign, *k/n*, the stop sign (closed only). */
function Heading({ x, open, want }) {
  const { g, nodes, working } = x, name = g.short || g.title, stops = open ? 0 : x.stops, leads = `${leaderOf(g)} leads`;
  const lead = g.leader?.slug || "taskmaster", alone = open && solo.value === lead;        // the open heading is its leader's: a press shows only its work (spec 73 §2)
  const press = () => (open ? (solo.value = alone ? "" : lead) : show(g.slug, want));
  return html`<button type="button" class=${cls("arena-phead", { "is-open": open })} data-goal=${g.slug} data-state=${open ? "open" : "closed"} aria-expanded=${open} aria-current=${open ? "true" : undefined}
      aria-pressed=${open ? String(alone) : undefined}
      title=${open ? `${name} · ${leads} · ${countTip(g, nodes)}` : `Open ${name}`} onClick=${press}>
    <span class="arena-plist__head">${g.leader?.head ? html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} />` : null}</span>
    ${open ? html`<span class="arena-phead__who"><span class="arena-phead__name" title=${g.title}>${name}</span><span class="arena-phead__leads">${leads}</span></span>`
      : html`<span class="arena-phead__name" title=${g.title}>${name}</span>`}
    ${working && html`<span class="arena-phead__work"><${Sign} name="work" label="at work" /></span>`}
    <span class="arena-phead__count" title=${countTip(g, nodes)}>${countWords(g, nodes)}</span>
    <${WaitSign} n=${stops} failed=${x.failed} name=${name} />
  </button>`;
}

/** Opens a closed party from its line (spec 72 §1.3): shown as a press on its heading would, then with `goal` alone picked into its filter (spec 50 §3.5), or with no pick. */
function openWith(slug, goal, want) {
  show(slug, want);
  if (goal) picks.value = { ...picks.value, [slug]: [goal] }; else clearPicks(slug);
}

/** A closed party's goals at work, in one quiet line under its heading (spec 72, decisions §87): each its element and short name, joined by ·, what does not fit ending *and k more*;
 *  none at work, no line. Drawn in full first and measured (`fit` follows the goals and the width); a name is never cut in the middle. */
function AtWork({ x, want }) {
  const mine = x.nodes.filter((n) => n.state === "working"), line = useRef();
  const sig = mine.map((n) => `${n.slug}|${n.short || n.title}|${n.element}`).join("\n");
  const [fit, setFit] = useState({ sig: "", n: mine.length });
  const measured = fit.sig === sig;
  useLayoutEffect(() => {
    const el = line.current;
    if (!el || measured || !mine.length) return;
    const sizes = [...el.querySelectorAll("[data-measure=item]")].map((e) => Math.ceil(e.getBoundingClientRect().width)), more = Math.ceil(el.querySelector("[data-measure=more]")?.getBoundingClientRect().width || 0), gap = 0;
    const room = el.clientWidth - el.querySelector(".arena-atwork__sign").offsetWidth - 6 - 1;
    let n = 0, used = 0;
    for (let i = 0; i < sizes.length; i++) {
      const next = used + (i ? gap : 0) + sizes[i], tail = i < sizes.length - 1 ? gap + more : 0;
      if (next + tail > room && sizes.length > 1) break;           // a name that does not fit is left to *and k more*, never cut (one goal alone is the exception: it ends in an ellipsis)
      used = next; n = i + 1;
    }
    setFit({ sig, n });
  }, [sig, measured]);
  useEffect(() => {                                   // the column's width changed: measure again
    const el = line.current;
    if (!el || typeof ResizeObserver !== "function") return;
    let w = el.clientWidth;
    const again = () => setFit((f) => ({ ...f, sig: "" })), ro = new ResizeObserver(() => { if (el.clientWidth !== w) { w = el.clientWidth; again(); } });
    ro.observe(el);
    document.fonts?.addEventListener?.("loadingdone", again);        // the text face arrives after the first measure: the names are wider
    return () => { ro.disconnect(); document.fonts?.removeEventListener?.("loadingdone", again); };
  }, [mine.length > 0]);
  if (!mine.length) return null;
  const shown = measured ? mine.slice(0, fit.n) : mine, rest = mine.length - shown.length, words = `At work: ${mine.map((n) => n.title).join(", ")}`;
  return html`<div class=${cls("arena-atwork", { "is-measuring": !measured })} role="group" aria-label=${words} title=${words} ref=${line}>
    <span class="arena-atwork__sign"><${Sign} name="work" /></span>
    ${shown.map((n, i) => html`<span key=${n.slug} class="arena-atwork__item" data-measure=${measured ? undefined : "item"}>
      ${i ? html`<span class="arena-atwork__dot" aria-hidden="true">·</span>` : null}<button type="button" class="arena-atwork__goal" data-slug=${n.slug} title=${n.title} aria-label=${n.title}
        onClick=${() => openWith(x.g.slug, n.slug, want)}><${Elem} name=${n.element || ""} /><span class="arena-atwork__name">${n.short || n.title}</span></button></span>`)}
    ${rest > 0 && html`<button type="button" class="arena-atwork__more" onClick=${() => openWith(x.g.slug, "", want)}>and ${rest} more</button>`}
    ${!measured && html`<span class="arena-atwork__more" data-measure="more" aria-hidden="true">and 9 more</span>`}
  </div>`;
}

function OpsHeading({ ps, open, want }) {
  const n = open ? 0 : ps.opStops;
  return html`<button type="button" class=${cls("arena-phead", { "is-open": open })} data-goal=${OPS} data-state=${open ? "open" : "closed"} aria-expanded=${open} aria-current=${open ? "true" : undefined}
      title=${open ? "Operations is open" : "Open Operations"} onClick=${() => show(OPS, want)}>
    <span class="arena-plist__head arena-plist__icon"><${Icon} name="sliders" /></span>
    <span class="arena-phead__name">Operations</span>
    <${WaitSign} n=${n} failed=${ps.opFailed} name="Operations" />
  </button>`;
}

/** The Orkmaster in the project's line (spec 70 §2.1): its head, a button *The project*, pressed while the project's level is shown. Only a host that has the level draws it. */
function Orkmaster({ ork, open, want }) {
  return html`<button type="button" class=${cls("arena-ork", { "is-open": open })} data-goal=${PROJECT} data-state=${open ? "open" : "closed"} aria-pressed=${open} title=${THE_PROJECT}
      aria-label=${THE_PROJECT} onClick=${() => show(PROJECT, want)}><${Head} race=${ork.race || "peon"} tier=${ork.tier || "crown"} /></button>`;
}

/** The left column: the project's line, the parties, Operations, *+ New party*; `body` is the open party's, drawn under its heading. */
export function PartyList({ body = null }) {
  const m = mapData.value, root = useRef(), list = useRef();
  const ps = partiesOf(), goals = ps.goals.map((x) => x.g);
  const want = m ? shownOf(goals, track.value) : track.value;
  // The party shown is `want`; `track` follows it only to start (a pick that no list has yet, a party just saved, shows the kept one until it does).
  useEffect(() => { if (m && !track.value && want) track.value = want; }, [m, want]);
  useEffect(() => { if (m && want && want !== OPS && want === track.value) keepGoal(want); }, [m, want, track.value]);
  const waiting = gather.value, modal = dialog.value;
  useEffect(() => {                         // a new party was saved: its heads gather onto its heading's head, in the first render that shows it once the dialog has closed (spec 63 §3.2)
    if (!waiting || waiting.party !== want || modal) return;
    dropGather(waiting);
    const head = root.current?.querySelector(`.arena-phead[data-goal="${CSS.escape(want)}"] .arena-plist__head`);
    if (!reducedMotion() && !document.hidden && head) gatherInto(head, waiting.from);
  }, [want, waiting, modal]);
  useLayoutEffect(() => { if (list.current) list.current.scrollTop = scrolled; }, []);
  const move = (e) => {                     // ↑ and ↓ move between the headings
    const k = e.key === "ArrowDown" ? 1 : e.key === "ArrowUp" ? -1 : 0;
    if (!k || !e.target.matches?.(".arena-phead, .arena-pnew")) return;
    const all = [...root.current.querySelectorAll(".arena-phead, .arena-pnew")], at = all.indexOf(e.target);
    e.preventDefault();
    all[Math.min(all.length - 1, Math.max(0, at + k))]?.focus();
  };
  const open = (slug) => slug === want;
  const ork = m?.project?.orkmaster, level = want === PROJECT;          // the project's level: every heading closed, the project's line marked as an open heading is
  return html`<aside class="arena-left" aria-label="Parties" ref=${root} onKeyDown=${move}>
    <div class=${cls("arena-left__proj", { "has-ork": !!ork, "is-open": level && !!ork })}>
      ${ork && html`<${Orkmaster} ork=${ork} open=${level} want=${want} />`}<${NewGoalPlus} want=${want} /><${ProjectSwitcher} /></div>
    <div class="arena-plist" ref=${list} onScroll=${(e) => { scrolled = e.currentTarget.scrollTop; }}>
      ${ps.goals.map((x) => html`<section key=${x.g.slug} class=${cls("arena-party", { "is-open": open(x.g.slug) })}>
        <${Heading} x=${x} open=${open(x.g.slug)} want=${want} />
        ${open(x.g.slug) ? body : html`<${AtWork} x=${x} want=${want} />`}
      </section>`)}
      ${ps.ops && html`<section class=${cls("arena-party", { "is-open": want === OPS })}><${OpsHeading} ps=${ps} open=${want === OPS} want=${want} /></section>`}
      <button type="button" class="arena-pnew" title="One of yours, or its leader, builders and checkers from the library" onClick=${() => openDialog("goal")}>
        <span class="arena-plist__head arena-plist__icon"><${Icon} name="plus" /></span><span class="arena-phead__name">New party</span></button>
    </div>
  </aside>`;
}
