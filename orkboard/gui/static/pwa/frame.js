// The installed app's frame (docs/specs/117-the-phone-a-menu-of-the-leaders.md §2, docs/specs/94-one-page-fitted-to-the-width.md §4): what only a phone has, around the
// desktop's page (page/board.js, which gui/pwa.py serves beside it). It pairs the phone (the code from the QR or the link, the key an iOS Home Screen app is handed),
// tells js/link.js it is paired (`pairWith`) and only then imports the page, which speaks the phone's protocol through that link; it registers the worker, keeps the
// push subscription, and takes the arrival from a notification. It draws nothing of the Board: the only things it draws are the cards before the page is paired and
// after the computer forgot the phone. The computer's update is the page's own (js/shell/update.js `UpdateAsk`: the snapshot carries it). The old face (old.html,
// board-app.js) keeps its own copy of all this until spec 94 E.
import { effect } from "@preact/signals";
import { forgotten, offlineLine, pairWith } from "./page/js/link.js";
import { store } from "./page/js/linkpaired.js";
import { picked } from "./page/js/frame/state.js";

const PRODUCT = document.documentElement.dataset.product || "Orkboard";
const API = 1;
const IOS = "standalone" in navigator;                // only iOS Safari has navigator.standalone
const STANDALONE = () => matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;

const app = document.getElementById("app");           // the page's
const card = document.getElementById("phone");        // the frame's own: the cards below
const status = document.getElementById("phone-status");   // …and the line that says there is no signal
const h = (tag, attrs = {}, ...kids) => {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined && kid !== false) el.append(kid);
  return el;
};
const show = (...kids) => { card.replaceChildren(h("section", { class: "phone-card" }, ...kids)); card.hidden = false; app.hidden = true; };

function guessName() {
  const ua = navigator.userAgent;
  if (/iPhone/.test(ua)) return "iPhone";
  if (/iPad/.test(ua)) return "iPad";
  if (/Android/.test(ua)) return "Android phone";
  return "Browser";
}

// -- what the address brings: a pairing code, a token for an iOS Home Screen app, a notification -------------

const read = () => new URLSearchParams(location.hash.slice(1));
const hash = read();
let device = store.get();
if (hash.get("k") && !device) {                       // an iOS Home Screen app's first start (gui/pwa.py `manifest`)
  device = { id: "", token: hash.get("k"), name: guessName() };
  store.set(device);
}
const code = hash.get("pair");
/** Opened from a notification (sw.js `notificationclick`, `#from=push-<tag>`): which push, logged once, and the goal it names (`#goal=<slug>`) if it does. */
const arrivalOf = (params, url = "") => {
  const from = params.get("from");
  if (!from?.startsWith("push-")) return null;
  return { tag: from.slice(5), goal: params.get("goal") || new URLSearchParams(String(url).split("#")[1] || "").get("goal") || "" };
};
let arrival = arrivalOf(hash);
// Nothing of it stays in the address: a code is once, a token is this phone's own.
if (location.hash || location.search) history.replaceState(null, "", location.pathname);

if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js?app=board").catch(() => {});

// -- the cards before the page ------------------------------------------------------------------------------

let started = false, link = null;

function unpaired(note = "") {
  show(h("h1", {}, PRODUCT),
    note && h("p", { class: "warn" }, note),
    h("p", {}, "This phone is not paired with the board yet."),
    h("p", { class: "muted" }, "On the computer: the gear → Phones → Pair a phone, then scan the second QR code, "
      + "“Open in the phone’s browser”, with this phone’s camera. Both need Tailscale, logged in, with HTTPS certificates on."));
}

/** Opened from the computer's QR code: it pairs at once, by the phone's kind as its name. */
function pairing(pairCode) {
  const msg = h("p", { class: "muted" }, "Pairing…");
  const again = h("button", { class: "ork-btn", type: "button", hidden: true, onclick: () => pair(pairCode, guessName(), msg, again) }, "Try again");
  show(h("h1", {}, "Pairing this phone"),
    h("p", {}, "It will see the board: parties and goals, what needs you, the orks at work and the results to review. "
      + "It may answer, start, merge or send back, and stop all. It never types into a terminal."),
    msg, again);
  pair(pairCode, guessName(), msg, again);
}

