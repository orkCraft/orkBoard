// A member's open tasks as cards in stacks, in rows by phase (docs/specs/50-parties-and-goals.md §3.4): under the member, its tasks lie in rows —
// *now* (a task at its goal's current wave), *next* (one wave after), *later* —, in a row one stack per goal (the goals in the Board's order),
// the front card first (at work, failed, in Review, ready, waiting, tonight), behind it one or two edges and ×n when there are more. A card is 5:7:
// the goal's element top left, its type's sign top right in the element's colour (spec 55), the goal's short name, the task's name, its foot. A press on a stack of one opens the
// task (its result in Review), on a stack of more spreads it (spread.js); hovering a card draws what it waits for and what waits for it (arrows.js).
// What the member's rows do as tasks come and go is motion.js's (a column's `useColumn`); the cards of a plan just started from the hand are dealt in (`is-dealt`, spec 57).
// A card the stop in the hand that is looked at is about wears `is-linked` (spec 58): the ring is drawn on its stack's box, a 2-px ink outline (the card itself is clipped to its notch).
// A stop is marked once (docs/specs/52-goal-types.md §4.5): a pick's card keeps its alert sign and has no alert edge or alert words; a failure keeps its danger edge.
// A card says how far its goal is (docs/specs/85-the-elf-asks-and-shows.md §4: *4 of 9 done*), wears the picture of what its task changed as its face when it has one (§3, look.css), and the card of a task
// that merged turns over once as it leaves, to *What it made* (its first commit's subject).
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { mapData, showPick, showResult, showTask } from "../shell/store.js";
import { rises } from "./motion.js";
import { taskHover, taskHoverBy, spread, stopAbout, stopLook } from "./arenastate.js";
import { RUN, ROW_LABEL, afterWords, followsBuild, heldOf, heldWords, rowsOf, taskFoot, waitersOf, waitsForOf } from "./arenawords.js";
import { doneWords, elementOf } from "./goalwords.js";

export const keyOf = (n, t) => `${n.slug}/${t.id}`;

/** The class of a type's sign, its goal's colour (docs/specs/55-type-top-right.md §1.2): the element's, `dim` (faint) while the element is drawn dim, `none` (muted) for a goal with no element. */
export const typeTone = (n) => { const el = elementOf(n); return el.name ? (el.dim ? "dim" : el.name) : "none"; };
/** A goal's type's sign, top right of a card in its goal's colour (spec 55 §1); none for a goal with no type. `kind`: the node's class (a card's or a goal row's). */
export const typeSign = (n, kind = "arena-task__type") => (n?.type?.sign ? html`<span class=${`${kind} ${typeTone(n)}`} title=${n.type.name}><${Sign} name=${n.type.sign} /></span>` : null);
/** A goal's name in a card's label, its type after it (spec 53 §3): *Sign in with a passkey, Fix a bug*. */
export const goalWords = (n) => (n.type?.name ? `${n.title}, ${n.type.name}` : n.title);

/** Whether the stop that is looked at is about one of the cards of a stack (spec 58 §2): `keys` and `goals` are the cards' own. A stop about a task rings that task's card (its stack's front when it
 *  lies behind another); one about a goal rings every card of the goal. */
export function linkedTo(keys, goals) {
  const a = stopLook.value && stopAbout.value;
  return !!a && (a.task ? keys.includes(a.task) : goals.includes(a.idea));
}

/** What a task's hover says to a card: it is the one hovered (*src*, with what waits for it), one that waits for it (*after*) or one it waits for (*before*). */
export function relationOf(n, t) {
  const hover = taskHover.value;
  if (!hover) return { src: false, after: false, before: false, hovered: null };
  const [goal, id] = [hover.slice(0, hover.lastIndexOf("/")), hover.slice(hover.lastIndexOf("/") + 1)];
  if (goal !== n.slug) return { src: false, after: false, before: false, hovered: null };
  const h = n.tasks.find((x) => x.id === id);
  if (!h) return { src: false, after: false, before: false, hovered: null };
  return { src: h.id === t.id, after: waitersOf(n, h).some((x) => x.id === t.id), before: waitsForOf(n, h).some((x) => x.id === t.id), hovered: h };
}

