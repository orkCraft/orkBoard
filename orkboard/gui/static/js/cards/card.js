// The table of cards' three sizes (goal 170, the talk of 11 November 2026; docs/mockups/table-cards/): one card ratio, 2.5:3.5.
// **S**, upright: a goal (at work, in the discard, in the hand). **M**, on its side: a leader's word, a post in its lane, read
// through table/post.js's head and body. **L**: a card opened; pressed, an M turns back upright and grows over the table
// (`openCard`), Esc or Close puts it away and the focus goes back to the card it came from. A leader's view of a goal is a
// **token** on its S: round, its party's colour, its sign, its word beside it (§295.4). Layout only (cards.css).
import { useEffect, useRef } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Elem, Icon, Sign } from "../orkui.js";
import { GoalLine, PostBody, PostHead, KINDS, TAGS, when, whoOf } from "../table/post.js";

/** A leader's view, its sign and its word (§295.4). */
export const VIEWS = { for: { mark: "✓", word: "for" }, risk: { mark: "!", word: "risk" }, question: { mark: "?", word: "question" }, against: { mark: "✕", word: "against" } };

/** A token: whose (`leader`), which view, the word beside it (the view's word when none is given). */
export function Token({ leader, view, word = "" }) {
  const w = whoOf(leader), v = VIEWS[view] || VIEWS.question;
  return html`<span class="cards-tok" data-race=${w.race || "orkmaster"} data-view=${view} title=${`${w.name}: ${v.word}`}>
    <i aria-hidden="true">${v.mark}</i><span>${word || v.word}</span></span>`;
}

/** The rune and the kind's sign of a goal, a card's index (its top left, and turned at its bottom right). */
const Index = ({ n, turned = false }) => html`<span class=${cls("cards-ix", { "is-turned": turned })} aria-hidden="true">
  <${Elem} name=${n?.element || ""} hue=${n?.hue || ""} dim=${!n?.element} />${n?.sign && html`<${Sign} name=${n.sign} />`}</span>`;

/** S: a goal upright. `n`: {slug, title, element, hue, sign, leader}; `line` under its name; `bar` its share done (0–1) or null;
 *  `tokens` [{leader, view, word}]; `asks`: it waits for the person; `onOpen`: pressed. */
export function CardS({ n, line = "", bar = null, tokens = [], asks = false, ready = false, onOpen = null, tilt = 0 }) {
  const w = whoOf(n.leader || "orkmaster");
  return html`<button type="button" class=${cls("ork-card cards-s", { "is-asks": asks, "is-ready": ready })} data-race=${w.race || "orkmaster"} data-goal=${n.slug}
      style=${tilt ? `--rot:${tilt}deg` : ""} aria-label=${`${n.title}${line ? `: ${line}` : ""}`} onClick=${onOpen}>
    <${Index} n=${n} />${asks && html`<span class="cards-s__asks" aria-hidden="true">!</span>`}
    <b class="cards-s__name">${n.title}</b>${line && html`<small class="cards-s__line">${line}</small>`}
    ${bar !== null && html`<span class="cards-bar" aria-hidden="true"><i style=${`width:${Math.round(bar * 100)}%`}></i></span>`}
    ${tokens.length > 0 && html`<span class="cards-toks">${tokens.map((t) => html`<${Token} ...${t} />`)}</span>`}
    <${Index} n=${n} turned=${true} /></button>`;
}

/** A card's back: a goal not shown, a pile's thickness. */
export const Back = ({ tilt = 0, x = 0 }) => html`<span class="ork-card cards-back" aria-hidden="true" style=${`--rot:${tilt}deg;--dx:${x}px`}></span>`;

const subOf = (p) => [KINDS[p.kind] || KINDS.news, when(p.at)].filter(Boolean).join(" · ");

/** M: a leader's word on its side; its head at the top left, its words, the goal it is about; pressed, it opens as an L.
 *  `more`: the leader's posts after it, its stack (`onMore` spreads them). */
export function CardM({ p, more = 0, onOpen, onPick, onMore = null }) {
  const ref = useRef();
  const open = () => openCard({ kind: "post", p, from: ref.current });
  return html`<article ref=${ref} class=${cls("ork-card cards-m", { "is-asks": !!p.asks, "is-stacked": more > 0 })} data-race=${whoOf(p.leader).race || "orkmaster"}
      data-kind=${p.kind} tabindex="0" aria-label=${`${whoOf(p.leader).name}: ${p.text}. Press to open.`}
      onClick=${(e) => { if (!e.target.closest("button")) open(); }} onKeyDown=${(e) => { if (e.key === "Enter" && e.target === ref.current) open(); }}>
    <${PostHead} leader=${p.leader} sub=${subOf(p)} tag=${TAGS[p.kind] || ""} asks=${!!p.asks} />
    <div class="cards-m__body"><${PostBody} p=${p} onPick=${onPick} /></div>
    ${more > 0 && onMore && html`<button type="button" class="cards-m__more" onClick=${onMore}><${Icon} name="chevron-down" /><span>More from ${whoOf(p.leader).name}</span></button>`}
  </article>`;
}

/** The card opened: `{kind: "post", p, from}` or `{kind: "goal", n, line, tokens, acts, from}`; null when none. */
export const opened = signal(null);
export const openCard = (what) => { opened.value = what; };
const shut = () => { const was = opened.peek(); opened.value = null; was?.from?.focus?.(); };

/** L: the card opened over the table, upright and big; Esc or Close puts it away. */
export function CardL({ onPick }) {
  const o = opened.value, root = useRef();
  useEffect(() => {
    if (!o) return undefined;
    root.current?.querySelector(".cards-l__shut")?.focus();
    const key = (e) => { if (e.key === "Escape") { e.preventDefault(); shut(); } };
    addEventListener("keydown", key, true);
    return () => removeEventListener("keydown", key, true);
  }, [o]);
  if (!o) return null;
  const leader = o.kind === "post" ? o.p.leader : o.n.leader || "orkmaster";
  return html`<div class="cards-veil" onClick=${(e) => { if (e.target === e.currentTarget) shut(); }}>
    <article ref=${root} class="ork-card cards-l" role="dialog" aria-modal="true" aria-label=${o.kind === "post" ? `${whoOf(leader).name}: ${o.p.text}` : o.n.title}
        data-race=${whoOf(leader).race || "orkmaster"} data-from=${o.kind}>
      <button type="button" class="ork-btn quiet cards-l__shut" onClick=${shut}><${Icon} name="close" /><span>Close</span></button>
      ${o.kind === "post" ? html`<${PostHead} leader=${o.p.leader} sub=${subOf(o.p)} tag=${TAGS[o.p.kind] || ""} asks=${!!o.p.asks} />
          <div class="cards-l__body"><${PostBody} p=${o.p} onPick=${(s) => { shut(); onPick?.(s); }} /></div>`
        : html`<${PostHead} leader=${leader} sub=${o.line || ""} />
          <h2 class="cards-l__title">${o.n.title}</h2>
          ${o.tokens?.length > 0 && html`<div class="cards-toks is-big">${o.tokens.map((t) => html`<${Token} ...${t} />`)}</div>`}
          ${o.n.slug && html`<${GoalLine} slug=${o.n.slug} onPick=${(s) => { shut(); onPick?.(s); }} />`}`}
      ${o.acts?.length > 0 && html`<div class="cards-l__acts">${o.acts.map((a) => html`<button type="button" class=${cls("ork-btn", { primary: a.main })} onClick=${() => { a.run(); shut(); }}>${a.label}</button>`)}</div>`}
    </article></div>`;
}
