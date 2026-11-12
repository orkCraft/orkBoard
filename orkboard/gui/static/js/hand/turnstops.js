// The hand's stops of a card at its turns and of a battle (decisions §298.6, §298.7; the contract proposed in js/mock/parts/turns.js: `proposed.turns` `[{goal, kind: "rated" | "spec_rated" | "battle", at}]`
// and `proposed.battles`), read by hand/data.js; their cards in play are hand/turncards.js's. The table of cards only: nothing else imports the hand's faces here.
import { signal } from "@preact/signals";
import { proposed } from "../link.js";
import { ORKMASTER } from "../frame/state.js";
import { blockedBy } from "../cards/verdict.js";
import { droppedSlugs } from "../cards/dropped.js";
import { way } from "./ways.js";

way("turn", { sign: "flag", tone: "alert" });
way("battle", { sign: "flag", tone: "alert" });

export const settled = signal([]);              // `slug:kind` of the turns answered on this page: their cards are gone from the hand

export const settle = (slug, kind) => { settled.value = [...settled.value, `${slug}:${kind}`]; };

/** What a battle says of what it goes against: a decision by its §, a goal by its title (*vs §240 and The table, its edge*). */
export const vsWords = (against) => `vs ${(against || []).map((a) => (a.kind === "decision" ? a.ref : a.title)).join(" and ")}`;

/** The hand's stops of the turns that wait, after the other stops, in the Orkmaster's lane. `ctx`: as questions.js `projectStops` has it (`party(slug)`, `open`). */
export function turnStops(map, ctx) {
  const out = [], gone = droppedSlugs();
  for (const t of proposed("turns") || []) {
    const n = (map?.nodes || []).find((x) => x.slug === t.goal);
    if (!n || gone.includes(n.slug) || settled.value.includes(`${n.slug}:${t.kind}`)) continue;
    const party = ctx.party(n.goal), fight = t.kind === "battle", against = proposed("battles")?.[n.slug]?.against || [];
    if (fight && !against.length) continue;
    const text = fight ? vsWords(against) : t.kind === "spec_rated" ? "its spec, rated" : "its idea, rated", title = n.short || n.title;
    out.push({ key: `turn/${n.slug}/${t.kind}`, kind: fight ? "battle" : "turn", ref: { slug: n.slug, turn: t.kind, against }, row: { goal: n.goal, idea: n.slug, kind: fight ? "battle" : "turn", blocks: false }, node: n, task: null,
      label: fight ? "Battle" : `${t.kind === "spec_rated" ? "Spec rated" : "Rated"}${blockedBy(n.slug) ? ", blocked" : ""}`, gem: "", tone: "alert", gemTip: "", head: party?.head || null, small: true, whoTip: "",
      title, full: n.title, text, why: "", g: null, party: party || null, other: ctx.open !== ORKMASTER && ctx.open !== n.goal });
  }
  return out;
}

