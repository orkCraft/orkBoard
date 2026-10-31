// The page's link when it is paired with a computer (docs/specs/94-one-page-fitted-to-the-width.md §2): the phone's socket,
// `wss://<host>/ws` with the device's bearer and the protocol `orkcraft.v1` (gui/phones.py): the snapshot (`state`), a
// command and its `reply`, and `news` while it is open. Moved from pwa/board-app.js and pwa/util.js, which the phone's
// old face keeps a copy of until it is removed (spec 94 E); js/link.js picks it (`pairWith`) and no other module knows.
//
// Away from the computer the page shows what it last saw, greyed and said "As of 14:02."; an answer or an idea given with
// no signal is kept on the phone (`outbox`) and sent when the computer answers again, said "Sent when the computer answers".
import { signal } from "@preact/signals";

export const PROTOCOL = "orkcraft.v1";
export const SENT_WHEN = "Sent when the computer answers";

/** The commands this phone may send (`mobile.hello`'s `commands`, as the computer lets a phone); null until it has said. */
export const allowedCommands = signal(null);
/** The line over the page while there is no signal ("As of 14:02. The board went away: trying again…"), "" when it answers. */
export const status = signal("");
/** The page shows the last snapshot kept on this phone, not the computer's now: draw it greyed and act on none of it. */
export const stale = signal(false);
/** What waits to be sent: [{key, name, label, at}], each marked SENT_WHEN where it is drawn. */
export const waiting = signal([]);
/** The phone was forgotten on the computer: the words to say with the pairing card, "" otherwise. */
export const forgotten = signal("");

const KEPT = "orkcraft.town", OUTBOX = "orkcraft.outbox", DEVICE = "orkcraft.device", SPACE = "orkcraft.orkspace";
const randomId = () => Array.from(crypto.getRandomValues(new Uint8Array(8)), (b) => b.toString(16).padStart(2, "0")).join("");
export const clock = (ms) => new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/** The last town the phone saw, kept on this phone only; wiped with the pairing. */
export const kept = {
  get() { try { return JSON.parse(localStorage.getItem(KEPT)); } catch { return null; } },
  set(state) { try { localStorage.setItem(KEPT, JSON.stringify({ at: Date.now(), state })); } catch { /* not kept */ } },
  clear() { try { localStorage.removeItem(KEPT); } catch { /* nothing kept */ } },
};

/** What the person gave with no signal, kept on this phone until the computer answers again; wiped with the pairing. */
export const outbox = {
  all() { try { return JSON.parse(localStorage.getItem(OUTBOX)) || []; } catch { return []; } },
  /** False when this phone had no room to keep it. */
  add(item) {
    const all = outbox.all();
    all.push({ ...item, key: randomId() });
    try { localStorage.setItem(OUTBOX, JSON.stringify(all.slice(-50))); return true; } catch { return false; }
    finally { outbox.show(); }
  },
  remove(key) {
    try { localStorage.setItem(OUTBOX, JSON.stringify(outbox.all().filter((x) => x.key !== key))); } catch { /* kept */ }
    outbox.show();
  },
  /** Take an item to send: true when it was still there (another page of the app, or this one before a reload, may have
   *  taken it already: then it is not sent twice). */
  claim(key) {
    if (!outbox.all().some((x) => x.key === key)) return false;
    outbox.remove(key);
    return true;
  },
  /** An item taken but not sent (no signal): back where it was. */
  restore(item) {
    const all = outbox.all();
    if (!all.some((x) => x.key === item.key)) all.unshift(item);
    try { localStorage.setItem(OUTBOX, JSON.stringify(all.slice(-50))); } catch { /* this run only */ }
    outbox.show();
  },
  clear() { try { localStorage.removeItem(OUTBOX); } catch { /* nothing kept */ } outbox.show(); },
  show() { waiting.value = outbox.all().map(({ key, name, label, at }) => ({ key, name, label, at })); },
};

