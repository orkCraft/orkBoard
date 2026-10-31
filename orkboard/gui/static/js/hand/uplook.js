// What the phone's middle looks at (docs/specs/117-the-phone-a-menu-of-the-leaders.md §5, decisions §195.2): **a goal** when `picked` names one (a press on a card of the hand's row, a goal of the menu, a push's arrival), **a party** when the person picked one in the menu
// (`tab` a party's slug and `picked` empty), **else the goal of the hand's first card** (the one `entries.js` `placeOf` names), and with no card **nothing**. The phone keeps no state of its own beyond `frame/state.js` and `entries.js`.
// A goal is its header, the context's lines that are not its way and its top card with its answers when it has an entry in the hand (the entry whose goal it is), then its way (upway.js); a card of no goal (*Go on paid?*, a sign-in, a project's question) is its context and
// its card; a party is its leader's header (upparty.js); with nothing: *Nothing waits for you.* The hand's row raises the card the middle shows, none while a party or a goal with no card is looked at.
import { html } from "../html.js";
import { ORKMASTER, picked, tab } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { partiesAll } from "../table/data.js";
import { Context } from "./context.js";
import { goalOfEntry } from "./entries.js";
import { ReadyCard, readyStop } from "./readycard.js";
import { Lifted } from "./stopcard.js";
import { Party } from "./upparty.js";
import { GoalHead, Phases, Route, Tasks, Waits, Why } from "./upway.js";

/** What is looked at, `{kind: "goal" | "party" | "card" | "none", entry, node?, slug?, g?}`; `entry` is the card shown (its entry in the hand), null for none. `i`: the place the hand's first entry holds (`placeOf`). */
export function lookOf(entries, i) {
  const nodes = mapData.value?.nodes || [], slug = picked.value, node = slug ? nodes.find((n) => n.slug === slug) : null;
  if (node) return { kind: "goal", slug, node, entry: entries.find((e) => goalOfEntry(e) === slug) || null };
  const g = tab.value !== ORKMASTER ? partiesAll().find((x) => x.slug === tab.value) : null;
  if (g) return { kind: "party", g, entry: null };
  const e = entries[i] || null, goal = e ? goalOfEntry(e) : "", n = goal ? nodes.find((x) => x.slug === goal) : null;
  if (!e) return { kind: "none", entry: null };
  return n ? { kind: "goal", slug: goal, node: n, entry: e } : { kind: "card", entry: e };
}

/** The middle. `entries`: the hand's entries, for a goal of a party's rows to be picked as its card. */
export function Look({ look, entries }) {
  if (look.kind === "none") return html`<div class="up-mid"><p class="up-none" role="status">Nothing waits for you.</p></div>`;
  if (look.kind === "party") return html`<div class="up-look" data-look="party"><${Party} key=${look.g.slug} g=${look.g} entries=${entries} /></div>`;
  const e = look.entry, stop = e ? (e.kind === "ready" ? readyStop(e) : e.stops[0]) : null;
  const card = e && (e.kind === "ready" ? html`<${ReadyCard} key=${e.key} e=${e} />` : html`<${Lifted} key=${stop.key} s=${stop} inline=${true} />`);
  if (look.kind === "card") return html`<div class="up-look" data-look="card" data-entry=${e.key}><${Context} s=${stop} />${card}</div>`;
  const n = look.node, line = n.place === "deck";
  return html`<div class="up-look" data-look="goal" data-goal=${n.slug} data-entry=${e ? e.key : undefined}>
    <${GoalHead} n=${n} />${stop && html`<${Context} s=${stop} bare=${true} />`}${card}
    <${Phases} n=${n} />${line ? html`<${Waits} n=${n} />` : html`<${Route} n=${n} />`}<${Why} n=${n} />${!line && html`<${Tasks} n=${n} />`}
  </div>`;
}
