// A card at its turns, in the hand (decisions §298.6, §298.7; the contract proposed in js/mock/parts/turns.js, `proposed.turns`: `[{goal, kind: "rated" | "spec_rated" | "battle", at}]`):
// the table of cards only. A goal's idea rated (*Play it*, *Change it*, *Put off*, *Drop*) and its spec rated (*Start* with its price, *Change the spec*, *Drop*) are stops of kind `turn`
// of the Orkmaster's lane, S cards with the goal's craft tokens (cards/handcards.js); a risk that blocks rings the card and holds *Play it* and *Start*, and says whose risk it is. Pressed,
// its ways lie in the hand as cards, as a question's do (sayplay.js `PlayWays`); each sends a proposed command with `{slug}` (`ideas.turn_play`, `ideas.turn_change` with its words,
// `ideas.put_off`, `ideas.drop`) and the card goes: a change sends the goal back to the table to be rated again, *Drop* lays it face down in the Dropped pile (cards/dropped.js).
// A battle (kind `battle`, `proposed.battles`) is a card of its own; pressed it opens the Orkmaster's spread of it (cards/spreads/battle.js), where its ways lie. Wide only.
import { useEffect } from "preact/hooks";
import { html } from "../html.js";
import { command, proposed } from "../link.js";
import { ORKMASTER, lower } from "../frame/state.js";
import { blockedBy } from "../cards/verdict.js";
import { dropGoal } from "../cards/dropped.js";
import { openSpread } from "../cards/spreads/open.js";
import { whoOf } from "../table/post.js";
import { PlayWays } from "./sayplay.js";
import { settle } from "./turnstops.js";

const toolName = (id) => (proposed("costs")?.tools || []).find((t) => t.id === id)?.name || String(id || "").replace(/^./, (c) => c.toUpperCase());
/** What starting a goal costs, said as the cost spread says it (*about 12% of Claude*), "" when no price is known. */
export function priceWords(slug) {
  const p = proposed("costs")?.goals?.[slug];
  return p?.tool ? `about ${p.pct}% of ${toolName(p.tool)}` : "";
}

/** A turn's card as `PlayWays` draws it (and the phone's opened card, turnphone.js): its ways, the Pen of *Change it*. */
export function turnCard(s) {
  const { slug, turn } = s.ref, n = s.node, by = blockedBy(slug), lead = by ? whoOf(by).name : "", spec = turn === "spec_rated", price = priceWords(slug);
  const send = (name, then, extra = {}) => Promise.resolve(command(name, { slug, ...extra })).then(() => { then(); lower(); }).catch(() => {});      // refused: the host's toast says why, the card stays
  const away = () => settle(slug, turn), why = `${lead}'s risk blocks it until ${lead} lifts it.`;
  const go = { id: "play", name: spec ? "Start" : "Play it", pick: false, kind: "go_on", disabled: !!by, run: () => send("ideas.turn_play", away),
    line: by ? why : spec ? `The work starts now${price ? `, ${price}` : ""}.` : "The goal goes on to its spec." };
  const put = { id: "put_off", name: "Put off", line: "It waits in line; nothing starts until you take it.", pick: false, kind: "later", run: () => send("ideas.put_off", away) };
  const drop = { id: "drop", name: "Drop", line: "It lies face down in the Dropped pile; you can take it back.", pick: false, kind: "drop", run: () => send("ideas.drop", () => dropGoal(slug)) };
  return { title: s.title, foot: s.text, sign: "flag", element: n?.element || "", hue: n?.hue || "", head: s.head, tab: ORKMASTER, whole: true,
    ways: spec ? [go, drop] : [go, put, drop],
    pen: { name: spec ? "Change the spec" : "Change it", line: spec ? "Write what to change in its spec; its leaders rate it again." : "Write what to change; it goes back to the table and is rated again.", at: 1, who: "the Orkmaster",
      send: (text) => send("ideas.turn_change", away, { text }), ask: { label: spec ? "What to change in the spec" : "What to change", hold: "What should be different…", button: "Send the change", note: "Enter sends · Shift+Enter a new line", rows: 4 } } };
}

/** A turn's card in play: its ways the hand's row. */
export function TurnPlay({ s }) {
  return html`<${PlayWays} card=${turnCard(s)} id=${s.key} idea=${s.ref.slug} kind="turn" />`;
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
