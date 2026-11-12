// A card at its turns and a battle on the phone (decisions §298.7; the contract proposed in js/mock/parts/turns.js): the table of cards only. The hand's row draws them as it draws its other cards (uprow.js, an entry of their own each); a turn's card pressed opens as a question's does, the opened card (stopcard.js `Lifted`
// with `inline`), its ways the body's buttons, each with the line that says what it does: *Play it* (held, saying whose risk blocks it, while a risk blocks) or *Start*, *Put off*, *Drop*, and *Change it* (*Change the spec*), which opens one field for the words and *Send the change*. The ways are the descriptor turncards.js `turnCard` builds for the desktop, so
// the two faces send the same commands. A battle's card in the row opens the Orkmaster's spread at once (uprow.js); where the goal was picked some other way, its opened card holds one button, *Open the battle*, that opens it. Registered on the ways' table by being imported (upright.js). Layout only (cards/phone.css).
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { openSpread } from "../cards/spreads/open.js";
import { turnCard } from "./turncards.js";
import { way } from "./ways.js";

/** The opened turn's body: what it is, then its ways, the Pen's field in the place the desktop gives its card. */
export function TurnLifted({ s }) {
  const c = turnCard(s), [writing, setWriting] = useState(false), [words, setWords] = useState(""), pen = c.pen;
  const at = pen && pen.at >= 0 && pen.at <= c.ways.length ? pen.at : c.ways.length;
  const send = () => { const text = words.trim(); if (text) pen.send(text); };
  const rows = c.ways.map((w) => html`<div key=${w.id} class="up-turn__way" data-way=${w.id}>
    <button type="button" class=${w.kind === "go_on" ? "ork-btn primary" : "ork-btn"} data-way=${w.id} disabled=${w.disabled || undefined} onClick=${() => w.run()}>${w.name}</button>
    <span class="cap up-turn__line">${w.line}</span></div>`);
  const own = pen && html`<div key="own" class="up-turn__way" data-way="own">
    <button type="button" class="ork-btn" data-way="own" aria-expanded=${writing ? "true" : "false"} onClick=${() => setWriting(!writing)}>${pen.name}</button>
    <span class="cap up-turn__line">${pen.line}</span>
    ${writing && html`<div class="up-turn__pen">
      <textarea class="ork-field" rows=${pen.ask?.rows || 4} aria-label=${pen.ask?.label || "Your words"} placeholder=${pen.ask?.hold || ""} value=${words} onInput=${(e) => setWords(e.currentTarget.value)}></textarea>
      <button type="button" class="ork-btn primary" data-act="send-words" onClick=${send}>${pen.ask?.button || "Send"}</button></div>`}</div>`;
  return html`<div class="up-turn" role="group" aria-label="Answers"><p class="body up-turn__text">${s.text}</p>${[...rows.slice(0, at), own, ...rows.slice(at)]}</div>`;
}

/** The opened battle: one button for its spread. */
export function BattleLifted({ s }) {
  return html`<div class="up-turn" role="group" aria-label="Answers"><p class="body up-turn__text">${s.text}</p>
    <button type="button" class="ork-btn primary" data-act="open-battle" onClick=${(e) => openSpread({ kind: "battle", slug: s.ref.slug, from: e.currentTarget })}>Open the battle</button></div>`;
}

way("turn", { Lifted: TurnLifted });
way("battle", { Lifted: BattleLifted });
