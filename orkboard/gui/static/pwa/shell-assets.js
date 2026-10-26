// The project's assets on the phone (docs/specs/88-assets-and-play.md §0, §7; the project's sheet, spec 70 §2): a section *Assets* in the project's sheet. The files the project is made of lie by kind (*Screens*,
// *Art and icons*, *Sound*, *Music*, *Clips*, *Fonts*) as rows of tokens (74 px wide, 5:7, spec 67 §2), each token's face the thing itself: art drawn whole, a sound or a clip its sign and its length, a font its
// name set in it. A folder of one kind with more than six files is a stack (*×n*) that a press opens in place. What changed since this device's last look (`localStorage` `orkcraft.assets.look`, a commit of dev
// by project, kept when the sheet is put away after the section was in view) wears its goal's element, and a file that was removed lies as a dashed ghost with it. A token pressed opens **the asset's screen**,
// large: art drawn whole, a sound or a clip playing with its controls, a font set in itself; a changed file has *Before* / *Now*; the variants a *Pick one* did not pick lie under it as *Not picked (n)*
// (picks.js's tiles). Play is the machine's own address: its place says *Play on the computer*. `ideas.assets` and `ideas.asset_before` are the host's (gui/ideas_assets.py); a host without them has no section.
import { h, sheet } from "./util.js";
import { elem, sign } from "./shell-marks.js";
import { tiles, lengthWords, stopAll } from "./shell-picks.js";

/** The kinds in the order they are laid out: `[kind, words, sign]`. */
export const KINDS = [["screen", "Screens", "screen"], ["art", "Art and icons", "picture"], ["sound", "Sound", "sound"],
  ["music", "Music", "sound"], ["clip", "Clips", "film"], ["font", "Fonts", "text"]];
const MEDIA_OF = { screen: "image", art: "image", sound: "audio", music: "audio", clip: "video" };
const SHOWN = 8;                                     // the tokens a kind shows before *All n* (two lines of four)
const SMALL_SIDE = 64;                               // art this small on its side is pixel art: drawn crisp
const LOOK = "orkcraft.assets.look";                 // {project: the commit of dev this device last looked at}

/** The commit of dev this device last looked at in a project ("" never). */
export const lookOf = (project) => { try { return (JSON.parse(localStorage.getItem(LOOK)) || {})[project || ""] || ""; } catch { return ""; } };
/** Keeps the commit looked at (this run only when the phone has no room). */
export function keepLook(project, commit) {
  try { localStorage.setItem(LOOK, JSON.stringify({ ...(JSON.parse(localStorage.getItem(LOOK)) || {}), [project || ""]: commit })); } catch { /* said again next time */ }
}

/** *Changed by Register screen*. */
export const changedBy = (goal) => `Changed by ${goal?.title || ""}`.trim();
const baseName = (path) => String(path || "").split("/").pop();
const folderName = (folder) => baseName(String(folder || "").replace(/\/+$/, "")) || String(folder || "");

/** The entries of one kind as the row lays them: a stack of more than six files is one entry `{stack, items}`, the others `{item}`; the order is the host's (the changed first). */
export function entriesOf(items) {
  const out = [], at = new Map();
  for (const a of items) {
    if (!a.stack) { out.push({ item: a }); continue; }
    if (!at.has(a.stack)) { const e = { stack: a.stack, items: [] }; at.set(a.stack, e); out.push(e); }
    at.get(a.stack).items.push(a);
  }
  return out;
}

// -- a font set in itself ---------------------------------------------------------------------------------------------------------------------------
const fonts = new Map();                             // url → Promise<family | "">
let fontNo = 0;
/** The family a font file is loaded as (`FontFace`), or "" when the browser cannot read it. */
function loadFont(url) {
  if (!fonts.has(url)) {
    const family = `ork-asset-${++fontNo}`;
    fonts.set(url, typeof FontFace === "function" && document.fonts
      ? new FontFace(family, `url("${url}")`).load().then((f) => { document.fonts.add(f); return family; }).catch(() => "")
      : Promise.resolve(""));
  }
  return fonts.get(url);
}

