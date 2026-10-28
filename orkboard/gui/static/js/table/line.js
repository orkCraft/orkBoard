// The line over the pane (docs/specs/101-the-cards-the-cascade-and-the-hand-under-the-lanes.md §3.3, decisions §167.5; kind `line` of frame/kinds.js): past about seven goals the first lane's last cascade ends in *All · search*, which opens
// the whole line over the pane — a search, then every goal in line with its party and why it waits; a press picks it, the arrows move it. The move is the Board's own (`ideas.move`): a goal moves among its own party's goals (before another of
// its party, else last), so a drop among the goals of other parties changes nothing and the card goes back. The moves are written here for the cascade (cascade.js) and this list alike.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Icon, Sign } from "../orkui.js";
import { act } from "../shell/store.js";
import { pick, picked } from "../frame/state.js";
import { drawn } from "../frame/kinds.js";
import { lineNow, waitsWords } from "./data.js";

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

/** The whole line over the pane. */
export function LineList() {
  const [q, setQ] = useState(""), line = lineNow(), want = q.trim().toLowerCase();
  const found = line.filter((g) => !want || `${g.full} ${g.partyName}`.toLowerCase().includes(want));
  return html`<div class="table-line" aria-label="The goals in line">
    <div class="table-line__search"><${Icon} name="search" /><input type="search" class="ork-field" aria-label="Search the goals in line" placeholder="Search the goals in line" value=${q}
      onInput=${(e) => setQ(e.currentTarget.value)} autofocus /></div>
    ${!found.length && html`<p class="table-over__muted">${line.length ? "No goal in line matches." : "Nothing is in line."}</p>`}
    <ul class="table-line__rows">${found.map((g) => html`<li key=${g.slug} class="table-line__item">
      <button type="button" class=${cls("ork-row table-line__row", { "is-on": picked.value === g.slug })} data-slug=${g.slug} onClick=${() => pick(g.slug)}>
        <${Elem} name=${g.element} dim=${!g.element} /><span class="table-line__text"><span class="body">${g.full}</span><span class="cap table-line__sub">${g.partyName}</span></span>
        <span class="cap table-line__place">${g.reset && html`<${Sign} name="moon" /> `}${waitsWords(g)}</span>
      </button>
      <button type="button" class="ork-btn quiet" aria-label=${`Move earlier: ${g.full}`} disabled=${neighbour(line, g.slug, -1) < 0} onClick=${() => moveGoal(line, g.slug, neighbour(line, g.slug, -1))}><${Icon} name="chevron-up" /></button>
      <button type="button" class="ork-btn quiet" aria-label=${`Move later: ${g.full}`} disabled=${neighbour(line, g.slug, 1) < 0} onClick=${() => moveGoal(line, g.slug, neighbour(line, g.slug, 1))}><${Icon} name="chevron-down" /></button>
    </li>`)}</ul>
  </div>`;
}

drawn("line", LineList);
