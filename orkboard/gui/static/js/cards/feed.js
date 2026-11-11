// The feed the table of cards lays (goal 170 E, the talk of 11 November 2026): `ideas.feed` asked once a snapshot
// (realm/board_feed.py), kept as a signal, and cut by leader in the page; nothing sorted here that the reader sorted.
import { signal, effect } from "@preact/signals";
import { command, town } from "../link.js";
import { mapData } from "../shell/store.js";

export const feed = signal(null);
let asked = null;
effect(() => {
  const snap = town.value;
  if (!snap || snap === asked) return;
  asked = snap;
  command("ideas.feed", {}, true).then((r) => { feed.value = r || {}; }).catch(() => { feed.value = feed.peek() || {}; });
});

/** A leader's posts in the feed's order, what asks first: [{p, more}] (`more`: its stack under it). */
export function postsOf(leader) {
  const all = (feed.value?.posts || []).filter((s) => s.leader === leader).map((s) => ({ p: s.post, more: s.more || [] }));
  return [...all.filter((s) => s.p.asks), ...all.filter((s) => !s.p.asks)];
}

/** The Board's goals by slug (the map's nodes). */
export const nodes = () => mapData.value?.nodes || [];
export const nodeOf = (slug) => nodes().find((n) => n.slug === slug) || null;

/** What each leader said of a goal, from the feed's posts about it, the first of each leader (what asks first): [{leader, p, view}]. A concern is a
 *  risk, an ask a question, else for (the host answers no tokens yet; this is the contract proposed, docs/mockups/table-cards/). */
export function viewsOf(slug) {
  const seen = new Map();
  for (const s of feed.value?.posts || []) for (const p of [s.post, ...(s.more || [])]) {
    if (p.goal !== slug) continue;
    const view = p.asks ? "question" : p.kind === "concern" ? "risk" : "for", had = seen.get(p.leader);
    if (!had || (p.asks && !had.p.asks)) seen.set(p.leader, { leader: p.leader, p, view });
  }
  return [...seen.values()];
}

/** The leaders' views of a goal as tokens: [{leader, view}]. */
export const tokensOf = (slug) => viewsOf(slug).map(({ leader, view }) => ({ leader, view }));

/** A goal's share done, by its route's steps (0–1), or null when its route says nothing. */
export function shareOf(n) {
  const steps = (n?.route || []).filter((r) => r.total > 0);
  if (!steps.length) return null;
  return steps.reduce((a, r) => a + (r.done || 0), 0) / steps.reduce((a, r) => a + r.total, 0);
}
