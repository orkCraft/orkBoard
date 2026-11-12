// A move that waits and a battle on the phone (decisions §298.7, §300.2; goal 171 K): the table of cards only. The hand's row draws them as it draws its other cards (uprow.js, an entry of their own each); a move's card pressed opens as a question's does, the opened card (stopcard.js `Lifted`
// with `inline`): a goal that asks has its question's ways as the body's buttons and *In your own words*, which opens one field and *Send the answer*; a goal whose Talk is all said or whose spec is all written has one button, *Open it*, for the mat its move lies on. The ways are the descriptor turncards.js `turnCard` builds for the desktop, so
// the two faces send the same commands. A battle's card in the row opens the Orkmaster's spread at once (uprow.js); where the goal was picked some other way, its opened card holds one button, *Open the battle*, that opens it. Registered on the ways' table by being imported (upright.js). Layout only (cards/phone.css).
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { openSpread } from "../cards/spreads/open.js";
import { turnCard } from "./turncards.js";
import { way } from "./ways.js";

/** The opened move: what it is, then its ways (a question's, one after the other, with *In your own words*, whose field is one textarea and *Send the answer*), or one button for the mat its move lies on (the goal's stages). */
export function TurnLifted({ s }) {
  const [picked, setPicked] = useState([]), [writing, setWriting] = useState(false), [words, setWords] = useState("");
  if (s.ref.turn !== "asks") return html`<div class="up-turn" role="group" aria-label="Answers"><p class="body up-turn__text">${s.text}</p>
    <button type="button" class="ork-btn primary" data-act="open-move" onClick=${(e) => openSpread({ kind: "track", slug: s.ref.slug, from: e.currentTarget })}>Open it</button></div>`;
  const c = turnCard(s, picked, (next) => { setPicked(next); setWriting(false); setWords(""); }), pen = c.pen;
  const send = () => { const text = words.trim(); if (text) pen.send(text); };
  const rows = c.ways.map((w) => html`<div key=${w.id} class="up-turn__way" data-way=${w.id}>
    <button type="button" class="ork-btn" data-way=${w.id} onClick=${() => w.run()}>${w.name}</button></div>`);
  const own = html`<div key="own" class="up-turn__way" data-way="own">
    <button type="button" class="ork-btn" data-way="own" aria-expanded=${writing ? "true" : "false"} onClick=${() => setWriting(!writing)}>${pen.name}</button>
    <span class="cap up-turn__line">${pen.line}</span>
    ${writing && html`<div class="up-turn__pen">
      <textarea class="ork-field" rows=${pen.ask.rows} aria-label=${pen.ask.label} placeholder=${pen.ask.hold} value=${words} onInput=${(e) => setWords(e.currentTarget.value)}></textarea>
      <button type="button" class="ork-btn primary" data-act="send-words" onClick=${send}>${pen.ask.button}</button></div>`}</div>`;
  return html`<div class="up-turn" role="group" aria-label="Answers"><p class="body up-turn__text">${c.foot}</p>${rows}${own}</div>`;
}

/** The opened battle: one button for its spread. */
export function BattleLifted({ s }) {
  return html`<div class="up-turn" role="group" aria-label="Answers"><p class="body up-turn__text">${s.text}</p>
    <button type="button" class="ork-btn primary" data-act="open-battle" onClick=${(e) => openSpread({ kind: "battle", slug: s.ref.slug, from: e.currentTarget })}>Open the battle</button></div>`;
}

way("turn", { Lifted: TurnLifted });
way("battle", { Lifted: BattleLifted });
