// The implementation through a leader (docs/specs/168 C4, decisions §283.16.8; the arrows of §256's two rounds): the lanes are **its seats**, left to right as the work goes: *Those who make* (its tasks of the build band), *Those who check* (its
// check tasks), *Acceptance* (its leader checks the step against its section) and, after it, *Sent back* (the tasks the acceptance sent back to run again, four at most), an arrow between each: task → check → acceptance → the tasks sent back.
// A lane's card is the lane card of the table's own (card.js `TaskCard`, pressed it is lifted as everywhere), the seats heading each lane are those of the party that do that work (the map's `team`, `checks`). The data is the map node's tasks of
// this party (`party`, `band`, `round`, `by`) and the party's team; no data of its own. Layout: seatlanes.css. The words are the lexicon's `lane_*`.
import { html, cls } from "../html.js";
import { Head, Icon } from "../orkui.js";
import { TaskCard } from "./card.js";
import { nameOf } from "./data.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./seatlanes.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const SENT_BACK_MAX = 4;                                          // four tasks sent back at most (decisions §256)

/** The lanes of the party `g` on the goal `n`: `{make, check, back}` (its tasks by band; a task of round 2 or more was sent back and runs again), `accept` how its acceptance stands: `now` (its leader checks the step), `done` (every task merged), else `waits`. */
export function lanesOf(n, g) {
  const mine = (n.tasks || []).filter((t) => t.state !== "dropped" && (t.party || n.goal) === g.slug), back = mine.filter((t) => (t.round || 1) > 1), rest = mine.filter((t) => !((t.round || 1) > 1));
  const accept = n.busy === "accepting" ? "now" : mine.length > 0 && mine.every((t) => t.state === "merged") ? "done" : "waits";
  return { make: rest.filter((t) => t.band !== "check"), check: rest.filter((t) => t.band === "check"), back: back.slice(0, SENT_BACK_MAX), accept, seats: g.team || [] };
}

const WORDS = { now: "checks its step now", done: "step accepted", waits: "waits for the tasks" };

function Arrow() {
  return html`<span class="seat-arrow" aria-hidden="true"><${Icon} name="arrow-right" /></span>`;
}

/** A lane: its words, the heads of the seats that do its work, its task cards. */
function Lane({ id, label, seats = [], tasks, n, none }) {
  return html`<section class="seat-lane" data-lane=${id} aria-label=${label}>
    <header class="seat-lane__hd"><span class="ork-label">${label}</span>
      <span class="seat-lane__seats">${seats.map((s) => html`<span key=${s.slug} class="seat-lane__seat" title=${s.name} data-seat=${s.slug}>${s.head && html`<${Head} race=${s.head.race} tier=${s.head.tier} />`}<span class="cap">${s.name}</span></span>`)}</span></header>
    <div class="seat-lane__cards">${tasks.length ? tasks.map((t) => html`<div key=${t.id} class="seat-lane__card"><${TaskCard} n=${n} t=${t} /></div>`) : html`<p class="seat-lane__none">${none}</p>`}</div>
  </section>`;
}

/** The leader's acceptance, a lane of its own: its head and how it stands. */
function Acceptance({ g, accept }) {
  const head = g.leader?.head;
  return html`<section class="seat-lane seat-lane--accept" data-lane="accept" data-state=${accept} aria-label="Acceptance">
    <header class="seat-lane__hd"><span class="ork-label">Acceptance</span></header>
    <div class="seat-lane__cards"><p class=${cls("seat-accept", `is-${accept}`)}>${head && html`<${Head} race=${head.race} tier=${head.tier} size="mid" />`}<span class="body">${nameOf(g)}</span><span class="cap">${WORDS[accept]}</span></p></div>
  </section>`;
}

/** The lanes of the party `g`'s implementation of `n`. */
export function SeatLanes({ n, g }) {
  const l = lanesOf(n, g), makers = l.seats.filter((s) => !s.checks), checkers = l.seats.filter((s) => s.checks);
  return html`<div class="seat-lanes" data-view="seats" data-goal=${n.slug} data-party=${g.slug} aria-label=${`${nameOf(g)}'s seats at work on ${n.title}`}>
    <${Lane} id="make" label="Those who make" seats=${makers} tasks=${l.make} n=${n} none="Nothing to make" /><${Arrow} />
    <${Lane} id="check" label="Those who check" seats=${checkers} tasks=${l.check} n=${n} none="Nothing to check" /><${Arrow} />
    <${Acceptance} g=${g} accept=${l.accept} />
    ${l.back.length > 0 && html`<${Arrow} /><${Lane} id="back" label="Sent back" tasks=${l.back} n=${n} none="" />`}
  </div>`;
}
