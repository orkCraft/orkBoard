// The leaders' tables' state (goal 170, the talk of 11 November 2026; docs/mockups/frameworks/): what each leader's framework holds
// (`ideas.tables`, the host's: gui/ideas_mats.py), which of a party's faces is
// shown, and the person's own tokens. The person never moves a card: it turns one, spreads a pile, and asks its leader about a part.
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

/** The part a mat laid the table at (mat.js): {party, framework, card, p} (`p`: the leader's post, said at the table's head), or null. */
export const laidAt = signal(null);

/** Whether the card `id` of a table is the part a mat laid it at. */
export const isAt = (ctx, id) => { const a = laidAt.value; return !!a && a.party === ctx.party && a.framework === ctx.framework && a.card === id; };

/** Ask a leader about a part of its table (decisions §298.5: the person asks, never puts a token): `ideas.ask_leader {party, framework, card, text, sealed}`: the host gives the leader the question
 *  about that part of its table, a paid pass whose cost the field said before it ran (cards/askcost.js). */
export function askLeader({ party, framework, card, text }) {
  return command("ideas.ask_leader", { party, framework, card, text: text.trim(), sealed: true }, true).catch(() => {});
}
