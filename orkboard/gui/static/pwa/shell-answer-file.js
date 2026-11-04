// The phone's answer to a card of the hand, as a file of the project's inbox (docs/specs/137 C, decisions §244.5):
// `inbox/<device>/<id>.answer.json` = {v: 1, id, device, at, card, kind, answer}. The computer that holds the Board takes it as it takes a goal
// (realm/remote_answers.py) and runs the hand's own command with `answer` — the arguments that command takes for that kind of card. What names
// the card (the goal, a fork's id) is the computer's to find from `card` and `kind`, so only the answer's own keys are written here.
// `KINDS` is realm/remote_answers.py's, key for key (tests/test_remote_answers_js.py keeps the two together).
// The writing itself (the repository's API, the token, the outbox) is spec 136 C's: this module makes the file and says where it goes.

export const KINDS = {
  talk: ["answers", "decide"],
  cause: ["yes", "text", "answers"],
  hearing: ["dir", "text"],
  fork: ["side", "text"],
  decision: ["text"],
  project_q: ["answers", "decide"],
  change: ["take"],
  party: ["take", "reason"],
  proposal: ["take", "priority", "reason"],
  collide: ["answer"],
};

/** The id a card of the hand is named by: its own `id` (a fork's), a stop's (`collide.id`), else its goal's (`idea`), else its party's (`goal`). */
export function cardKey(row) {
  const stop = row && typeof row.collide === "object" && row.collide ? row.collide : {};
  for (const v of [row && row.id, stop.id, row && row.idea, row && row.goal]) if (typeof v === "string" && v) return v;
  return "";
}

const ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";

/** An id that sorts by time (26 characters of Crockford's alphabet: 10 of the clock, 16 of chance), as the goals' files have. */
export function newId(now = Date.now(), random = Math.random) {
  let t = "", n = Math.floor(now);
  for (let i = 0; i < 10; i++) { t = ALPHABET[n % 32] + t; n = Math.floor(n / 32); }
  let r = "";
  for (let i = 0; i < 16; i++) r += ALPHABET[Math.floor(random() * 32)];
  return t + r;
}

/** `{path, body}` for the answer to `row` (a card of the hand) with the hand's command's arguments `args`, or null for a kind a phone does not
 *  answer through the inbox. Only the answer's own keys of that kind are kept. */
export function answerFile(row, args, { device, id = newId(), at = new Date().toISOString() }) {
  const keys = row && KINDS[row.kind];
  if (!keys || !device || !/^[A-Za-z0-9._-]+$/.test(device)) return null;
  const answer = {};
  for (const k of keys) if (args && k in args) answer[k] = args[k];
  return { path: `inbox/${device}/${id}.answer.json`, body: { v: 1, id, device, at, card: cardKey(row), kind: row.kind, answer } };
}
