// Weigh two at a time (docs/mockups/spreads/, "duel"): two goals side by side, *Which matters more now?*; the pile still to weigh at the left (its
// thickness, no number), the order so far at the right. Each goal of the pile is set into the order by asking against the one in its middle (a
// binary insertion: few pairs for many goals), so the order builds itself. Choosing only reorders here; *Done: keep this order* sends it
// (`ideas.order {order: [slug]}`, the contract proposed: the host keeps no order of goals yet, the mock logs it). ← and → choose, ↓ skips the
// pair (the goal is asked again after the others; the last one left stays out of the order).
import { Fragment } from "preact";
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { command, proposed, toast } from "../../link.js";
import { Icon } from "../../orkui.js";
import { whoOf } from "../../table/post.js";
import { nodeOf, nodes } from "../feed.js";
import { closeSpread } from "./open.js";
import { Key, SpCard, SpreadFrame, Thick, faceOf } from "./shell.js";

const IN_TALK = new Set(["new", "talk", "spec", "idea"]);

/** The order so far (goals already in line, the contract proposed) and the pile of goals to weigh into it. */
const start = () => ({ ranked: (proposed("order")?.ranked || []).filter((s) => nodeOf(s)), pile: nodes().filter((n) => IN_TALK.has(n.state)).map((n) => n.slug), lo: 0, hi: null, left: [] });

/** One step of the weighing: `win` is "new" (the goal asked about matters more), "old" (the one in the order does), or "skip". Pure. */
export function step(s, win) {
  const [cur, ...rest] = s.pile, hi = s.hi ?? s.ranked.length, mid = (s.lo + hi) >> 1;
  if (win === "skip") return rest.length ? { ...s, pile: [...rest, cur], lo: 0, hi: null } : { ...s, pile: [], left: [...s.left, cur], lo: 0, hi: null };
  const [lo, high] = win === "new" ? [s.lo, mid] : [mid + 1, hi];
  if (lo < high) return { ...s, lo, hi: high };
  return { ...s, ranked: [...s.ranked.slice(0, lo), cur, ...s.ranked.slice(lo)], pile: rest, lo: 0, hi: null };
}

/** Sets in the goals that need no asking (the order is empty: the first goal is the order). */
const settle = (s) => (s.pile.length && !s.ranked.length ? { ...s, ranked: [s.pile[0]], pile: s.pile.slice(1) } : s);

export function Duel() {
  const [s, set] = useState(() => settle(start())), cur = s.pile[0], hi = s.hi ?? s.ranked.length, other = s.ranked[(s.lo + hi) >> 1];
  const choose = (win) => set((x) => (x.pile.length ? settle(step(x, win)) : x));
  useEffect(() => {
    const key = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "ArrowLeft") choose("new"); else if (e.key === "ArrowRight") choose("old"); else if (e.key === "ArrowDown") { e.preventDefault(); choose("skip"); }
    };
    addEventListener("keydown", key);
    return () => removeEventListener("keydown", key);
  }, []);
  const a = nodeOf(cur), b = nodeOf(other), title = (n) => n?.short || n?.title || "";
  const keep = () => Promise.resolve(command("ideas.order", { order: s.ranked })).then(() => { toast("Sent: the order of the goals"); closeSpread(); }).catch((e) => toast(e?.message || "The order was not sent", "error"));
  const card = (n, tilt, side) => html`<div class="sp-col"><${SpCard} party=${n.goal} n=${faceOf(n)} name=${title(n)} line=${n.line || n.state} size="xl" tilt=${tilt} onPress=${() => choose(side)} picked=${null}
      label=${`${title(n)}: matters more`} /><button type="button" class="ork-btn" onClick=${() => choose(side)} aria-label=${`This one: ${title(n)}`}>${side === "new" && html`<${Icon} name="arrow-left" />`}<span>This one</span>${side === "old" && html`<${Icon} name="arrow-right" />`}</button></div>`;
  const rung = (slug, i, at) => { const n = nodeOf(slug), w = whoOf(n?.goal || "orkmaster"); return html`<${Fragment} key=${slug}>${at === i && html`<span class="sp-rung is-gap">${title(a)} or ${title(b)}?</span>`}<span class="sp-rung" data-race=${w.race || "orkmaster"}>${title(n)}</span></${Fragment}>`; };
  const gapAt = s.lo;
  return html`<${SpreadFrame} kind="duel" title="Which matters more now?" line="Two at a time; the order builds itself" say="Pick one of two. Skip when you can't tell; I'll ask the pair again later."
      note=${html`Can't tell? <${Key} k="↓" /> skip this pair.`}
      acts=${html`<button type="button" class="ork-btn" data-act="skip" disabled=${!cur} onClick=${() => choose("skip")}><${Icon} name="arrow-right" /><span>Skip</span></button>
        <button type="button" class="ork-btn primary" data-act="keep" onClick=${keep}><${Icon} name="check" /><span>Done: keep this order</span></button>`}>
    <${Thick} n=${s.pile.length} label="still to weigh" />
    ${cur && other ? html`${card(a, -2, "new")}<span class="sp-or" aria-hidden="true">or</span>${card(b, 2, "old")}`
      : html`<p class="sp-cap sp-field__say">${s.ranked.length ? "Every goal is weighed. Keep this order, or leave it." : "There are no goals to weigh."}${s.left.length ? " One was skipped and stays out of the order." : ""}</p>`}
    <aside class="sp-ladder" aria-label="The order so far"><p class="cards-lab" data-race="orkmaster">The order so far</p>
      ${s.ranked.map((slug, i) => rung(slug, i, cur && other ? gapAt : -1))}${cur && other && gapAt >= s.ranked.length && html`<span class="sp-rung is-gap">${title(a)} or ${title(b)}?</span>`}</aside>
  </${SpreadFrame}>`;
}
