// The journal, read from the project's remote (docs/specs/136 C.3–C.4, decisions §243.5): `status.json` of `orkboard/journal` through GitHub's API with the ETag last given, so a read
// with nothing new answers 304 and costs nothing; every minute while the app is open and seen, never in the background, and only while the computer is not reached (on the same network
// the live Board is the truth). What it keeps is what the journal said and when it was *written*: a screen says *As of 14:02*, never as if it were now. The goals this phone sent and
// the journal has not named wait face down (*Waiting to be taken*); one taken with an error says the error's words.
import { asOf } from "./shell-remote-words.js";

export const EVERY_MS = 60_000;                // the journal is asked this often (C.3)

/** *14:02* from the journal's `written` (the computer's own clock, as it wrote it), else "". */
export function writtenClock(written) {
  const m = /T(\d\d:\d\d)/.exec(String(written || ""));
  return m ? m[1] : "";
}

/** The goals of this phone that are not on the Board yet, for the face-down cards: [{id, text, state: "waiting" | "network" | "taken" | "error", error}]. `taken` is the journal's list. */
export function waitingOf({ sent = [], outbox = [], taken = [] }) {
  const by = new Map(taken.map((t) => [t.id, t]));
  const out = [];
  for (const item of outbox) if (item.kind === "goal") out.push({ id: item.id, text: item.text, state: item.error ? "error" : "network", error: item.error || "" });
  for (const s of sent) {
    if (s.kind !== "goal" || outbox.some((o) => o.id === s.id)) continue;
    const t = by.get(s.id);
    if (!t) out.push({ id: s.id, text: s.text, state: "waiting", error: "" });
    else if (t.error) out.push({ id: s.id, text: s.text, state: "error", error: String(t.error) });
    else if (!t.slug) out.push({ id: s.id, text: s.text, state: "taken", error: "" });
  }
  return out;
}

/** The answers sent that the computer took with an error: [{id, error}] (a card gone, or answered already). */
export function answersRefused({ sent = [], taken = [] }) {
  const by = new Map(taken.map((t) => [t.id, t]));
  return sent.filter((s) => s.kind === "answer" && by.get(s.id)?.error).map((s) => ({ id: s.id, error: String(by.get(s.id).error) }));
}

export function journalPart(r) {
  const { keep, now } = r;
  let busy = false, timer = 0, gates = null;

  Object.assign(r, {
    /** What the journal last said, `{data, written: "14:02", at}`, or null (none read yet). */
    journal() {
      const held = keep.journal();
      return held?.data ? { data: held.data, written: writtenClock(held.data.written), at: held.at } : null;
    },
    /** *As of 14:02*, or "". */
    asOf() { const j = r.journal(); return j?.written ? asOf(j.written) : ""; },
    /** What the screens draw: the journal's parties and failed goals, and this phone's goals not yet on the Board. */
    view() {
      const j = r.journal();
      if (!j) return null;
      const taken = Array.isArray(j.data.taken) ? j.data.taken : [];
      const parties = (Array.isArray(j.data.parties) ? j.data.parties : []).map((p) => ({ slug: String(p.slug || ""), title: String(p.title || p.slug || ""), goals: Array.isArray(p.goals) ? p.goals : [] }));
      return { asOf: asOf(j.written), written: j.written, parties, failed: Array.isArray(j.data.failed) ? j.data.failed : [],
               waiting: waitingOf({ sent: keep.sent(), outbox: keep.outbox(), taken }), refused: answersRefused({ sent: keep.sent(), taken }), line: r.line() };
    },

    /** One read. `{read: true, changed}` or `{read: false, why}`; a failure is said by `line()` (a limit, a refused token) and changes nothing shown. */
    async poll() {
      if (!r.ready()) return { read: false, why: "not set" };
      if (r.waiting()) return { read: false, why: "limit" };
      if (busy) return { read: false, why: "busy" };
      busy = true;
      try {
        const held = keep.journal();
        const got = await r.api().journal(held?.etag || "");
        r.me.refused = false;
        if (got.changed && got.data) { keep.setJournal(got.etag, got.data, now()); prune(got.data); }
        r.emit();
        return { read: true, changed: Boolean(got.changed) };
      } catch (e) {
        r.noted(e);
        return { read: false, why: e.kind || "failed" };
      } finally {
        busy = false;
      }
    },

    /**
     * Reads now and then every minute while `reached()` is false and `seen()` is true (the app is open and visible): the first read is at once, when the link to the computer fails.
     * Returns nothing; `stopWatching()` ends it. `kick()` is the same decision taken now (the link failed, the app came back to the screen).
     */
    watch({ reached, seen, every = EVERY_MS }) {
      r.stopWatching();
      gates = { reached, seen };
      timer = setInterval(() => { if (gates?.seen()) { r.flush?.(); r.kick(); } }, every);
    },
    kick() { if (gates && !gates.reached() && gates.seen()) return r.poll(); return Promise.resolve({ read: false, why: "not now" }); },
    stopWatching() { clearInterval(timer); timer = 0; gates = null; },
  });

  /** What the journal now names is no longer waited for: a goal laid on the Board, an answer taken without a word against it. */
  function prune(data) {
    const taken = new Map((Array.isArray(data.taken) ? data.taken : []).map((t) => [t.id, t]));
    const left = keep.sent().filter((s) => { const t = taken.get(s.id); return !t || t.error || (s.kind === "goal" && !t.slug); });
    keep.setSent(left);
  }
}
