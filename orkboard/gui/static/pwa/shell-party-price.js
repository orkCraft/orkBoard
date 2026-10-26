// What a party costs a goal and what it can take, on the phone (docs/specs/43-party-measured.md §3, docs/specs/63-party-gathered.md §2): `ideas.party_price` asked for the party as it stands (at once when a picker
// opens, 300 ms after a seat or *Every goal* changes), *This party: about $2–6 a goal* with where it comes from and its hints (quiet lines, never a block, no button), *It can take:* the goal types the seats would
// be offered (three lines at most, then *and k more*; a type the last change opened is lit once) and what each check adds to a goal. Shared by the team's sheet (shell-goal-new.js `makeParty`) and New party
// (shell-party-new.js): each says its party as `current()` and draws again on `redraw()`.
import { h } from "./util.js";
import { pctOf, pctRange } from "./shell-spend.js";
import { sign } from "./shell-marks.js";
import { motionOn, pulse } from "./shell-motion.js";

const TAKES_LINES = 3;                                         // *It can take* runs to three lines at most, then *and k more* (spec 63 §2.1)
const PRICE_MS = 300;

/** `current()`: what `ideas.party_price` is asked ({leader, team, every, craft?, size?}); `redraw()`: the answer is in. Returns {ask(now, lights), reset(), line(), takes(), fit(), adds(id), get()}. */
export function makePrice(core, { current, redraw }) {
  let price = null, timer = 0;                             // `ideas.party_price`: asked when the picker opens, 300 ms after a seat or *Every goal* changes
  let seen = null, opened = new Set();                     // the goal types of the answer before (none at the first), and those the last change opened: lit once (spec 63 §2.2)
  let takes = null;                                        // the *It can take* line drawn last, cut to its lines once it is in the page

  /** `lights`: whether the types this answer newly offers are lit (a seat the person changed); the answers to the picker's opening are the baseline and light nothing (spec 63 §2.2). */
  function ask(now = false, lights = true) {
    clearTimeout(timer);
    const go = async () => {
      const got = await core.call("ideas.party_price", current());
      if (!got) return;
      const ids = Array.isArray(got.types) ? got.types.map((t) => t.id) : null;           // an older host sends none: no line
      opened = new Set(lights && seen && ids ? ids.filter((id) => !seen.has(id)) : []);
      seen = ids && new Set(ids);
      price = got;
      redraw();
    };
    if (now) go(); else timer = setTimeout(go, PRICE_MS);
  }

  /** *This party: about $2–6 a goal* (below $1, in cents) and, muted, where it comes from; its hints under it. */
  function line() {
    if (!price) return null;
    const { low, high } = price, a = Math.round(low), b = Math.round(high);
    const range = pctRange(low, high) || (low < 1 ? `$${low.toFixed(2)}–${high.toFixed(2)}` : a === b ? `$${a}` : `$${a}–${b}`);
    const [one, many] = price.pitch ? ["pitch", "pitches"] : ["goal", "goals"];            // Ideation's price is a pitch's (spec 65 §3)
    return h("div", { class: "party-price-box" },
      h("p", { class: "party-price", role: "status" }, `This party: about ${range} a ${one}`,
        h("small", { class: "muted" }, ` ${price.learned ? `from this project's last ${price.ideas} ${many}` : `a first guess: it learns from this project's ${many}`}`)),
      ...(price.hints || []).map((t) => h("p", { class: "muted party-hint" }, t)));    // spec 43 §5: quiet lines, never a block, no button
  }

  /** *It can take:* the goal types a party of these seats would be offered (spec 63 §2): `ideas.party_price`'s `types`, each its sign and name, joined by ·; then *with one more:* the types that
   *  miss someone (*New screen (needs Design system designer)*); none at all, *nothing of its own yet: add a builder*. Three lines at most (`fit`); a type the last change opened is
   *  lit once. Null for an older host (no `types`). */
  function takesLine() {
    takes = null;
    if (!Array.isArray(price?.types) || price.pitch) return null;                        // a pitch has no goal type: its decision names the one it will have
    const lit = motionOn() ? opened : new Set();
    opened = new Set();
    const have = price.types.filter((t) => !t.missing), all = [...have, ...price.types.filter((t) => t.missing)];
    const words = (t) => (t.missing ? `${t.name} (needs ${t.missing})` : t.name);
    const item = (t) => h("span", { class: `take${t.missing ? " is-missing" : ""}`, "data-type": t.id }, sign(t.sign), words(t));
    const el = h("p", { class: "party-takes" });
    /** The first `n` types; the rest are said as *and k more*, their names in its title. */
    const paint = (n) => {
      const nodes = all.slice(0, n).map(item), kids = [h("b", {}, "It can take:"), " "];
      if (!have.length) kids.push("nothing of its own yet: add a builder", nodes.length ? ", " : ".");
      nodes.forEach((node, i) => {
        if (i === have.length) kids.push(i ? ", " : "", h("span", { class: "take-with" }, "with one more:"), " ");
        else if (i) kids.push(" · ");
        kids.push(node);
      });
      if (n < all.length) kids.push(" ", h("span", { class: "take-more", title: all.map(words).join(", ") }, `and ${all.length - n} more`));
      el.replaceChildren(...kids);
      nodes.forEach((node, i) => lit.has(all[i].id) && pulse(node));
    };
    paint(all.length);
    takes = { el, count: all.length, paint };
    return el;
  }

  /** The line cut to its lines once it is in the page (its sheet open): types come off its end until it fits. */
  function fit() {
    if (!takes?.el.getClientRects().length) return;
    const { el, count, paint } = takes, style = getComputedStyle(el);
    const lineHeight = parseFloat(style.lineHeight) || parseFloat(style.fontSize) * 1.4;
    for (let n = count; n > 1 && el.getBoundingClientRect().height > lineHeight * TAKES_LINES + 1; n--) paint(n - 1);
  }

  /** *adds about $0.35 to a goal it checks · about half of them* (*· every goal* when it checks every goal). */
  function adds(id) {
    const c = (price?.checks || []).find((x) => x.by === id);
    if (!c) return "";
    const share = c.every ? "every goal" : Math.abs(c.share - 0.5) < 0.03 ? "about half of them" : `about ${Math.round(c.share * 100)} % of them`;
    return ` · adds about ${pctOf(c.usd) || `$${c.usd.toFixed(2)}`} to a goal it checks · ${share}`;
  }

  return { ask, line, takes: takesLine, fit, adds, get: () => price, reset() { clearTimeout(timer); price = null; seen = null; opened = new Set(); takes = null; } };
}
