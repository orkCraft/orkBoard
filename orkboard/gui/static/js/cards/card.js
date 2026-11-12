// The table of cards' three sizes (goal 170, the talk of 11 November 2026; docs/mockups/table-cards/): one card ratio, 2.5:3.5.
// **S**, upright: a goal (at work, in the discard, in the hand). **M**, on its side: a leader's word, a post in its lane, read
// through table/post.js's head and body. **L**: a card opened; pressed, an M turns back upright and grows over the table
// (`openCard`), Esc or Close puts it away and the focus goes back to the card it came from. A craft's verdict on a goal is a
// **token** on its S (verdict.js, §298.3). Layout only (cards.css).
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { openSpread } from "./spreads/open.js";
import { giveBack, keepTab } from "./back.js";
import { MatFoot, matOf, matSays } from "./mat.js";
import { AskRow, Marks, SlipsColumn } from "./around.js";
import { SlipBeside } from "./slip.js";
import { CraftToken, blockedBy, verdictsOf } from "./verdict.js";
import { GoalLine, PostBody, PostHead, KINDS, TAGS, when, whoOf } from "../table/post.js";

/** A leader's view, its sign and its word (§295.4). */
export const VIEWS = { for: { mark: "✓", word: "for" }, risk: { mark: "!", word: "risk" }, question: { mark: "?", word: "question" }, against: { mark: "✕", word: "against" } };

/** A token: whose (`leader`), which view, the word beside it (the view's word when none is given). */
export function Token({ leader, view, word = "" }) {
  const w = whoOf(leader), v = VIEWS[view] || VIEWS.question;
  return html`<span class="cards-tok" data-race=${w.race || "orkmaster"} data-view=${view} title=${`${w.name}: ${v.word}`}>
    <i aria-hidden="true">${v.mark}</i><span>${word || v.word}</span></span>`;
}

/** A card's two upper corners (the person, 11 November 2026): its goal's rune at the top left, the kind's sign at the top right. A card's
 *  corners each say one thing, so no corner repeats another (`turned` draws nothing: the mirrored index of a playing card is gone). */
export const Index = ({ n, turned = false }) => (turned ? null : html`<span class="cards-c cards-c--tl" aria-hidden="true"><${Elem} name=${n?.element || ""} hue=${n?.hue || ""} dim=${!n?.element} /></span>
  ${n?.sign && html`<span class="cards-c cards-c--tr" aria-hidden="true"><${Sign} name=${n.sign} /></span>`}`);

/** The slip open on an S, one at a time on the page: {id (the card's), leader, token (its element)}, or null. */
const slipNow = signal(null);
let cardIds = 0;

/** S: a goal upright (the person, 11 November 2026). Its corners: the rune top left, the kind's sign top right, **when** bottom left
 *  (`when`: put off, starts by itself at a time, at work), **its act** and **its craft tokens** bottom right (`act`: {label, cost, run}, or its share done when
 *  `bar` is given); the head of the leader who does it is its picture in the middle, its name and `line` under it. The tokens are the goal's verdicts
 *  (cards/verdict.js, decisions §298.3), read here: a token pressed lays its slip beside the card on a thread (slip.js). A risk that blocks rings the card,
 *  says *blocked* where *when* is and holds its act. A card with an act or tokens of its own is a group of buttons; else the card is one. */
