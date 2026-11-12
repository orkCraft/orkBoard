// A craft's verdict on a goal and its token (decisions §298.3): what each leader of a goal's route found, `{leader, checks: [{kind, text, fix?}]}`,
// kind ok (approved), q (a question), r (a risk), b (a risk that blocks). The host does not answer it yet: it is the contract the mock holds
// (`proposed.verdicts`, js/mock/parts/verdicts.js), so off mocks a goal has none. The token is its leader's tool in its party's ring, its checks
// as squares under it, always in the order ok, q, r, b: who looked is the ring's colour, what it found the squares'. No total.
import { html, cls } from "../html.js";
import { proposed } from "../link.js";
import { raceOf } from "../table/felt.js";
import { whoOf } from "../table/post.js";

/** A leader's race: the party's (post.js), else the one its slug names (felt.js), so a party the page has not loaded yet still has its tool and colour. */
export const raceIn = (leader) => whoOf(leader).race || raceOf({ slug: leader });

export const KINDS = ["ok", "q", "r", "b"];
export const WORDS = { ok: ["approved", "approved"], q: ["question", "questions"], r: ["risk", "risks"], b: ["risk that blocks", "risks that block"] };
/** A race's tool, orkUI's class (`.ork-tool`). */
export const TOOLS = { ork: "drum-gear", elf: "bow-drip", knight: "map-cross", goblin: "pick-gem", gnome: "bell-waves", undead: "hourglass-candle" };
const MOST = 5;                                                 // squares of a kind on an S

/** The verdicts of a goal: [{leader, checks}], in the route's order; [] when none. */
export const verdictsOf = (slug) => (proposed("verdicts")?.[slug] || []).filter((v) => v?.leader && Array.isArray(v.checks));

/** The leader whose risk blocks the goal, or "" when none does. */
export const blockedBy = (slug) => verdictsOf(slug).find((v) => v.checks.some((c) => c.kind === "b"))?.leader || "";
export const blocked = (slug) => !!blockedBy(slug);

/** How many of each kind: {ok, q, r, b}. */
export const countOf = (checks) => Object.fromEntries(KINDS.map((k) => [k, checks.filter((c) => c.kind === k).length]));

/** What a screen reader says of a verdict: *Tech: 2 approved, 1 question, 1 risk*. */
export function saysOf(leader, checks) {
  const n = countOf(checks), parts = KINDS.filter((k) => n[k]).map((k) => `${n[k]} ${WORDS[k][n[k] === 1 ? 0 : 1]}`);
  return `${whoOf(leader).name}: ${parts.join(", ") || "nothing found"}`;
}

/** A square of a check: its kind's colour and shape (CSS `data-kind`). */
export const Square = ({ kind }) => html`<i class="cards-sq" data-kind=${kind} role="img" aria-label=${WORDS[kind]?.[0] || kind}></i>`;

/** A craft's token: a button, its leader's tool in its party's ring, its checks as squares under it. `on`: its slip is open. */
export function CraftToken({ leader, checks, onPress = null, on = false }) {
  const race = raceIn(leader), tool = TOOLS[race] || TOOLS.ork;
  return html`<button type="button" class=${cls("cards-ct", { "is-on": on })} data-race=${race || "orkmaster"} data-leader=${leader} data-ct=${leader}
      aria-label=${saysOf(leader, checks)} aria-expanded=${on ? "true" : "false"} title=${saysOf(leader, checks)}
      onClick=${(e) => { e.stopPropagation(); onPress?.(e); }} onKeyDown=${(e) => { if (e.key === "Enter" || e.key === " ") e.stopPropagation(); }}>
    <span class="cards-ct__ring"><span class=${`ork-tool ${tool}`} aria-hidden="true"></span></span>
    <span class="cards-ct__sq" aria-hidden="true">${KINDS.flatMap((k) => checks.filter((c) => c.kind === k).slice(0, MOST).map((_, i) => html`<${Square} key=${`${k}${i}`} kind=${k} />`))}</span>
  </button>`;
}
