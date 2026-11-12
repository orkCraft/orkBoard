// The hand's cards of the moves that wait for the person (goal 171 stage K; decisions §300.2, §301.2; the table of cards only): `ideas.turns` is the host's, read from the Board's pages with no model and no write
// (`{turns: [{goal, kind, at, questions?}]}`, kinds `asks` (a question waits), `talk` (its leaders have all said their Talk), `spec` (every section is written)), asked once a snapshot as `ideas.feed` is.
// One card a goal that waits, grouped by goal (data.js `stackKey`): what is not asked of the person has none, and nothing is dealt that the host did not name. A goal whose question is already a card of the
// hand (the Needs you rows keep their stops as today) is that card: it gets no second one. Pressed, the card lifts its ways (`asks`: turncards.js) or opens the mat its move lies on (talk, spec).
// A battle is a card of its own (kind `battle`), laid by a mat of its own goal; none is dealt here. Their cards in play are turncards.js's.
import { signal, effect } from "@preact/signals";
import { command, town } from "../link.js";
import { cardsOn } from "../cards/on.js";
import { way } from "./ways.js";

way("turn", { sign: "flag", tone: "alert" });
way("battle", { sign: "flag", tone: "alert" });

export const turns = signal(null);               // the host's answer to `ideas.turns`, null until it comes
export const settled = signal([]);               // `slug:kind` of the turns played on this page: their cards are gone from the hand until the host answers anew (an Undo brings one back)

export const settle = (slug, kind) => { settled.value = [...settled.value.filter((k) => k !== `${slug}:${kind}`), `${slug}:${kind}`]; };
export const unsettle = (slug, kind) => { settled.value = settled.value.filter((k) => k !== `${slug}:${kind}`); };

let asked = null;
effect(() => {                                   // only the table of cards asks: the table as it is sends nothing more
  const snap = town.value;
  if (!cardsOn() || !snap || snap === asked) return;
  asked = snap;
  command("ideas.turns", {}, true).then((r) => { turns.value = r || {}; settled.value = []; }).catch(() => { turns.value = turns.peek() || {}; });
});

/** What a battle says of what it goes against: a decision by its §, a goal by its title (*vs §240 and The table, its edge*). */
export const vsWords = (against) => `vs ${(against || []).map((a) => (a.kind === "decision" ? a.ref : a.title)).join(" and ")}`;

/** What a turn says, for its card's foot and its lifted card. */
export const TURN_WORDS = {
  asks: (t) => (t.questions?.length ? t.questions[0].ask : "A question waits for you."),
  talk: () => "Its leaders have all said their Talk: you decide.",
  spec: () => "Every part has written its section: you decide.",
};

const HEAD = { race: "peon", tier: "crown" };      // the Orkmaster's, who deals the moves that wait

/** The hand's stops of the moves that wait: one a goal, in the pages' order. `ctx`: as questions.js `projectStops` has it (`party(slug)`), `covered`: the goals whose question already lies in the hand as a card. */
export function turnStops(map, ctx = {}) {
  const out = [];
  for (const t of turns.value?.turns || []) {
    if (!TURN_WORDS[t.kind] || settled.value.includes(`${t.goal}:${t.kind}`) || settled.value.includes(`${t.goal}:*`)) continue;      // `*`: the goal's mat played a move that ends all its turns (a Drop, a Hold)
    if (t.kind === "asks" && ctx.covered?.has(t.goal)) continue;
    const n = (map?.nodes || []).find((x) => x.slug === t.goal);
    if (!n) continue;                            // a goal the Board does not show has no card to lie on
    const title = n.short || n.title || t.goal, text = TURN_WORDS[t.kind](t), party = ctx.party?.(n.goal) || null;
    out.push({ key: `turn/${t.goal}/${t.kind}`, kind: "turn", ref: { slug: t.goal, turn: t.kind, questions: t.questions || [], at: t.at || "" }, row: { goal: n.goal, idea: t.goal, kind: "turn", blocks: true }, node: n, task: null,
      label: "Waits for you", gem: "", tone: "alert", gemTip: "", head: HEAD, small: true, whoTip: "", title, full: n.title || title, text, why: "", party, other: false });
  }
  return out;
}
