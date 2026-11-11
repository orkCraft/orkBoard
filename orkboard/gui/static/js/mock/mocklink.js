// The page on mocks (goal 170, stage M): with `?mock=1` js/link.js asks no host. The snapshot and the host's replies come
// from `static/mock/board.json`, recorded from a real host on a real project (tools/record_mock.py); a command the
// recording holds is answered from it (its exact arguments first, then any of its name), and any other is a change: it is
// kept in `sent` (what would have gone to the host) and said once in a toast, never sent. The faces under it are the real
// page's; only the link is not. A face drawn for something the host does not answer yet reads it from the recording's
// `proposed` part, which is the contract the host is to answer later.
import { signal } from "@preact/signals";

// Beside this module's own folder, so it is found on the desktop (/static/mock/) and on the phone (/app/page/mock/) alike.
const URL_OF = new URL("../../mock/board.json", import.meta.url).href;
/** What is laid over the recording, each a module of `parts/` with its own `lay(data)`: examples marked as such, and what the
 *  spreads and the leaders' tables read that the host does not answer yet (the contract proposed). */
const PARTS = ["examples", "spreads", "tables"];
let data = { state: null, replies: [], proposed: {} };
const exact = new Map(), byName = new Map();
/** What the page would have sent to the host, newest last: [{name, args, at}]. */
export const sent = signal([]);
/** When the recording was made and on which folder, for the plate that says the page runs on mocks. */
export const recorded = signal(null);
const said = new Set();
let toastOf = () => {};

const key = (name, args) => name + JSON.stringify(sortKeys(args || {}));
function sortKeys(v) {
  if (Array.isArray(v)) return v.map(sortKeys);
  if (v && typeof v === "object") return Object.fromEntries(Object.keys(v).sort().map((k) => [k, sortKeys(v[k])]));
  return v;
}

/** Load the recording and give the page its snapshot (link.js `connect`). */
export async function open({ town, online, toast }) {
  toastOf = toast;
  const r = await fetch(URL_OF);
  data = await r.json();
  for (const part of PARTS) await (await import(`./parts/${part}.js`)).lay(data);       // what the recording lacks: the examples, the spreads', the tables'
  for (const x of data.replies || []) {
    exact.set(key(x.name, x.args), x);
    if (!byName.has(x.name)) byName.set(x.name, x);
  }
  recorded.value = { at: data.recorded, folder: data.folder };
  town.value = data.state;
  online.value = true;
}

/** A proposed part the host does not answer yet (the contract): `proposed("tokens")`. */
export const proposed = (part) => (data.proposed || {})[part];

/** Answer a command as the host would have (link.js `command`). */
export function command(name, args = {}) {
  const x = exact.get(key(name, args)) || byName.get(name);
  if (x) return x.ok ? Promise.resolve(structuredClone(x.result)) : Promise.reject(Object.assign(new Error(x.error || "Refused"), { refused: true }));
  sent.value = [...sent.value, { name, args, at: new Date().toISOString() }];
  if (!said.has(name)) { said.add(name); toastOf(`Not sent: the page runs on mocks (${name})`, "information"); }
  return Promise.resolve(null);
}