/** This phone's pairing: {id, token, name}. */
export const store = {
  get() { try { return JSON.parse(localStorage.getItem(DEVICE)); } catch { return null; } },
  set(v) { try { localStorage.setItem(DEVICE, JSON.stringify(v)); } catch { /* private mode: this run only */ } },
  clear() { try { localStorage.removeItem(DEVICE); localStorage.removeItem(SPACE); } catch { /* nothing kept */ } kept.clear(); outbox.clear(); },
};

/**
 * The paired link. `page` is what js/link.js hands over: `{town, online, toast}` (its signals and toast), so this module
 * imports nothing of it. Returns `{connect, command, deliver, close, unpair, opened}`:
 * - `connect()` opens the phone's socket with the stored device (nothing to open with: `forgotten` stays "");
 * - `command(name, args, quiet)` as link.js's, refused with `offline` when there is no socket;
 * - `deliver(name, args, label)` sends now, or keeps it for later (`{ok, kept}`);
 * - `opened(fn)` runs `fn(send)` each time the socket opens (the frame's push renewal), `news(fn)` each news item.
 */
export function makePaired(page, device = store.get()) {
  let ws = null, opened = false, retry = 1, retryTimer = 0, nextId = 1, board = null, seenAt = 0, flushing = false, closed = false, toldAt = 0;
  const TELL_S = 10;                               // "Not connected to the town" is toasted at most this often
  const waits = new Map();
  const onOpen = new Set(), onNews = new Set();

  const fail = (error) => ({ ok: false, error });

  /** One command out, its reply back (never throws): `{ok, result}` | `{ok: false, error}`. */
  function send(name, args = {}) {
    return new Promise((resolve) => {
      if (!ws || ws.readyState !== 1) { resolve(fail("Not connected to the town")); return; }
      const id = nextId++;
      waits.set(id, resolve);
      ws.send(JSON.stringify({ t: "cmd", id, name, args }));
    });
  }

  async function command(name, args = {}, quiet = false) {
    const r = await send(name, args);
    if (r.ok) return r.result;
    const offline = r.error === "Not connected to the town";
    if (offline) {                                  // said once in a while: a page opened with no signal asks the Board's commands one after another, and the line over it says "As of …"
      if (Date.now() - toldAt > TELL_S * 1000) { toldAt = Date.now(); page.toast("Not connected to the town", "error"); }
    } else if (!quiet) page.toast(r.error, "error", name);
    throw Object.assign(new Error(offline ? "offline" : r.error || "Refused"), { refused: true });
  }

  /** Send now, or with no signal keep it on the phone and send it when the computer answers again. */
  async function deliver(name, args, label) {
    if (ws && ws.readyState === 1) {
      const r = await send(name, args);
      if (r.ok || r.error !== "The town went away") return r;
    }
    if (outbox.add({ name, args, label, at: Date.now() })) return { ok: true, kept: true };
    if (args?.photos || args?.lens?.some((a) => a.image)) {   // no room for the pictures on this phone: the words are kept all the same
      const { photos: _left, ...rest } = args;
      if (rest.lens) rest.lens = rest.lens.filter((a) => !a.image);
      if (outbox.add({ name, args: rest, label, at: Date.now() })) return { ok: true, kept: true, unphotographed: true };
    }
    return { ok: true, kept: true };
  }

  async function flush() {
    if (flushing) return;
    flushing = true;
    try {
      for (const item of outbox.all()) {
        if (!ws || ws.readyState !== 1) break;
        if (!outbox.claim(item.key)) continue;          // taken by another page of the app: never sent twice
        const r = await send(item.name, item.args);
        if (!r.ok && (r.error === "Not connected to the town" || r.error === "The town went away")) { outbox.restore(item); break; }
        page.toast(r.ok ? `Sent: ${item.label}` : `Not sent: ${item.label}. ${r.error}`, r.ok ? "information" : "warning");
      }
    } finally {
      flushing = false;
    }
  }

  /** The commands a phone may send, from the computer: a face whose command is not among them is not drawn. */
  async function hello() {
    const r = await send("mobile.hello");
    if (r.ok && Array.isArray(r.result?.commands)) allowedCommands.value = new Set(r.result.commands);
  }

  // `keptAt`: the board comes from this phone's storage (seen then), not from the socket.
  function render(s, keptAt = 0) {
    board = s;
    seenAt = keptAt || Date.now();
    if (!keptAt) kept.set(s);
    page.town.value = s;
    try {                                          // the icon's badge: how many answers wait
      Promise.resolve(s.needs_you ? navigator.setAppBadge?.(s.needs_you) : navigator.clearAppBadge?.()).catch(() => {});
    } catch { /* a browser without badges */ }
  }

  function offline(at, why) {
    stale.value = Boolean(board);
    status.value = board && at ? `As of ${clock(at)}. ${why}` : why;
  }

  function news(items) {
    for (const item of items) {
      page.toast(item.line);
      for (const fn of onNews) fn(item);
      if (document.visibilityState === "hidden" && "Notification" in window && Notification.permission === "granted") {
        navigator.serviceWorker?.ready.then((reg) => reg.showNotification(page.product, { body: item.line, tag: item.id || item.kind, icon: "icon-192.png" }));
      }
    }
    if (items.length && navigator.vibrate) navigator.vibrate(80);
  }

  function connect() {
    clearTimeout(retryTimer);
    closed = false;
    if (!device?.token) { forgotten.value = forgotten.value || "This phone is not paired with the board yet."; return; }
    if (ws && ws.readyState <= 1) return;
    outbox.show();
    status.value = "Connecting…";
    if (!board) {                                  // the board as it was last seen, greyed, until it answers
      const last = kept.get();
      if (last?.state) { render(last.state, last.at); offline(last.at, "Connecting…"); }
    }
    opened = false;
    const socket = new WebSocket(`wss://${location.host}/ws`, [PROTOCOL, `bearer.${device.token}`]);
    ws = socket;
    socket.onopen = () => {
      opened = true; retry = 1; status.value = "";
      hello(); flush();
      for (const fn of onOpen) fn(send);
    };
    socket.onmessage = (e) => {
      let msg;
      try { msg = JSON.parse(e.data); } catch { return; }
      if (msg.t === "state") { render(msg.state); stale.value = false; page.online.value = true; status.value = ""; }
      else if (msg.t === "reply") { const w = waits.get(msg.id); waits.delete(msg.id); w?.(msg); }
      else if (msg.t === "news") news(msg.news || []);
    };
    socket.onclose = (e) => {
      if (ws === socket) ws = null;
      page.online.value = false;
      for (const w of waits.values()) w(fail("The town went away"));
      waits.clear();
      if (e.code === 1008) {                       // forgotten on the computer: the token is dead
        store.clear();
        device = null;
        board = null;
        allowedCommands.value = null;
        stale.value = false;
        status.value = "";
        forgotten.value = "The board forgot this phone. Pair it again to use it.";
        return;
      }
      if (closed) return;
      offline(seenAt, opened ? "The board went away: trying again…" : "Cannot reach the board: is it running, and Tailscale on?");
      retryTimer = setTimeout(connect, retry * 1000);
      retry = Math.min(retry * 2, 30);
    };
  }

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && device?.token && !closed && (!ws || ws.readyState > 1)) connect();
  });

  return {
    connect, command, deliver, send,
    opened(fn) { onOpen.add(fn); return () => onOpen.delete(fn); },
    news(fn) { onNews.add(fn); return () => onNews.delete(fn); },
    /** Close the socket and stay closed (the frame forgets the pairing here). */
    close() { closed = true; clearTimeout(retryTimer); ws?.close(1000); },
    /** Forget the pairing on this phone. */
    unpair() { this.close(); store.clear(); device = null; board = null; allowedCommands.value = null; stale.value = false; status.value = ""; },
  };
}
