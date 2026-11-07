// A hero's table (docs/specs/157-the-inventory-a-merchants-stall.md E, decisions §267.2): the map of a party whose leader's hero is not its craft's default. Its places are the hero's school laid out as lanes or rows, its cards the
// kept frame's (`ideas.hero_table {party}`, realm/hero_table.py); a card is a map card of the mockup (docs/mockups/merchant/tables.css `.mc`): title, line, its goal's element at the top left, its state as the border.
// Over the table, while nothing is kept or the kept frame is stale, one line says who lays it and the goal that does (spec 157 F).
import { html, cls } from "../html.js";
import { Elem } from "../orkui.js";
import { pick, picked } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { MapFrame, useRead } from "./mapkit.js";

if (typeof document !== "undefined") {
  const href = new URL("./heromap.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const MAP = "hero", LAYING = "Lay the tables", STATES = ["hot", "bad", "good", "ghost"];

/** The one place that knows the host's shape: `{hero, layout: "lanes"|"rows", laid, stale, places: [{name, ask, cards: [{title, line, goal, state}]}], elements: {<goal slug>: <element>}}`. */
export function readTable(d) {
  if (!d) return null;
  const elements = d.elements || d.goal_elements || {};
  return {
    layout: d.layout === "rows" ? "rows" : "lanes",
    laid: d.laid || "",
    stale: !!d.stale,
    places: (d.places || []).map((p) => ({
      name: p.name || "", ask: p.ask || "",
      cards: (p.cards || []).map((c) => ({ title: c.title || "", line: c.line || "", goal: c.goal || "", state: STATES.includes(c.state) ? c.state : "", element: c.goal ? elements[c.goal] || "" : "" })),
    })),
  };
}

/** The goal that lays the tables, found on the Board by its title (null while the snapshot holds none). */
export const layingGoal = () => (mapData.value?.nodes || []).find((n) => n.title === LAYING) || null;

function Card({ c }) {
  return html`<article class=${cls("hm-card", { [c.state]: !!c.state })} data-goal=${c.goal || undefined} data-state=${c.state || undefined}>
    <div class="hm-card__top">${c.element && html`<${Elem} name=${c.element} />`}</div>
    <b>${c.title}</b>${c.line && html`<small>${c.line}</small>`}
  </article>`;
}

function Place({ p }) {
  return html`<section class=${cls("hm-place", { "is-empty": !p.cards.length })} data-place=${p.name}>
    <header class="hm-place__h"><h3 class="hm-place__nm">${p.name}</h3>${p.ask && html`<span class="hm-place__ask">${p.ask}</span>`}</header>
    ${p.cards.length > 0 && html`<div class="hm-place__cards">${p.cards.map((c, i) => html`<${Card} key=${i} c=${c} />`)}</div>`}
  </section>`;
}

function Laying({ hero, party, stale }) {
  const goal = layingGoal();
  const name = stale ? `Lay ${party}'s table` : LAYING;
  return html`<p class="hm-laying" data-laying=${stale ? "stale" : "none"}>${hero} lays this table with the goal ${goal
    ? html`<button type="button" class="ork-btn quiet hm-laying__goal" aria-pressed=${String(picked.value === goal.slug)} onClick=${() => pick(goal.slug)}>${name}</button>`
    : html`<span class="hm-laying__goal">${name}</span>`}</p>`;
}

export function HeroMap({ g }) {
  const [rd] = useRead("ideas.hero_table", { party: g.slug }), t = readTable(rd.data), hero = g.leader?.hero?.name || "The hero";
  return html`<${MapFrame} map=${MAP} className="mp--hero">
    ${t && (!t.laid || t.stale) && html`<${Laying} hero=${hero} party=${g.title || g.slug} stale=${t.stale} />`}
    ${t && html`<div class=${cls("hm", `is-${t.layout}`)} data-layout=${t.layout}>${t.places.map((p) => html`<${Place} key=${p.name} p=${p} />`)}</div>`}
    ${!t && rd.err && html`<p class="mp-err" role="alert">${rd.err}</p>`}
  </${MapFrame}>`;
}
