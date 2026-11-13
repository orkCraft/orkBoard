// A battle, the hand's conflict card's mat (decisions §303; goal "The battle and the gate" stage J; docs/mockups/mats/, the shot battle-2): a goal's decision goes against standing decisions, and the host says
// which (`ideas.battle {idea}` → `{idea, against: [{number, title, point, rests: {goals, decisions, tests}}], cost}`, read only, asked when the mat opens). It lies upright in goal 171's frame (cards/matframe.js):
// the zone *What it goes against* above (each §N a decision card face up with its § for its picture, three at most and the rest a pile; under each in one line what rests on it by kind, its slip listing
// them), across the middle the line (a column for each craft of the goal's route with the new card's token under it, nothing above it for a decision, *No total* beside), the zone *Yours* below with the new card,
// the phases along the foot. No mana, price, potion or total. The ways of a battle are stage K's: the mat holds their place (the hand, the seal) and sends nothing. Opening it starts no pass and spends nothing.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { command } from "../../link.js";
import { Index } from "../card.js";
import { nodeOf } from "../feed.js";
import { CraftToken, verdictsOf } from "../verdict.js";
import { Slip } from "../slip.js";
import { phaseOf } from "../../table/data.js";
import { whoOf } from "../../table/post.js";
import { Zone } from "../matframe.js";
import { SpBack, SpCard, SpreadFrame, faceOf } from "./shell.js";
import { routeOf } from "./deal.js";

const FACE_UP = 3;
const NUMBER = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];
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

export function Battle({ slug }) {
  const n = nodeOf(slug), [got, setGot] = useState(null), [open, setOpen] = useState(""), [token, setToken] = useState("");
  useEffect(() => {
    let live = true;
    command("ideas.battle", { idea: slug }, true).then((r) => { if (live) setGot(r || { against: [] }); }).catch(() => { if (live) setGot({ against: [] }); });
    return () => { live = false; };
  }, [slug]);
  const against = got?.against || [];
  if (!n || !against.length) return null;
  const mine = verdictsOf(slug), route = routeOf(n), crafts = route.length ? route : mine.map((v) => v.leader);
  const up = against.slice(0, FACE_UP), more = against.slice(FACE_UP), title = n.short || n.title || slug, nums = against.map((a) => `§${a.number}`).join(" and ");
  const old = up.find((a) => `§${a.number}` === open), tok = mine.find((v) => v.leader === token);
  return html`<${SpreadFrame} kind="battle" title=${`${title} vs ${nums}`} line="A new card against what it goes against; nothing is decided by opening it"
      say=${`It goes against ${againstWords(against.map((a) => ({ kind: "decision", ...a })))}. Read what rests on it.`} hand=${null} phase=${phaseOf(slug) || "talk"}>
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
