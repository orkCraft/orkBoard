// A goal's questions as the hand holds them (docs/specs/100-a-goals-way-as-cards.md §2, decisions §153.5–§153.6, §158.1): the rows `talk` (a goal's Talk: `questions`), `cause` (a bug's diagnosis: the case cards `q`, then the guess)
// and `project_q` (the project's questions, a row of no goal's: `questions`) each hold question cards `{id, by, leader, q, choices, pick, why, project}` (realm/idea_questions.py `card`). The hand draws **one card a question**, a
// goal's questions one stack, the next on top when one is answered; the answers are sent together after the last (`ideas.talk_answer`, `ideas.project_answer`), and a bug's with the cause's answer (`ideas.cause_answer`).
// This module keeps the answers given and not yet sent (`given`), the rows sent and not yet gone from the Board (`sent`), makes the stops of the cards (`questionStops` for a talk and a cause row, `projectStops` for the project's),
// and sends. data.js `stopsOfProject` calls the two; the faces are questioncard.js and causecard.js; the cards are dealt over the pane by choose.js. Nothing here draws.
import { signal } from "@preact/signals";
import { say, toast } from "../link.js";
import { act } from "../shell/store.js";
import { ORKMASTER } from "../frame/state.js";
import { named } from "./todoform.js";

/** The answers given and not yet sent: `{<cardSig>: {pick: index} | {text}}`. */
export const given = signal({});
/** The rows sent and not yet gone from the Board (the host's snapshot takes them): `{<rowSig>: true}`. They are not dealt again meanwhile. */
export const sent = signal({});

/** A card's place in the answers: its row, its id and its question (a later round may reuse an id). */
export const cardSig = (scope, c) => `${scope}|${c.id}|${c.q}`;
/** A row's: its cards (and, for a bug, its guess), so that a new round is a new row. */
export const rowSig = (scope, cards, extra = "") => `${scope}|${(cards || []).map((c) => `${c.id}:${c.q}`).join("|")}|${extra}`;
/** The scope of a row: its kind and its goal (`talk/<idea>`, `cause/<idea>`), or the project's. */
export const scopeOf = (row) => (row?.kind === "project_q" ? "project_q" : `${row?.kind}/${row?.idea}`);
/** The cards a row holds. */
export const cardsOf = (row) => (row?.kind === "talk" || row?.kind === "project_q" ? row.questions : row?.kind === "cause" ? row.q : null) || [];
const sigOfRow = (row) => rowSig(scopeOf(row), cardsOf(row), row?.kind === "cause" ? row.cause : "");

/** The guess of a cause as the card says it: *I think …* (the host's words may already begin so). */
export const guessWords = (text) => (/^i think\b/i.test(String(text || "").trim()) ? String(text).trim() : `I think ${String(text || "").trim()}`);

// -- the stops --------------------------------------------------------------------------------------------------------------

const ownerOf = (ctx, slug, base) => ctx.party(slug) || base.party;

/** A question card as a stop of the hand: the row's stop with the card's question as its line, its asker's head and party. `kind` is the row's (`talk`, `cause`). */
function cardStop(base, c, scope, ctx) {
  const party = ownerOf(ctx, c.by, base);
  return { ...base, key: `${base.kind}/${scope}/${c.id}`, scope, card: c, ref: base.row, label: "Question", full: c.q, text: c.q, why: "", gem: "?", head: party?.head || base.head || null,
    party, other: ctx.open !== ORKMASTER && ctx.open !== party?.slug };
}

/** The stops of a stop `s`: a `talk` row's stop is one card a question not yet answered; a `cause` row's the case questions not yet answered, then the card of the guess; any other stop is itself.
 *  `ctx`: `{party(slug) -> {slug, name, head, lead}, open}`. Nothing of a row already sent. */
export function questionStops(s, ctx) {
  const row = s.row;
  if (row?.kind !== "talk" && row?.kind !== "cause") return [s];
  const scope = scopeOf(row), cards = cardsOf(row);
  if (sent.value[sigOfRow(row)]) return [];
  const asks = cards.filter((c) => !given.value[cardSig(scope, c)]).map((c) => cardStop({ ...s, kind: row.kind }, c, scope, ctx));
  if (row.kind === "talk") return asks;
  return [...asks, { ...s, kind: "cause", key: `cause/${row.idea}`, scope, ref: row, label: "Asks you", title: "The cause", full: s.title, text: guessWords(row.cause), why: "", gem: "?" }];
}