async function pair(pairCode, name, msg, button) {
  button.hidden = true;
  msg.textContent = "Pairing…";
  msg.className = "muted";
  try {
    const v = await fetch("/api/version", { headers: { Authorization: `Bearer ${pairCode}` } });
    if (!v.ok) throw new Error("The code was not taken: show a new one on the computer and scan it again.");
    const version = await v.json();
    if (version.api !== API) throw new Error(`This app speaks api ${API}, the board ${version.api}: update ${PRODUCT}.`);
    const r = await fetch("/api/pair", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code: pairCode, name }) });
    const body = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(body.error || `Not paired (${r.status})`);
    device = { id: body.id, token: body.token, name: body.name };
    store.set(device);
    if (IOS && !STANDALONE()) homeScreen();
    else go();
  } catch (e) {
    msg.textContent = e.message || String(e);
    msg.className = "warn";
    button.hidden = false;
  }
}

// iOS keeps a Home Screen app's storage apart from Safari's: the app the person adds opens with the token in its start_url once (gui/pwa.py `manifest`), and keeps it from then on.
function handOff() {
  if (!IOS || STANDALONE() || !device?.token) return;
  document.getElementById("manifest").href = `manifest.webmanifest?k=${encodeURIComponent(device.token)}`;
  history.replaceState(null, "", `${location.pathname}#k=${encodeURIComponent(device.token)}`);
}

function homeScreen() {
  handOff();
  show(h("h1", {}, `Paired: ${device.name}`),
    h("p", {}, `Now add it to the Home Screen: Share → Add to Home Screen, then open ${PRODUCT} from there.`),
    h("p", { class: "muted" }, "Until then this page’s address holds the phone’s key: do not share it."),
    h("button", { class: "ork-btn", type: "button", onclick: () => go() }, "Use it in Safari for now"));
}

/** Paired: the page starts; if it ran before (the computer forgot the phone), it starts anew. */
function go() {
  if (started) location.reload();
  else start();
}

// -- the page -----------------------------------------------------------------------------------------------

async function start() {
  started = true;
  card.hidden = true;
  app.hidden = false;
  app.replaceChildren();
  link = pairWith(device);                            // before the page: its first `connect()` goes by the phone's socket
  link.opened((send) => { renewPush(send); arrive(send); });
  effect(() => { if (forgotten.value) unpaired(forgotten.value); });     // the computer forgot this phone: the page is covered by the card
  effect(() => { const line = offlineLine.value; status.textContent = line; status.hidden = !line; });   // "As of 14:02. Connecting…": the page is the kept snapshot
  await import("./page/board.js");
}

/** The person came from a notification: `opened` `push` is logged once and, for a push that names a goal, that goal is picked (the hand's first card is the page's own start). */
function arrive(send, from = arrival) {
  if (!from) return;
  arrival = null;
  send("ideas.log", { event: "opened", what: "push", ref: from.tag, device: "phone" });
  if (from.goal) pickWhenKnown(from.goal);
}

/** Picks the goal once the page has its Board (`mapData` is emptied when a project is shown, then filled): within half a minute, else it stays as it was. */
async function pickWhenKnown(slug) {
  const { mapData } = await import("./page/js/shell/store.js");
  let done = false;
  const stop = effect(() => {
    if (done || !mapData.value?.nodes?.some((n) => n.slug === slug)) return;
    done = true;
    picked.value = slug;
  });
  setTimeout(stop, 30000);
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.addEventListener("message", (e) => {
    if (e.data?.type !== "push-open" || !link) return;
    arrival = arrivalOf(new URLSearchParams({ from: `push-${String(e.data.tag || "")}` }), e.data.url);
    link.send && arrive(link.send);
  });
}

// A code scanned while the app is open (the address changed, the page did not).
window.addEventListener("hashchange", () => {
  const next = read().get("pair");
  if (!next) return;
  history.replaceState(null, "", location.pathname);
  pairing(next);
});

