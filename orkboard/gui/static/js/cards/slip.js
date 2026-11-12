// A token's note is a slip (decisions §298.4, docs/mockups/token-notes/ D): a slip in orkUI's plaque, its party's stripe, its leader's head,
// its checks one a line (a risk says what fixes it). On an S the token stays and its slip lies beside the card on a thread (`SlipBeside`,
// drawn over the page, so no lane cuts it); on an opened card the slips lie round it with a reply under each (cards/open.js).
import { render } from "preact";
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { HeadOf, whoOf } from "../table/post.js";
import { CraftToken, Square, saysOf } from "./verdict.js";

/** The slip's lines: a square and its words, a risk's *Fixed by* under it. */
export const Checks = ({ checks }) => html`<ul class="cards-slip__checks">${checks.map((c, i) => html`<li key=${i} data-kind=${c.kind}><${Square} kind=${c.kind} />
  <span>${c.text}${c.fix && html`<small>Fixed by: ${c.fix}</small>`}</span></li>`)}</ul>`;

/** A slip: its leader's head and name, its token when given (`token`), its checks, `children` under them (a reply). */
export function Slip({ leader, checks, token = null, children = null, ...rest }) {
  const w = whoOf(leader);
  return html`<section class="cards-slip" data-race=${w.race || "orkmaster"} data-slip=${leader} aria-label=${`${saysOf(leader, checks)}: its checks`} ...${rest}>
    <header class="cards-slip__head">${token}<span class="cards-slip__av"><${HeadOf} w=${w} /></span><b>${w.name}</b><small>its checks</small></header>
    <${Checks} checks=${checks} />${children}</section>`;
}

/** Draws `children` over the page, outside whatever clips the card (the lanes scroll and clip). */
export function Overlay({ children }) {
  const host = useRef(null);
  if (!host.current && typeof document !== "undefined") { host.current = document.createElement("div"); host.current.className = "cards-over"; }
  useLayoutEffect(() => { document.body.append(host.current); return () => { render(null, host.current); host.current.remove(); }; }, []);
  useLayoutEffect(() => { render(children, host.current); });
  return null;
}

const WIDE = 264, GAP = 22;

/** The slip of an S's token, beside the card on a thread of its party's colour: on the card's right, else its left; the thread from the token to the slip.
 *  Measured after layout, and again when the page scrolls or is resized. Esc, a second press or a press elsewhere puts it away (`onClose`). */
export function SlipBeside({ v, card, token, onClose }) {
  const [at, setAt] = useState(null), me = useRef(null), w = whoOf(v.leader);
  const place = () => {
    if (!card?.isConnected || !token?.isConnected || !me.current) return;
    const c = card.getBoundingClientRect(), t = token.getBoundingClientRect(), h = me.current.offsetHeight;
    const right = c.right + GAP + WIDE <= innerWidth - 8, x = right ? c.right + GAP : Math.max(8, c.left - GAP - WIDE);
    const y = Math.max(8, Math.min(t.top + t.height / 2 - 20, innerHeight - h - 8));
    const x1 = t.left + t.width / 2, y1 = t.top + t.height / 2, x2 = right ? x : x + WIDE, y2 = Math.min(Math.max(y1, y + 14), y + h - 14);
    setAt({ x, y, x1, y1, len: Math.hypot(x2 - x1, y2 - y1), deg: Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI });
  };
  useLayoutEffect(place, [v]);
  useEffect(() => {
    const key = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); onClose(true); } };
    const down = (e) => { if (!e.target.closest?.(".cards-slip, .cards-ct")) onClose(false); };
    addEventListener("keydown", key, true); addEventListener("pointerdown", down, true); addEventListener("resize", place); addEventListener("scroll", place, true);
    return () => { removeEventListener("keydown", key, true); removeEventListener("pointerdown", down, true); removeEventListener("resize", place); removeEventListener("scroll", place, true); };
  }, [v, card, token]);
  return html`<${Overlay}><div class="cards-beside" data-race=${w.race || "orkmaster"}>
    ${at && html`<i class="cards-thread" aria-hidden="true" style=${`left:${at.x1}px;top:${at.y1}px;width:${at.len}px;transform:rotate(${at.deg}deg)`}></i>`}
    <div ref=${me} class=${cls("cards-beside__slip", { "is-hidden": !at })} style=${at ? `left:${at.x}px;top:${at.y}px;width:${WIDE}px` : `left:0;top:0;width:${WIDE}px`}>
      <${Slip} leader=${v.leader} checks=${v.checks} /></div></div><//>`;
}

export { CraftToken };
