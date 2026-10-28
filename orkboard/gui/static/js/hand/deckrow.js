// The deck opened (docs/specs/98-the-table-and-the-hand.md §4.1, decisions §160.3): pressed, the deck fans out in a row over the hand: the + card, then the goals in line in the
// Orkmaster's order, each its element and name (one that waits for the reset shows the moon and its hour); a goal dragged moves in the line (`ideas.move`), a goal pressed is picked;
// past seven, the last card is *All · search*, which opens the whole line over the pane (`deck`, face: DeckList). Esc or a press away closes the row (hand.js). A drag starts from the
// goal itself with a mouse and from its handle on touch (the row scrolls sideways there); Alt+← and Alt+→ move the goal that has the focus, so no move needs a pointer.
// `ideas.move` moves a goal among its own party's (before another of its party, else last): a drop among the goals of other parties changes nothing and the card goes back.
import { useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Icon, Sign } from "../orkui.js";
import { act } from "../shell/store.js";
import { hhmm } from "../board/store.js";
import { openOver, pick, picked } from "../frame/state.js";
import { lineOf, MANY } from "./data.js";
import { PlusCard } from "./pluscard.js";
import { useFan, leans } from "./motion.js";
import { rowOpen } from "./state.js";

const THRESHOLD = 6;                                               // px a pointer moves before a press is a drag

/** The call that puts `slug` at `to` (an index in `line`) among its party's goals, null when that changes nothing: `{slug, before?}`. */
export function moveArgs(line, slug, to) {
  const from = line.findIndex((g) => g.slug === slug);
  if (from < 0 || to === from) return null;
  const me = line[from], next = [...line.slice(0, from), ...line.slice(from + 1)];
  next.splice(Math.max(0, Math.min(to, next.length)), 0, me);
  const mine = (list) => list.filter((g) => g.party === me.party).map((g) => g.slug);
  const was = mine(line), now = mine(next);
  if (was.join("|") === now.join("|")) return null;
  const after = now[now.indexOf(slug) + 1];
  return { slug, ...(after ? { before: after } : {}) };
}

/** Where `slug` goes to move one place among its own party's goals (-1 earlier, 1 later): the index of the next goal of its party that way, -1 with none. */
export function neighbour(line, slug, dir) {
  const i = line.findIndex((g) => g.slug === slug);
  if (i < 0) return -1;
  let j = i + dir;
  while (line[j] && line[j].party !== line[i].party) j += dir;
  return line[j] ? j : -1;
}

export async function moveGoal(line, slug, to) {
  const args = moveArgs(line, slug, to);
  return args ? act("ideas.move", args) : null;
}

/** What a goal in line says under its name: the moon and its hour when it waits for the reset; else why it waits. */
function Waits({ g }) {
  if (g.reset) return html`<span class="hand-card__wait"><${Sign} name="moon" />${g.at && html`<span class="cap">from ${hhmm(g.at)}</span>`}</span>`;
  if (g.waits === "held") return html`<span class="cap hand-card__wait">Held</span>`;
  if (g.waits === "line") return html`<span class="cap hand-card__wait">Waits for a goal</span>`;
  return null;
}