/** A card's foot: its state in words; under a hover the words of the dependency (*<before> waits for <short>*, *<after> n wait for it*). Parts: [{sign, text}]. */
export function footParts(n, t, rel) {
  const held = t.state === "held" ? heldOf(t, n) : null;                                    // a held card says its reason with the reason's sign (spec 82 §3): window, tonight, sign in, week
  const rest = { sign: t.state === "picking" ? "alert" : held?.word || held?.kind === "files" ? held.sign : "", text: taskFoot(t, n) };         // a pick waits for the person: *asks you to pick* with the alert sign (spec 51 §6)
  const mine = waitersOf(n, t).length;
  if (rel.src && mine) return [{ sign: "after", text: `${mine} ${mine === 1 ? "waits" : "wait"} for it` }];
  if (rel.after) return [{ sign: "before", text: `waits for ${rel.hovered.short || rel.hovered.title}` }];
  if (rel.before && mine) return [{ sign: "after", text: `${mine} ${mine === 1 ? "waits" : "wait"} for it` }];
  const on = t.state === "waiting" && !followsBuild(t, n) ? waitsForOf(n, t) : [];          // a waiting task's foot says what it waits for (spec 67 §3.2); the names are in its tooltip and its label
  if (on.length) return [{ sign: "before", text: `waits for ${on.length === 1 ? on[0].short || on[0].title : on.length}` }];
  return [rest];
}
export const Foot = ({ parts }) => parts.map((p, i) => html`<span key=${i} class="arena-task__line">${p.sign && html`<${Sign} name=${p.sign} /> `}${p.text}</span>`);

/** The tooltip of a card: its title and what it says of its state. */
export function cardTip(n, t) {
  const foot = taskFoot(t, n), head = `${t.title} (${goalWords(n)})`;
  return t.state === "failed" ? `${head} · ${t.error || "failed"}` : t.state === "held" ? `${head} · ${heldWords(t, n)}` : `${head} · wave ${t.wave}${afterWords(t, n) ? ` · ${afterWords(t, n)}` : ""}`;
}

/** What a press on a card opens: its result at Review, its pick while it asks, else the task. */
export const open = (n, t) => (t.state === "review" ? showResult(n.slug, t.id, { via: "map" }) : t.state === "picking" ? showPick(n.slug, t.id, { via: "map" }) : showTask(n.slug, t.id, { via: "map" }));

/** The look of a card (shared by a stack's front and a spread's): the element, the type, the goal, the name. `phase`: the spread's word over the name. */
export function CardBody({ n, t, phase = "", foot, deps = [], many = 0 }) {
  const el = elementOf(n);
  return html`${t.shot?.url && html`<img class="arena-task__shot" src=${t.shot.url} alt="" draggable="false" />`}<span class="arena-task__top">${RUN.includes(t.state) && html`<span class="ork-busy" title=${t.state === "testing" ? "testing" : "working"}></span>`}<${Elem} name=${el.name} dim=${el.dim} />${phase && html`<span class="arena-task__phase">${phase}</span>`}${typeSign(n)}</span>
    <span class="arena-task__goal">${n.short || n.title}</span>
    ${doneWords(n) && html`<span class="arena-task__count">${doneWords(n)}</span>`}
    <span class="arena-task__name" title=${t.title}>${t.short || t.title}</span>
    ${deps.length > 0 && html`<span class="arena-task__deps">${deps.map((d, i) => html`<span key=${i}><${Sign} name=${d.sign} /> ${d.text}</span>`)}</span>`}
    <span class="arena-task__foot"><${Foot} parts=${foot} /></span>
    ${many > 1 && html`<span class="arena-stk__n">×${many}</span>`}`;
}

/** The classes a card wears for its task's state and what the hover says of it. */
export const stateCls = (n, t, rel, later) => ({ "is-run": t.state === "running" || t.state === "testing", "is-review": t.state === "review", "is-pick": t.state === "picking", "is-next": t.state === "ready",
  "is-wait": t.state === "waiting", "is-held": t.state === "held", "is-fail": t.state === "failed", "is-later": later, "is-src": rel.src && waitersOf(n, t).length > 0,
  "is-after": rel.after, "is-before": rel.before, "has-shot": !!t.shot?.url });

/** One stack: the front card, edges behind it and ×n. `items`: the stack's entries as the column shows them ([{it: {n, t}, key, sign, quiet, fresh}]),
 *  the front first; a stack of more than one live card spreads on a press, a stack of one opens its task. */
