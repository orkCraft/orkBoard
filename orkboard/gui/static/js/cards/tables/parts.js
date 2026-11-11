// What a leader's table is laid with (docs/mockups/frameworks/): a card that turns over on press, a pile that spreads on press, the person's
// own token and the strip where the person takes one (the hand's place on this table). Nothing here moves: a card is turned, a pile spread.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { Sign } from "../../orkui.js";
import { whoOf } from "../../table/post.js";
import { Token } from "../card.js";
import { WORDS, asking, held, placed, putToken } from "./state.js";

/** The person's token: bone with a brass rim, never a leader's round colour (tables.css `.tb-you`). */
export const YouToken = ({ view, big = false }) => html`<span class=${cls("tb-you", { "is-big": big })} data-view=${view} aria-hidden="true"><i>${(WORDS[view] || WORDS.question).mark}</i></span>`;

/** The tokens the person put on a card. */
const Mine = ({ ctx, id }) => {
  const mine = placed.value.filter((t) => t.party === ctx.party && t.framework === ctx.framework && t.card === id);
  return mine.length ? html`<span class="tb-placed">${mine.map((t, i) => html`<${YouToken} key=${i} view=${t.view} />`)}</span>` : null;
};

/** Pressing with a token in the hand asks for its words; without one the press is the card's own (turn, spread). */
const press = (ctx, id, name, own) => () => {
  if (held.value) asking.value = { party: ctx.party, framework: ctx.framework, card: id, name };
  else own();
};

/** A card, face up; pressed, it turns over to its back (`back`: lines of what is behind it). `kind`: ext, frame, mod, hired, fired. */
export function TCard({ ctx, id, title, line = "", sign = "work", size = "md", kind = "", tilt = 0, back = [], tokens = [], mono = false, extra = null, face = null }) {
  const [over, setOver] = useState(false), marked = placed.value.some((t) => t.party === ctx.party && t.framework === ctx.framework && t.card === id);
  return html`<div class=${cls(`tb-slot is-${size}`, { "is-marked": marked })}>
    <button type="button" class=${cls("ork-card tb-card", { "is-over": over, "is-marked": marked, [`is-${kind}`]: !!kind })} data-card=${id} data-kind=${kind} data-race=${ctx.race} aria-pressed=${String(over)}
        style=${tilt ? `--rot:${tilt}deg` : ""} aria-label=${`${title}${line ? `: ${line}` : ""}. ${held.value ? "Press to put your token here." : over ? "Press to turn it back." : "Press to turn it over."}`}
        onClick=${press(ctx, id, title, () => setOver(!over))}>
      <span class="tb-ix" aria-hidden="true"><${Sign} name=${sign} /></span>
      ${over ? html`<b class=${cls("tb-name", { "is-mono": mono })}>${title}</b>${back.map((b, i) => html`<small class="tb-line" key=${i}>${b}</small>`)}`
        : face || html`<b class=${cls("tb-name", { "is-mono": mono })}>${title}</b>${line && html`<small class="tb-line">${line}</small>`}${extra}`}
      ${tokens.length > 0 && html`<span class="tb-toks">${tokens.map((t, i) => html`<${Token} key=${i} ...${t} word=" " />`)}</span>`}
    </button><${Mine} ctx=${ctx} id=${id} /></div>`;
}

/** A pile of cards: its top card and the backs under it. Pressed, it spreads (`onSpread`); `n` the backs. */
export function TPile({ ctx, id, title, line = "", sign = "work", n = 3, open = false, onSpread, kind = "", size = "md", mono = false, count = "" }) {
  const marked = placed.value.some((t) => t.party === ctx.party && t.framework === ctx.framework && t.card === id);
  return html`<div class=${cls(`tb-slot tb-pile is-${size}`, { "is-open": open, "is-marked": marked })} style=${`--ov:${n}`}>
    ${Array.from({ length: n }, (_, i) => html`<span key=${i} class="ork-card tb-under" style=${`--dx:${(n - i) * 4}px`} aria-hidden="true"></span>`).reverse()}
    <button type="button" class=${cls("ork-card tb-card", { "is-marked": marked, [`is-${kind}`]: !!kind })} data-card=${id} data-pile="true" data-race=${ctx.race} aria-expanded=${String(open)}
        aria-label=${`${title}, a pile${count ? ` of ${count}` : ""}. ${held.value ? "Press to put your token here." : open ? "Press to close it." : "Press to spread it."}`}
        onClick=${press(ctx, id, title, onSpread)}>
      <span class="tb-ix" aria-hidden="true"><${Sign} name=${sign} /></span>
      <b class=${cls("tb-name", { "is-mono": mono })}>${title}</b>${line && html`<small class="tb-line">${line}</small>`}${count && html`<small class="tb-count">${count}</small>`}
    </button><${Mine} ctx=${ctx} id=${id} /></div>`;
}

/** A card face down; pressed, it turns up (`onTurn`). */
export const TBack = ({ name, onTurn }) => html`<button type="button" class="tb-faced" data-card="face-down" aria-label=${`${name}, face down. Press to turn it.`} onClick=${onTurn}></button>`;

/** The person's two tokens, Question and Concern (decisions §145: what the person decides is in the hand): drawn at the left of the hand's cards
 *  while a leader's table is open (hand/hand.js); held, the next press on a card of the table puts it there and asks for its few words (`TokenStrip`). */
export function TokenTakes() {
  return html`<div class="tb-takes" role="group" aria-label="Your tokens">
    ${["question", "concern"].map((v) => html`<button type="button" key=${v} class=${cls("tb-take", { "is-held": held.value === v })} data-token=${v} aria-pressed=${String(held.value === v)}
        onClick=${() => { held.value = held.value === v ? "" : v; asking.value = null; }}><${YouToken} view=${v} big=${true} /><b>${WORDS[v].word}</b></button>`)}
  </div>`;
}

/** The foot of a leader's table: where a held token's few words are asked, or what to do with the tokens in the hand. */
export function TokenStrip({ ctx, leader }) {
  const ask = asking.value, box = useRef(), [text, setText] = useState("");
  useEffect(() => { if (ask) { setText(""); box.current?.focus(); } }, [ask]);
  const w = whoOf(ctx.party), name = w.name || leader;
  const send = (e) => {
    e.preventDefault();
    if (held.value && ask) putToken({ ...ask, view: held.value, text });
  };
  const cancel = () => { asking.value = null; held.value = ""; };
  return html`<footer class="tb-hand" aria-label="Your words on this table">
    ${ask && held.value ? html`<form class="tb-ask" onSubmit=${send} onKeyDown=${(e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); cancel(); } }}>
        <label class="tb-ask__to" for="tb-ask-words">Your ${held.value} to ${name} · on <b>${ask.name}</b></label>
        <input ref=${box} id="tb-ask-words" class="ork-input" value=${text} placeholder=${held.value === "concern" ? "What worries you here?" : "What do you want to ask?"} onInput=${(e) => setText(e.currentTarget.value)} />
        <button type="submit" class="ork-btn primary">Send to ${name}</button><button type="button" class="ork-btn quiet" onClick=${cancel}>Cancel</button></form>`
      : html`<p class="tb-note">${held.value ? `Press a card to put your ${held.value} on it.` : `Take a token in the hand, then put it on a card: ${name} gets it, and the part of its table it marks is what it betters. Its cards you only turn over, or spread a pile.`}</p>`}
  </footer>`;
}
