// The spreads laid over the window (goal 170; docs/mockups/spreads/): rendered once in frame/frame.js, only while the table of cards is drawn.
// `openSpread` (open.js) says which, `track.js`, `gate.js`, `diff.js`, `cost.js`, `duel.js`, `sort.js`, `deal.js` and `battle.js` draw it on `shell.js`'s frame; the sheet is `spreads.css`.
import { html } from "../../html.js";
import { spread } from "./open.js";
import { Track } from "./track.js";
import { Gate } from "./gate.js";
import { Diff } from "./diff.js";
import { Cost } from "./cost.js";
import { Duel } from "./duel.js";
import { Sort } from "./sort.js";
import { Deal } from "./deal.js";
import { Battle } from "./battle.js";

export function Spreads() {
  const s = spread.value;
  if (!s) return null;
  if (s.kind === "track") return html`<${Track} key=${s.slug} slug=${s.slug} />`;
  if (s.kind === "gate") return html`<${Gate} key=${s.slug} slug=${s.slug} />`;
  if (s.kind === "diff" && s.p) return html`<${Diff} key=${s.p.at + s.p.text} p=${s.p} />`;
  if (s.kind === "cost") return html`<${Cost} />`;
  if (s.kind === "duel") return html`<${Duel} />`;
  if (s.kind === "sort") return html`<${Sort} />`;
  if (s.kind === "deal") return html`<${Deal} key=${s.slug} slug=${s.slug} />`;
  if (s.kind === "battle") return html`<${Battle} key=${s.slug} slug=${s.slug} />`;
  return null;
}
