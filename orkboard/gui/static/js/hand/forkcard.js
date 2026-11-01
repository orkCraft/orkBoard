// A fork (docs/specs/100-a-goals-way-as-cards.md §3.2; docs/specs/99-a-goals-way.md §7.3; decisions §117.3, §198.6): what two leaders' sections disagree on, in the person's hand. The row is `{kind: "fork", idea, id, about,
// sides: [{party, leader, says, why}], hearing}`, the goal's first fork open; `hearing` holds its sides as a hearing has them (realm/idea_hearing.py `of_fork`). Its face is the hand's card (stopcard.js): the question sign, the first side's leader's head
// as its asker, *<A> and <B> disagree* at its foot, under the first lane (data.js `laneOf`). Lifted, it is a hearing (hearing.js; spec 120 §6.7): the goal's card in the middle and the sides around it, thrown to the one the person takes
// (`ideas.throw {idea, moment: "fork", dir | text}`: the side's way stands and the other sides' leaders write their sections again; the person's own words are written again by every side's leader). Under it the pane shows the goal's Spec
// (table/specpage.js) with the sections of the sides lit. The next fork of the goal, if one is left, takes the pane's place.
import { nameOf, partiesAll } from "../table/data.js";
import { HearingLifted, hearingOf } from "./hearing.js";
import { way } from "./ways.js";

const partyBy = (slug) => partiesAll().find((g) => g.slug === slug) || null;
const sideName = (side) => nameOf(partyBy(side.party)) || side.party;

/** *Design and Tech disagree*, *Design, Tech and Art disagree*. */
export function disagreeWords(sides) {
  const names = (sides || []).map(sideName);
  return names.length < 2 ? "" : `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]} disagree`;
}

// The face: the question sign, the first side's leader as its asker, the sides at its foot (stopcard.js asks the way's `head` and `foot`); lifted, the hearing (hearing.js).
way("fork", { sign: "question", head: (s) => partyBy(s.row?.sides?.[0]?.party)?.leader?.head || null, foot: (s) => disagreeWords(s.row?.sides) || hearingOf(s.row)?.title || "", Lifted: HearingLifted });