/** The row: the + card, the goals (seven at most), *All · search*. */
export function DeckRow({ line, onPlus }) {
  const fan = useFan(true), shown = line.slice(0, MANY), [drag, setDrag] = useState(null), box = useRef(), still = useRef(false);
  const begin = (g, i) => (e) => {
    if (e.button > 0 || (e.pointerType === "touch" && !e.target.closest(".hand-grip"))) return;
    const cards = [...box.current.querySelectorAll(".hand-line")], rects = cards.map((c) => c.getBoundingClientRect());
    const step = rects.length > 1 ? rects[1].left - rects[0].left : rects[0].width, from = { x: e.clientX, y: e.clientY, slug: g.slug, i, rects, step, id: e.pointerId, live: false };
    const move = (m) => {
      if (m.pointerId !== from.id) return;
      const dx = m.clientX - from.x;
      if (!from.live && Math.abs(dx) < THRESHOLD && Math.abs(m.clientY - from.y) < THRESHOLD) return;
      from.live = true;
      const centre = rects[i].left + rects[i].width / 2 + dx, to = Math.max(0, Math.min(shown.length - 1, rects.filter((r, k) => k !== i && r.left + r.width / 2 < centre).length));
      setDrag({ slug: g.slug, dx, i, to, step });
    };
    const end = (m) => {
      if (m.pointerId !== from.id) return;
      window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", end); window.removeEventListener("pointercancel", end);
      if (from.live) {
        still.current = true; setTimeout(() => { still.current = false; }, 0);          // the click that follows a drag is not a press
        const centre = rects[i].left + rects[i].width / 2 + (m.clientX - from.x), to = Math.max(0, Math.min(shown.length - 1, rects.filter((r, k) => k !== i && r.left + r.width / 2 < centre).length));
        setDrag(null);
        if (m.type === "pointerup") moveGoal(line, g.slug, to);
      }
    };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", end); window.addEventListener("pointercancel", end);
  };
  const shift = (i) => {
    if (!drag) return undefined;
    if (i === drag.i) return `transform:translateX(${drag.dx}px);z-index:3`;
    if (drag.i < drag.to && i > drag.i && i <= drag.to) return `transform:translateX(${-drag.step}px)`;
    if (drag.i > drag.to && i < drag.i && i >= drag.to) return `transform:translateX(${drag.step}px)`;
    return undefined;
  };
  const key = (g, i) => (e) => {
    if (!e.altKey || (e.key !== "ArrowLeft" && e.key !== "ArrowRight")) return;
    e.preventDefault();
    const to = neighbour(line, g.slug, e.key === "ArrowLeft" ? -1 : 1);
    if (to >= 0) moveGoal(line, g.slug, to);
  };
  const press = (g) => () => { if (!still.current) pick(g.slug); };
  if (!fan.shown) return null;
  return html`<div ref=${box} class=${cls("hand-fan ork-fan hand-row", { closing: fan.closing })} role="group" aria-label="The deck, fanned out">
    <div class="hand-fan__card" style="--ork-fan-i:0;--ork-fan-mid:4"><${PlusCard} onPress=${onPlus} /></div>
    ${shown.map((g, i) => html`<div key=${g.slug} class="hand-fan__card" style=${`--ork-fan-i:${i + 1};--ork-fan-mid:4`}>
      <button type="button" class=${cls("ork-card ork-leans hand-card hand-line", { "is-on": picked.value === g.slug, "is-dragged": drag?.slug === g.slug })} data-slug=${g.slug} data-party=${g.party}
        style=${shift(i)} aria-label=${`${g.title}${g.reset ? ", waits for the reset" : ""}. Alt and the arrow keys move it in the line.`} title=${g.full} onPointerDown=${begin(g, i)} onKeyDown=${key(g, i)}
        onClick=${press(g)} ...${drag ? {} : leans}>
        <span class="hand-card__top"><${Elem} name=${g.element} dim=${!g.element} />
          <span class="hand-grip" aria-hidden="true" title="Drag to move in line"><i></i><i></i><i></i><i></i><i></i><i></i></span></span>
        <span class="hand-card__name">${g.title}</span>
        <span class="hand-card__foot"><${Waits} g=${g} /></span>
      </button></div>`)}
    ${line.length >= MANY && html`<div class="hand-fan__card" style="--ork-fan-i:8;--ork-fan-mid:4">
      <button type="button" class="ork-card ork-leans hand-card hand-all" aria-label="All goals in line, with a search" onClick=${() => { rowOpen.value = false; openOver("deck", {}, null, "In line"); }} ...${leans}>
        <${Icon} name="search" /><span class="body">All · search</span></button></div>`}
  </div>`;
}

/** The whole line over the pane (`deck`): a search, then every goal in line with its party and why it waits; a press picks it, the arrows move it. */
export function DeckList() {
  const [q, setQ] = useState(""), line = lineOf(), want = q.trim().toLowerCase();
  const found = line.filter((g) => !want || `${g.full} ${g.partyName}`.toLowerCase().includes(want));
  return html`<div class="hand-list" aria-label="The goals in line">
    <div class="hand-list__search"><${Icon} name="search" /><input type="search" class="ork-field" aria-label="Search the goals in line" placeholder="Search the goals in line" value=${q}
      onInput=${(e) => setQ(e.currentTarget.value)} autofocus /></div>
    ${!found.length && html`<p class="ok-tone-muted">${line.length ? "No goal in line matches." : "Nothing is in line."}</p>`}
    <ul class="hand-list__rows">${found.map((g) => {
      return html`<li key=${g.slug} class="hand-list__item">
        <button type="button" class=${cls("ork-row hand-list__row", { "is-on": picked.value === g.slug })} data-slug=${g.slug} onClick=${() => pick(g.slug)}>
          <${Elem} name=${g.element} dim=${!g.element} /><span class="hand-list__text"><span class="body">${g.full}</span><span class="cap hand-list__sub">${g.partyName}</span></span>
          <span class="cap hand-list__place">${g.reset ? html`<${Sign} name="moon" /> Waits for the reset${g.at ? ` · from ${hhmm(g.at)}` : ""}` : g.waits === "held" ? "Held" : g.waits === "line" ? "Waits for a goal" : "In line"}</span>
        </button>
        <button type="button" class="ork-btn quiet" aria-label=${`Move earlier: ${g.full}`} disabled=${neighbour(line, g.slug, -1) < 0} onClick=${() => moveGoal(line, g.slug, neighbour(line, g.slug, -1))}><${Icon} name="chevron-up" /></button>
        <button type="button" class="ork-btn quiet" aria-label=${`Move later: ${g.full}`} disabled=${neighbour(line, g.slug, 1) < 0} onClick=${() => moveGoal(line, g.slug, neighbour(line, g.slug, 1))}><${Icon} name="chevron-down" /></button>
      </li>`;
    })}</ul>
  </div>`;
}
