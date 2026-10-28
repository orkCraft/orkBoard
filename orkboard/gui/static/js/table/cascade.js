// A goal's cascade and the line (docs/specs/101-the-cards-the-cascade-and-the-hand-under-the-lanes.md §3, decisions §167.4–§167.5): in a party's lane a goal is a thin strip (its element, its name on one line, the whole strip a button that
// picks the goal) over its tasks laid as a solitaire's cascade — the front one whole, the others as strips above it (the stage's small sign and the task's name, each a button that lifts its task). Collapsed always but the picked goal's,
// which unfolds into whole cards in the same order. A goal in two lanes at once has its strip in both, lit alike (orkUI's `.ork-picked`). The first lane's last cascade is **the line**: the goals in line (`lineNow()`), the front one
// the next to start, whole, the others strips above it; a strip pressed picks its goal, a goal dragged among them moves it (`ideas.move`, line.js), past about seven *All · search* opens the whole line over the pane (kind `line`).
// A drag starts from the goal with a mouse; Alt+↑ and Alt+↓ move the goal that has the focus, so no move needs a pointer (and the list over the pane has its arrows).
import { useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Icon, Sign } from "../orkui.js";
import { lifted, lift, openOver, pick, picked } from "../frame/state.js";
import { MANY, STAGES, stageOf, waitsWords } from "./data.js";
import { TaskCard, OwnCard, Token, aboutTokens, leans, litKey, taskKey } from "./card.js";
import { moveGoal, neighbour } from "./line.js";

const THRESHOLD = 6;                                               // px a pointer moves before a press is a drag

/** A goal's strip: its element and its name on one line; the whole strip picks the goal (or puts it down), and wears orkUI's pick while it is the picked one. */
export function GoalStrip({ n }) {
  const on = picked.value === n.slug;
  return html`<button type="button" class=${cls("ork-card table-gstrip", { "ork-picked": on, "is-on": on })} data-goal=${n.slug} data-about=${`idea:${n.slug}`} aria-pressed=${String(on)}
    aria-label=${n.title} title=${n.title} onClick=${() => pick(n.slug)}><${Elem} name=${n.element} dim=${!n.element} /><span class="table-gstrip__nm">${n.short || n.title}</span></button>`;
}

/** A task behind the front one: the stage's small sign and its name; a press lifts it. */
export function TaskStrip({ n, t }) {
  const key = taskKey(n, t), on = lifted.value === key, bad = t.state === "failed", asks = t.state === "picking";
  return html`<button type="button" class=${cls("ork-card table-tstrip", { fails: bad, asks, "is-lifted": on, "is-lit": litKey.value === key })} data-lkey=${key} data-goal=${n.slug} data-task=${t.id}
    data-about=${aboutTokens(n, [t])} data-state=${t.state} data-stage=${stageOf(t)} aria-pressed=${String(on)} aria-label=${`${t.title}: ${STAGES[stageOf(t)].word}${bad ? ", failed" : ""}`} title=${t.title}
    onClick=${() => lift(on ? "" : key)}><${Sign} name=${STAGES[stageOf(t)].sign} /><span class="table-tstrip__nm">${t.short || t.title}</span></button>`;
}

/** A goal's tasks, the front one first: collapsed, the others as strips above the whole front one (the nearest the front the next in turn); the picked goal's unfolded into whole cards in the same order. */
export function Cascade({ n, tasks }) {
  const open = picked.value === n.slug, rest = tasks.slice(1).reverse();
  return html`<div class=${cls("table-casc", { "is-open": open })} data-goal=${n.slug} data-open=${String(open)}>
    ${open ? [...tasks].reverse().map((t) => html`<${TaskCard} key=${t.id} n=${n} t=${t} />`)
      : html`${rest.map((t) => html`<${TaskStrip} key=${t.id} n=${n} t=${t} />`)}<${TaskCard} key=${tasks[0].id} n=${n} t=${tasks[0]} />`}
  </div>`;
}