// -- a token's face ---------------------------------------------------------------------------------------------------------------------------------
const pixel = (a) => !/\.svg$/i.test(a.id || "") && Math.max(a.w || 0, a.h || 0) > 0 && Math.max(a.w, a.h) <= SMALL_SIDE;

/** What a token shows of an asset: the thing, never cropped. */
function faceOf(a) {
  if (a.kind === "art" || a.kind === "screen") return [h("img", { class: `as-img${pixel(a) ? " is-pixel" : ""}`, src: a.url, alt: "", draggable: "false", loading: "lazy" })];
  if (a.kind === "font") {
    const aa = h("span", { class: "as-aa" }, sign("text", "", { big: true }));
    loadFont(a.url).then((family) => { if (family) { aa.replaceChildren("Aa"); aa.style.fontFamily = `"${family}", sans-serif`; } });
    return [aa];
  }
  const len = lengthWords(a.seconds);
  return [sign(a.kind === "clip" ? "film" : "sound", "", { big: true }), len ? h("span", { class: "as-len" }, len) : null];
}

/** One token: the face, the goal's element when it changed, the name at its foot. */
function token(a, goals, press) {
  const goal = goals[a.goal];
  const changed = a.change === "added" || a.change === "changed";
  const label = `${a.name}${changed && goal ? ` · ${changedBy(goal)}` : ""}`;
  return h("button", { class: `as-token${changed ? " is-changed" : ""}`, type: "button", "data-id": a.id, "data-kind": a.kind, "data-change": a.change || null, "data-goal": changed ? a.goal || null : null,
    title: label, "aria-label": label, onclick: () => press(a) },
  h("span", { class: "as-face" }, ...faceOf(a), changed && goal ? h("span", { class: "as-mark" }, elem(goal.element)) : null, h("span", { class: "as-name" }, a.name)));
}

/** A file that was removed since the last look: a dashed ghost with its goal's element, nothing to press. */
function ghost(r, goals) {
  const goal = goals[r.goal];
  const name = baseName(r.id);
  return h("div", { class: "as-token is-removed", "data-id": r.id, "data-kind": r.kind, "data-change": "removed", "data-goal": r.goal || null, title: goal ? `${name} · ${changedBy(goal)}` : name, role: "group", "aria-label": name },
    h("span", { class: "as-face" }, sign("cross", "", { big: true }), goal ? h("span", { class: "as-mark" }, elem(goal.element)) : null, h("span", { class: "as-name" }, name)));
}

/** A stack: the front token (the first), edges behind it and *×n*; a press opens it in place. */
function stackToken(e, goals, press) {
  const front = e.items[0], edges = Math.min(e.items.length - 1, 2);
  const changed = e.items.some((a) => a.change === "added" || a.change === "changed");
  const goal = goals[(e.items.find((a) => a.change && a.goal) || {}).goal];
  return h("button", { class: `as-token is-many${changed ? " is-changed" : ""}`, type: "button", "data-stack": e.stack, "data-kind": front.kind, "data-n": String(e.items.length), title: e.stack, "aria-label": `${folderName(e.stack)} ×${e.items.length}`,
    "aria-expanded": "false", onclick: press },
  ...Array.from({ length: edges }, (_, i) => h("i", { class: `deck__edge e${edges - i}`, "aria-hidden": "true" })),
  h("span", { class: "as-face" }, ...faceOf(front), changed && goal ? h("span", { class: "as-mark" }, elem(goal.element)) : null, h("span", { class: "as-name" }, folderName(e.stack))),
  h("span", { class: "ork-gem deck__n", "aria-hidden": "true" }, `×${e.items.length}`));
}

