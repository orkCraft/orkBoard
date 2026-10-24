// The open party's body in the left column, under its heading (docs/specs/49-one-window.md §4.4, docs/specs/50-parties-and-goals.md §3.3, docs/specs/52-goal-types.md §3.2, §4,
// docs/specs/69-parties-in-the-column.md §3, docs/specs/73-a-lighter-column.md §1, §3; the headings are partylist.js): its groups — *At work*, *Planning* — then *New · n* with
// *Process now* at its right and *Flags · n* with *k wait for main*, each folded, one 28 px row. The party's leader is the heading (partylist.js), there is no row of its own and no
// *Goals n*; a party's New goal is the + in the project line (newgoal.js). A goal's row is one line (28 px): its element, its type's sign in its goal's colour, its title, its moon (spec 74 §6), its state's
// sign; what its second line said is in its title (the tooltip). A press on the row picks the goal into the filter, a second press on a picked row opens its screen (a raw goal opens on
// the first); hovering it peeks (the board shows only that goal's cards while the pointer is on the row). A stop is marked once, by its sign (no alert edge, no alert words).
// Ideation (docs/specs/65-ideation.md §8) lists its pitches by state instead (pitches.js), with *Judge now* in place of *Process now*.
// A project with a Release party (docs/specs/68-release-and-route.md §7.4, §7.5): that party's goals begin with *k flags wait for a release* (a press opens New goal of *A release*), its Flags say a release's
// version and *k goals* with **Mark it out** (asking first) and then *Out in 1.4*; another party's flags say *In Release 1.4*, *Out in 1.4* or *Waits for a release*.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Chev, Elem, Moon, Sign } from "../orkui.js";
import { act, showIdea, showPlan } from "../shell/store.js";
import { openDialog } from "../shell/modals.js";
import { reducedMotion } from "./motion.js";
import { picks, peek, rawOpen, flagsOpen, flagsAll, togglePick, clearPicks } from "./arenastate.js";
import { litFlags } from "./flags.js";
import { waitsOf, waitsForWords } from "./collidewords.js";
import { show } from "./partylist.js";
import { powerOf } from "./arenawords.js";
import { typeSign } from "./stacks.js";
import { elementOf, flagRow, goalMark, listsOf, moonOf, pickTip, waitsMain, workLine } from "./goalwords.js";
import { FoldRow } from "./foldrow.js";
import { PitchGoals } from "./pitches.js";
import { judgePower, pitchLists } from "./pitchwords.js";
import { flagRelease, outAsk, releaseLine, waitWords } from "./releasewords.js";

const SHOWN_FLAGS = 10;

const TONES = { danger: "is-danger", alert: "is-alert" };

/** One goal of the party, one line (spec 73 §1): its element, its type's sign (the space kept for a goal with none), its title, its state's sign. `plan`: a Planning row (its words come from the
 *  leader's reading); a raw goal (`raw`) opens on a press, it has no task to pick. A press picks, a second press on a picked row opens its screen; the whole line is in its title. */
