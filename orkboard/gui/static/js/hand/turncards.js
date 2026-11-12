// A card of a move that waits, in play (goal 171 stage K; decisions §300.2, §302.4; the host's `ideas.turns`, hand/turnstops.js): the table of cards only.
// A goal that asks (kind `asks`) lifts its ways as a question's do (sayplay.js `PlayWays`): the ways of its question, one question after the other when it asks several, and *In your own
// words*; the last answer sends `ideas.answer_way {slug, answers, from: "hand"}` (the answers written under their questions, no keeper pass begun), one press, its toast saying what it sent with **Undo** (cards/played.js). A goal whose Talk is all said or whose spec
// is all written (kinds `talk`, `spec`) opens the mat its move lies on, the goal's stages (cards/spreads/track.js), where its ways lie in the hand. A battle (kind `battle`) opens its own spread.
// `turnCard` is the descriptor `PlayWays` draws (and the phone's opened card, turnphone.js draws the same ways). Wide only.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { ORKMASTER, lower } from "../frame/state.js";
import { playMove } from "../cards/played.js";
import { openSpread } from "../cards/spreads/open.js";
import { PlayWays } from "./sayplay.js";
import { settle, unsettle } from "./turnstops.js";

const OWN = { label: "Your answer", hold: "Your answer…", button: "Send the answer", note: "Enter sends · Shift+Enter a new line", rows: 4 };

/** What an answer to a goal's questions says it did (the toast), at most 120 characters. */
export const sentWords = (answers) => `Sent: ${answers.join(" · ")}`.slice(0, 120);

/** The card of a goal that asks, at question `picked.length` (`picked`: the answers so far); `pick(answers)` is called with the answers so far, the last one sends. */
export function turnCard(s, picked = [], pick = () => {}) {
  const { slug, questions, party } = s.ref, n = s.node, qs = questions || [], i = Math.min(picked.length, Math.max(0, qs.length - 1)), q = qs[i] || { ask: s.text, ways: [] };
  const take = (text) => {
    const next = [...picked, text];
    if (next.length < qs.length) { pick(next); return Promise.resolve(); }
    return playMove("ideas.answer_way", { slug, answers: next, ...(party ? { party: true } : {}) }, { from: "hand", goal: slug, party: !!party, said: sentWords(next), done: () => { settle(slug, "asks"); lower(); }, back: () => unsettle(slug, "asks") });
  };
  const ways = (q.ways || []).map((w, k) => ({ id: `way-${k}`, name: w, line: "", pick: false, kind: "", run: () => take(w) }));
  return { title: s.title, foot: `${q.ask}${qs.length > 1 ? ` (${i + 1} of ${qs.length})` : ""}`, sign: "question", element: n?.element || "", hue: n?.hue || "", head: s.head, tab: ORKMASTER, whole: true, ways,
    pen: { name: "In your own words", line: "Write the answer yourself.", at: ways.length, who: s.party?.lead || "the Orkmaster", send: (text) => take(text), ask: OWN } };
}

/** The mat a goal's move lies on (its talk all said, its spec all written): the goal's stages; the card goes back to the hand, where the focus returns when the mat is put away. */
export function openMoveMat(s, from) {
  openSpread({ kind: "track", slug: s.ref.slug, from });
}

/** A card of a move that waits, in play: a question's ways the hand's row, else its mat opened. */
export function TurnPlay({ s }) {
  const [picked, setPicked] = useState([]);
  useEffect(() => { setPicked([]); }, [s.key]);
  useEffect(() => {
    if (s.ref.turn === "asks") return;
    openMoveMat(s, document.querySelector(`.frame-hand button.hand-card[data-key="${CSS.escape(s.key)}"]`));
    lower();
  }, [s.key]);
  if (s.ref.turn !== "asks") return null;
  return html`<${PlayWays} card=${turnCard(s, picked, setPicked)} id=${`${s.key}#${picked.length}`} idea=${s.ref.slug} kind="turn" />`;
}

/** A battle's card pressed: its spread opens (the goal's Orkmaster lays it) and the card goes back to the hand, where the focus returns when the spread is put away. */
export function BattlePlay({ s }) {
  useEffect(() => {
    const from = document.querySelector(`.frame-hand button.hand-card[data-key="${CSS.escape(s.key)}"]`);
    openSpread({ kind: "battle", slug: s.ref.slug, from });
    lower();
  }, [s.key]);
  return null;
}
