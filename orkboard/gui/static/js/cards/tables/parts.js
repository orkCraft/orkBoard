// What a leader's table is laid with (docs/mockups/frameworks/): a card that turns over on press, a pile that spreads on press. Nothing here moves: a card is
// turned, a pile spread. The person never puts a token (decisions §298.5): a card turned over says *Ask <leader> about this part*, and the words go to the leader.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { Sign } from "../../orkui.js";
import { AskCost, useAskCost } from "../askcost.js";
import { Token } from "../card.js";
import { named, signOf } from "../kind.js";
import { askLeader, isAt } from "./state.js";

/** The ask on a card's back: a button-link; pressed, a small field and *Send to <leader>*. It lies over the card's foot, not inside the card's own button. */
function AskPart({ ctx, id }) {
  const [open, setOpen] = useState(false), [text, setText] = useState(""), [sent, setSent] = useState(false), box = useRef(), cost = useAskCost();
  useEffect(() => { if (open) box.current?.focus(); }, [open]);
  const send = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    askLeader({ party: ctx.party, framework: ctx.framework, card: id, text });
    setText(""); setOpen(false); setSent(true);
  };
  if (!open) return html`<span class="tb-askrow">${sent && html`<small class="tb-asked" role="status">Sent to ${ctx.leader}</small>`}
    <button type="button" class="tb-asklink" data-ask-part=${id} onClick=${() => { setSent(false); setOpen(true); }}>Ask ${ctx.leader} about this part</button></span>`;
  return html`<form class="tb-askbox" data-ask-form=${id} onSubmit=${send} onKeyDown=${(e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setOpen(false); } }}>
    <input ref=${box} class="ork-input" aria-label=${`Your words to ${ctx.leader} about this part`} value=${text} placeholder="What do you want to ask?" onInput=${(e) => setText(e.currentTarget.value)} />
    <${AskCost} words=${cost.words} />
    <span class="tb-askbox__acts"><button type="submit" class="ork-btn primary" disabled=${!cost.ready}>Send to ${ctx.leader}</button><button type="button" class="ork-btn quiet" onClick=${() => setOpen(false)}>Cancel</button></span></form>`;
}

/** A card, face up; pressed, it turns over to its back (`back`: lines of what is behind it). `kind`: ext, frame, mod, hired, fired. */
export function TCard({ ctx, id, title, line = "", sign = "work", size = "md", kind = "", tilt = 0, back = [], tokens = [], mono = false, extra = null, face = null }) {
  const [over, setOver] = useState(false);
  const at = isAt(ctx, id);      // the part a mat laid the table at (mat.js)
  return html`<div class=${cls(`tb-slot is-${size}`, { "is-over": over })}>
    <button type="button" class=${cls("ork-card tb-card", { "is-over": over, "is-at": at, [`is-${kind}`]: !!kind })} data-card=${id} data-kind=${kind} data-cardkind="part" data-race=${ctx.race} aria-pressed=${String(over)}
        style=${tilt ? `--rot:${tilt}deg` : ""} aria-label=${`${named(`${title}${line ? `: ${line}` : ""}`, "part")}. ${over ? "Press to turn it back." : "Press to turn it over."}`}
        onClick=${() => setOver(!over)}>
      <span class="tb-ix" aria-hidden="true"><${Sign} name=${signOf("part")} /></span>
      ${over ? html`<b class=${cls("tb-name", { "is-mono": mono })}>${title}</b>${back.map((b, i) => html`<small class="tb-line" key=${i}>${b}</small>`)}`
        : face || html`<b class=${cls("tb-name", { "is-mono": mono })}>${title}</b>${line && html`<small class="tb-line">${line}</small>`}${extra}`}
      ${tokens.length > 0 && html`<span class="tb-toks">${tokens.map((t, i) => html`<${Token} key=${i} ...${t} word=" " />`)}</span>`}
    </button>${over && html`<${AskPart} ctx=${ctx} id=${id} />`}</div>`;
}

/** A pile of cards: its top card and the backs under it. Pressed, it spreads (`onSpread`); `n` the backs. */
export function TPile({ ctx, id, title, line = "", sign = "work", n = 3, open = false, onSpread, kind = "", size = "md", mono = false, count = "" }) {
  const at = isAt(ctx, id);
  return html`<div class=${cls(`tb-slot tb-pile is-${size}`, { "is-open": open })} style=${`--ov:${n}`}>
    ${Array.from({ length: n }, (_, i) => html`<span key=${i} class="ork-card tb-under" style=${`--dx:${(n - i) * 4}px`} aria-hidden="true"></span>`).reverse()}
    <button type="button" class=${cls("ork-card tb-card", { "is-at": at, [`is-${kind}`]: !!kind })} data-card=${id} data-pile="true" data-cardkind="part" data-race=${ctx.race} aria-expanded=${String(open)}
        aria-label=${`${title}, a part, a pile${count ? ` of ${count}` : ""}. ${open ? "Press to close it." : "Press to spread it."}`}
        onClick=${onSpread}>
      <span class="tb-ix" aria-hidden="true"><${Sign} name=${signOf("part")} /></span>
      <b class=${cls("tb-name", { "is-mono": mono })}>${title}</b>${line && html`<small class="tb-line">${line}</small>`}${count && html`<small class="tb-count">${count}</small>`}
    </button></div>`;
}

/** A card face down; pressed, it turns up (`onTurn`). */
export const TBack = ({ name, onTurn }) => html`<button type="button" class="tb-faced" data-card="face-down" aria-label=${`${name}, face down. Press to turn it.`} onClick=${onTurn}></button>`;

/** The foot of a leader's table: what to do with its cards. */
export function TableFoot() {
  return html`<footer class="tb-hand" aria-label="Your words on this table"><p class="tb-note">Press a card to turn it over; ask its leader about any part.</p></footer>`;
}
