// What the phone keeps of its way through the remote, in the app's own storage (docs/specs/136 C.1, decisions §243.7): the repository and its token (until the native frame's
// keychain, spec 103), the journal last read with its ETag, the goals this phone sent and the ones that wait for the network. Every read and write is guarded: a private window,
// a full phone or blocked storage leave the page working with what it holds in memory. `wipe()` forgets all of it (unpairing); `forget()` only the token.
// The keys follow the app's other ones (`orkcraft.*`, js/linkpaired.js); the outbox is its own, since the app's `orkcraft.outbox` is sent to the computer.

const SETTINGS = "orkcraft.remote", OUTBOX = "orkcraft.remote.outbox", SENT = "orkcraft.remote.sent", JOURNAL = "orkcraft.remote.journal";
const SENT_DAYS = 30, SENT_MAX = 50, OUTBOX_MAX = 50;

export function makeKeep(storage = globalThis.localStorage) {
  const mem = new Map();
  const read = (key, fallback) => {
    try { const raw = storage?.getItem(key); if (raw !== null && raw !== undefined) return JSON.parse(raw); } catch { /* the memory's */ }
    return mem.has(key) ? mem.get(key) : fallback;
  };
  /** False when this phone had no room to keep it (it is held in memory for this run all the same). */
  const write = (key, value) => {
    mem.set(key, value);
    try { storage.setItem(key, JSON.stringify(value)); return true; } catch { return false; }
  };
  const drop = (key) => { mem.delete(key); try { storage?.removeItem(key); } catch { /* nothing kept */ } };

  const keep = {
    /** `{repo, token, phone}`: the repository as owner/name, its token, and an id of this phone's own (made once; the pairing's id is the device's when it has one). */
    settings: () => ({ repo: "", token: "", phone: "", ...(read(SETTINGS, {}) || {}) }),
    setSettings(patch) { return write(SETTINGS, { ...keep.settings(), ...patch }); },
    forget() { const s = keep.settings(); write(SETTINGS, { ...s, token: "" }); drop(JOURNAL); },
    /** The id of this phone for the inbox (`inbox/<device>/…`): the pairing's, else one of its own. */
    phone(paired = "") {
      if (/^[A-Za-z0-9._-]{1,64}$/.test(paired)) return paired;
      const s = keep.settings();
      if (s.phone) return s.phone;
      const id = "phone-" + Array.from(crypto.getRandomValues(new Uint8Array(6)), (b) => b.toString(16).padStart(2, "0")).join("");
      keep.setSettings({ phone: id });
      return id;
    },

    /** The journal last read: `{etag, data, at}` (`at` the ms it was read), or null. */
    journal: () => read(JOURNAL, null),
    setJournal(etag, data, at) { return write(JOURNAL, { etag, data, at }); },
    dropJournal: () => drop(JOURNAL),

    /** The goals and answers this phone sent: `[{id, kind, text, at}]`, the newest last, a month kept. */
    sent: () => (read(SENT, []) || []).filter((x) => x && Date.now() - x.at < SENT_DAYS * 864e5),
    setSent(list) { return write(SENT, list.slice(-SENT_MAX)); },

    /** What waits for the network: `[{key, id, kind, path, body, photos: [{path, base64}], text, at}]`. */
    outbox: () => read(OUTBOX, []) || [],
    setOutbox(list) { return write(OUTBOX, list.slice(-OUTBOX_MAX)); },

    /** Everything: the pairing is forgotten on this phone. */
    wipe() { for (const k of [SETTINGS, OUTBOX, SENT, JOURNAL]) drop(k); },
  };
  return keep;
}
