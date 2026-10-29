// Art's map: the assets (docs/specs/102-the-other-maps-and-picking-on-them.md §3.1, §5.4; decisions §135.3–§135.4, §171.1; mockup docs/mockups/s3/ state 4). The kinds are lanes, Art's four first (art and icons, sound, music, clips),
// the others (fonts, the screens' pictures) under them; an asset is a card — a picture is its own window (the asset's `url`), a sound or a music track its two-tone sign and a play button, a clip its first frame and a play
// button; *new* is the gem of one a goal made or changed since the device's last look at this map. Lifted, an asset shows large and plays (an audio or a video element), its file (a press opening it over the pane), its size and
// where it was picked, and the variants not picked under it. Registered with maps.js for the craft `art`.
import { useEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { town } from "../link.js";
import { lift } from "../frame/state.js";
import { mapFor } from "./maps.js";
import { FileLink, MapBack, MapCard, MapFrame, Nothing, Sec, Win, countWords, keyOf, useLifted, useRead } from "./mapkit.js";

const MAP = "art", NONE_WHAT = "the project's pictures, sounds, music and clips", SHOWN = 6, SHOWN_NARROW = 4;
const KINDS = { art: ["Art and icons", "picture", "pictures"], sound: ["Sound", "sound", "sounds"], music: ["Music", "music track", "music tracks"], clip: ["Clips", "clip", "clips"],
  font: ["Fonts", "font", "fonts"], screen: ["Screens' pictures", "screen picture", "screen pictures"] };
const SIGNS = { sound: "tune", music: "tune", clip: "picture", font: "tagline", art: "picture", screen: "screen" };         // the two-tone drawings (decisions §170.1, §171.2): a sound and a tune the lyre, an animation the picture
const LOOK = "orkboard.art.look.", PIXEL_MAX = 64;
const read = (k) => { try { return localStorage.getItem(k) || ""; } catch { return ""; } };
const write = (k, v) => { try { localStorage.setItem(k, v); } catch { /* the new ones are marked again next time */ } };

/** A length: *0.4 s*, *1:12*. */
export function lengthWords(s) {
  if (!(s > 0)) return "";
  if (s < 60) return `${s < 10 ? (Math.round(s * 10) / 10).toString() : Math.round(s)} s`;
  return `${Math.floor(s / 60)}:${String(Math.round(s % 60)).padStart(2, "0")}`;
}
const bytesWords = (b) => (b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : b >= 1024 ? `${Math.round(b / 1024)} KB` : b > 0 ? `${b} B` : "");
const sizeWords = (a) => (a.w && a.h ? `${a.w} × ${a.h}` : lengthWords(a.seconds) || bytesWords(a.bytes));
const isAudio = (a) => a.kind === "sound" || a.kind === "music";

/** A lane's caption under its name: its folder and what it holds (*sprites/: 40 pictures*), else the count and the folders. */
export function laneWords(k) {
  const [, one, many] = KINDS[k.kind] || ["", "file", "files"];
  if (k.kind === "screen" || !k.folders?.length) return countWords(k.n, one, many);
  if (k.folders.length === 1) return `${k.folders[0].folder}: ${countWords(k.folders[0].n, one, many)}`;
  return `${countWords(k.n, one, many)} in ${countWords(k.folders.length, "folder", "folders")}`;
}

// One sound plays at a time (a card's play button); a clip is played on its lifted card.
const playing = signal("");
let current = null;
function stop() { if (current) { current.pause(); current = null; } playing.value = ""; }
function toggle(a) {
  if (playing.value === a.id) { stop(); return; }
  stop();
  const au = new Audio(a.url);
  current = au;
  playing.value = a.id;
  au.addEventListener("ended", () => { if (current === au) stop(); });
  au.play().catch(() => { if (current === au) stop(); });
}
let wantPlay = "";                                                                       // a clip's card asked to play: its lifted video starts at once

function Pic({ a, big = false }) {
  const pixel = a.w > 0 && a.h > 0 && Math.max(a.w, a.h) <= PIXEL_MAX && a.kind !== "screen";
  return html`<img class=${cls("mp-pic", { "is-pixel": pixel })} src=${a.url} alt=${a.name} draggable="false" loading=${big ? "eager" : "lazy"} />`;
}

function AssetCard({ a, goals, narrow }) {
  const goal = a.goal && goals[a.goal], element = goal?.element || "", on = playing.value === a.id;
  const gem = a.change === "added" ? "new" : a.change === "changed" ? "changed" : "";
  const play = (e) => {
    e.stopPropagation();
    if (isAudio(a)) toggle(a);
    else { wantPlay = a.id; lift(keyOf(MAP, a.id)); }
  };
  const pic = a.kind === "art" || a.kind === "screen";
  return html`<${MapCard} map=${MAP} id=${a.id} name=${a.name} code=${true} element=${element} group=${a.kind} gem=${gem} row=${sizeWords(a)} rowCode=${true} className="mp-asset">
    <${Win} tone=${element} tall=${true} pic=${pic}>
      ${pic ? html`<${Pic} a=${a} />`
        : a.kind === "clip" ? html`<video class="mp-pic" src=${`${a.url}#t=0.001`} preload="metadata" muted playsinline aria-hidden="true"></video>`
        : html`<${Sign} name=${SIGNS[a.kind] || "picture"} big=${true} />`}
      ${(isAudio(a) || a.kind === "clip") && html`<button type="button" class=${cls("ork-btn mp-play", { "is-on": on })} data-nopress="1" aria-label=${on ? `Stop ${a.name}` : `Play ${a.name}`} aria-pressed=${String(on)}
        title=${on ? "Stop" : "Play"} onClick=${play}><${Sign} name=${on ? "pause" : "play"} /></button>`}
    </${Win}>
  </${MapCard}>`;
}

function Lane({ k, goals, narrow, open, setOpen }) {
  const [head] = KINDS[k.kind] || [k.kind], cap = narrow ? SHOWN_NARROW : SHOWN, all = open.has(k.kind), shown = all ? k.assets : k.assets.slice(0, cap), more = k.assets.length - shown.length;
  return html`<section class="mp-lane" data-kind=${k.kind} aria-label=${head}>
    <header class="mp-lane__head"><span class="ork-label">${head}</span><span class="mp-cap">${k.n ? laneWords(k) : "None yet"}</span></header>
    <div class="mp-lane__cards">${shown.map((a) => html`<${AssetCard} key=${a.id} a=${a} goals=${goals} narrow=${narrow} />`)}</div>
    ${more > 0 && html`<button type="button" class="ork-btn quiet mp-more" onClick=${() => setOpen(new Set([...open, k.kind]))}>and ${more} more</button>`}
  </section>`;
}

function Variant({ v }) {
  const image = String(v.mime || "").startsWith("image/");
  return html`<figure class="ork-card mp-variant"><div class=${cls("mp-win is-pic", { "is-tall": true })}>${image ? html`<img class="mp-pic" src=${v.url} alt=${v.name} draggable="false" />` : html`<${Sign} name=${String(v.mime || "").startsWith("video/") ? "picture" : "tune"} big=${true} />`}</div>
    <figcaption class="mp-cap">${v.name}</figcaption></figure>`;
}

/** The back of a lifted asset: large, playing where it plays, its file, its size, where it was picked, and the variants not picked. */
function Back({ a, goals }) {
  const key = keyOf(MAP, a.id), goal = a.goal && goals[a.goal], picked = a.others && goals[a.others.goal], vs = a.others?.variants || [], auto = wantPlay === a.id;
  useEffect(() => { wantPlay = ""; }, []);
  useEffect(() => stop, []);
  return html`<div class="mp-back__top">${goal?.element && html`<${Elem} name=${goal.element} />`}<h3 class="mp-back__nm is-code">${a.name}</h3></div>
    <div class=${cls("mp-back__body", { "is-media": !(a.kind === "art" || a.kind === "screen") })}>
      <div class="mp-big">
        ${a.kind === "art" || a.kind === "screen" ? html`<${Pic} a=${a} big=${true} />`
          : a.kind === "clip" ? html`<video class="mp-media" src=${a.url} controls preload="metadata" playsinline autoplay=${auto}></video>`
          : isAudio(a) ? html`<div class="mp-sound"><${Sign} name="tune" big=${true} /><audio class="mp-media" src=${a.url} controls preload="none"></audio></div>`
          : html`<${Sign} name=${SIGNS[a.kind] || "picture"} big=${true} />`}
      </div>
      <div class="mp-back__facts">
        ${a.kind !== "screen" && html`<${Sec} label="File"><${FileLink} path=${a.id} from=${key} /></${Sec}>`}
        ${sizeWords(a) && html`<${Sec} label="Size"><span class="mp-cap">${[sizeWords(a), a.w ? bytesWords(a.bytes) : ""].filter(Boolean).join(" · ")}</span></${Sec}>`}
        ${goal && !(picked && a.others.goal === a.goal) && html`<${Sec} label=${a.change === "added" ? "Made by" : "Last changed by"}><span class="mp-cap">${goal.title}</span></${Sec}>`}
        ${picked && html`<${Sec} label="Picked"><span class="mp-cap">In “${picked.title}”</span></${Sec}>`}
      </div>
    </div>
    ${vs.length > 0 && html`<${Sec} label="Variants not picked"><div class="mp-variants">${vs.map((v) => html`<${Variant} key=${v.key || v.name} v=${v} />`)}</div></${Sec}>`}`;
}

export function ArtMap({ g, narrow }) {
  const host = useRef(), project = town.value?.projects?.current || "", since = useRef(read(LOOK + project)).current, [open, setOpen] = useState(() => new Set());
  const [rd] = useRead("ideas.art_map", since ? { since } : {}), d = rd.data, at = useLifted(MAP), seen = useRef("");
  seen.current = d?.commit || seen.current;
  useEffect(() => () => { stop(); if (seen.current) write(LOOK + project, seen.current); }, [project]);        // leaving the map is looking at it: what is new is new once
  const goals = d?.goals || {}, kinds = (d?.kinds || []).filter((k) => k.own || k.n > 0);
  const asset = at ? kinds.flatMap((k) => k.assets).find((x) => x.id === at) : null;
  const back = asset ? html`<${MapBack} host=${host} name=${asset.name} narrow=${narrow} wide=${true}><${Back} key=${asset.id} a=${asset} goals=${goals} /></${MapBack}>` : null;
  return html`<${MapFrame} map=${MAP} host=${host} back=${back} className="mp--art">
    ${d && d.none ? html`<${Nothing} what=${NONE_WHAT} />`
      : d && html`<div class="mp-lanes">${kinds.map((k) => html`<${Lane} key=${k.kind} k=${k} goals=${goals} narrow=${narrow} open=${open} setOpen=${setOpen} />`)}</div>`}
    ${!d && rd.err && html`<p class="mp-err" role="alert">${rd.err}</p>`}
  </${MapFrame}>`;
}

mapFor(MAP, ArtMap);
