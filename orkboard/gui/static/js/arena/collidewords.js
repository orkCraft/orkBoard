// Two parties' goals that change the same thing, and a goal that waits for another party's (docs/specs/71-orkmaster-keeps-parties-apart.md §6, §8, decisions §86), in words: pure functions over the
// Needs you row of kind `collide`, the map node's `waits_for` and `project.collisions`. A host from before spec 71 sends none of them, and every function here says nothing then. No signal, no template.
// The code's goal is a party and its idea is a goal; a person reads *party* and *goal*.

export const KIND = "Orkmaster asks";

/** The goals a collide row is about: [{idea, party, party_name, title, element}], the goal whose spec changed first (`by: "change"`). */
export const goalsOfRow = (row) => row?.collide?.goals || [];

/** One goal as the stop says it: *Backend · Auth API*. */
export const goalLine = (g) => `${g.party_name || g.party} · ${g.title}`;

/** An answer of a collide stop as a button: {answer, text, tip, primary}. *first:<slug>* is *<one> first*, *one* is *One goal*, *leave* *Leave it*, *replan* *Re-plan it* — each says what happens in its title.
 *  The one the judge suggested first is the primary button; with none suggested, the first answer is. */
export function answersOf(row) {
  const c = row?.collide || {}, goals = c.goals || [], by = (slug) => goals.find((g) => g.idea === slug);
  return (c.answers || []).map((a, i) => {
    const at = a.startsWith("first:") ? a.slice(6) : "", one = by(at), other = goals.find((g) => g.idea !== at);
    const primary = at ? at === c.first : !c.first && i === 0;
    if (at) return { answer: a, primary, text: `${one?.title || at} first`, tip: `${other ? `«${other.title}»` : "The other goal"} waits until «${one?.title || at}» is done and flagged, then it starts` };
    if (a === "one") return { answer: a, primary, text: "One goal", tip: "The later goal’s text joins the earlier one as a change, and the later goal is dropped" };
    if (a === "replan") return { answer: a, primary, text: "Re-plan it", tip: `${row.title ? `«${row.title}»` : "The goal"}’s leader re-plans what is left, told what changed` };
    if (a === "leave") return { answer: a, primary, text: "Leave it", tip: "Both goals stay as they are; this pair is not asked about again" };
    return { answer: a, primary, text: a, tip: "" };
  });
}

/** The open waits of a goal: the ones whose flag is not raised yet. */
export const waitsOf = (n) => (n?.waits_for || []).filter((w) => !w.flag);

/** *waits for Backend · Auth API* (more than one: joined with a comma); "" for a goal that waits for none. */
export function waitsForWords(n) {
  const w = waitsOf(n);
  return w.length ? `waits for ${w.map((x) => `${x.party_name || x.party} · ${x.title}`).join(", ")}` : "";
}

/** The links the Orkmaster draws on the project's level: [{key, from, to, kind}], a collision (`collide`: between its two decks, no direction) for each open one, and a wait (`wait`: from the goal waited
 *  for to the one that waits). Only between goals the map has; one named twice is drawn once. */
export function orkLinks(collisions, nodes) {
  const party = new Map(nodes.map((n) => [n.slug, n.goal])), seen = new Set(), out = [];
  const add = (key, from, to, kind) => { if (!seen.has(key) && party.has(from) && party.has(to) && from !== to) { seen.add(key); out.push({ key, from, to, kind }); } };
  for (const c of collisions || []) add(`collide:${c.id}`, c.a, c.b, "collide");
  for (const n of nodes) for (const w of waitsOf(n)) add(`wait:${w.goal}>${n.slug}`, w.goal, n.slug, "wait");
  return out;
}
