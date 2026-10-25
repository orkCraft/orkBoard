// Canvases (docs/specs/78-canvases.md §3): what an AI tool drew outside the code, a card each, in the right column above *Waits for your look*. A fold row *Canvases · n* (FoldRow,
// spec 73 §3), folded, shown only when there are canvases (new or seen); n is what is not seen (the snapshot's `canvases_new`), and the cards are read again (`ideas.canvases`) when the
// snapshot's `canvases_rev` moves and when the row is unfolded. A card is an `.ork-frame` like a result's: the elf's head (a small accent), the kind in the pixel face's small caps, the title in
// the text face, the tool and when, its goal and task when it has them, and what it offers: **Open on claude.ai** (its host: a link of another host is text, never a link), **Show here**
// (a local file in the drawer: a picture, a page in a sandbox with no scripts; Markdown as text) and **Seen**, which folds it into *Seen* at the foot (the last 20). A canvas is not a signal
// and not a result (decisions §54.1): no alert colour, nothing in the top bar. One that comes while the page is seen draws in once (0.36 s, in steps; none under reduced motion).
import { useEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { town } from "../link.js";
import { WhoHead } from "../orkui.js";
import { ask } from "../board/store.js";
import { show, showTask } from "../shell/store.js";
import { currentProject } from "../shell/projects.js";
import { FoldRow } from "./foldrow.js";
import { reducedMotion, DRAWN_MS } from "./motion.js";
import { sinceWords } from "./arenawords.js";

const KIND_WORDS = { design: "Design", slides: "Slides", document: "Document", page: "Page", picture: "Picture" };
const OPEN_WORDS = { "claude.ai": "Open on claude.ai", "figma.com": "Open in Figma", "tldraw.com": "Open on tldraw", "canva.com": "Open on Canva" };

const data = signal({ canvases: [], seen: [] });           // ideas.canvases
const open = signal(false), seenOpen = signal(false);      // the two folds: both folded by default
const drawn = signal([]);                                  // the keys drawing in now
let known = { project: null, keys: null };                 // the keys the page has read for this project (null: not read yet: nothing draws in on the first read)
let reading = 0;

/** *just now* · *4 min ago* · *3 h ago* · *3 d ago* (from 48 hours); "" when the time is not read. */
export function whenWords(iso, now = Date.now()) {
  const t = Date.parse(iso || "");
  if (Number.isNaN(t)) return "";
  const w = sinceWords(iso, now);
  if (!w) return "just now";                               // a clock a little ahead
  const hours = (now - t) / 3600000;
  return w === "just now" ? w : hours >= 48 ? `${Math.floor(hours / 24)} d ago` : `${w} ago`;
}

/** The cards from the host, the last read winning. The keys that are new to the page (none on its first read of a project) are set in `drawn` just before the cards are, so a card is
 *  drawn with its motion from its first frame; they are drawn in only where they can be seen (the row open), while the page is seen, and when the person has not asked for none. */
async function read(project) {
  const mine = ++reading, got = await ask("ideas.canvases");
  if (!got || mine !== reading || !Array.isArray(got.canvases)) return false;
  const seen = Array.isArray(got.seen) ? got.seen : [], keys = [...got.canvases, ...seen].map((c) => c.key), had = known.project === project ? known.keys : null;
  known = { project, keys: new Set([...(had || []), ...keys]) };
  const fresh = had && open.value && !reducedMotion() && !document.hidden ? keys.filter((k) => !had.has(k)) : [];
  if (fresh.length) drawn.value = fresh;
  data.value = { canvases: got.canvases, seen };
  return fresh.length > 0;
}

/** A canvas's local file in the drawer (`ideas.canvas_file`): a picture, an HTML page in a sandbox with no scripts and no origin, Markdown and the rest as text. */
export function CanvasView({ p }) {
  const [got, setGot] = useState(undefined);
  useEffect(() => {
    let on = true;
    setGot(undefined);
    ask("ideas.canvas_file", { key: p.path }).then((r) => { if (on) setGot(r); });
    return () => { on = false; };
  }, [p.path]);
  if (got === undefined) return html`<p class="ok-tone-muted">Opening…</p>`;
  if (!got || (!got.data && typeof got.text !== "string")) return html`<p class="ok-tone-muted">That canvas cannot be shown here.</p>`;
  const page = /html/i.test(got.mime || "");
  return html`<div class="arena-cview" data-name=${got.name}>
    <p class="arena-cap">${p.title ? `${p.title} · ` : ""}${got.name}</p>
    ${got.data ? html`<img class="arena-cview__pic" alt=${p.title || got.name} src=${`data:${got.mime};base64,${got.data}`} />`
      : page ? html`<iframe class="arena-cview__page" sandbox="" title=${p.title || got.name} srcdoc=${got.text}></iframe>`
      : html`<pre class="shell-log shell-doc__text" aria-label=${got.name}>${got.text}</pre>`}
  </div>`;
}

function Card({ c, fresh = false, isSeen = false, onSeen = null }) {
  const [busy, setBusy] = useState(false);
  const link = c.host && c.url, when = whenWords(c.at);
  const seen = async () => { setBusy(true); await onSeen(c); setBusy(false); };
  return html`<div class=${cls("arena-canvas ork-frame", { "is-drawn": fresh })} data-key=${c.key} data-kind=${c.kind} data-tool=${c.tool}>
    <div class="arena-canvas__top"><${WhoHead} head=${c.head} small=${true} /><span class="arena-canvas__kind">${KIND_WORDS[c.kind] || c.kind}</span></div>
    <p class="arena-canvas__title">${c.title || KIND_WORDS[c.kind] || ""}</p>
    <span class="arena-cap">${[c.tool_word, when].filter(Boolean).join(" · ")}</span>
    ${c.idea && c.task && html`<button type="button" class="arena-link arena-canvas__goal" title="Open the task that drew it" onClick=${() => showTask(c.idea, c.task, { via: "map" })}>${c.idea_title || c.idea}</button>`}
    ${!link && c.link_text && html`<span class="arena-cap arena-canvas__text" data-text>${c.link_text}</span>`}
    <div class="arena-canvas__acts">
      ${link && html`<button type="button" class="ork-btn" title="Opens it in your browser" onClick=${() => ask("ideas.canvas_open", { key: c.key })}>${OPEN_WORDS[c.host] || `Open on ${c.host}`}</button>`}
      ${c.local && html`<button type="button" class="ork-btn" title="Shows its file in the drawer" onClick=${() => show({ kind: "canvas", path: c.key, title: c.title })}>Show here</button>`}
      ${!isSeen && html`<button type="button" class="ork-btn" disabled=${busy} title="Folds it into Seen" onClick=${seen}>Seen</button>`}
    </div>
  </div>`;
}

/** The right column's row: *Canvases · n*, and in it, after the cards, *Seen · k* once a canvas has been seen. */
export function Canvases() {
  const t = town.value, rev = t?.canvases_rev ?? 0, count = t?.canvases_new ?? 0, project = currentProject.value?.path || "";
  const timer = useRef(0);
  const { canvases, seen } = data.value;
  const load = async () => {
    if (!await read(project)) return;
    clearTimeout(timer.current);
    timer.current = setTimeout(() => { drawn.value = []; }, DRAWN_MS);
  };
  useEffect(() => { load(); }, [rev, project, open.value]);
  useEffect(() => () => clearTimeout(timer.current), []);
  const done = async (c) => { await ask("ideas.canvas_seen", { key: c.key }); await load(); };
  if (!count && !canvases.length && !seen.length) return null;
  return html`<section class="arena-canvases" aria-label="Canvases">
    <${FoldRow} word="Canvases" n=${count} open=${open.value} toggle=${() => { open.value = !open.value; }} />
    ${open.value && html`<div class="arena-canvases__list">
      ${canvases.map((c) => html`<${Card} key=${c.key} c=${c} fresh=${drawn.value.includes(c.key)} onSeen=${done} />`)}
      ${!canvases.length && html`<p class="arena-cap">Nothing new. What an AI tool draws comes here.</p>`}
      ${seen.length > 0 && html`<${FoldRow} word="Seen" n=${seen.length} open=${seenOpen.value} toggle=${() => { seenOpen.value = !seenOpen.value; }} kind="arena-canvases__seen" />
        ${seenOpen.value && seen.map((c) => html`<${Card} key=${c.key} c=${c} isSeen=${true} />`)}`}
    </div>`}
  </section>`;
}