// -- push (docs/specs/42-coming-back.md §3.4): the computer sends it to the subscription this browser gave it ------------------

const unb64 = (text) => Uint8Array.from(atob(text.replace(/-/g, "+").replace(/_/g, "/") + "=".repeat((4 - (text.length % 4)) % 4)), (c) => c.charCodeAt(0));
let quiet = "";                                       // the computer's quiet hours as it last said them: "23:00-09:00"

/** Why this phone cannot be notified, in words; "" when it can ask. */
function pushUnsupported() {
  if ("serviceWorker" in navigator && "PushManager" in window && "Notification" in window) return "";
  return IOS && !STANDALONE() ? `Add ${PRODUCT} to the Home Screen to get notifications here` : `This browser cannot show notifications from ${PRODUCT}`;
}
async function subscription() {
  try { return await (await navigator.serviceWorker.ready).pushManager.getSubscription(); } catch { return null; }
}
const wire = (sub) => { const j = sub.toJSON ? sub.toJSON() : sub; return { endpoint: j.endpoint, p256dh: j.keys?.p256dh, auth: j.keys?.auth }; };

/** On every connect while on, the subscription is sent again (an endpoint the browser renewed reaches the computer this way). */
async function renewPush(send) {
  if (pushUnsupported() || Notification.permission !== "granted") return;
  const sub = await subscription();
  if (!sub) return;
  const r = await send("mobile.push_on", wire(sub));
  if (r.ok && r.result?.quiet) quiet = r.result.quiet;
}

/** Notifications on, from a tap: the browser's permission, then the computer's key, then the subscription, then the computer is told. `{ok}` or `{ok: false, error}`. */
async function pushOn() {
  const why = pushUnsupported();
  if (why) return { ok: false, error: why };
  try {
    if ((await Notification.requestPermission()) !== "granted") return { ok: false, error: `Notifications are off for ${PRODUCT} in this phone’s settings` };
    const k = await link.send("mobile.push_key");
    if (!k.ok) return { ok: false, error: k.error };
    const sub = await (await navigator.serviceWorker.ready).pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: unb64(k.result.key) });
    const r = await link.send("mobile.push_on", wire(sub));
    if (!r.ok) { await sub.unsubscribe().catch(() => {}); return { ok: false, error: r.error }; }
    quiet = r.result?.quiet || k.result.quiet || "";
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e?.message || String(e) };
  }
}

/** Notifications off here and on the computer. Unpairing does the first before it forgets. */
async function pushOff() {
  await dropPush();
  return link.send("mobile.push_off");
}
async function dropPush() {
  try { await (await subscription())?.unsubscribe(); } catch { /* the pairing goes all the same */ }
}

/** The quiet hours, "HH:MM" to "HH:MM", set on the computer. */
async function pushQuiet(from, to) {
  if (!from || !to) return { ok: false, error: "Name both times" };
  const r = await link.send("mobile.push_quiet", { quiet: `${from}-${to}` });
  if (r.ok) quiet = `${from}-${to}`;
  return r;
}

// -- what the page may ask of its frame -------------------------------------------------------------------------

/** `globalThis.orkboardPhone`: the page asks the frame for these (js/hand/upphone.js, at the foot of the crown's menu: notifications and unpairing; spec 117 As built E); the page imports nothing of it. */
globalThis.orkboardPhone = Object.freeze({
  paired: () => device !== null && started,
  /** Forget the pairing here (the person confirmed): notifications stop first, the socket closes, the storage is wiped; then the card says to pair again. */
  async unpair() {
    await dropPush();
    link?.unpair();
    device = null;
    unpaired();
  },
  push: Object.freeze({
    async state() {
      const why = pushUnsupported();
      const permission = why ? "unsupported" : Notification.permission;
      return { supported: !why, why, permission, on: permission === "granted" && Boolean(await subscription()), quiet };
    },
    on: pushOn, off: pushOff, setQuiet: pushQuiet,
  }),
});

// -- start --------------------------------------------------------------------------------------------------

if (code) pairing(code);
else if (device?.token) start();
else unpaired();