function GoalRow({ g, n, plan = null, raw = false, party }) {
  const el = elementOf(n), mark = goalMark(n), moon = moonOf(n), on = (picks.value[party] || []).includes(n.slug), some = (picks.value[party] || []).length > 0;
  const stop = mark.sign === "alert";
  const waits = waitsOf(n), words = [raw || plan ? plan.words : workLine(n), waitsForWords(n)].filter(Boolean).join(" · ");     // *waits for Backend · Auth API* is in the title, whatever sign the row wears
  const toWait = () => { const w = waits[0]; show(w.party, party); picks.value = { ...picks.value, [w.party]: [w.goal] }; };          // the sign: that goal's party, with it picked
  const open = () => (plan?.kind === "plan" ? showPlan(n.slug, "", { via: "map" }) : showIdea(n.slug, { via: "map" }));
  const press = () => { if (raw || on) open(); else togglePick(party, n.slug); };
  const enter = (e) => { if (e.movementX || e.movementY) peek.value = n.slug; }, leave = () => { if (peek.value === n.slug) peek.value = ""; };   // a peek follows a move, not a layout under a pointer at rest (a switch draws the new body under the heading just pressed)
  return html`<div class=${cls("arena-goal", { "is-on": on, "is-off": some && !on && !raw, "is-stop": stop })} data-slug=${n.slug} data-state=${stop ? "stop" : mark.sign === "work" ? "work" : "idle"}
      onMouseMove=${raw ? undefined : enter} onMouseLeave=${raw ? undefined : leave}>
    <button type="button" class="arena-goal__main" aria-pressed=${raw ? undefined : on} title=${raw ? `${n.title} · ${words}` : `${n.title} · ${words}. ${on ? "Press again to open it" : pickTip(on)}`} onClick=${press}>
      <${Elem} name=${el.name} dim=${el.dim} />
      ${typeSign(n, "arena-goal__type") || html`<span class="arena-goal__type is-none" aria-hidden="true"></span>`}
      <span class="arena-goal__title">${n.short || n.title}</span>
      ${moon && html`<${Moon} phase=${moon} />`}
      <span class=${cls("arena-goal__mark", TONES[mark.tone])} title=${mark.label || undefined}>${mark.sign && html`<${Sign} name=${mark.sign} />`}</span>
    </button>
    ${mark.sign === "before" && html`<button type="button" class="arena-goal__go" aria-label=${`${mark.label}: open it`} title=${`${mark.label} · opens ${waits[0].party_name || waits[0].party} with it picked`} onClick=${toWait}></button>`}
  </div>`;
}

/** *Flags · n* with *k wait for main* at its right (spec 73 §3): the goals done that wait for main (a check), then the flags (the newest ten, then *All n*): the goal, its day, its price,
 *  how many of its tasks merged in their first round. A goal whose flag was raised a moment ago is lit once. */
function FlagsFold({ lists, g, nodes }) {
  const waits = waitsMain(g, nodes), n = lists.flagged.length, all = flagsAll.value, open = flagsOpen.value;
  if (!n && !waits) return null;
  const shown = all ? lists.flagged : lists.flagged.slice(0, SHOWN_FLAGS);
  return html`<div class="arena-flags">
    <${FoldRow} word="Flags" n=${n} open=${open} toggle=${() => { flagsOpen.value = !open; }} kind="arena-flagsrow">
      ${waits > 0 && html`<span class="arena-cap arena-frow__aside">${waits === 1 ? "1 waits for main" : `${waits} wait for main`}</span>`}<//>
    ${open && html`<ul class="arena-flags__list">
      ${lists.waiting.map((x) => html`<li key=${x.slug}><button type="button" class="arena-flagrow" data-slug=${x.slug} onClick=${() => showIdea(x.slug, { via: "flags" })}>
        <${Sign} name="check" /> <span class="arena-flagrow__t">${x.short || x.title}</span><span class="arena-cap">in dev · waits for main</span></button></li>`)}
      ${shown.map((x) => html`<${FlagRow} key=${x.slug} n=${x} />`)}
      ${!all && n > SHOWN_FLAGS && html`<li><button type="button" class="ork-btn quiet" onClick=${() => { flagsAll.value = true; }}>All ${n}</button></li>`}
    </ul>`}
  </div>`;
}

function FlagRow({ n }) {
  const ref = useRef(), f = flagRow(n), own = n.release, rel = flagRelease(n);
  const [asking, setAsking] = useState(false), [busy, setBusy] = useState(false);
  useEffect(() => {                                   // a flag raised a moment ago is lit once, when it is on screen
    if (!litFlags.has(n.slug) || !ref.current) return;
    litFlags.delete(n.slug);
    if (!reducedMotion() && typeof ref.current.animate === "function") {
      ref.current.animate([{ background: "var(--ork-ink)", color: "var(--ork-on-ink)" }, { background: "transparent" }], { duration: 600, easing: "steps(4, end)" });
    }
  }, []);
  const out = async () => {                           // a refusal is the host's words, as a toast; the question stays
    setBusy(true);
    const got = await act("ideas.release_out", { slug: n.slug });
    setBusy(false);
    if (got) setAsking(false);
  };
  return html`<li data-release=${own ? (own.out ? "out" : "own") : undefined}><button ref=${ref} type="button" class="arena-flagrow" data-slug=${f.slug} data-flag=${f.at} title=${f.title} onClick=${() => showIdea(f.slug, { via: "flags" })}>
    <span class="arena-flagrow__flag"><${Sign} name="flag" /></span> <span class="arena-flagrow__t">${f.short}</span>
    ${own && html`<span class="arena-cap arena-flagrow__rel" data-rel="own">${releaseLine(own)}</span>`}<span class="arena-cap">${f.words}</span>
    ${rel && html`<span class="arena-cap arena-flagrow__rel" data-rel=${n.flag?.release ? (n.flag.release.out ? "out" : "in") : "waits"}>${rel}</span>`}</button>
    ${own && !own.out && (asking ? html`<div class="arena-out" role="alert"><p class="arena-cap">${outAsk(own.version)}</p>
        <div class="arena-out__row"><button type="button" class="ork-btn primary" data-act="out" disabled=${busy} onClick=${out}>Out</button>
          <button type="button" class="ork-btn" data-act="not-yet" onClick=${() => setAsking(false)}>Not yet</button></div></div>`
      : html`<button type="button" class="ork-btn arena-flagrow__out" data-act="mark-out" onClick=${() => setAsking(true)}>Mark it out</button>`)}
  </li>`;
}