export function CardS({ n, line = "", when = "", bar = null, act = null, asks = false, ready = false, onOpen = null, tilt = 0, ...rest }) {
  const w = whoOf(n.leader || "orkmaster"), root = useRef(), id = useRef(null);
  if (!id.current) id.current = ++cardIds;
  const verdicts = verdictsOf(n.slug), by = blockedBy(n.slug), held = !!by, now = slipNow.value, shown = now?.id === id.current ? verdicts.find((v) => v.leader === now.leader) : null;
  const group = !!act || verdicts.length > 0;
  const Tag = group ? "div" : "button";
  const label = `${n.title}${line ? `: ${line}` : ""}${held ? ", blocked" : when ? `, ${when}` : ""}`;
  const own = group ? { role: "group", tabindex: "0", onKeyDown: (e) => { if ((e.key === "Enter" || e.key === " ") && e.target === e.currentTarget) { e.preventDefault(); onOpen?.(e); } },
    onClick: (e) => { if (!e.target.closest("button")) onOpen?.(e); } } : { type: "button", onClick: onOpen };
  const press = (v, e) => { const el = e.currentTarget; slipNow.value = now?.id === id.current && now.leader === v.leader ? null : { id: id.current, leader: v.leader, token: el }; };
  const close = (back) => { const t = slipNow.peek()?.token; slipNow.value = null; if (back) t?.focus?.(); };
  return html`<${Tag} ref=${root} class=${cls("ork-card cards-s", { "is-asks": asks, "is-ready": ready, "is-group": group, "has-toks": verdicts.length > 0, "has-act": !!act, "is-blocked": held })} data-race=${w.race || "orkmaster"} data-goal=${n.slug}
      style=${tilt ? `--rot:${tilt}deg` : ""} aria-label=${label} ...${own} ...${rest}>
    <${Index} n=${n} />
    <span class="cards-s__pic" aria-hidden="true">${w.head && html`<${Head} race=${w.head.race} tier=${w.head.tier} />`}</span>
    <b class="cards-s__name">${n.title}</b>${line && html`<small class="cards-s__line">${line}</small>`}
    ${bar !== null && html`<span class="cards-bar" aria-hidden="true"><i style=${`width:${Math.round(bar * 100)}%`}></i></span>`}
    <span class=${cls("cards-c cards-c--bl", { "is-blocked": held })}>${held ? "blocked" : asks && !when ? html`<span class="cards-s__asks" aria-hidden="true">!</span><span>waits for you</span>` : when}</span>
    <span class="cards-c cards-c--br">
      ${act ? html`<button type="button" class="ork-btn cards-act" disabled=${held} title=${held ? `Blocked: ${whoOf(by).name}'s risk blocks it until ${whoOf(by).name} lifts it` : undefined}
          onClick=${(e) => { e.stopPropagation(); act.run(); }}><span>${act.label}</span>${act.cost && html`<small>${act.cost}</small>`}</button>`
        : bar !== null ? html`<span class="cards-pct">${Math.round(bar * 100)}%</span>` : ""}
      ${verdicts.length > 0 && html`<span class="cards-cts">${verdicts.map((v) => html`<${CraftToken} key=${v.leader} leader=${v.leader} checks=${v.checks} on=${shown === v} onPress=${(e) => press(v, e)} />`)}</span>`}</span>
    ${shown && html`<${SlipBeside} v=${shown} card=${root.current} token=${now.token} onClose=${close} />`}
  <//>`;
}

/** A card's back: a goal not shown, a pile's thickness. */
export const Back = ({ tilt = 0, x = 0 }) => html`<span class="ork-card cards-back" aria-hidden="true" style=${`--rot:${tilt}deg;--dx:${x}px`}></span>`;

const subOf = (p) => [KINDS[p.kind] || KINDS.news, when(p.at)].filter(Boolean).join(" · ");

/** The spreads have no phone face yet: on a narrow screen a mat opens as an L of words (decisions §297 points to the spreads' own goal). */
const narrow = () => !!globalThis.matchMedia?.("(max-width: 700px)").matches;

/** M: a leader's word on its side; its head at the top left, its words, the goal it is about; pressed, it opens as an L.
 *  `more`: the leader's posts after it, its stack (`onMore` spreads them). */
export function CardM({ p, more = 0, onOpen, onPick, onMore = null }) {
  const ref = useRef();
  const mat = matOf(p);
  const open = () => (mat && !narrow() ? mat.open(ref.current) : openCard({ kind: "post", p, from: ref.current, acts: [{ label: "What changed", main: p.kind === "change", run: () => openSpread({ kind: "diff", p, from: ref.current }) }] }));
  return html`<article ref=${ref} class=${cls("ork-card cards-m", { "is-stacked": more > 0, "is-mat": !!mat })} data-race=${whoOf(p.leader).race || "orkmaster"}
      data-kind=${p.kind} tabindex="0" data-mat=${mat?.kind} aria-label=${`${whoOf(p.leader).name}: ${p.text}. ${mat ? `${matSays(mat)}. Press to open it.` : "Press to open."}`}
      onClick=${(e) => { if (!e.target.closest("button")) open(); }} onKeyDown=${(e) => { if (e.key === "Enter" && e.target === ref.current) { e.preventDefault(); open(); } }}>
    <${PostHead} leader=${p.leader} sub=${subOf(p)} tag=${TAGS[p.kind] || ""} />
    <div class="cards-m__body"><${PostBody} p=${p} onPick=${onPick} /></div>
    ${mat && html`<${MatFoot} mat=${mat} />`}
    ${more > 0 && onMore && html`<button type="button" class="cards-m__more" onClick=${onMore}><${Icon} name="chevron-down" /><span>More from ${whoOf(p.leader).name}</span></button>`}
  </article>`;
}