/** A goal in its party's lane: its strip over its cascade. At a lane a token wide, one token with its stack's edges. */
export function GoalBlock({ n, tasks, tokens }) {
  if (tokens) return html`<${Token} n=${n} tasks=${tasks} />`;
  return html`<div class="table-goal" data-goal=${n.slug}><${GoalStrip} n=${n} /><${Cascade} n=${n} tasks=${tasks} /></div>`;
}

/** A goal the Orkmaster reads, routes or joins itself, in the first lane: its strip over its card. */
export function OwnBlock({ n, stage, tokens }) {
  if (tokens) return html`<${Token} n=${n} stage=${stage} />`;
  return html`<div class="table-goal" data-goal=${n.slug}><${GoalStrip} n=${n} /><${OwnCard} n=${n} stage=${stage} /></div>`;
}

// -- the line ----------------------------------------------------------------------------------------------------------------------

/** What a goal in line says it waits for, on hover and to a screen reader. */
const wordsOf = (g) => `${g.full}: ${waitsWords(g)}`;

/** The moon, with the hour on hover, on a goal that waits for the window's reset. */
const moon = (g) => (g.reset ? html`<${Sign} name="moon" label=${waitsWords(g)} />` : null);

/** The front of the line, whole: the goal's element and name, its type in the window (the moon beside it when it waits for the reset), *In line* in the label row. */
function LineCard({ g, grip }) {
  const sign = g.type?.sign || "";
  return html`<button type="button" class=${cls("ork-card ork-leans table-card table-card--line", { "ork-picked": picked.value === g.slug })} data-line-item="1" data-slug=${g.slug} data-party=${g.party} data-about=${`idea:${g.slug}`}
    aria-label=${wordsOf(g)} title=${wordsOf(g)} ...${grip}>
    <span class="table-card__head"><${Elem} name=${g.element} dim=${!g.element} /><span class="table-card__nm">${g.title}</span></span>
    <span class=${`table-card__win is-${g.element || "none"}`}>${sign && html`<${Sign} name=${sign} big=${true} />`}${g.reset && html`<${Sign} name="moon" big=${true} label=${waitsWords(g)} />`}</span>
    <span class="table-card__row"><span class="table-stage">In line</span></span>
  </button>`;
}

function LineStrip({ g, grip }) {
  const on = picked.value === g.slug;
  return html`<button type="button" class=${cls("ork-card table-gstrip table-lstrip", { "ork-picked": on, "is-on": on })} data-line-item="1" data-slug=${g.slug} data-party=${g.party} data-about=${`idea:${g.slug}`}
    aria-label=${wordsOf(g)} title=${wordsOf(g)} ...${grip}><${Elem} name=${g.element} dim=${!g.element} /><span class="table-gstrip__nm">${g.title}</span>${moon(g)}</button>`;
}

const openLine = () => openOver("line", {}, { title: "Board", key: "" }, "In line");

/** The line at a lane a token wide: a token a goal (its element and its type), the moon on one that waits for the reset; a press picks it, the last token opens the whole line. */
function LineTokens({ shown }) {
  return html`<div class="table-line-tokens" role="group" aria-label="In line">
    ${shown.map((g) => html`<button type="button" key=${g.slug} class=${cls("ork-card table-token", { "ork-picked": picked.value === g.slug })} data-slug=${g.slug} data-party=${g.party} data-about=${`idea:${g.slug}`}
      aria-label=${wordsOf(g)} title=${wordsOf(g)} aria-pressed=${String(picked.value === g.slug)} onClick=${() => pick(g.slug)}>
      <span class="table-card__top"><${Elem} name=${g.element} dim=${!g.element} />${moon(g)}</span>
      <span class=${`table-card__win is-${g.element || "none"}`}>${g.type?.sign && html`<${Sign} name=${g.type.sign} big=${true} />`}</span>
    </button>`)}
    <button type="button" class="ork-card table-token table-token--all" aria-label="All goals in line, with a search" title="All · search" onClick=${openLine}><${Icon} name="search" /></button>
  </div>`;
}

