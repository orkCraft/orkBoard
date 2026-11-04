// What the phone writes to the project's inbox (docs/specs/136 C.5–C.6, spec 137 C, decisions §243.2, §244.5): a goal as `inbox/<device>/<id>.json` with its photos beside it
// (`<id>.<n>.jpg`, written first, so the computer never reads a goal without its pictures), an answer to a card of the hand as `<id>.answer.json` (pwa/shell-answer-file.js builds
// its path and body), both through the same writer: files only added, the branch made on the first, a 409 tried again. With no network, or GitHub asking to wait, it is kept in the
// app's storage (the outbox) and sent when the network comes back: the card says *Waits for the network*. Nothing is ever edited or removed in the repository.
import { RemoteError } from "./shell-remote-api.js";
import { answerFile, newId } from "./shell-answer-file.js";
import { NO_ROOM, REFUSED, SET_REPO } from "./shell-remote-words.js";

export const MAX_PHOTOS = 4;                   // realm/remote_inbox.py: at most four, each at most 2 MB
export const MAX_PHOTO_BYTES = 2 * 1024 * 1024;

/** The hand's commands that answer a card, and the kind of card each answers (realm/remote_answers.py `KINDS`). */
export const ANSWER_KINDS = {
  "ideas.talk_answer": "talk", "ideas.cause_answer": "cause", "ideas.throw": "hearing", "ideas.fork_answer": "fork", "ideas.confirm": "decision",
  "ideas.project_answer": "project_q", "ideas.revise_answer": "change", "ideas.party_answer": "party", "ideas.proposal": "proposal", "ideas.collide_answer": "collide",
};

/** The time with the phone's own offset (`2026-11-04T14:02:11+01:00`). */
export function isoLocal(date) {
  const p = (n, w = 2) => String(Math.trunc(Math.abs(n))).padStart(w, "0"), off = -date.getTimezoneOffset();
  return `${date.getFullYear()}-${p(date.getMonth() + 1)}-${p(date.getDate())}T${p(date.getHours())}:${p(date.getMinutes())}:${p(date.getSeconds())}`
    + `${off < 0 ? "-" : "+"}${p(off / 60)}:${p(off % 60)}`;
}

/** A picture as the inbox keeps it: the base64 of a data URL's JPEG, or null for anything else or a picture over the limit. */
export function photoOf(url) {
  const m = /^data:image\/jpe?g;base64,([A-Za-z0-9+/=]+)$/.exec(String(url || ""));
  return m && Math.floor(m[1].length * 3 / 4) <= MAX_PHOTO_BYTES ? m[1] : null;
}

/** The pictures of an answer or a goal that fit the inbox's limits (`photos` as `ideas.add` takes them: data URLs). */
const pictures = (list) => (Array.isArray(list) ? list : []).map(photoOf).filter(Boolean).slice(0, MAX_PHOTOS);

