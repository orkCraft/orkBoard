// A battle, the hand's conflict card's mat (decisions §303; goal "The battle and the gate" stage J; docs/mockups/mats/, the shot battle-2): a goal's decision goes against standing decisions, and the host says
// which (`ideas.battle {idea}` → `{idea, against: [{number, title, point, rests: {goals, decisions, tests}}], cost}`, read only, asked when the mat opens). It lies upright in goal 171's frame (cards/matframe.js):
// the zone *What it goes against* above (each §N a decision card face up with its § for its picture, three at most and the rest a pile; under each in one line what rests on it by kind, its slip listing
// them), across the middle the line (a column for each craft of the goal's route with the new card's token under it, nothing above it for a decision, *No total* beside), the zone *Yours* below with the new card,
// the phases along the foot. No mana, price, potion or total. Opening it starts no pass and spends nothing.
// Its three ways lie in the hand (stage K; decisions §303.4), each card's line saying what it does and whether it asks first, and answer the §N first face up through `ideas.conflict {idea, number, choice, from}`: *New wins* (the new decision
// replaces §N) is one press with its Undo; *Old wins* (the new decision worded again within §N) and *Your words* (worded again with yours, written in the hand's place first) light the seal with their cost said (`ideas.battle`'s `cost`) and
// send `sealed: true` from it. With more conflicts left (the answer's `left`) the mat lays the next, the last closes it. `from` is `hand` when its hand card opened it, `mat` from the goal's card on the table. The words typed go to the host and
// into no event. The ways' words are realm/lexicon.py `TERMS`' (new_wins, old_wins, your_words).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { command } from "../../link.js";
import { Index } from "../card.js";
import { PenField } from "../../hand/penfield.js";
import { costWords } from "../askcost.js";
import { playMove } from "../played.js";
import { nodeOf } from "../feed.js";
import { CraftToken, verdictsOf } from "../verdict.js";
import { Slip } from "../slip.js";
import { phaseOf } from "../../table/data.js";
import { whoOf } from "../../table/post.js";
import { Seal, Zone } from "../matframe.js";
import { closeSpread } from "./open.js";
import { SpBack, SpCard, SpreadFrame, faceOf } from "./shell.js";
import { routeOf } from "./deal.js";

const FACE_UP = 3;
const NUMBER = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];
export const NEW_WINS = "New wins", OLD_WINS = "Old wins", YOUR_WORDS = "Your words";      // realm/lexicon.py new_wins, old_wins, your_words (tests/test_conflict.py keeps them so)
const KINDS = [["goals", "goal", "goals"], ["decisions", "decision", "decisions"], ["tests", "test", "tests"]];

/** *a decision and a goal*: what the new card goes against, said by kind (an entry's `kind` is `decision` or `goal`). */
export function againstWords(against) {
  const n = (k) => against.filter((a) => a.kind === k).length, one = (k, word) => (n(k) === 1 ? `a ${word}` : n(k) > 1 ? `${NUMBER[n(k)] || n(k)} ${word}s` : "");
  return [one("decision", "decision"), one("goal", "goal")].filter(Boolean).join(" and ");
}

/** What rests on an old card, in one line by kind with its counts, a kind with none left out: *rests on it: 3 goals · 5 decisions · 12 tests*; *nothing rests on it* when none. */
export function restsWords(rests) {
  const parts = KINDS.map(([key, one, many]) => [(rests?.[key] || []).length, one, many]).filter(([n]) => n > 0).map(([n, one, many]) => `${n} ${n === 1 ? one : many}`);
  return parts.length ? `rests on it: ${parts.join(" · ")}` : "nothing rests on it";
}

/** The slip of an old card: what rests on it, each kind listed. */
function Rests({ a }) {
  const lists = KINDS.map(([key, one, many]) => [one, many, a.rests?.[key] || []]).filter(([, , l]) => l.length > 0);
  return html`<section class="bt-slip ork-plate" data-slip=${`§${a.number}`} aria-label=${`What rests on §${a.number}`}><b>§${a.number}: ${a.point}</b>
    ${lists.length ? lists.map(([one, many, l]) => html`<div key=${one}><small>${l.length} ${l.length === 1 ? one : many}</small><ul>${l.map((x) => html`<li key=${x}><code>${x}</code></li>`)}</ul></div>`) : html`<small>nothing rests on it</small>`}</section>`;
}

