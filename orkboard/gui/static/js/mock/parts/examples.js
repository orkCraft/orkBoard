// The examples laid over the recording (goal 170, stage T): this repository's Board is quiet, so nothing waits for main or
// dev, nothing is to review and nothing waits for the person. These lay a few, each marked " · example" in its name, so the
// discard, the gate, the dealer's wait and a leader's ask can be pressed. What the host does not answer yet (a post's words
// before it changed) is the contract proposed (docs/mockups/table-cards/).
import { EXAMPLE, ensure, latest, reply } from "./kit.js";

export function lay(data) {
  const now = new Date(), at = (h, m) => { const d = new Date(now); d.setHours(h, m, 0, 0); return d.toISOString(); };
  const mark = (n) => { if (!n.title.endsWith(EXAMPLE)) { n.title += EXAMPLE; n.short = (n.short || n.title) + EXAMPLE; } return n; };
  // two goals done in dev that wait for main, one done and not yet seen, one waiting for dev
  const [m1, m2, seen, wait] = latest(data, "done", 4).map(mark);
  for (const n of [m1, m2, seen, wait]) n.place = "discard";
  const gate = ensure(data, "ideas.gate", { into: "dev", main: "main", same: false, commits: 0, files: 0, ideas: [] });
  Object.assign(gate, { commits: 6, files: 11, ideas: [m1, m2].map((n) => ({ slug: n.slug, title: n.title, goal: n.goal })) });
  const board = reply(data, "ideas.board")?.result;
  if (board) { board.review = true; board.ideas = [...(board.ideas || []), { slug: wait.slug, waits_for_dev: true }]; }
  // one goal at work comes to review: the gate can be opened from it
  const [rev] = latest(data, "ready", 1).map(mark);
  if (rev) rev.state = "review";
  // the dealer's wait, a leader's ask and a change with its words before it, in the feed
  const feed = ensure(data, "ideas.feed", { since: "", heads: [], waits: [], posts: [], seen: null });
  const [talk] = latest(data, "talk", 1);
  if (talk) feed.waits = [{ kind: "starts", goal: talk.slug, short: (talk.short || talk.title) + EXAMPLE, leader: "orkmaster", at: at(13, 40),
    acts: [{ act: "change_spec", command: "ideas.spec_change", args: { idea: talk.slug } }, { act: "start_now", command: "ideas.start_now", args: { slug: talk.slug } }] }];
  const goal = talk?.slug || m1.slug;
  feed.posts = [
    { leader: "tech", post: { leader: "tech", at: at(11, 58), kind: "concern", goal, asks: true, text: "Which way does the table open first, the lanes or the dealer?" + EXAMPLE, acts: [] }, more: [] },
    { leader: "design", post: { leader: "design", at: at(10, 5), kind: "change", goal, text: "The lanes keep a card's ratio; a post lies on its side, an open card stands up." + EXAMPLE,
      before: "The lanes draw a post as tall as its words; an open post is a drawer.", acts: [] }, more: [] },
    ...(feed.posts || []),
  ];
  // the same question waits in the hand (decisions §145): a goal's open question, as the host keeps it in the Board's needs;
  // the hand draws one card a goal, so it joins the goal's own card when the goal already waits there
  const ask = { id: "page-example", by: "claude-code", leader: "architect", q: "Which way does the table open first, the lanes or the dealer?" + EXAMPLE,
    choices: ["The lanes first", "The dealer first", "Both at once"], pick: 0, why: "Tech's view: the lanes are what is read most" + EXAMPLE, project: false,
    kinds: ["take", "take", "other"], lines: ["The leaders' words are seen first", "What waits is seen first", "Both stand at once, the lanes narrower"] };
  if (board && talk) {
    const needs = board.needs_you || [], had = needs.find((x) => x.idea === talk.slug);
    if (had) had.questions = [ask, ...(had.questions || [])];
    else board.needs_you = [{ idea: talk.slug, goal: talk.goal || "tech", title: talk.title, priority: "normal", blocks: false, at: at(11, 58), kind: "talk", round: 1,
      stances: [], text: ask.q, outside: true, questions: [ask] }, ...needs];
  }
  feed.heads = (feed.heads || []).map((h) => (h.leader === "tech" ? { ...h, asks: true, news: true } : h));
}
