// The project's Assets (docs/specs/88-assets-and-play.md §6, decisions §104.11, §105.3): the project's own files, read from dev's tree (`ideas.assets`), laid out on the table as the field's cards, the kinds as
// sections one under another (docs/specs/90-what-the-first-look-said.md §3) — Screens, Art and icons, Sound, Music, Clips, Fonts, the order of §0, then the canvases (canvases.js, spec 90 §2.3) —, a section's name
// over its cards and its cards wrapping across the whole width, a folder of more than six of one kind a stack (×n, a press opens it). A card's face is the thing itself: art and a screen drawn whole
// (contained, crisp when it is smaller than the card), a sound or music its name over orkUI's *sound* sign and its length, a clip its first frame (else the *film* sign), a font its name set in it. Its foot is its name
// and, when a goal changed it last, *Changed by <goal>* with the goal's element. A press opens the file in the window's right column (spec 90 §2, a tab of kind `asset`, never over the window): art at its size up to
// the column, a sound or a clip playing with its controls (picks.js's pieces, large), *Not picked (n)* under it (the variants a *Pick one* left), and for a changed file *Before* / *Now*: the stage turns over
// (orkUI's steps, 0.42 s) to the file as it was at the device's last look.
// What changed since that look (`localStorage` `orkboard.assets.look.<project>`, the commit shown when the tab was left) is played once when the tab is opened (spec 74 §0's rules: only while the page is seen and
// the person has not asked for no motion): an added file is dealt, a changed one sealed with its goal's element, a removed one crumbles. A filter by kind and by goal. No model, nothing sent anywhere.
import { useEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Chev, Elem, Sign, Switch } from "../orkui.js";
import { command, town } from "../link.js";
import { mapData, preview, show } from "../shell/store.js";
import { reducedMotion } from "./motion.js";
import { Picture, Player } from "./picks.js";
import { isPixel, labelOf, lengthWords } from "./pickwords.js";
import { CanvasSection, useCanvases } from "./canvases.js";

/** The last answer of `ideas.assets` the page read: a file opened in the right column is found in it. */
export const assetsDoc = signal(null);
export const CANVASES = "Canvases";

/** The kinds in the order of the sections (spec 88 §0): [id, the section's word]. */
export const KINDS = [["screen", "Screens"], ["art", "Art and icons"], ["sound", "Sound"], ["music", "Music"], ["clip", "Clips"], ["font", "Fonts"]];
export const ALL_GOALS = "All goals";
export const NOTHING = "Nothing here yet";
export const NOTHING_HOW = "The pictures, sounds, clips and fonts the project is made of show here once they are in dev";
export const changedBy = (title) => `Changed by ${title}`;
export const notPicked = (n) => `Not picked (${n})`;

const STACK_MIN = 2;                                    // a folder with the host's `stacks` entry and two or more files left after the filter is a stack
const DEAL_MS = 300, APART_MS = 35, DEALT = 6, SEAL_MS = 700, CRUMBLE_MS = 420, REVEAL_MS = DEAL_MS + DEALT * APART_MS + 450;      // spec 74 §0: the deal's steps, the seal, the crumble
const LOOK = "orkboard.assets.look.";
const read = (k) => { try { return localStorage.getItem(k) || ""; } catch { return ""; } };
const write = (k, v) => { try { localStorage.setItem(k, v); } catch { /* the changes are marked again next time */ } };
const motion = () => !reducedMotion() && typeof document !== "undefined" && !document.hidden;
const isSvg = (a) => /\.svg$/i.test(a.id || "");
const isStill = (a) => a.kind === "art" || a.kind === "screen";

/** The way a font's family is named for the page, from its address. */
const familyOf = (url) => { let h = 5381; for (const c of String(url)) h = ((h * 33) ^ c.charCodeAt(0)) >>> 0; return `orkboard-asset-${h.toString(36)}`; };
const loaded = new Map();                               // family → the promise of its FontFace, one a font however often a face is drawn
/** A font asset's family once it has loaded ("" before, and for a file the browser will not read: its name is then set in the page's own). */
function useFont(a) {
  const [family, setFamily] = useState("");
  useEffect(() => {
    if (a.kind !== "font" || typeof FontFace !== "function" || !a.url) return undefined;
    let live = true;
    const name = familyOf(a.url);
    if (!loaded.has(name)) {
      const face = new FontFace(name, `url(${JSON.stringify(a.url)})`);
      loaded.set(name, face.load().then(() => { document.fonts.add(face); return name; }).catch(() => ""));
    }
    loaded.get(name).then((got) => { if (live) setFamily(got); });
    return () => { live = false; };
  }, [a.kind, a.url]);
  return family;
}