/** A question is answered in the hand (decisions §145, §296.4): a question token pressed raises its goal's card there:
 *  the card is pressed, which opens its ways. After the L is put away, so the focus lands on the hand's card. */
export function answerInHand(slug) {
  setTimeout(() => {
    const c = document.querySelector(`.frame-hand button.hand-card[data-goal="${CSS.escape(slug)}"]`);
    if (!c) return;
    c.scrollIntoView?.({ block: "nearest", inline: "nearest" });
    c.focus();
    c.click();
  }, 0);
}

/** The card opened: `{kind: "post", p, from}` or `{kind: "goal", n, line, acts, from}`; null when none. */
export const opened = signal(null);
export const openCard = (what) => { opened.value = what; };
const shut = () => { const was = opened.peek(); opened.value = null; giveBack(was?.from); };

/** L: the card opened over the table, upright and big; Esc or Close puts it away. */
export function CardL({ onPick }) {
  const o = opened.value, root = useRef();
  useLayoutEffect(() => {   // the keys at once, before the first paint: an Esc pressed as the card opens closes it
    if (!o) return undefined;
    root.current?.querySelector(".cards-l__shut")?.focus();
    const key = (e) => { if (e.key === "Escape") { e.preventDefault(); shut(); } else keepTab(root.current?.closest(".cards-veil"), e); };
    addEventListener("keydown", key, true);
    return () => removeEventListener("keydown", key, true);
  }, [o]);
  if (!o) return null;
  const leader = o.kind === "post" ? o.p.leader : o.n.leader || "orkmaster", goal = o.kind === "goal", verdicts = goal ? verdictsOf(o.n.slug) : [];
  const card = html`<article ref=${root} class="ork-card cards-l" role="dialog" aria-modal="true" aria-label=${o.kind === "post" ? `${whoOf(leader).name}: ${o.p.text}` : o.n.title}
        data-race=${whoOf(leader).race || "orkmaster"} data-from=${o.kind}>
      <button type="button" class="ork-btn quiet cards-l__shut" onClick=${shut}><${Icon} name="close" /><span>Close</span></button>
      ${!goal ? html`<${PostHead} leader=${o.p.leader} sub=${subOf(o.p)} tag=${TAGS[o.p.kind] || ""} />
          <div class="cards-l__body"><${PostBody} p=${o.p} onPick=${(s) => { shut(); onPick?.(s); }} /></div>`
        : html`<${PostHead} leader=${leader} sub=${o.line || ""} />
          <h2 class="cards-l__title">${o.n.title}</h2>
          <${Marks} verdicts=${verdicts} />
          ${o.n.slug && html`<${GoalLine} slug=${o.n.slug} onPick=${(s) => { shut(); onPick?.(s); }} />`}`}
      ${o.acts?.length > 0 && html`<div class="cards-l__acts">${o.acts.map((a) => html`<button type="button" class=${cls("ork-btn", { primary: a.main })} onClick=${() => { a.run(); shut(); }}>${a.label}</button>`)}</div>`}
    </article>`;
  if (!goal) return html`<div class="cards-veil" onClick=${(e) => { if (e.target === e.currentTarget) shut(); }}>${card}</div>`;
  const route = [...new Set([...(verdicts.map((v) => v.leader)), ...(o.n.leader && o.n.leader !== "orkmaster" ? [o.n.leader] : [])])];
  return html`<div class="cards-veil" onClick=${(e) => { if (e.target === e.currentTarget) shut(); }}>
    <div class="cards-stage" onClick=${(e) => { if (e.target === e.currentTarget) shut(); }}>
      <${SlipsColumn} slug=${o.n.slug} verdicts=${verdicts} side=${0} />
      <div class="cards-stage__mid">${card}<${AskRow} slug=${o.n.slug} route=${route} /></div>
      <${SlipsColumn} slug=${o.n.slug} verdicts=${verdicts} side=${1} /></div></div>`;
}