export function sendPart(r) {
  const { keep, now } = r;
  let flushing = false, told = false;
  const onLine = () => globalThis.navigator?.onLine !== false;

  /** Writes one item: its photos, then its file. Throws a `RemoteError`. */
  async function deliver(item) {
    const api = r.api();
    if (!api) throw new RemoteError("token", REFUSED);
    for (const p of item.photos || []) await api.add(p.path, { base64: p.base64 });
    await api.add(item.path, { text: JSON.stringify(item.body) });
  }

  function remember(item) {
    keep.setSent([...keep.sent().filter((s) => s.id !== item.id), { id: item.id, kind: item.kind, text: item.text || "", at: now() }]);
  }

  /** The item is written now, or kept for the network; `{ok, kept?, error?}`. */
  async function put(item) {
    if (!r.ready()) return { ok: false, error: SET_REPO };
    if (!onLine()) return queue(item);
    try {
      await deliver(item);
    } catch (e) {
      if (e.kind === "network" || e.kind === "limit") { r.noted(e); return queue(item); }
      r.noted(e);
      return { ok: false, error: e.kind === "token" ? REFUSED : e.message };
    }
    remember(item);
    r.emit();
    return { ok: true, id: item.id };
  }

  function queue(item) {
    const before = keep.outbox();
    if (!keep.setOutbox([...before, { ...item, key: item.id }])) { keep.setOutbox(before); return { ok: false, error: NO_ROOM }; }
    r.emit();
    return { ok: true, kept: true, id: item.id };
  }

  Object.assign(r, {
    /** *Set your repository in Settings to send goals while your computer is away*: the line the first time it is needed, "" after. */
    hint() { if (r.ready() || told) return ""; told = true; return SET_REPO; },
    online: onLine,

    /**
     * A goal written to the inbox: `{text, party, element, type, asks, marks, photos}` as the + card has them. `{ok, id}` sent, `{ok, kept: true}` kept for the network,
     * `{ok: false, error}` not sent (the words stay with the person).
     */
    async sendGoal(goal) {
      const text = String(goal?.text || "").trim();
      if (!text) return { ok: false, error: "Write the goal first" };
      const id = newId(now()), device = r.phone(), shots = pictures(goal.photos);
      const photos = shots.map((base64, i) => ({ path: `inbox/${device}/${id}.${i + 1}.jpg`, base64 }));
      const body = { v: 1, id, device, at: isoLocal(new Date(now())), text,
        ...(goal.element ? { element: goal.element } : {}), ...(goal.party ? { party: goal.party } : {}), ...(goal.type ? { type: goal.type } : {}), ...(goal.asks ? { asks: goal.asks } : {}),
        marks: Array.isArray(goal.marks) ? goal.marks : [], photos: photos.map((p) => p.path.split("/").pop()) };
      const got = await put({ id, kind: "goal", text, at: now(), path: `inbox/${device}/${id}.json`, body, photos });
      return { ...got, photos: shots.length };
    },

    /** Whether the hand's command `name` can be answered through the inbox (a card of a kind a phone answers). */
    answers: (name) => name in ANSWER_KINDS,

    /** An answer to a card of the hand, from the command the page would have sent: `{ok, id}`, `{ok, kept}` or `{ok: false, error}`. */
    async sendAnswer(name, args = {}) {
      const kind = ANSWER_KINDS[name];
      if (!kind) return { ok: false, error: "A phone does not answer this kind of card" };
      const row = { kind, idea: args.idea || args.slug, goal: args.goal, ...(kind === "fork" ? { id: args.id } : {}), ...(kind === "collide" ? { collide: { id: args.id } } : {}) };
      const id = newId(now()), file = answerFile(row, args, { device: r.phone(), id, at: isoLocal(new Date(now())) });
      if (!file) return { ok: false, error: "A phone does not answer this kind of card" };
      return put({ id, kind: "answer", text: "", at: now(), path: file.path, body: file.body, photos: [] });
    },

    /** What waits for the network is sent, one by one, oldest first; it stops at the first the network or GitHub's limit refuses. `{sent, left}`. */
    async flush() {
      if (flushing || !r.ready() || r.waiting() || !onLine()) return { sent: 0, left: keep.outbox().length };
      flushing = true;
      let sent = 0;
      try {
        for (const item of keep.outbox().filter((x) => !x.error)) {
          try {
            await deliver(item);
          } catch (e) {
            r.noted(e);
            if (e.kind === "network" || e.kind === "limit" || e.kind === "token") break;
            keep.setOutbox(keep.outbox().map((x) => (x.key === item.key ? { ...x, error: e.message } : x)));        // refused for good: said, not tried again
            continue;
          }
          keep.setOutbox(keep.outbox().filter((x) => x.key !== item.key));
          remember(item);
          sent += 1;
        }
      } finally {
        flushing = false;
        r.emit();
      }
      return { sent, left: keep.outbox().length };
    },
  });
}