// -- the asset's own screen -------------------------------------------------------------------------------------------------------------------------
/** The thing, large, for `v` = {kind, url, name, w, h, seconds}: art drawn whole, a sound or a clip with its controls, a font set in itself. Returns the nodes and the element to play (or null). */
function bigView(v) {
  if (v.kind === "art" || v.kind === "screen") {
    const img = h("img", { class: "as-big", src: v.url, alt: v.name, draggable: "false" });
    if (pixel({ id: v.name, w: v.w, h: v.h })) {
      img.classList.add("is-pixel");
      img.style.width = `${v.w * Math.max(1, Math.min(8, Math.floor(300 / Math.max(v.w, v.h))))}px`;       // crisp pixels, a whole number of times its size, and `max-width: 100%` keeps it in the pane
    }
    return { nodes: [img], play: null };
  }
  if (v.kind === "font") {
    const specimen = h("div", { class: "as-font" }, h("b", {}, v.name), h("span", {}, "ABCDEFGHIJKLM"), h("span", {}, "abcdefghijklm"), h("span", {}, "0123456789"));
    loadFont(v.url).then((family) => { if (family) specimen.style.fontFamily = `"${family}", sans-serif`; });
    return { nodes: [specimen], play: null };
  }
  const video = v.kind === "clip";
  const m = h(video ? "video" : "audio", { class: "as-media", src: v.url, controls: true, preload: "metadata", ...(video ? { playsinline: true } : {}) });
  const len = lengthWords(v.seconds);
  return { nodes: video ? [m] : [sign("sound", "", { big: true }), len ? h("span", { class: "as-len" }, len) : null, m], play: m };
}

