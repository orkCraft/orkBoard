// The lanes of the Orkmaster's tables of a goal at its Talk and its spec (stageboard.js; docs/specs/168 C3): the Board's own grid (`.table-board`, one lane a party standing under its tab), with what the stage lays in the lanes of the leaders of the route
// and the other lanes empty. `children`: a function of the party that draws the leader's place.
import { html } from "../html.js";
import { isLive, nameOf, partiesNow, wide } from "./data.js";
import { raceOf } from "./felt.js";

export function Lanes({ n, stage, leaders, children }) {
  const draw = Array.isArray(children) ? children[0] : children;
  return html`<div class="table-board sb-board" data-picked=${n.slug} data-stage=${stage} data-tokens="false">
    ${partiesNow().map((g) => html`<div key=${g.slug} class="table-lane" data-party=${g.slug} data-live=${wide.value && isLive(g) ? "1" : undefined} role="group" aria-label=${nameOf(g)} data-race=${raceOf(g) || undefined}
      data-onroute=${leaders.includes(g.slug) ? "1" : "0"}>${leaders.includes(g.slug) && draw(g)}</div>`)}
    <div class="table-lane table-lane--free"></div>
  </div>`;
}