// -- the device's last look and what changed since ----------------------------------------------------------------------------------------------------------------------

/** What `ideas.assets` says for this device: its last look (`since`) sent, the answer kept; the first answer plays the changes since once (`reveal`: the ids added, changed, the removed rows). Refreshed when the Board's map is.
 *  The commit shown is written as the device's look when the tab is left (the component goes) or the page. */
function useAssets() {
  const key = useRef(`${LOOK}${town.value?.projects?.current || ""}`), since = useRef(read(key.current));
  const [doc, setDoc] = useState(null), [err, setErr] = useState(""), [reveal, setReveal] = useState(null);
  const now = useRef(null), played = useRef(false), rev = mapData.value?.rev;
  useEffect(() => {
    let live = true;
    command("ideas.assets", since.current ? { since: since.current } : {}, true).then((r) => {
      if (!live) return;
      if (!r || r.error) { setErr(r?.error || "The assets could not be read"); return; }
      now.current = r;
      setErr("");
      setDoc(r);
      assetsDoc.value = r;
      if (played.current) return;
      played.current = true;
      const added = r.assets.filter((a) => a.change === "added").map((a) => a.id), changed = r.assets.filter((a) => a.change === "changed").map((a) => a.id);
      if (motion() && (added.length || changed.length || r.removed.length)) setReveal({ added, changed, removed: r.removed });
    }).catch((e) => { if (live) setErr(e.message || "The assets could not be read"); });
    return () => { live = false; };
  }, [rev]);
  useEffect(() => {
    if (!reveal) return undefined;
    const t = setTimeout(() => setReveal(null), REVEAL_MS + CRUMBLE_MS);
    return () => clearTimeout(t);
  }, [reveal]);
  useEffect(() => {
    const save = () => { if (now.current?.commit) write(key.current, now.current.commit); };
    addEventListener("pagehide", save);
    return () => { removeEventListener("pagehide", save); save(); };
  }, []);
  return { doc, err, reveal };
}

// -- a card -------------------------------------------------------------------------------------------------------------------------------------------------------------

