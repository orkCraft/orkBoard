// The middle of the Orkmaster's face-down card (decisions §241): in the ring of its seal, the heads of who has the goal now, laid by how many (one large, two side by side, three a pyramid, four a square, more than four the square with the fourth
// place's head fanned over the rest, never a number) — or, while an agreed decision waits, orkUI's play sign, a press on it *Start now*. Pure over a node (`middleOf`), and drawn with orkUI's heads, sign and sigil; the places are the page's layout (column.css).
import { html, cls } from "../html.js";
import { Head, Sign } from "../orkui.js";
import { act } from "../shell/store.js";
import { waitRuns } from "./data.js";

const WRITING = ["talk", "sketch", "sections"];                                                       // the route's leaders have the goal: in Talk, and while the spec is written (the Orkmaster reads and routes it: its middle is empty)

/** What the middle of a front card holds: `{heads: [{key, race, tier, still}], fill: share of the spec written | null, wait: share of the wait left | null}`. A wait that runs: the play (`wait`), no heads; Talk: the route's leaders, the ones that have
 *  answered still; the spec: the route's leaders, the ones whose section is written still, the ring filled by the sections written of the route's, the Orkmaster's join the last share (`fill` is null until the first is written: the ring runs as before). Else empty. */
export function middleOf(n) {
  const b = n.back || {};
  if (waitRuns(n)) { const r = b.ripe, total = Number(r.seconds) || 0, left = Number(r.left_s); return { heads: [], fill: null, wait: total > 0 && Number.isFinite(left) ? Math.min(1, Math.max(0, left / total)) : 0 }; }
  if (!WRITING.includes(n.state)) return { heads: [], fill: null, wait: null };
  const route = b.route || [], said = new Set(n.state === "talk" ? b.heard : b.written);
  const heads = route.filter((s) => s.head).map((s) => ({ key: s.party, race: s.head.race, tier: s.head.tier, still: said.has(s.party) }));
  return { heads, fill: n.state === "talk" ? null : route.length && (b.written || []).length ? (b.written || []).filter((p) => route.some((s) => s.party === p)).length / (route.length + 1) : null, wait: null };
}

/** The heads, laid by how many: `data-n` is the count up to four, `more` past it (the 5th and on lie fanned behind the 4th). Each steps (`is-working`, orkUI's guard step) while its call runs. */
export function MidHeads({ heads }) {
  if (!heads.length) return null;
  const one = (h, extra) => html`<span key=${h.key} class=${cls("col-mid__h", { "is-working": !h.still })} data-party=${h.key} data-still=${h.still ? "1" : "0"} style=${extra}><${Head} race=${h.race} tier=${h.tier} size=${heads.length === 1 ? "mid" : ""} /></span>`;
  const first = heads.slice(0, 3), rest = heads.slice(3);
  return html`<span class="col-mid" data-n=${Math.min(4, heads.length)} data-more=${heads.length > 4 ? "1" : undefined}>
    ${first.map((h) => one(h))}
    ${rest.length > 0 && html`<span class="col-mid__fan">${rest.slice(1).map((h, k) => [h, Math.min(k + 1, 3)]).reverse().map(([h, k]) => one(h, `--k:${k}`))}${one(rest[0], "--k:0")}</span>`}
  </span>`;
}

/** The play in the ring's middle: *Start now* for an agreed decision whose wait runs. A sibling of the card (a button inside a button is not one), over its middle, and it takes its press, not the card's. */
export function Play({ n }) {
  const press = (e) => { e.stopPropagation(); act("ideas.confirm", { idea: n.slug }); };
  return html`<button type="button" class="ork-btn quiet col-play" data-play=${n.slug} aria-label=${`Start now: ${n.title}`} title="Start now" onClick=${press}><${Sign} name="play" big=${true} /></button>`;
}
