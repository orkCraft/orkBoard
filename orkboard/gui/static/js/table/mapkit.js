// What the four maps of spec 102 part E share (docs/specs/102-the-other-maps-and-picking-on-them.md §5.3–§5.6; decisions §167.1, §168, §171.1; mockup docs/mockups/s3/ states 3–6): a map's card in the face of §167.1 (the element of the
// goal that changed it at the left of its header — none when no goal did —, its name in the body face, a low window with its picture or a two-tone big sign, a label row with its word and, at its right, the gem where the data says
// the card is new), the card lifted where it lies and turned over (card.js `Lifted`, with the table's own key, `data-lkey`, Esc and press-away), a file opened over the pane, and the read of a map's command. Each card is wrapped in
// `Pickable` (maps.js; part F fills it). Written for part E; the sheet is maps.css.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem } from "../orkui.js";
import { command } from "../link.js";
import { lift, lifted, lower, openOver, tab } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { Lifted, leans, litKey } from "./card.js";
import { mapName, partiesNow } from "./data.js";
import { Pickable } from "./maps.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./maps.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const COULD_NOT = "The map could not be read";

/** The key of a map's card as the table lifts it (`t:` is the table's: Esc and a press away lower it, a card lifted anywhere lowers the last). */
export const keyOf = (map, id) => `t:map:${map}:${id}`;
const headOf = (map) => `t:map:${map}:`;

/** The id of this map's card that is lifted, "" none. */
export function useLifted(map) {
  const k = lifted.value, head = headOf(map);
  return k.startsWith(head) ? k.slice(head.length) : "";
}

/** The answer of one of a map's commands, read again when the Board changes (`ideas.map`'s `rev`): `[{data, err}, reload]`. `args` must be plain data. */
export function useRead(name, args = {}) {
  const [st, set] = useState({ data: null, err: "" }), [tick, setTick] = useState(0), rev = mapData.value?.rev, key = JSON.stringify(args);
  useEffect(() => {
    let live = true;
    command(name, args, true).then((r) => {
      if (!live) return;
      if (!r || r.error) set((s) => ({ data: s.data, err: r?.error || COULD_NOT }));
      else set({ data: r, err: "" });
    }).catch((e) => { if (live) set((s) => ({ data: s.data, err: e?.message && e.message !== "offline" ? e.message : COULD_NOT })); });
    return () => { live = false; };
  }, [name, key, rev, tick]);
  return [st, () => setTick((n) => n + 1)];
}

/** A file of the project opened over the pane (frame/kinds.js `file`), the map it came from named in the title (*← Loop · config/balance.ts*), the card lit on the way back. */
export function openFile(path, key = "") {
  openOver("file", { path }, { title: mapName(tab.value, partiesNow()), key }, path);
}

/** A map's body: the part that scrolls, with a card lifted over it (`back`, from `MapBack`). A card still lifted when the map goes (another tab) is lowered. */
export function MapFrame({ map, host, back = null, className = "", children }) {
  useEffect(() => () => { if (lifted.peek().startsWith(headOf(map))) lower(); }, [map]);
  return html`<div class=${cls("mp", className)} data-map=${map} ref=${host}><div class="mp-scroll">${children}</div>${back}</div>`;
}

/** The back of a lifted card, over the card where it lies (card.js `Lifted`); `wide`: a card and more (an asset shown large). */
export function MapBack({ host, name, narrow, wide = false, children }) {
  return html`<div class=${cls("mp-lift", { "is-wide": wide && !narrow })}><${Lifted} host=${host} name=${name} narrow=${narrow}>${children}</${Lifted}></div>`;
}

/** A back's section: a label over its lines. */
export const Sec = ({ label, children }) => html`<div class="mp-sec"><span class="ork-label">${label}</span>${children}</div>`;

/** A file of the project as a press that opens it over the pane. */
export const FileLink = ({ path, from, label = "" }) => html`<button type="button" class="ork-btn quiet mp-file" title=${`Open ${path} over the pane`} onClick=${() => openFile(path, from)}>${label || path}</button>`;

/** The window of a card: a picture (`url`), or a sign drawn big, or whatever `children` draw; `tone` an element's name, "" none. `tall`: a taller window (a picture wants room). */
export function Win({ tone = "", tall = false, pic = false, children }) {
  return html`<div class=${cls("mp-win", { [`is-${tone}`]: !!tone, "is-tall": tall, "is-pic": pic })}>${children}</div>`;
}

/** A map's card, in §167.1's face. `element`: the goal's element that changed it, "" none (no element is drawn); `name`: its words (`code`: a path, in the code face); `row`: its label row's word at the left (`rowCode`
 *  in the code face), `gem` and `mark` (a head) at its right; `foot`: a line under the row; `group`: the lane or step it lies in, for picking; `style`: a place on the map. `children`: its window. A press anywhere on it lifts it; the name is the
 *  button the keyboard reaches. */
export function MapCard({ map, id, name, element = "", row = null, rowCode = false, gem = "", mark = null, foot = null, code = false, group = "", ghost = false, className = "", style = undefined, children }) {
  const key = keyOf(map, id), on = lifted.value === key;
  const press = (e) => { if (e.target.closest?.("[data-nopress]")) return; lift(on ? "" : key); };
  return html`<${Pickable} map=${map} id=${id} name=${name} group=${group}>
    <article class=${cls(`ork-card ork-leans mp-card ${className}`, { "is-lifted": on, "is-lit": litKey.value === key, "is-ghost": ghost })} data-lkey=${key} data-id=${id} data-map=${map} style=${style} onClick=${press} ...${leans}>
      <h3 class="mp-card__head">${element && html`<${Elem} name=${element} />`}<button type="button" class=${cls("mp-card__nm", { "is-code": code })} aria-pressed=${String(on)} title=${name}>${name}</button></h3>
      ${children}
      <div class="mp-card__row"><span class=${cls("mp-card__l", { "is-code": rowCode })} title=${typeof row === "string" ? row : undefined}>${row}</span>${(gem || mark) && html`<span class="mp-card__r">${gem && html`<span class="ork-gem">${gem}</span>`}${mark}</span>`}</div>
      ${foot}
    </article>
  </${Pickable}>`;
}

/** How wide an element is, kept up to date. */
export function useWidth(ref) {
  const [w, set] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const measure = () => set(el.clientWidth);
    measure();
    const ro = typeof ResizeObserver === "function" ? new ResizeObserver(measure) : null;
    ro?.observe(el);
    return () => ro?.disconnect();
  }, []);
  return w;
}

/** `Nothing to read yet: <what would be read>` (spec 102 §0, decisions §112.9), as a quiet box. */
export const Nothing = ({ what }) => html`<div class="mp-nothing"><p>Nothing to read yet: <span class="mp-code">${what}</span></p></div>`;

/** The words of a count: *1 file*, *3 files*. */
export const countWords = (n, one, many) => `${n} ${n === 1 ? one : many}`;

/** The last piece of a path. */
export const baseOf = (path) => String(path || "").split("/").filter(Boolean).pop() || String(path || "");
