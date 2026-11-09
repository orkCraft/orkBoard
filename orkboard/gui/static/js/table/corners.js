// A card's four corners (docs/specs/147-one-card-four-corners.md part A, decisions §251.2): top left the rune (which goal), top right the kind (what card), bottom left who (whose work), bottom right how much (one figure by the card's state).
// Two rows, 20 px tall, `space-between` (corners.css): the sign is 14 px and the head 16 on every card, so they read as an index. The signal colours (the alert: it waits for you; the danger: it failed; the success: done) are in the kind's corner only.
// `muchOf` is pure: its cost before it is agreed, its time left at work (else the time it has worked, as the card said before), the time it took when done, *asks you* while it waits for the person; nothing known draws nothing.
import { html, cls } from "../html.js";
import { Elem, Head, Sign, headWords } from "../orkui.js";
import { workedWords } from "./worktime.js";
import { town } from "../link.js";
import { pctShort, rated } from "../spend.js";

// the words, as realm/lexicon.py says them (corner_*; tests/test_corners_browser.py keeps them so)
export const ASKS = "asks you", LEFT = "left", TOOK = "took", WORKED = "worked", IN_MAIN = "in main since", TOK = "tok", ESTIMATE = "≈";

/** *4 min left*, *2 h left*: the time a task at work has left (`secs`). */
export function leftWords(secs) {
  const s = Math.max(0, Math.round(secs));
  return `${s < 3600 ? Math.max(1, Math.ceil(s / 60)) + " min" : Math.round(s / 3600) + " h"} ${LEFT}`;
}

/** *took 18 min*, *took 2 h*: the time it took. */
export function tookWords(secs) {
  const s = Math.max(0, Math.round(secs));
  return `${TOOK} ${s < 60 ? s + " s" : s < 3600 ? Math.round(s / 60) + " min" : Math.round(s / 3600) + " h"}`;
}

/** The seconds from one ISO time of the host to another, NaN when either is not usable. */
export const secondsBetween = (from, to) => (Date.parse(to || "") - Date.parse(from || "")) / 1000;

const known = (x) => typeof x === "number" && Number.isFinite(x) && x >= 0;

/** A count of tokens in the page's words (arena/limits.js `tokensWords`), with the corner's short unit: *840 tok*, *18k tok*, *1.2M tok*. */
export function tokWords(n) {
  const v = Math.max(0, Math.round(Number(n) || 0));
  const num = v >= 1e6 ? `${(v / 1e6).toFixed(1).replace(/\.0$/, "")}M` : v >= 1e4 ? `${Math.round(v / 1e3)}k` : v >= 1e3 ? `${(v / 1e3).toFixed(1).replace(/\.0$/, "")}k` : String(v);
  return `${num} ${TOK}`;
}

/** Money in the corner: *$0.42*, *$3.10*, *$12*. */
export const usdWords = (usd) => `$${usd < 10 ? usd.toFixed(2) : Math.round(usd)}`;

/** What of a spend `{tokens, usd, tool}` (the host's `spend` / `spend_est`) the page can say: `{share, tokens, usd}` (a number, or words for the share, or null). The share of the tool's window only where the page has measured that window
 *  (spend.js `rated`: the host learnt the rate of `town.rate.tool`) and the spend was made with that tool and has a price; money only with a price (Codex has none); tokens otherwise. It reuses the mana's notion of the window, never a second one. */
export function figureOf(spend) {
  if (!spend || typeof spend !== "object") return null;
  const usd = known(spend.usd) ? spend.usd : null, tokens = known(spend.tokens) && spend.tokens > 0 ? spend.tokens : null;
  if (usd === null && tokens === null) return null;
  const measured = usd !== null && rated() && (!spend.tool || spend.tool === (town.value?.rate?.tool || "claude"));
  return { share: measured ? pctShort(usd).replace(/\s+%$/, "%") : null, tokens, usd };
}

/** The spend of several tasks (a goal done: what it spent in all) as one `figureOf`: tokens added, money only when every task that spent has a price; null when none spent. */
export function spendOfTasks(tasks = []) {
  const got = (tasks || []).map((t) => t?.spend).filter((x) => x && typeof x === "object");
  if (!got.length) return null;
  const priced = got.every((x) => known(x.usd));
  return figureOf({ tokens: got.reduce((a, x) => a + (known(x.tokens) ? x.tokens : 0), 0), usd: priced ? got.reduce((a, x) => a + x.usd, 0) : null, tool: got.find((x) => x.tool)?.tool || "" });
}

/** The words of a `figureOf`: the share where measurable, else money where priced, else tokens; `{unit: "share" | "usd" | "tokens", text}`, or null. */
export function spendWords(fig) {
  if (!fig) return null;
  if (fig.share) return { unit: "share", text: fig.share };
  if (known(fig.usd) && fig.usd > 0) return { unit: "usd", text: usdWords(fig.usd) };
  if (known(fig.tokens) && fig.tokens > 0) return { unit: "tokens", text: tokWords(fig.tokens) };
  return null;
}

/** The one figure of the bottom right corner (decisions §283.17, which changes §251.2's time), `{ kind: "ask" | "spend" | "gem", text, unit?, est? }`, or null when nothing is known.
 *  `asks`: it waits for the person (*asks you* wins); `spend`: what a task at work has spent so far, or a task done in all; `est`: ahead, its party's average for its kind, said after *≈*; both are `figureOf`'s.
 *  `cost` (words): the gem of a card that is about to spend (the hand's cards), when there is no spend. The time is not here: it is in the preview and the tooltip (`timeWords`); `done`/`took`/`left`/`worked` are kept only for a face that has not moved yet. */
