// The cards of a leader's say (docs/specs/168-the-window-played-as-a-card-games-table.md C4, decisions §283.16.4, §283.23, §284.1): an idea through a leader is one row of three groups, each a few big cards (144 x 202, the corners of card.js:
// the goal's rune and the kind's sign at the top, the line, a window, who and how much at the foot). The verdict is the leader's own card (its sign by `Verdict`); a need shows its kind (risk, conflict, question), its line and what it rests on;
// a better its line and its weight (lighter, the same, heavier). A card of an item still open is pressable (sayask.js lifts it); one taken or turned down shows how it stands. Layout: say.css. Data: the map node's `say` (realm/idea_say.py `node`).
import { html, cls } from "../html.js";
import { Head, Sign } from "../orkui.js";
import { ASKS, CornerFoot, CornerTop, Verdict } from "./corners.js";

export const MAX_CARDS = 3;                                   // three cards a group at most (decisions §283.16.4)
export const NEED_SIGN = { risk: "alert", conflict: "conflict", question: "question" };
export const NEED_WORDS = { risk: "A risk", conflict: "A conflict", question: "A question" };
export const WEIGHT_WORDS = { lighter: "lighter", same: "the same", heavier: "heavier" };
export const VERDICT_WORDS = { go: "Go", doubt: "Doubt", no: "No" };
const STATE_WORDS = { taken: "taken", left: "turned down" };

/** The cards of a group that fit: the open ones first (they ask), then the answered, at most `MAX_CARDS`. */
export const fitted = (items) => [...items.filter((x) => x.state === "open"), ...items.filter((x) => x.state !== "open")].slice(0, MAX_CARDS);

const rune = (n) => ({ name: n.element, hue: n.hue, dim: !n.element });

/** One big card of the say: `kind` a sign's name (or `kindNode`), `title` its line, `win` what its window holds (text or a node), `who` the head at its foot, `much` the word at the right, `open` it waits for the person (pressed it is lifted). */
export function SayCard({ n, id, kind = "", kindNode = null, title, win = null, who = null, much = "", open = false, onPress = null, group = "", label = "", extra = {} }) {
  const body = html`
    <${CornerTop} rune=${rune(n)} kind=${kind} kindNode=${kindNode} signal=${open ? "alert" : ""} />
    <span class="say-card__t" title=${title}>${title}</span>
    <span class="say-card__win">${typeof win === "string" ? html`<span class="say-card__line">${win}</span>` : win}</span>
    <${CornerFoot} who=${who ? { heads: [who] } : null} muchNode=${much ? html`<span class=${cls("corner__much", open && "is-ask")} data-much="say">${much}</span>` : null} />`;
  const props = { class: cls("ork-card say-card", { "is-alert": open, "is-done": !open && !!group && group !== "verdict" }), "data-say": id, "data-group": group, "data-state": open ? "open" : "answered", "aria-label": label || title, ...extra };
  return onPress ? html`<button type="button" ...${props} onClick=${onPress}>${body}</button>` : html`<span tabindex="0" role="group" ...${props}>${body}</span>`;
}

/** The leader's own card: its verdict's sign, what it says of the goal, its head in the window. */
export function VerdictCard({ n, l, head }) {
  const word = VERDICT_WORDS[l.verdict] || VERDICT_WORDS.doubt, title = l.why ? `${word}: ${l.why}` : word;
  return html`<${SayCard} n=${n} id=${`verdict:${l.party}`} group="verdict" kindNode=${html`<${Verdict} verdict=${l.verdict} />`} title=${title}
    win=${html`<span class="say-card__fig">${head && html`<${Head} race=${head.race} tier=${head.tier} size="big" />`}${l.instead && html`<span class="say-card__line">${l.instead}</span>`}</span>`}
    who=${head} label=${`${l.leader || l.party}'s verdict: ${title}`} />`;
}

/** A need's card: its kind's sign, its line, what it rests on in the window; open it asks you. */
export function NeedCard({ n, need, head, onPress }) {
  const open = need.state === "open", rests = need.rests_on ? `Rests on ${need.rests_on}` : "";
  return html`<${SayCard} n=${n} id=${need.id} group="needs" kind=${NEED_SIGN[need.kind] || "question"} title=${need.title || need.line} open=${open} onPress=${open ? onPress : null}
    win=${html`<span class="say-card__fig"><span class="say-card__line">${need.title ? need.line : rests || NEED_WORDS[need.kind] || ""}</span>${need.title && rests && html`<span class="say-card__rest">${rests}</span>`}</span>`}
    who=${head} much=${open ? ASKS : STATE_WORDS[need.state] || ""} extra=${{ "data-kind": need.kind }}
    label=${`${need.kind}: ${need.title || need.line}${open ? ", asks you" : `, ${STATE_WORDS[need.state] || ""}`}`} />`;
}

/** A better's card: its line, its weight at the foot. */
export function BetterCard({ n, better, head, onPress }) {
  const open = better.state === "open", weight = WEIGHT_WORDS[better.weight] || WEIGHT_WORDS.same;
  return html`<${SayCard} n=${n} id=${better.id} group="better" kind="tune" title=${better.line} open=${open} onPress=${open ? onPress : null}
    win=${html`<span class="say-card__fig"><${Sign} name="tune" big=${true} /></span>`} who=${head} much=${open ? weight : `${weight} · ${STATE_WORDS[better.state] || ""}`}
    extra=${{ "data-weight": better.weight || "same" }} label=${`Could be better: ${better.line}, ${weight}${open ? "" : `, ${STATE_WORDS[better.state] || ""}`}`} />`;
}

/** The open fork's card: what was taken disagrees, so it asks which way. */
export function ForkCard({ n, fork, onPress }) {
  return html`<${SayCard} n=${n} id=${fork.id} group="needs" kind="conflict" title=${fork.card.q} open=${true} onPress=${onPress}
    win=${html`<span class="say-card__fig"><span class="say-card__line">${(fork.card.choices || []).join(" · ")}</span></span>`} label=${`A conflict between what you took: ${fork.card.q}, asks you`} extra=${{ "data-kind": "fork" }} />`;
}