/** The line, the first lane's last cascade (the line: `lineNow()`; the front one the next to start, the farthest at the top). */
export function Line({ line, tokens }) {
  const box = useRef(), still = useRef(false), [drag, setDrag] = useState(null);
  const shown = line.slice(0, MANY), more = line.length > MANY, ord = [...shown].reverse();     // top to bottom: the farthest first, the front last
  if (!line.length) return null;
  if (tokens) return html`<${LineTokens} shown=${shown} />`;
  const begin = (g) => (e) => {
    if (e.button > 0 || e.pointerType === "touch" || !box.current) return;
    const els = [...box.current.querySelectorAll("[data-line-item]")], rects = els.map((el) => el.getBoundingClientRect()), i = els.findIndex((el) => el.dataset.slug === g.slug);
    const gap = parseFloat(getComputedStyle(box.current).rowGap) || 0, from = { x: e.clientX, y: e.clientY, id: e.pointerId, live: false };
    const target = (dy) => {
      const centre = rects[i].top + rects[i].height / 2 + dy;
      return Math.max(0, Math.min(shown.length - 1, rects.filter((r, k) => k !== i && r.top + r.height / 2 < centre).length));
    };
    const move = (m) => {
      if (m.pointerId !== from.id) return;
      const dy = m.clientY - from.y;
      if (!from.live && Math.abs(dy) < THRESHOLD && Math.abs(m.clientX - from.x) < THRESHOLD) return;
      from.live = true;
      setDrag({ slug: g.slug, dy, i, to: target(dy), step: rects[i].height + gap });
    };
    const end = (m) => {
      if (m.pointerId !== from.id) return;
      removeEventListener("pointermove", move); removeEventListener("pointerup", end); removeEventListener("pointercancel", end);
      if (!from.live) return;
      still.current = true;
      setTimeout(() => { still.current = false; }, 0);                // the click that follows a drag is not a press
      const to = shown.length - 1 - target(m.clientY - from.y);       // the top of the cascade is the end of the line
      setDrag(null);
      if (m.type === "pointerup") moveGoal(line, g.slug, to);
    };
    addEventListener("pointermove", move); addEventListener("pointerup", end); addEventListener("pointercancel", end);
  };
  const shift = (v) => {
    if (!drag) return undefined;
    if (v === drag.i) return `transform:translateY(${drag.dy}px);z-index:3;position:relative`;
    if (drag.i < drag.to && v > drag.i && v <= drag.to) return `transform:translateY(${-drag.step}px)`;
    if (drag.i > drag.to && v < drag.i && v >= drag.to) return `transform:translateY(${drag.step}px)`;
    return undefined;
  };
  const key = (g) => (e) => {
    if (!e.altKey || (e.key !== "ArrowUp" && e.key !== "ArrowDown")) return;
    e.preventDefault();
    const to = neighbour(line, g.slug, e.key === "ArrowUp" ? 1 : -1);        // up is farther from the front: later in line
    if (to >= 0) moveGoal(line, g.slug, to);
  };
  const grip = (g) => ({ onPointerDown: begin(g), onKeyDown: key(g), onClick: () => { if (!still.current) pick(g.slug); }, ...(drag ? {} : leans) });
  return html`<div ref=${box} class=${cls("table-casc table-casc--line", { "is-dragging": !!drag })} role="group" aria-label="In line. Alt and the up and down arrows move a goal.">
    ${more && html`<button type="button" class="ork-card table-gstrip table-lstrip table-lstrip--all" aria-label="All goals in line, with a search" onClick=${openLine}><${Icon} name="search" /><span class="table-gstrip__nm">All · search</span></button>`}
    ${ord.map((g, v) => html`<div key=${g.slug} class="table-line-item" style=${shift(v)}>${v === ord.length - 1 ? html`<${LineCard} g=${g} grip=${grip(g)} />` : html`<${LineStrip} g=${g} grip=${grip(g)} />`}</div>`)}
  </div>`;
}