export function muchOf({ asks = false, spend = null, est = null, cost = "", done = false, took = NaN, left = NaN, worked = NaN } = {}) {
  if (asks) return { kind: "ask", text: ASKS };
  const got = spendWords(spend);
  if (got) return { kind: "spend", ...got, est: false };
  const ahead = spendWords(est);
  if (ahead) return { kind: "spend", unit: ahead.unit, text: `${ESTIMATE} ${ahead.text}`, est: true };
  const time = timeWords({ done, took, left, worked });                       // legacy: a face that has not moved its time to the preview yet (the Orkmaster's column, piles.js) still gets it here
  if (time) return { kind: "time", text: time };
  if (cost) return { kind: "gem", text: cost };
  return null;
}

/** A card's time in words, for its preview and its tooltip: *took 18 min* when done, *4 min left* with an estimate, *worked 30 s* else; "" with none known. All in seconds. */
export function timeWords({ done = false, took = NaN, left = NaN, worked = NaN } = {}) {
  if (done && known(took) && took > 0) return tookWords(took);
  if (!done && known(left)) return leftWords(left);
  if (!done && known(worked)) return `${WORKED} ${workedWords(worked)}`;
  return "";
}

/** A verdict's sign (decisions §283.18): `go` is ✓ in the success colour with no ring; `doubt` is ! and `no` is ✗, both in the ink; the danger (red) only for a call that **failed** (`failed`); the alert's ring only where a question waits
 *  for the person (`waits`). The faces of a leader's say, a hearing's seat and a gate's call draw their verdicts with this, so none invents a colour. `label`: its words, when it stands alone (else it is `aria-hidden`, its words beside it). */
export const VERDICT_SIGN = { go: "check", doubt: "alert", no: "cross" };
export function Verdict({ verdict = "go", failed = false, waits = false, label = "" }) {
  const v = VERDICT_SIGN[verdict] ? verdict : "doubt";
  return html`<span class=${cls("verdict", { [`is-${v}`]: true, "is-failed": failed, "is-waiting": waits })} data-verdict=${v} role=${label ? "img" : undefined} aria-label=${label || undefined}><${Sign} name=${VERDICT_SIGN[v]} /></span>`;
}

/** The tooltip of a spend figure: what it is in plain words. */
const spendTitle = (f) => `${f.est ? "about " : ""}${f.unit === "share" ? "of the tool's window" : f.unit === "usd" ? "at API prices" : "tokens"}`;

/** The top row: the goal's rune at the left (`rune`: Elem's props), the kind's sign at the right (`kind`: a sign's name) in the `signal`'s colour (`alert`, `danger`, `success`, else the muted ink). */
export function CornerTop({ rune = null, kind = "", signal = "", name = "", word = "", large = false, slot = "", kindSlot = "", kindClass = "", runeNode = null, kindNode = null }) {
  return html`<span class=${cls("corner corner--top", large && "corner--large")}>
    <span class="corner__rune">${runeNode ? runeNode : slot ? html`<span class="corner__slot" data-slot="rune">${slot}</span>` : rune && html`<${Elem} ...${rune} />`}${name && html`<span class="corner__name" title=${name}>${name}</span>`}</span>
    <span class=${cls("corner__kind", signal && `is-${signal}`)}>${kindNode ? kindNode : kindSlot ? html`<span class="corner__slot" data-slot="kind">${kindSlot}</span>` : html`${word && html`<span class=${cls("corner__word", kindClass)}>${word}</span>`}${kind && !kind.startsWith("tool:") && html`<${Sign} name=${kind} />`}`}</span>
  </span>`;
}

/** The bottom row (a gem whose `much.share` is false is a price in dollars, not a share of a window: spec 147 C): who at the left (`who`: `{ heads: [head…], word }`, one to three heads at 16 px and an optional word), how much at the right (`much`: `muchOf`'s; `ask`: it waits for you, the figure is then *asks you* in the alert). */
export function CornerFoot({ who = null, much = null, ask = false, large = false, whoSlot = "", muchSlot = "", whoNode = null, muchNode = null }) {
  const figure = ask ? { kind: "ask", text: ASKS } : much, heads = (who?.heads || []).filter(Boolean).slice(0, 3);
  return html`<span class=${cls("corner corner--foot", large && "corner--large")}>
    ${whoNode ? whoNode : whoSlot ? html`<span class="corner__slot" data-slot="who">${whoSlot}</span>` : html`<span class="corner__who" title=${heads.map(headWords).join(", ") || undefined}>${heads.map((h, i) => html`<${Head} key=${i} race=${h.race} tier=${h.tier} />`)}${who?.word && html`<span class="corner__word">${who.word}</span>`}</span>`}
    ${muchNode ? muchNode : muchSlot ? html`<span class="corner__slot" data-slot="much">${muchSlot}</span>` : figure && (figure.kind === "gem"
      ? html`<span class="corner__much"><span class=${figure.share === false ? "ork-gem" : "ork-gem share"} data-cost=${figure.text}>${figure.text}</span></span>`
      : figure.kind === "spend"
        ? html`<span class=${cls("corner__much", figure.est && "is-est")} data-much="spend" data-unit=${figure.unit} data-est=${figure.est ? "1" : undefined} title=${spendTitle(figure)}>${figure.text}</span>`
        : html`<span class=${cls("corner__much", figure.kind === "ask" && "is-ask")} data-much=${figure.kind}>${figure.text}</span>`)}
  </span>`;
}
