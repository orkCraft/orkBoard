// The parts of Design's map (docs/specs/102-the-other-maps-and-picking-on-them.md §5.1, mockup docs/mockups/s3/ states 1 and 2): a screen's card (§167.1 at the maps' size), a pain's small card, a screen's back.
// screensmap.js lays them out. Written by part D. A screen is a room (docs/specs/117-each-lens-a-games-shape.md §6): a door in its left side for each screen that leads to it, one in its right for each it leads to, a wall where there is none.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { command } from "../link.js";
import { openOver } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { leans, litKey, Sec } from "./card.js";
import { Pickable } from "./maps.js";

if (typeof document !== "undefined") {
  const href = new URL("./screens.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

/** The key of a lifted screen (the table's: card.js `mineKey`, so Esc and a press away lower it). */
export const screenKey = (party, id) => `t:screen:${party}:${id}`;

/** The element of the goal that changed a screen (its newest picture is a task's shot of that goal), "" when no goal did. */
export function elementOf(s) {
  const goal = s.picture?.kind === "shot" ? s.picture.goal : "";
  return goal ? (mapData.value?.nodes || []).find((n) => n.slug === goal)?.element || "" : "";
}

const LENS = new Map();                                    // a kept screen's picture, fetched once: id → data address
/** The address of a screen's picture: a shot's signed url, a lens picture fetched with `ideas.lens_screen` (once), "" when it has none. */
export function usePicture(pic) {
  const id = pic?.kind === "lens" ? pic.id : "", [src, setSrc] = useState(() => LENS.get(id) || "");
  useEffect(() => {
    if (!id) { setSrc(""); return undefined; }
    if (LENS.has(id)) { setSrc(LENS.get(id)); return undefined; }
    let live = true;
    command("ideas.lens_screen", { id }, true).then((r) => {
      if (!r || r.error || !r.data) return;
      const at = `data:${r.type || "image/png"};base64,${r.data}`;
      LENS.set(id, at);
      if (live) setSrc(at);
    }).catch(() => {});
    return () => { live = false; };
  }, [id]);
  return pic?.kind === "shot" ? pic.url || "" : src;
}

/** A screen's picture in its window, else orkUI's `screen` sign at the signs' big size. */
function Window({ s }) {
  const src = usePicture(s.picture);
  return html`<span class=${cls("scr-win", { "is-pic": !!src })}>${src ? html`<img src=${src} alt="" draggable="false" />` : html`<${Sign} name="screen" big=${true} />`}</span>`;
}

const DOORS = 3;                                           // doors a side shows at most; the others are *and n more* in its title

/** One side of a screen's room, drawn inside the card's box (the notch clips what lies outside it): `names` the screens at the other end of its doors, in the flow's order; a door is a gap in the frame, a side with none a wall.
 *  The entry's left side has one door more, from outside, with a chevron in it (`entry`). It counts among the three. */
function Side({ side, names, entry }) {
  const from = side === "in", outside = from && entry, shown = names.slice(0, DOORS - (outside ? 1 : 0)), more = names.length - shown.length, n = shown.length + (outside ? 1 : 0);
  const verb = from ? "Leads here" : "Leads to", title = shown.length ? `${verb}: ${shown.join(", ")}${more ? ` and ${more} more` : ""}` : undefined;
  const door = (k, plain) => html`<i class=${plain ? "scr-door scr-door--in" : "scr-door"} key=${`d${k}`} title=${plain ? "Where people come in" : undefined}>${plain && html`<i class="ork-chev right"></i>`}</i>`;
  const parts = [];
  for (let k = 0; k < n; k++) parts.push(html`<i class="scr-frame" key=${`f${k}`}></i>`, door(k, outside && k === 0));
  return html`<span class=${cls("scr-side", { "is-wall": n === 0 })} data-side=${side} data-doors=${n} data-more=${more} title=${title} aria-hidden="true">
    ${parts}<i class="scr-frame" key="f"></i></span>`;
}

/** A screen as a card: the element of the goal that changed it at the left (none when no goal did), its name in the body face, a low window with its picture or the `screen` sign, and the label row with its path. The gem
 *  *new* (changed since the leader's last call) is not drawn: `ideas.screens` does not say it (reported with part D). `lit`: a pain is carried and this is where it may go; `over`: a dragged pain is above it. */
export function ScreenCard({ s, party, step, on, carry, over, onPress, room }) {
  const el = elementOf(s), key = screenKey(party, s.id), r = room || { ins: [], outs: [], tags: "" };
  const card = html`<button type="button" class=${cls("ork-card ork-leans scr-card", { "is-lifted": on, "is-lit": litKey.value === key, "is-aim": carry, "is-over": over })} data-lkey=${key} data-screen=${s.id} data-drop=${s.id} data-step=${step} data-room=${r.tags || undefined}
    aria-pressed=${String(on)} aria-label=${`${s.name}, ${s.path}${carry ? ": pin the pain here" : ""}`} title=${carry ? `Pin the pain to ${s.name}` : s.file} onClick=${onPress} ...${leans}>
    <${Side} side="in" names=${r.ins} entry=${r.tags.includes("entry")} /><${Side} side="out" names=${r.outs} />
    <span class="scr-card__head">${el && html`<${Elem} name=${el} />`}<span class="scr-card__nm">${s.name}</span></span>
    <${Window} s=${s} />
    <span class="scr-card__row"><${Sign} name="screen" /><span class="scr-card__path" title=${s.path}>${s.path}</span></span>
  </button>`;
  return html`<${Pickable} map="screens" id=${s.id} name=${s.name} group=${`step:${step}`}>${card}</${Pickable}>`;
}

/** A pain as a small card pinned under its screen or step: its segment (the `target` sign) and its words. A press carries it (then a press on a screen or a step pins it there); a drag with a mouse carries it too. */
export function PainCard({ p, carried, dragging, onPress, onDown }) {
  return html`<button type="button" class=${cls("ork-card scr-pain", { "is-carried": carried, "is-dragged": dragging })} data-pain=${p.text} data-segment=${p.segment} aria-pressed=${String(carried)}
    aria-label=${`${p.segment}: ${p.text}${carried ? ", carried: press a screen to pin it there" : ""}`} title=${p.text} onClick=${onPress} onPointerDown=${onDown}>
    <span class="scr-pain__sg"><${Sign} name="target" />${p.segment}</span>
    <span class="scr-pain__nm">${p.text}</span>
  </button>`;
}

/** A screen's back: its picture large, its path, its file (opened over the pane), its links (each lifts the screen at the other end) and the pains pinned to it. */
export function ScreenBack({ s, doc, party, from, pains, byId, lift }) {
  const src = usePicture(s.picture), el = elementOf(s);
  const w = s.picture?.w, h = s.picture?.h, ratio = w && h ? `${w} / ${h}` : "64 / 40";
  const ins = (doc.links || []).filter((l) => l.to === s.id && byId.has(l.from)), outs = (doc.links || []).filter((l) => l.from === s.id && byId.has(l.to));
  const file = () => openOver("file", { path: s.file }, from, s.file);
  return html`<div class="scr-back">
    <div class="scr-back__top">${el && html`<${Elem} name=${el} />`}<h3 class="scr-back__nm">${s.name}</h3></div>
    <div class=${cls("scr-bigpic", { "is-none": !src })} style=${src ? `aspect-ratio:${ratio}` : undefined}>${src ? html`<img src=${src} alt=${`${s.name}, as it looks`} />` : html`<${Sign} name="screen" big=${true} />`}</div>
    <${Sec} label="Path"><span class="scr-back__code">${s.path}</span></${Sec}>
    <${Sec} label="File"><button type="button" class="ork-btn quiet scr-back__file" title="Open the file over the pane" onClick=${file}>${s.file}</button></${Sec}>
    ${(ins.length > 0 || outs.length > 0) && html`<${Sec} label="Links"><ul class="scr-back__links">
      ${ins.map((l) => html`<li key=${`i${l.from}`}><${Sign} name="before" /><button type="button" class="ork-btn quiet" data-link=${l.from} onClick=${() => lift(l.from)}>From ${byId.get(l.from).name}</button></li>`)}
      ${outs.map((l) => html`<li key=${`o${l.to}`}><${Sign} name="after" /><button type="button" class="ork-btn quiet" data-link=${l.to} onClick=${() => lift(l.to)}>To ${byId.get(l.to).name}</button></li>`)}
    </ul></${Sec}>`}
    ${pains.length > 0 && html`<${Sec} label="Pains"><ul class="scr-back__pains">${pains.map((p) => html`<li key=${`${p.segment}\n${p.text}`}><b>${p.segment}</b> ${p.text}</li>`)}</ul></${Sec}>`}
  </div>`;
}
