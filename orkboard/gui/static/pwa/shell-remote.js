// The phone's way through the project's remote (docs/specs/136-the-phone-through-the-projects-remote.md C, decisions §243): the repository and its token kept on this phone, checked
// when they are given, and what comes of them: the journal read (shell-remote-journal.js), the goals and answers written to the inbox (shell-remote-send.js). This module is the one
// object the frame makes (`makeRemote`) and hands the page through `globalThis.orkboardPhone.remote`; the token stays inside it and goes to GitHub's API alone. It draws nothing
// (shell-remote-settings.js and shell-remote-view.js do) and imports no library, so a test runs it with a fake `fetch` and a fake storage.
import { client, cleanRepo } from "./shell-remote-api.js";
import { makeKeep } from "./shell-remote-keep.js";
import { journalPart } from "./shell-remote-journal.js";
import { sendPart } from "./shell-remote-send.js";
import * as say from "./shell-remote-words.js";

export const clock = (ms) => new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/** `device()`: the pairing `{id, …}` or null. `fetch`, `storage`, `now`, `sleep` are the browser's; a test gives its own. */
export function makeRemote({ fetch: fetcher = globalThis.fetch?.bind(globalThis), storage, device = () => null, now = Date.now, sleep } = {}) {
  const keep = makeKeep(storage);
  const listeners = new Set();
  const me = { limitUntil: 0, refused: false };           // GitHub asked us to wait till …; the token was refused
  const emit = () => { for (const fn of listeners) { try { fn(); } catch { /* a listener's own */ } } };
  const open = (repo, token) => client({ fetch: fetcher, repo, token, now, sleep });

  const remote = {
    keep, say, now, emit, me,
    /** Whether a repository and a token are set: goals and the journal can go through them. */
    ready() { const s = keep.settings(); return Boolean(s.repo && s.token); },
    /** What Settings shows: the repository and whether a token is kept (never the token). */
    settings() { const s = keep.settings(); return { repo: s.repo, token: Boolean(s.token) }; },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
    /** The id of this phone in the inbox: the pairing's, else one of its own. */
    phone() { return keep.phone(device()?.id || ""); },
    /** The api for the repository set, or null. */
    api() { const s = keep.settings(); return s.repo && s.token ? open(s.repo, s.token) : null; },

    /** The computer told the repository at pairing (`/api/pair`'s `remote`): it fills the field when the person has not set one. */
    prefill(repo) { const r = cleanRepo(repo); if (r && !keep.settings().repo) { keep.setSettings({ repo: r }); emit(); } },

    /** A line to say now about GitHub's limits or the token, or "": *GitHub asks us to wait till 14:30*, *The token was refused: give a new one in Settings*. */
    line() {
      if (me.refused) return say.REFUSED;
      return me.limitUntil > now() ? say.waitTill(clock(me.limitUntil)) : "";
    },
    /** What a failed call to GitHub means for the lines above (the caller still has the error). */
    noted(e) {
      if (e?.kind === "limit") me.limitUntil = e.until;
      else if (e?.kind === "token") me.refused = true;
      emit();
      return e;
    },
    /** GitHub's calls are stopped for now (a limit said wait). */
    waiting() { return me.limitUntil > now(); },

    /**
     * The repository and its token, given: `GET /repos/{owner}/{repo}` says whether it is private and whether the token can write (C.2). Kept only when both hold.
     * `token` blank keeps the one held (the repository alone changed). `{ok, line}`.
     */
    async save({ repo, token }) {
      const name = cleanRepo(repo), held = keep.settings(), secret = String(token || "").trim() || held.token;
      if (!name) return { ok: false, line: say.NO_REPO };
      if (!secret) return { ok: false, line: say.NO_TOKEN };
      let info;
      try {
        info = await open(name, secret).info();
      } catch (e) {
        if (e.kind === "token") return { ok: false, line: say.REFUSED };
        if (e.kind === "limit") { remote.noted(e); return { ok: false, line: remote.line() }; }
        if (e.kind === "missing") return { ok: false, line: say.NOT_FOUND };
        return { ok: false, line: e.kind === "network" ? say.OFFLINE_CHECK : e.message };
      }
      if (!info.private) return { ok: false, line: say.PUBLIC };
      if (!info.push) return { ok: false, line: say.NO_WRITE };
      keep.setSettings({ repo: name, token: secret });
      me.refused = false;
      emit();
      return { ok: true, line: say.READY };
    },

    /** *Remove*: the token is forgotten at once, and the journal read with it. What waits to be sent stays, kept without it. */
    forget() { keep.forget(); me.refused = false; emit(); },
    /** Unpairing: everything of the remote is forgotten on this phone. */
    wipe() { keep.wipe(); me.refused = false; me.limitUntil = 0; emit(); },
  };
  journalPart(remote);
  sendPart(remote);
  return remote;
}
