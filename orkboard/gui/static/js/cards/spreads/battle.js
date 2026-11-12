// A battle, the Orkmaster's spread (decisions §298.6; docs/mockups/card-path/ ?v=battle): a new card against the old cards it goes against, goals at work or done and decisions (a decision a
// card of its own with its § for its picture). The new card at the left, the old ones at the right (three face up at most, more as a pile), between them one row for each craft on the new
// card's route, **axis by axis, no total, no winner said**: the new card's token at the left of the row and the old cards' at the right. Under an old card what it costs to undo it
// (`undo`: `{pct, tool, what}`). The person's hand holds its four ways as cards; each sends `ideas.battle_settle {slug, way}` (the host answers none of it yet, and no battle is laid: this mat lies empty until the battles' goal fills it) and the battle's card is gone from the hand. No victory is drawn. Esc and *Close* put the spread away. On a phone width the field stacks: new card, axes, old cards.
import { html } from "../../html.js";
import { command } from "../../link.js";
import { Index } from "../card.js";
import { nodeOf } from "../feed.js";
import { TokenDot } from "../handtokens.js";
import { verdictsOf } from "../verdict.js";
import { settle } from "../../hand/turnstops.js";
import { whoOf } from "../../table/post.js";
import { phaseOf } from "../../table/data.js";
import { closeSpread } from "./open.js";
import { SpBack, SpCard, SpreadFrame, faceOf } from "./shell.js";

const FACE_UP = 3;
const NUMBER = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];
/** A craft's axis: what its leader weighs (Product value, Tech risk, Design experience); another craft's is its party's name. */
const AXIS = { product: "Value", tech: "Risk", design: "Experience", release: "Release" };

/** *a decision and a goal*: what the new card goes against, said by kind. */
export function againstWords(against) {
  const n = (k) => against.filter((a) => a.kind === k).length, one = (k, word) => (n(k) === 1 ? `a ${word}` : n(k) > 1 ? `${NUMBER[n(k)] || n(k)} ${word}s` : "");
  return [one("decision", "decision"), one("goal", "goal")].filter(Boolean).join(" and ");
}

/** The ways, each with its line, the old cards by kind. */
export function waysOf(against) {
  const goal = against.some((a) => a.kind === "goal"), decision = against.some((a) => a.kind === "decision");
  const wins = [goal && "the old goal reopens as a change", decision && "the old decision is replaced by a new one, never edited"].filter(Boolean).join("; ");
  return [
    { id: "new_wins", name: "New wins", line: wins || "the old cards give way" },
    { id: "old_wins", name: "Old wins", line: "the new card is dropped, or changed to fit" },
    { id: "merge", name: "Merge", line: "the leaders write one card of both" },
    { id: "not_a_battle", name: "Not a battle", line: "the Orkmaster read it wrong" },
  ];
}

/** An old card face up: a goal as its own card, a decision with its § for its picture and its number. */
function Old({ a }) {
  const goal = a.kind === "goal", n = goal ? nodeOf(a.ref) : null, w = whoOf(n?.goal || "orkmaster");
  if (goal) return html`<${SpCard} party=${n?.goal} n=${faceOf(n)} name=${a.title} line=${a.state || ""} size="lg" label=${`${a.title}, an old goal`} />`;
  return html`<div class="ork-card cards-s sp-card is-lg bt-decision" data-race=${w.race || "orkmaster"} role="group" aria-label=${`${a.ref} ${a.title}, a decision`}>
    <${Index} n=${{ element: "", hue: "", sign: "balance" }} /><span class="sp-pic bt-sect" aria-hidden="true">§</span>
    <b class="sp-card__name">${a.ref} ${a.title}</b><small class="sp-card__line">${a.state || ""}</small></div>`;
}

const undoWords = (u) => (u ? `to undo: ≈${u.pct}% ${u.tool}${u.what ? ` · ${u.what}` : ""}` : "");

export function Battle({ slug }) {
  const n = nodeOf(slug), against = [];
  if (!n || !against.length) return null;
  const mine = verdictsOf(slug), up = against.slice(0, FACE_UP), more = against.slice(FACE_UP);
  const settleWith = (way) => Promise.resolve(command("ideas.battle_settle", { slug, way: way.id })).then(() => { settle(slug, "battle"); closeSpread(); }).catch(() => {});
  const hand = waysOf(against).map((w) => html`<button key=${w.id} type="button" class="ork-card bt-way" data-way=${w.id} title=${w.line} aria-label=${`${w.name}: ${w.line}`} onClick=${() => settleWith(w)}>
    <b>${w.name}</b><small>${w.line}</small></button>`);
  const title = `A new card against ${NUMBER[against.length] || against.length}`;
  return html`<${SpreadFrame} kind="battle" title=${title} line="The Orkmaster's spread: a battle · nothing is decided for you"
      say=${`It goes against ${againstWords(against)}. Read each axis; the old cards carry what it costs to undo them.`}
      note="Play a way: every leader is told, the Orkmaster writes it in the journal." hand=${hand} phase=${phaseOf(slug) || "talk"}>
    <div class="bt">
      <section class="bt-side bt-new" aria-label="The new card"><p class="cards-lab" data-race="orkmaster">The new card</p>
        <${SpCard} party=${n.goal} n=${faceOf(n)} name=${n.short || n.title} line=${n.state === "talk" ? "talk" : n.state} size="xl" label=${`${n.title}, the new card`} /></section>
      <section class="bt-axes" aria-label="Axis by axis">
        <div class="bt-row bt-head" aria-hidden="true"><span>new</span><span></span><span>old</span></div>
        ${mine.map((v) => html`<div key=${v.leader} class="bt-row" data-axis=${v.leader}>
          <span class="bt-cell"><${TokenDot} v=${v} /></span>
          <span class="bt-axis"><b>${AXIS[v.leader] || whoOf(v.leader).name}</b><small>${whoOf(v.leader).name}'s axis</small></span>
          <span class="bt-cell">${up.map((a) => { const o = verdictsOf(a.ref).find((x) => x.leader === v.leader); return o ? html`<${TokenDot} key=${a.ref} v=${o} />` : html`<span key=${a.ref} class="bt-none" role="img" aria-label=${`${a.title}: not rated by ${whoOf(v.leader).name}`}>–</span>`; })}</span></div>`)}
        <p class="sp-cap bt-note">No total: one weakness can outweigh three strengths. The tokens are the leaders'; the price is the Orkmaster's.</p>
      </section>
      <section class="bt-side bt-old" aria-label="What it goes against"><p class="cards-lab" data-race="orkmaster">What it goes against</p>
        <div class="bt-olds">${up.map((a) => html`<div key=${a.ref} class="bt-one" data-old=${a.ref}><${Old} a=${a} /><small class="bt-undo">${undoWords(a.undo)}</small></div>`)}
          ${more.length > 0 && html`<div class="bt-one bt-pile" role="group" aria-label=${`${NUMBER[more.length] || more.length} more old cards, face down`}>${more.map((a, i) => html`<${SpBack} key=${a.ref} tilt=${i % 2 ? 3 : -3} size="md" />`)}</div>`}</div></section>
    </div>
  </${SpreadFrame}>`;
}