/** An old decision face up, a button: its § for its picture, its title, its line of what rests on it under it. */
function Old({ a, on, press }) {
  const name = `§${a.number}${a.title ? ` ${a.title}` : ""}`;
  return html`<div class="bt-one" data-old=${`§${a.number}`}>
    <button type="button" class=${cls("ork-card cards-s sp-card is-md bt-decision is-pick", { "is-picked": on })} data-cardkind="decision" data-race="orkmaster" aria-expanded=${on ? "true" : "false"}
      aria-label=${`${name}, a decision: ${restsWords(a.rests)}. Press to list what rests on it`} onClick=${press}>
      <${Index} n=${{ element: "", hue: "", sign: "balance" }} /><span class="sp-pic bt-sect" aria-hidden="true">§${a.number}</span>
      <b class="sp-card__name">${a.title || name}</b></button>
    <small class="bt-rests">${restsWords(a.rests)}</small></div>`;
}

/** A way in the hand: its name and what it does, plainly, with whether it asks first. `on` is given for a way that picks (the seal then follows it). */
const Way = ({ id, name, line, on, press }) => html`<button type="button" class="ork-card bt-way" data-way=${id} aria-pressed=${on === undefined ? undefined : String(on)} aria-label=${`${name}: ${line}`} onClick=${press}>
  <b>${name}</b><small>${line}</small></button>`;