function Stack({ goal, items, later, wide, member, row }) {
  const shown = items.filter((x) => !x.quiet), front = shown[0];
  if (!front) return null;
  const { n, t } = front.it, live = shown.filter((x) => !x.sign).length;
  const rel = relationOf(n, t), leaving = !!front.sign;
  const foot = footParts(n, t, rel), edges = Math.min(2, shown.length - 1);
  const linked = linkedTo(shown.filter((x) => !x.sign).map((x) => x.key), shown.filter((x) => !x.sign).map((x) => x.it.n.slug));
  const enter = () => { if (taskHover.value !== front.key) taskHover.value = front.key; taskHoverBy.value = "pointer"; };
  const focus = () => { taskHover.value = front.key; taskHoverBy.value = "focus"; };
  const leave = () => { if (taskHover.value === front.key) taskHover.value = ""; };
  const press = (e) => {
    if (leaving) return;
    if (live > 1) spread.value = { goal, member, row, keys: shown.filter((x) => !x.sign).map((x) => x.key), from: e.currentTarget.getBoundingClientRect() };
    else open(n, t);
  };
  const made = front.sign === "check" ? (mapData.value?.nodes || []).find((x) => x.slug === n.slug)?.tasks.find((x) => x.id === t.id)?.made || "" : "";      // the card of a merged task turns over once
  const said = `${t.title} (${goalWords(n)}): ${taskFoot(t, n)}, wave ${t.wave}${live > 1 ? `, and ${live - 1} more of this goal: a press shows them all` : ""}`;
  return html`<div class=${cls("arena-stk", { "is-many": live > 1, "is-fail": t.state === "failed", "is-wide": wide, "is-linked": linked })} data-goal=${goal} data-n=${live}>
    ${Array.from({ length: edges }, (_, i) => html`<i key=${i} class="arena-stk__edge" style=${`left:${(i + 1) * 4}px;top:${-(i + 1) * 4}px`}></i>`)}
    <button type="button" class=${cls("arena-task", { ...stateCls(n, t, rel, later), "is-drawn": front.fresh || (front.dealt && rises(front.key)), "is-dealt": front.dealt && !rises(front.key), "is-linked": linked, "is-leaving": !!front.sign, "is-gone": front.quiet, "has-n": live > 1 })}
      data-key=${front.key} data-task=${t.id} data-idea=${n.slug} data-state=${t.state} data-wave=${t.wave} data-sign=${front.sign || undefined} title=${cardTip(n, t)} aria-label=${said}
      aria-hidden=${leaving ? "true" : undefined} tabindex=${leaving ? -1 : undefined} onClick=${press}
      onMouseEnter=${enter} onMouseLeave=${leave} onFocus=${focus} onBlur=${leave}>
      <${CardBody} n=${n} t=${t} foot=${foot} many=${live} />
      ${leaving && html`<span class="arena-task__flash">${front.sign !== "fade" && html`<${Sign} name=${front.sign} big=${true} />`}</span>`}
      ${made && html`<span class="arena-task__made" data-made><b>What it made</b><span>${made}</span></span>`}
    </button>
  </div>`;
}

/** A member shown alone: its rows by phase across the field, the label over each row's left edge (*now*, *next*, *later*), the rows after *now* muted. `list`: what `useColumn` shows. */
export function Rows({ list, nodes, member, wide = false }) {
  return rowsOf(list, nodes).map((r) => html`<div key=${r.row} class=${cls("arena-phase", { "is-later": r.row !== "now", "is-wide": wide })} data-row=${r.row}>
    <span class="arena-phase__lbl">${r.row}</span>
    ${r.stacks.map((s) => html`<${Stack} key=${s.goal} goal=${s.goal} items=${s.items} later=${r.row !== "now"} wide=${wide} member=${member} row=${r.row} />`)}
  </div>`);
}

/** A member's cells on the field (spec 82 §2): one per row it has a stack in, each on its own
 *  grid line (`gridRow`), in the member's column (field.js `Column`: a subgrid of the field's rows), so that a row reads straight across the table. Rows of the grid: label, cards, label, cards, label, cards. */
export function Cells({ list, nodes, member }) {
  return rowsOf(list, nodes).map((r) => html`<div key=${r.row} class=${cls("arena-phase is-cell", { "is-later": r.row !== "now" })} data-row=${r.row} style=${`grid-row:${gridRow(r.row)}`}>
    ${r.stacks.map((s) => html`<${Stack} key=${s.goal} goal=${s.goal} items=${s.items} later=${r.row !== "now"} wide=${false} member=${member} row=${r.row} />`)}
  </div>`);
}

/** The grid line of a row's cards (its label is the line above): now 2, next 4, later 6. */
export const gridRow = (row) => ["now", "next", "later"].indexOf(row) * 2 + 2;
/** A row's label, at the table's left edge, over its cells (spec 82 §2). */
export const RowLabel = ({ row }) => html`<span class=${cls("arena-row__lbl", { "is-later": row !== "now" })} data-row=${row} style=${`grid-row:${gridRow(row) - 1}`}>${ROW_LABEL[row]}</span>`;
