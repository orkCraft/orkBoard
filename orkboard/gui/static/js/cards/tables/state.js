// The leaders' tables' state (goal 170, the talk of 11 November 2026; docs/mockups/frameworks/): what each leader's framework holds
// (`ideas.tables`, proposed: the host does not answer it yet, the mock lays it, js/mock/parts/tables.js), which of a party's faces is
// shown, and the person's own tokens. The person never moves a card: it turns one, spreads a pile, and puts a token (a question or a concern).
import { signal, effect } from "@preact/signals";
import { command, town } from "../../link.js";

/** What every party holds: {party slug: {framework id: its cards}}, or null before it is asked (and when the host has none). */
export const tables = signal(null);
let asked = null;
effect(() => {
  const snap = town.value;
  if (!snap || snap === asked) return;
  asked = snap;
  command("ideas.tables", {}, true).then((r) => { tables.value = r && typeof r === "object" ? r : {}; }).catch(() => { tables.value = {}; });
});

export const FRAMEWORKS = { architecture: "Architecture", jtbd: "Jobs to be done" };

/** A party's framework `{id, name, data}`, or null when it has none: a lane's switch is drawn only for a party with one. */
export function frameworkOf(g) {
  const t = tables.value?.[g?.slug], id = t && Object.keys(t).find((k) => FRAMEWORKS[k]);
  return id ? { id, name: FRAMEWORKS[id], data: t[id] } : null;
}

/** Which party's table is laid in the pane in place of the lanes: a party slug, or "" for the lanes (Feed). */
export const laid = signal("");

/** The person's token held in the hand ("question" or "concern", "" none), the card it is about to be put on, and the tokens put. */
export const held = signal("");
export const asking = signal(null);                     // {party, framework, card, name}
export const placed = signal([]);                       // [{party, framework, card, name, view, text, at}]

export const WORDS = { question: { mark: "?", word: "Question" }, concern: { mark: "!", word: "Concern" } };

/** Put the person's token on a card: kept here, and the command it would be is sent (the mock logs it: `ideas.table_token`, proposed;
 *  the host is to take {party, framework, card, view, text} and give the token to the leader, marking that part of its table). */
export function putToken({ party, framework, card, name, view, text }) {
  const t = { party, framework, card, name, view, text: text.trim(), at: new Date().toISOString() };
  placed.value = [...placed.value, t];
  held.value = "";
  asking.value = null;
  command("ideas.table_token", { party, framework, card, view, text: t.text }, true).catch(() => {});
  return t;
}
