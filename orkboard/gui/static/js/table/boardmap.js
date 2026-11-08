// The project's tab is the Board (docs/specs/101-the-cards-the-cascade-and-the-hand-under-the-lanes.md §3, docs/specs/98-the-table-and-the-hand.md §3.3, decisions §143, §167.4–§167.6): the first lane is the whole project's — the goals the
// Orkmaster reads, routes or joins, each a card under its strip, and last the line (*In line*) —, then a lane a party, each standing under its party's tab: the tabs and the lanes read the one `--cols` of the frame, so a tab stands
// exactly over its lane. A party's lane holds its goals as cascades (cascade.js): a strip, its tasks behind the front one, the picked goal's unfolded; the lanes in the hand's order (a failure, a question, the rest). A lane narrower than a
// card lays a goal as one token with its stack's edges (spec 101 §5); no sideways scroll. **With a goal picked** (and the column pinned) the lanes hold that goal's plan alone (planboard.js, spec 128 F.1). **With the Orkmaster's column pinned** (`column`, the wide width: spec 128 B) the first lane is not drawn: its goals are the column's piles (table/column.js); the narrow width keeps it.
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { picked } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { mapData } from "../shell/store.js";
import { isLive, laneOf, lineNow, nameOf, ownOf, partiesNow, wide } from "./data.js";
import { GoalBlock, Line, OwnBlock } from "./cascade.js";
import { PlanBoard } from "./planboard.js";
import { raceOf } from "./felt.js";
import "./line.js";

/** An empty lane says whose it is, on a flat plate (spec 160 E, decisions §275.2): *Release is free · throw a goal here or @Release*. */
const freeWords = (g) => `${nameOf(g)} is free · throw a goal here or @${nameOf(g)}`;

const CARD_W = 144;                                                 // a card (frame.css `--card-w`); a lane whose room is narrower than this lays tokens

/** Whether the first lane's room is narrower than a card: the lanes' widths are the frame's (frame.css `--cols`), measured here once they are laid out. */
function useTokens(host, narrow) {
  const [tokens, setTokens] = useState(narrow);
  useLayoutEffect(() => {
    const measure = () => {
      const lane = host.current?.querySelector(".table-lane");
      let room = lane ? lane.clientWidth : CARD_W;
      if (lane) { const s = getComputedStyle(lane); room -= parseFloat(s.paddingLeft) + parseFloat(s.paddingRight); }
      setTokens(narrow || room < CARD_W - 1);
    };
    measure();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(measure) : null;
    if (host.current) ro?.observe(host.current);
    return () => ro?.disconnect();
  }, [narrow]);
  return tokens;
}

/** `parties`: every party (the Orkmaster reads, routes and joins the goals of Release and Live too); the lanes are the tabs' parties (`partiesNow`: not those two at the wide width, spec 111 §4.1). */
export function BoardMap({ parties, narrow, column = false }) {
  const host = useRef(), tokens = useTokens(host, narrow), only = picked.value;
  const plan = column && only ? (mapData.value?.nodes || []).find((x) => x.slug === only) : null;                  // a goal picked: its plan alone, with its arrows (planboard.js, spec 128 F.1)
  if (plan) return html`<${PlanBoard} n=${plan} />`;
  const own = ownOf(parties), line = lineNow(), lanes = partiesNow().map((g) => ({ g, goals: laneOf(g) }));
  const none = (column || (!own.length && !line.length)) && lanes.every((l) => !l.goals.length);
  return html`<div class="table-board" ref=${host} data-tokens=${String(tokens)} data-picked=${only || undefined}>
    ${!column && html`<div class="table-lane table-lane--first" data-lane="first" role="group" aria-label=${currentProject.value?.name || "The project"}>
      ${own.map(({ n, stage }) => html`<${OwnBlock} key=${n.slug} n=${n} stage=${stage} tokens=${tokens} />`)}
      <${Line} line=${line} tokens=${tokens} />
    </div>`}
    ${lanes.map(({ g, goals }) => html`<div key=${g.slug} class="table-lane" data-party=${g.slug} data-live=${wide.value && isLive(g) ? "1" : undefined} role="group" aria-label=${nameOf(g)} data-race=${raceOf(g) || undefined} data-empty=${goals.length ? undefined : ""}>
      ${!goals.length && html`<p class="table-lane__free ork-plate" data-free=${g.slug}>${freeWords(g)}</p>`}
      ${goals.map(({ n, tasks }) => html`<${GoalBlock} key=${n.slug} n=${n} tasks=${tasks} tokens=${tokens} />`)}
    </div>`)}
    <div class="table-lane table-lane--free">${none && html`<p class="table-board__none"><span class="ork-plate">Nothing is at work</span></p>`}</div>
  </div>`;
}