/** The project's questions (`project_q`, a row of no goal's): one stop a card not yet answered, under its leader's party's lane (`row.goal` is its party: data.js `laneOf`, `stackKey`), a question the work does
 *  not wait for. `rows`: the Needs you rows. `ctx`: as above, and `goal(slug)` the party's map entry, `ork` the Orkmaster's head. */
export function projectStops(rows, ctx) {
  const out = [];
  for (const row of rows.filter((r) => r.kind === "project_q")) {
    const scope = scopeOf(row), cards = cardsOf(row);
    if (sent.value[sigOfRow(row)]) continue;
    const g = ctx.goal(row.party), party = ctx.party(row.party)
      || { slug: "", name: "Orkmaster", head: ctx.ork ? { race: ctx.ork.race || "peon", tier: ctx.ork.tier || "crown" } : null, lead: "Orkmaster" };
    for (const c of cards.filter((x) => !given.value[cardSig(scope, x)])) {
      out.push({ key: `project_q/${c.id}`, kind: "project_q", scope, card: c, ref: row, row: { ...row, goal: row.party, idea: undefined }, node: null, task: null, label: "Project question", gem: "?", tone: "alert",
        gemTip: "A question costs nothing", head: party.head, small: true, whoTip: "", title: "The project", full: c.q, text: c.q, why: "", g: g || null, party, other: ctx.open !== ORKMASTER && ctx.open !== party.slug });
    }
  }
  return out;
}

// -- the answers --------------------------------------------------------------------------------------------------------------

/** Keeps an answer: a pick (an index of the card's choices) or the person's own words. */
export function give(scope, card, answer) {
  given.value = { ...given.value, [cardSig(scope, card)]: answer };
}

/** The pick of each of the cards not answered yet, kept as answered (a bug's *Let … decide*, whose guess is still the person's). */
export function givePicks(scope, cards) {
  given.value = { ...given.value, ...Object.fromEntries(cards.filter((c) => !given.value[cardSig(scope, c)]).map((c) => [cardSig(scope, c), { pick: c.pick }])) };
}

const answersOf = (row) => cardsOf(row).flatMap((c) => { const a = given.value[cardSig(scopeOf(row), c)]; return a ? [{ id: c.id, ...a }] : []; });

/** Takes a row back when the host refused: its cards are dealt again. */
function undo(row) {
  const { [sigOfRow(row)]: _gone, ...rest } = sent.value;
  sent.value = rest;
  const mine = new Set(cardsOf(row).map((c) => cardSig(scopeOf(row), c)));
  given.value = Object.fromEntries(Object.entries(given.value).filter(([k]) => !mine.has(k)));
}

/** Sends a talk row's or the project's answers together (`decide`: *Let … decide*, the rest answered with the picks). The row is not dealt again meanwhile; the host's refusal deals it again. */
export async function sendRow(row, lead, decide = false) {
  const answers = answersOf(row);
  sent.value = { ...sent.value, [sigOfRow(row)]: true };
  const got = row.kind === "project_q" ? await act("ideas.project_answer", { answers, ...(decide ? { decide: true } : {}) })
    : await act("ideas.talk_answer", { idea: row.idea, answers, ...(decide ? { decide: true } : {}) });
  if (!got) { undo(row); return null; }
  toast(say(row.kind === "project_q" ? "Kept: the answers are the project’s." : decide ? `Sent: ${named(lead)} decides.` : `Sent: ${named(lead)} reads the answers.`));
  return got;
}

/** Sends a bug's cause answered (`yes`, and `text` for *No, it's elsewhere* and *Other…*) with the case questions' answers. */
export async function sendCause(row, lead, yes, text = "") {
  const answers = answersOf(row);
  sent.value = { ...sent.value, [sigOfRow(row)]: true };
  const got = await act("ideas.cause_answer", { idea: row.idea, yes, ...(text ? { text } : {}), answers });
  if (!got) { undo(row); return null; }
  toast(say(`Sent: ${named(lead)} reads the answers.`));
  return got;
}