/** The thing itself, on the face of a card. */
function Face({ a }) {
  const [pixel, setPixel] = useState(false), [bad, setBad] = useState(false), [frame, setFrame] = useState(false), family = useFont(a);
  const len = lengthWords(a.seconds > 0 ? a.seconds : null);
  if (isStill(a) && !bad) {
    return html`<img class=${cls("assets-face__img", { "is-pixel": pixel, "is-top": a.kind === "screen" })} src=${a.url} alt="" draggable="false" loading="lazy"
      onLoad=${(e) => { const i = e.currentTarget, b = i.parentElement; setPixel(!isSvg(a) && i.naturalWidth < b.clientWidth && i.naturalHeight < b.clientHeight); }} onError=${() => setBad(true)} />`;
  }
  if (a.kind === "clip" && !bad) {
    return html`<video class=${cls("assets-face__video", { "is-shown": frame })} src=${`${a.url}#t=0.001`} preload="metadata" muted playsinline tabindex="-1" aria-hidden="true"
      onLoadedData=${() => setFrame(true)} onError=${() => setBad(true)}></video>${frame ? null : html`<span class="assets-face__sign"><${Sign} name="film" big=${true} /></span>`}${len && html`<span class="assets-face__len">${len}</span>`}`;
  }
  if (a.kind === "clip") return html`<span class="assets-face__sign"><${Sign} name="film" big=${true} /></span>`;
  if (a.kind === "sound" || a.kind === "music") {
    return html`<span class="assets-face__sound"><span class="assets-face__title">${a.name}</span><${Sign} name="sound" big=${true} />${len && html`<span class="assets-face__len">${len}</span>`}</span>`;
  }
  if (a.kind === "font") return html`<span class="assets-face__font" style=${family ? `font-family:"${family}"` : undefined}>${a.name}</span>`;
  return html`<span class="assets-face__sign"><${Sign} name="picture" big=${true} /></span>`;
}

/** One asset as the field's card (5:7, spec 87's size): its face, its name, *Changed by <goal>* with the goal's element. `many` > 1: the front of a stack (edges behind it, ×n). `fx`: what the reveal plays on it. */
function Card({ a, goals, fx, many = 0, onPress }) {
  const goal = a.goal ? goals[a.goal] : null, el = goal?.element || "", dealt = fx?.deal.get(a.id), sealed = fx?.seal.has(a.id);
  const on = many <= 1 && preview.value?.kind === "asset" && preview.value.path === a.id;              // open in the right column
  const edges = Math.min(2, many - 1), said = `${a.name}${goal ? `, ${changedBy(goal.title)}` : ""}${many > 1 ? `, and ${many - 1} more in ${a.stack}: a press opens them` : ""}`;
  return html`<div class=${cls("arena-stk assets-stk", { "is-many": many > 1 })} data-n=${many > 1 ? many : undefined}>
    ${Array.from({ length: edges }, (_, i) => html`<i key=${i} class="arena-stk__edge" style=${`left:${(i + 1) * 4}px;top:${-(i + 1) * 4}px`}></i>`)}
    <button type="button" class=${cls("arena-task assets-card", { "is-changed": !!a.change, "has-n": many > 1, "is-dealt-in": dealt != null, "is-sealed": sealed, "is-on": on })} data-asset=${a.id} data-kind=${a.kind}
      data-change=${a.change || undefined} style=${dealt != null ? `--delay:${dealt * APART_MS}ms` : undefined} title=${goal ? `${a.name} · ${changedBy(goal.title)}` : a.name} aria-label=${said}
      aria-expanded=${many > 1 ? "false" : undefined} onClick=${() => onPress(a)}>
      <span class="assets-face"><${Face} a=${a} /></span>
      <span class="arena-task__name assets-name">${a.name}</span>
      ${goal && html`<span class="arena-task__foot assets-changed"><${Elem} name=${el} dim=${!el} />${changedBy(goal.title)}</span>`}
      ${many > 1 && html`<span class="arena-stk__n">×${many}</span>`}
      ${sealed && html`<span class="assets-seal"><${Elem} name=${el} dim=${!el} big=${true} /></span>`}
    </button>
  </div>`;
}

/** A file that went since the last look: its place crumbles, 0.42 s in steps, and is gone. */
const Ghost = ({ r }) => html`<div class="arena-stk assets-stk"><div class="arena-task assets-card is-crumble" data-removed=${r.id} data-kind=${r.kind} aria-hidden="true">
  <span class="assets-face"></span><span class="arena-task__name assets-name">${r.id.split("/").pop()}</span></div></div>`;

/** A folder's stack: closed, the front card with its edges and ×n (a press opens it); open, a fold row and every card. */
function StackOf({ s, goals, fx, open, toggle, press }) {
  if (!open) return html`<${Card} a=${s.members[0]} goals=${goals} fx=${fx} many=${s.members.length} onPress=${toggle} />`;
  return html`<div class="assets-stack" data-folder=${s.folder}>
    <button type="button" class="ork-btn quiet arena-fold" aria-expanded="true" onClick=${toggle}><${Chev} dir="down" /> ${s.folder} ×${s.members.length}</button>
    ${s.members.map((a) => html`<${Card} key=${a.id} a=${a} goals=${goals} fx=${fx} onPress=${press} />`)}
  </div>`;
}

/** A section's entries: a card for a file, a stack for a folder with more than one file left (the list is the host's, the changed first). */
export function entriesOf(list) {
  const out = [], by = new Map();
  for (const a of list) {
    if (!a.stack) { out.push({ a }); continue; }
    const k = `${a.kind}:${a.stack}`;
    if (!by.has(k)) { const s = { stack: true, key: k, folder: a.stack, members: [] }; by.set(k, s); out.push(s); }
    by.get(k).members.push(a);
  }
  return out.map((e) => (e.stack && e.members.length < STACK_MIN ? { a: e.members[0] } : e));
}

// -- a card lifted ------------------------------------------------------------------------------------------------------------------------------------------------

/** A file's thing, large: art at its size up to the pane (contained; crisp when it is 64 px or less), a sound or a clip with picks.js's player, a font as a specimen. `v`: {url, seconds, w, h}. */
function Large({ a, v }) {
  const family = useFont(a);
  if (isStill(a)) return html`<img class=${cls("assets-lift__img", { "is-pixel": isPixel(isSvg(a) ? "image/svg+xml" : "image/png", v.w, v.h) })} src=${v.url} alt=${a.name} draggable="false"
    style=${v.w > 0 && !isSvg(a) ? `max-width:${v.w}px;max-height:${v.h}px` : undefined} />`;
  if (a.kind === "font") {
    return html`<div class="assets-lift__font" style=${family ? `font-family:"${family}"` : undefined}><b>${a.name}</b><p>ABCDEFGHIJKLMNOPQRSTUVWXYZ</p><p>abcdefghijklmnopqrstuvwxyz</p><p>0123456789 !?@</p></div>`;
  }
  return html`<${Player} v=${v} label=${a.name} video=${a.kind === "clip"} big=${true} />`;
}

/** A variant not picked, small: its picture or player and its label (*B · monogram*). */
function Other({ v }) {
  const label = labelOf(v), kind = String(v.mime || "").split("/")[0];
  return html`<div class="assets-other" data-variant=${v.key}><div class="assets-other__media">
    ${kind === "image" ? html`<${Picture} v=${v} label=${label} />` : kind === "audio" || kind === "video" ? html`<${Player} v=${v} label=${label} video=${kind === "video"} />` : null}</div>
    <span class="assets-other__label" title=${label}>${label}</span></div>`;
}

/** A card pressed, in the right column (spec 88 §6.3, spec 90 §2–§3). A changed file has *Before* / *Now*: the stage turns over to the file as it was at the device's last look. The tab's × (or Esc) closes it. */
function Lift({ a, goals, since }) {
  const [before, setBefore] = useState(null), [turned, setTurned] = useState(false), stage = useRef();
  const goal = a.goal ? goals[a.goal] : null, still = a.change === "changed" && !a.id.startsWith("screen:");
  useEffect(() => {                                                   // the card was pressed: a sound or a clip plays (the press is the person's)
    if (a.kind === "sound" || a.kind === "music" || a.kind === "clip") stage.current?.querySelector(".is-now audio, .is-now video")?.play?.().catch(() => {});
  }, [a.id]);
  useEffect(() => {
    if (!still || !since) return undefined;
    let live = true;
    command("ideas.asset_before", { path: a.id, since }, true).then((r) => { if (live && r && !r.error && r.url) setBefore(r); }).catch(() => {});
    return () => { live = false; };
  }, [a.id, since]);
  const turn = (id) => {
    stage.current?.querySelectorAll("audio, video").forEach((m) => m.pause());
    setTurned(id === "before");
  };
  const others = a.others?.variants || [];
  return html`<section class="assets-lift" aria-label=${a.name} data-asset=${a.id} data-kind=${a.kind}>
    <div class="assets-lift__head">
      <b class="assets-lift__name" title=${a.name}>${a.name}</b>
      ${goal && html`<span class="assets-lift__by"><${Elem} name=${goal.element || ""} dim=${!goal.element} />${changedBy(goal.title)}</span>`}
      <span class="arena-spacer"></span>
      ${before && html`<${Switch} label="Version" cls="assets-lift__turn" value=${turned ? "before" : "now"} onPick=${turn} options=${[["now", "Now"], ["before", "Before"]]} />`}
    </div>
    <p class="arena-cap assets-lift__path" title=${a.id}>${a.id.startsWith("screen:") ? "" : a.id}</p>
    <div class=${cls("assets-lift__stage", { "is-turned": turned })} ref=${stage} data-kind=${a.kind}>
      <div class="assets-lift__face is-now" aria-hidden=${turned ? "true" : undefined}><${Large} a=${a} v=${a} /></div>
      ${before && html`<div class="assets-lift__face is-before" data-before aria-hidden=${turned ? undefined : "true"}><${Large} a=${a} v=${before} /></div>`}
    </div>
    ${others.length > 0 && html`<section class="assets-lift__others" aria-label=${notPicked(others.length)}>
      <h3 class="arena-sec">${notPicked(others.length)}</h3>
      <div class="assets-others">${others.map((v) => html`<${Other} key=${v.key} v=${v} />`)}</div></section>`}
  </section>`;
}

/** A file opened in the right column (a tab `{kind: "asset", path: <its id>}`): found in the last answer of `ideas.assets`; a tab kept from an earlier visit reads it again. */
export function AssetView({ p }) {
  const doc = assetsDoc.value, [err, setErr] = useState("");
  useEffect(() => {
    if (doc) return undefined;
    let live = true;
    const since = read(`${LOOK}${town.value?.projects?.current || ""}`);
    command("ideas.assets", since ? { since } : {}, true).then((r) => {
      if (!live) return;
      if (!r || r.error) setErr(r?.error || "The assets could not be read");
      else assetsDoc.value = r;
    }).catch((e) => { if (live) setErr(e.message || "The assets could not be read"); });
    return () => { live = false; };
  }, [!doc]);
  if (!doc) return html`<p class="ok-tone-muted">${err || "Opening…"}</p>`;
  const a = doc.assets.find((x) => x.id === p.path);
  if (!a) return html`<p class="ok-tone-muted">This file is no longer in dev.</p>`;
  return html`<${Lift} key=${a.id} a=${a} goals=${doc.goals || {}} since=${doc.since} />`;
}

// -- the table ----------------------------------------------------------------------------------------------------------------------------------------------------

/** The reveal's effects by file: the order the added are dealt in (six travel in turn, the rest with the sixth), the changed that are sealed. */
function effects(reveal) {
  if (!reveal) return null;
  return { deal: new Map(reveal.added.map((id, i) => [id, Math.min(i, DEALT)])), seal: new Set(reveal.changed) };
}

/** A file pressed opens in the right column (spec 90 §2); pressed again while it is the tab shown there, it stays. */
const open = (a) => show({ kind: "asset", path: a.id, title: a.name }, { via: "assets" });

export function Assets() {
  const { doc, err, reveal } = useAssets(), canvas = useCanvases();
  const [kind, setKind] = useState(""), [goal, setGoal] = useState(""), [openStacks, setOpenStacks] = useState(() => new Set());
  if (err && !doc) return html`<div class="assets" data-state="failed"><p class="arena-cap assets-note">${err}</p></div>`;
  if (!doc) return html`<div class="assets" data-state="reading"><p class="arena-cap assets-note"><span class="ork-busy"></span></p></div>`;
  const goals = doc.goals || {}, fx = effects(reveal);
  const used = new Set(doc.assets.map((a) => a.goal).filter(Boolean)), goalIds = Object.keys(goals).filter((g) => used.has(g));
  const pick = (r) => (!kind || r.kind === kind) && (!goal || r.goal === goal);
  const shown = doc.assets.filter(pick), gone = reveal ? reveal.removed.filter(pick) : [];
  const anyCanvas = canvas.canvases.length + canvas.seen.length > 0;
  const has = (k) => (k === "canvas" ? anyCanvas : doc.assets.some((a) => a.kind === k));
  const pickCanvas = (c) => (!kind || kind === "canvas") && (!goal || c.idea === goal);
  const canvases = canvas.canvases.filter(pickCanvas), seen = canvas.seen.filter(pickCanvas);
  const toggle = (k) => setOpenStacks((s) => { const n = new Set(s); n.has(k) ? n.delete(k) : n.add(k); return n; });
  const secs = KINDS.map(([id, word]) => ({ id, word, list: shown.filter((a) => a.kind === id), gone: gone.filter((r) => r.kind === id) })).filter((c) => c.list.length || c.gone.length);
  const any = secs.length > 0 || canvases.length + seen.length > 0;
  return html`<div class="assets" data-state="shown">
    <div class="assets-bar">
      <div class="assets-kinds" role="group" aria-label="Kinds">
        ${[...KINDS, ["canvas", CANVASES]].filter(([id]) => has(id)).map(([id, word]) => html`<button type="button" key=${id} class="ork-btn" data-kind=${id} aria-pressed=${String(kind === id)} onClick=${() => setKind(kind === id ? "" : id)}>${word}</button>`)}
      </div>
      ${goalIds.length > 0 && html`<div class="ork-select assets-goals"><select class="ork-field" aria-label="Goal" value=${goal} onChange=${(e) => setGoal(e.target.value)}>
        <option value="">${ALL_GOALS}</option>${goalIds.map((g) => html`<option key=${g} value=${g} selected=${g === goal}>${goals[g].title}</option>`)}</select></div>`}
    </div>
    ${doc.assets.length === 0 && !anyCanvas ? html`<div class="assets-none"><p class="assets-none__title">${NOTHING}</p><p class="arena-cap">${NOTHING_HOW}</p></div>`
      : !any ? html`<div class="assets-none"><p class="assets-none__title">${NOTHING}</p></div>` : html`
      <div class="assets-body ork-table"><div class="assets-secs">
        ${secs.map((c) => html`<section key=${c.id} class="assets-sec" data-kind=${c.id} aria-label=${c.word}>
          <h3 class="arena-sec">${c.word} <span class="assets-sec__n">${c.list.length}</span></h3>
          <div class="assets-sec__cards">
            ${entriesOf(c.list).map((e) => (e.stack
              ? html`<${StackOf} key=${e.key} s=${e} goals=${goals} fx=${fx} open=${openStacks.has(e.key)} toggle=${() => toggle(e.key)} press=${open} />`
              : html`<${Card} key=${e.a.id} a=${e.a} goals=${goals} fx=${fx} onPress=${open} />`))}
            ${c.gone.map((r) => html`<${Ghost} key=${`gone:${r.id}`} r=${r} />`)}
          </div>
        </section>`)}
        <${CanvasSection} list=${canvases} seen=${seen} done=${canvas.done} />
      </div></div>`}
  </div>`;
}