export function Battle({ slug, opened }) {
  const from = opened === "hand" ? "hand" : "mat";
  const n = nodeOf(slug), [got, setGot] = useState(null), [open, setOpen] = useState(""), [token, setToken] = useState("");
  const [again, setAgain] = useState(0), [pick, setPick] = useState(""), [words, setWords] = useState(""), [field, setField] = useState(false), [busy, setBusy] = useState(false);
  useEffect(() => {
    let live = true;
    command("ideas.battle", { idea: slug }, true).then((r) => { if (live) setGot(r || { against: [] }); }).catch(() => { if (live) setGot({ against: [] }); });
    return () => { live = false; };
  }, [slug, again]);
  const was = useRef(false);
  useEffect(() => { if (was.current && !field) document.querySelector(".mathand [data-way=words], .sp-cards [data-way=words]")?.focus(); was.current = field; }, [field]);      // the field closed: the focus goes back to its card
  const against = got?.against || [];
  if (!n || !against.length) return null;
  const num = against[0].number, first = `§${num}`;
  const next = (r) => { setBusy(false); if ((r?.left ?? 0) > 0) { setPick(""); setWords(""); setField(false); setAgain(again + 1); } else closeSpread(); };      // more left: the next is laid, the last closes the mat
  const newWins = () => { if (busy) return; setBusy(true); playMove("ideas.conflict", { idea: slug, number: num, choice: "replace" }, { from, goal: slug, said: `${NEW_WINS}: ${first} gives way to the new decision.`, done: next, back: () => setAgain((a) => a + 1) }).then((ok) => { if (!ok) setBusy(false); }); };
  const choose = (way) => { if (way === "words") { setPick("words"); setField(true); } else { setPick(pick === way ? "" : way); setField(false); } };      // Your words opens its field each press
  const ways = field
    ? html`<${PenField} who="the Orkmaster" value=${words} close=${() => setField(false)} send=${(t) => { setWords(t); setField(false); }}
        ask=${{ label: "Your words for the new decision", hold: "Say what the decision should be…", button: "Use these words", note: "Enter keeps them · then the seal asks first", rows: 4 }} />`
    : [html`<${Way} key="new" id="new" name=${NEW_WINS} line=${`${first} gives way: the new decision replaces it. One press; you can undo it.`} press=${newWins} />`,
      html`<${Way} key="old" id="old" name=${OLD_WINS} line=${`The new decision is worded again within ${first}. Asks first, on the seal.`} on=${pick === "old"} press=${() => choose("old")} />`,
      html`<${Way} key="words" id="words" name=${YOUR_WORDS} line=${`Worded again with yours${words ? " (written)" : ""}. You write them, then the seal asks first.`} on=${pick === "words"} press=${() => choose("words")} />`];
  const cost = costWords(got?.cost), why = !pick ? "pick Old wins or Your words" : pick === "words" && !words ? "write your words first" : cost;
  const seal = pick === "old"
    ? html`<${Seal} word=${OLD_WINS} why=${cost} lit=${!busy} kind="reword" onPress=${() => { setBusy(true); playMove("ideas.conflict", { idea: slug, number: num, choice: "keep", sealed: true }, { from, goal: slug, sealed: true, said: `${OLD_WINS}: the new decision is worded again within ${first}.`, done: next }).then((ok) => { if (!ok) setBusy(false); }); }} />`
    : pick === "words" && words
      ? html`<${Seal} word=${YOUR_WORDS} why=${cost} lit=${!busy} kind="reword" onPress=${() => { setBusy(true); playMove("ideas.conflict", { idea: slug, number: num, choice: "other", text: words, sealed: true }, { from, goal: slug, sealed: true, said: `${YOUR_WORDS}: the new decision is worded again with them.`, done: next }).then((ok) => { if (!ok) setBusy(false); }); }} />`
      : html`<${Seal} word="Seal the way" why=${why} kind="reword" />`;
  const mine = verdictsOf(slug), route = routeOf(n), crafts = route.length ? route : mine.map((v) => v.leader);
  const up = against.slice(0, FACE_UP), more = against.slice(FACE_UP), title = n.short || n.title || slug, nums = against.map((a) => `§${a.number}`).join(" and ");
  const old = up.find((a) => `§${a.number}` === open), tok = mine.find((v) => v.leader === token);
  return html`<${SpreadFrame} kind="battle" title=${`${title} vs ${nums}`} line="A new card against what it goes against; nothing is decided by opening it"
      say=${`It goes against ${againstWords(against.map((a) => ({ kind: "decision", ...a })))}. Read what rests on it.`} hand=${ways} seal=${seal} phase=${phaseOf(slug)}>
    <div class="bt">
      <${Zone} label="What it goes against" class="bt-against">
        ${up.map((a) => html`<${Old} key=${a.number} a=${a} on=${open === `§${a.number}`} press=${() => setOpen(open === `§${a.number}` ? "" : `§${a.number}`)} />`)}
        ${more.length > 0 && html`<div class="bt-one bt-pile" role="group" aria-label=${`${NUMBER[more.length] || more.length} more old decisions, face down`}>${more.map((a, i) => html`<${SpBack} key=${a.number} tilt=${i % 2 ? 3 : -3} size="sm" />`)}</div>`}
        ${old && html`<${Rests} a=${old} />`}</${Zone}>
      <div class="bt-line" aria-label="The crafts' tokens">
        <div class="bt-crafts">${crafts.map((p) => { const v = mine.find((x) => x.leader === p); return html`<div key=${p} class="bt-craft" data-craft=${p}>
          <span class="bt-tok">${v ? html`<${CraftToken} leader=${v.leader} checks=${v.checks} on=${token === v.leader} onPress=${() => setToken(token === v.leader ? "" : v.leader)} />` : null}</span>
          <b class="bt-name ork-plate">${whoOf(p).name}</b></div>`; })}</div>
        <p class="bt-total ork-plate">No total</p>
        ${tok && html`<${Slip} leader=${tok.leader} checks=${tok.checks} />`}
      </div>
      <${Zone} label="Yours" class="bt-yours"><${SpCard} party=${n.goal} n=${faceOf(n)} name=${title} size="md" label=${`${title}, the new card`} /></${Zone}>
    </div>
  </${SpreadFrame}>`;
}
