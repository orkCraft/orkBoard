// A craft's verdict on a goal and its token (decisions §298.3): what each leader of a goal's route found, `{leader, checks: [{kind, text, fix?}]}`,
// kind ok (approved), q (a question), r (a risk), b (a risk that blocks). The host answers it (`ideas.verdicts`, gui/ideas_mats.py: each leader's `### Talk`
// of a goal's page, read free), asked once a snapshot and kept as a signal; a goal whose leaders have said nothing has none. The token is its leader's tool in
// its party's ring, its checks as squares under it, always in the order ok, q, r, b: who looked is the ring's colour, what it found the squares'. No total.
import { signal, effect } from "@preact/signals";
import { html, cls } from "../html.js";
import { command, town } from "../link.js";
import { cardsOn } from "./on.js";
import { raceOf } from "../table/felt.js";
import { whoOf } from "../table/post.js";

/** A leader's race: the party's (post.js), else the one its slug names (felt.js), so a party the page has not loaded yet still has its tool and colour. */
export const raceIn = (leader) => whoOf(leader).race || raceOf({ slug: leader });

export const KINDS = ["ok", "q", "r", "b"];
export const WORDS = { ok: ["approved", "approved"], q: ["question", "questions"], r: ["risk", "risks"], b: ["risk that blocks", "risks that block"] };
/** A race's tool, orkUI's class (`.ork-tool`). */
export const TOOLS = { ork: "drum-gear", elf: "bow-drip", knight: "map-cross", goblin: "pick-gem", gnome: "bell-waves", undead: "hourglass-candle" };
const MOST = 5;                                                 // squares of a kind on an S

/** What the host holds: {goal slug: [a leader's Talk]}, or null before it is asked. */
export const verdicts = signal(null);
let asked = null;
effect(() => {
  const snap = town.value;
  if (!cardsOn() || !snap || snap === asked) return;
  asked = snap;
  command("ideas.verdicts", {}, true).then((r) => { verdicts.value = r && typeof r === "object" ? r : {}; }).catch(() => { verdicts.value = verdicts.peek() || {}; });
});

const said = (x) => (typeof x === "string" ? x.trim() : "");
/** A leader's Talk (`{leader, verdict: go | doubt | no, why, for, against, instead, assumes: {text, signal} | null}`) as a token's checks: what it is for is approved, a
 *  doubt and what it assumes are questions, what it is against a risk (fixed by its *instead*), a *no* a risk that blocks. */
export function tokenOf(t) {
  const why = said(t.why), checks = [];
  if (said(t.for)) checks.push({ kind: "ok", text: said(t.for) });
  if (t.verdict === "go" && why) checks.push({ kind: "ok", text: why });
  if (t.verdict === "doubt") checks.push({ kind: "q", text: why || "a doubt" });
  if (t.verdict === "no") checks.push({ kind: "b", text: why || "no", fix: said(t.instead) });
  if (said(t.against)) checks.push({ kind: "r", text: said(t.against), fix: t.verdict === "no" ? "" : said(t.instead) });
  const assumes = said(t.assumes?.text ?? t.assumes);
  if (assumes) checks.push({ kind: "q", text: `assumes ${assumes}`, fix: said(t.assumes?.signal) && `shown by ${said(t.assumes.signal)}` });
  return { leader: t.leader, checks, verdict: t.verdict, stance: said(t.stance) };
}

/** The verdicts of a goal: [{leader, checks}], in the route's order; [] when none. */
export const verdictsOf = (slug) => (verdicts.value?.[slug] || []).filter((t) => t?.leader).map(tokenOf);

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
