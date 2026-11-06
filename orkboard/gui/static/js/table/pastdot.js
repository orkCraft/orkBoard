// The muted dot on a party's tab (docs/specs/156-one-pick-and-the-release-column.md D.5, decisions §261.9; before it the pyramid's edge, spec 150 E2.3): **a decision newer than the party's last look** (pastseen.js: the newest decision number seen, per party,
// in this browser) — the party's newest decision, by code (`ideas.chronicle_last {party, n: 1}`), read once a page and again when a look is written. It is gone once that tab's discard is scrolled to the past (lane.js calls `markSeen`). Never looked at,
// nothing is new: the first read is taken as seen. A dot is a mark, not a count; it is drawn in the muted ink (tabmarks.css `.table-tab__new`).
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { ask } from "./chronicleparts.js";
import { seenOf, seenTick, setSeen } from "./pastseen.js";

export const NEW_DECISION = "A decision is newer than your last look at this party's past";

/** The newest decision number of a party's past, 0 when it has none or the host does not say. */
export async function newestOf(party) {
  const [r] = await ask("ideas.chronicle_last", { ...(party ? { party } : {}), n: 1 });
  return Math.max(0, ...((r?.decisions || []).map((d) => Number(d.number) || 0)));
}

export function PastDot({ party }) {
  const [top, setTop] = useState(0), tick = seenTick.value;
  useEffect(() => {                                                                  // once a page for each party (the host reads its log for it) and again when a look is written
    let live = true;
    newestOf(party).then((n) => { if (live) setTop(n); });
    return () => { live = false; };
  }, [party, tick]);
  const seen = seenOf(party);
  useEffect(() => { if (top && seen === null) setSeen(party, top); }, [top, seen, party]);           // never looked at: nothing is new, the newest is taken as seen
  return top && seen !== null && top > seen ? html`<span class="table-tab__new" data-new=${party} role="img" aria-label=${NEW_DECISION} title=${NEW_DECISION}></span>` : null;
}