/** `core`: the board's frame (st, call). The asset's screen is a sheet of its own, mounted in the page's body when it is first opened (a sheet inside the project's would be found by its queries). Returns {el, load(), leave()}: `el` the section, hidden until the host has answered. */
export function makeAssets(core) {
  const st = core.st;
  const el = h("section", { class: "pj-assets", "data-section": "assets", "aria-label": "Assets", hidden: true });
  const body = h("div", { class: "as-screen" });
  const screen = sheet("Asset", body);
  screen.el.classList.add("full", "asset-sheet");
  screen.el.addEventListener("close", () => { stopAll(); body.replaceChildren(); });
  let data = null, project = "", seq = 0, seen = false;
  const all = new Set();                             // the kinds shown whole (*All n*)
  const opened = new Set();                          // the stacks opened in place: `kind:folder`
  const goals = () => data?.goals || {};

  // -- the asset's screen: large, *Before* / *Now*, *Not picked (n)* ---------------------------------------------------------------------------------
  function openAsset(a) {
    seen = true;
    const stage = h("div", { class: "as-stage" });
    const nodes = [];
    const goal = goals()[a.goal];
    const show = (v) => {
      stopAll();
      const big = bigView(v);
      stage.replaceChildren(...big.nodes);
      stage.dataset.kind = v.kind;
      if (big.play) big.play.play?.()?.catch?.(() => { /* a browser that waits for a press: the controls are there */ });
    };
    const meta = [lengthWords(a.seconds), a.w && a.h ? `${a.w} × ${a.h}` : ""].filter(Boolean).join(" · ");
    nodes.push(h("div", { class: "as-bar" }, sign(KINDS.find((k) => k[0] === a.kind)?.[2] || "picture"), h("b", {}, a.name), meta ? h("small", { class: "muted" }, meta) : null));
    if (a.change === "changed" && data?.since) {
      const now = h("button", { class: "ork-btn as-ver__now", type: "button", "aria-pressed": "true", "data-act": "now" }, "Now");
      const before = h("button", { class: "ork-btn as-ver__before", type: "button", "aria-pressed": "false", "data-act": "before" }, "Before");
      const ver = h("div", { class: "as-ver", role: "group", "aria-label": "Version" }, before, now);
      let was = null;                                // the version before, asked once
      const pick = (isBefore) => {
        before.setAttribute("aria-pressed", String(isBefore));
        now.setAttribute("aria-pressed", String(!isBefore));
        show(isBefore ? was : a);
      };
      before.addEventListener("click", async () => {
        if (was === null) {
          before.disabled = true;
          const got = await core.call("ideas.asset_before", { path: a.id, since: data.since });
          before.disabled = false;
          if (!got) return;
          if (!got.url) { ver.remove(); return; }    // added since: there is no version before
          was = { ...a, url: got.url, w: got.w ?? a.w, h: got.h ?? a.h, seconds: got.seconds ?? a.seconds };
        }
        pick(true);
      });
      now.addEventListener("click", () => pick(false));
      nodes.push(ver);
    }
    nodes.push(stage);
    if (a.change && goal) nodes.push(h("p", { class: "as-by" }, elem(goal.element), h("span", {}, changedBy(goal))));
    const others = a.others?.variants || [];
    if (others.length) {
      const group = tiles({ media: MEDIA_OF[a.kind] || "image", variants: others }, {});
      // The variants not picked are only looked at or listened to: a press never picks one.
      group.el.querySelectorAll(".pk__label").forEach((b) => { b.disabled = true; b.removeAttribute("role"); });
      group.el.addEventListener("click", (e) => { if (!e.target.closest(".pk__ctl")) e.stopPropagation(); }, true);
      nodes.push(h("section", { class: "as-others", "aria-label": `Not picked (${others.length})` }, h("h4", { class: "pj-group" }, `Not picked (${others.length})`), group.el));
    }
    body.replaceChildren(...nodes);
    screen.title(a.name);
    if (!screen.el.isConnected) document.body.append(screen.el);
    show(a);
    screen.open();
  }

  // -- the section --------------------------------------------------------------------------------------------------------------------------------
  function row(kind, words, items, removed) {
    const entries = entriesOf(items);
    const total = entries.length + removed.length;
    const whole = all.has(kind) || total <= SHOWN;
    const nodes = removed.map((r) => ghost(r, goals()));      // a change, so first
    for (const e of entries) {
      const key = `${kind}:${e.stack}`;
      if (!e.stack) nodes.push(token(e.item, goals(), openAsset));
      else if (opened.has(key)) {
        const fold = stackToken(e, goals(), () => { opened.delete(key); paint(); });
        fold.classList.add("is-open");
        fold.setAttribute("aria-expanded", "true");
        nodes.push(fold, ...e.items.map((a) => token(a, goals(), openAsset)));
      } else nodes.push(stackToken(e, goals(), () => { opened.add(key); paint(); }));
    }
    const shown = whole ? nodes : nodes.slice(0, SHOWN);
    return h("div", { class: "as-kind", "data-kind": kind },
      h("h4", { class: "pj-group as-kind__head" }, h("span", {}, words), h("small", { class: "muted" }, String(items.length))),
      h("div", { class: "as-row" }, ...shown),
      whole ? null : h("button", { class: "ork-btn quiet as-more", type: "button", "data-act": "all", onclick: () => { all.add(kind); paint(); } }, `All ${nodes.length}`));
  }

  function paint() {
    const assets = data?.assets || [], removed = data?.removed || [];
    const kinds = KINDS.map(([kind, words]) => ({ kind, words, items: assets.filter((a) => a.kind === kind), gone: removed.filter((r) => r.kind === kind) })).filter((k) => k.items.length || k.gone.length);
    el.replaceChildren(h("h3", { class: "pj-group as-title" }, "Assets"),
      ...(kinds.length ? kinds.map((k) => row(k.kind, k.words, k.items, k.gone)) : [h("p", { class: "cap as-empty" }, "Nothing here yet")]),
      h("p", { class: "cap as-play" }, sign("play"), h("span", {}, "Play on the computer")));      // Play is the machine's own address (spec 88 §5): never on a phone
  }

  if (typeof IntersectionObserver === "function") {
    new IntersectionObserver((rows) => { if (rows.some((r) => r.isIntersecting)) seen = true; }, { threshold: 0.1 }).observe(el);       // the section came into view: it was looked at
  }

  return {
    el,
    /** Asks the host for the assets, the changes marked since this device's last look; a host without them leaves the section out. */
    async load() {
      const n = ++seq;
      project = st.snap?.project || "";
      seen = typeof IntersectionObserver !== "function";
      const since = lookOf(project);
      const got = await core.call("ideas.assets", since ? { since } : {}, () => { /* an older host: no section */ });
      if (n !== seq || !got || !Array.isArray(got.assets)) { if (n === seq) { data = null; el.hidden = true; } return; }
      data = got;
      paint();
      el.hidden = false;
    },
    /** The project's sheet is put away: the commit of dev it showed is this device's last look, when the section was in view. */
    leave() {
      seq++;
      if (data?.commit && seen) keepLook(project, data.commit);
      data = null;
      el.hidden = true;
      if (screen.el.open) screen.close();
    },
  };
}