/** The open party's body, under its heading: its groups, then *New* and *Flags* as rows. Ideation's pitches by state, with *Judge now*. */
export function Left({ g, nodes, planning, lead }) {
  const party = g.slug, lists = listsOf(g, nodes, lead?.name || "Taskmaster"), pitch = !!g.ideation;
  const pl = pitch ? pitchLists(nodes) : null;          // Ideation: its pitches by state, *Judge now* in place of *Process now* (spec 65 §8)
  const power = pitch ? judgePower(pl.raw, lead?.name || "Investor") : powerOf(planning.raw, lead?.name || "Taskmaster");
  const picked = !pitch && (picks.value[party] || []).length > 0;
  const release = (g.types || []).find((t) => t.id === "release"), waiting = !pitch && release && g.wait_release > 0 ? g.wait_release : 0;          // flags that wait for a release (spec 68 §7.4)
  const go = pitch ? () => act("ideas.judge", { slug: power.slug, via: "party" }) : () => act("ideas.queue", { slug: power.slug, queue: "now", via: "party" });
  const button = html`<button type="button" class="ork-btn arena-power" disabled=${power.off} title=${power.tip} onClick=${go}>${pitch ? "Judge now" : "Process now"}</button>`;
  return html`<div class="arena-pbody">
    <section class="arena-goals" aria-label=${pitch ? "Pitches" : "Goals"}>
      ${picked && html`<div class="arena-showall"><button type="button" class="ork-btn quiet" title="Every goal of the party again" onClick=${() => clearPicks(party)}>Show all</button></div>`}
      ${waiting > 0 && html`<button type="button" class="ork-btn quiet arena-waitrel" aria-haspopup="dialog" title="New goal of A release, with these flags ticked"
        onClick=${() => openDialog("idea", { goal: party, type: release })}><${Sign} name="flag" /> <span>${waitWords(waiting)}</span><${Chev} dir="right" /></button>`}
      ${pitch ? html`<${PitchGoals} nodes=${nodes} power=${button} />` : html`<div class="arena-deck">
        ${lists.work.length > 0 && html`<h3 class="arena-sec">At work</h3>`}
        ${lists.work.map((x) => html`<${GoalRow} key=${x.slug} g=${g} n=${x} party=${party} />`)}
        <h3 class="arena-sec">Planning</h3>
        ${!lists.planRows.length && !lists.raw.length && html`<p class="arena-cap">Nothing in Planning. A new goal starts here.</p>`}
        ${lists.planRows.map((r) => html`<${GoalRow} key=${r.slug} g=${g} n=${r.node} plan=${r} party=${party} />`)}
        <${FoldRow} word="New" n=${lists.raw.length} open=${rawOpen.value} toggle=${() => { rawOpen.value = !rawOpen.value; }} kind="arena-raw">${button}<//>
        ${rawOpen.value && lists.raw.map((r) => html`<${GoalRow} key=${r.slug} g=${g} n=${r.node} plan=${r} raw=${true} party=${party} />`)}
        <${FlagsFold} lists=${lists} g=${g} nodes=${nodes} />
      </div>`}
    </section>
  </div>`;
}
