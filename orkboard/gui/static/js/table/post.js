// One post of a feed, the part both faces draw (goal 169 F, goal 170: one post part for the phone's feed and the desktop's lanes; decisions §291.5–§291.9; the mockup docs/mockups/phone/feed.html v3): a card of orkUI's, **its party's colour as its top edge**
// (`data-race`, table/look.css `--party-hue`; the Orkmaster's its own token), **its head** the leader's round head, its name in the heading face, *when* under it in the muted ink and the dots at its right; then its body (the post's words, the alert sign before a concern's, the
// goal it is about) or what waits (a spec's clock, a goal's way to main) with **only its own acts**, each the command the host's reader names (realm/board_feed.py; *Change the spec* asks the words first). **One leader's posts in a row are one stack**: the edges of the rest
// under its card, *More from <leader>* opening them. It knows nothing of the face it lies in and nothing of the window's state (frame/state.js): a goal pressed is the caller's `onPick(slug)`, a wait's act done is its `onDone()`. Layout only (table/post.css); every colour, face and corner is orkUI's.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { command } from "../link.js";
import { mapData } from "../shell/store.js";
import { nameOf, partiesAll } from "./data.js";
import { raceOf } from "./felt.js";

const ORKMASTER = "orkmaster";                                                                            // the reader's leader of a post that names no party
export const ACTS = { change_spec: "Change the spec", start_now: "Start now", to_main: "To main" };       // a wait's acts in words, by the reader's `act`
export const KINDS = { news: "news", concern: "a concern", change: "a change" };                         // a post's kind in its head's line
const two = (n) => String(n).padStart(2, "0");
const orkHeadOf = () => { const o = mapData.value?.project?.orkmaster || null; return { race: o?.race || "peon", tier: o?.tier || "crown" }; };      // the project's Orkmaster, as hand/context.js says it

/** A post's time in words: *12:40* today, *yesterday · 18:05*, else its day and time; "" for none. */
export function when(at, now = new Date()) {
  const d = at ? new Date(at) : null;
  if (!d || Number.isNaN(+d)) return "";
  const hm = `${two(d.getHours())}:${two(d.getMinutes())}`, day = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const back = Math.round((day(now) - day(d)) / 864e5);
  return back === 0 ? hm : back === 1 ? `yesterday · ${hm}` : `${d.toLocaleDateString([], { day: "numeric", month: "short" })} · ${hm}`;
}

/** Who says a post: the Orkmaster or a party's leader, `{name, head, race, g}` (`race` "" for the Orkmaster, whose colour is its own). */
export function whoOf(leader) {
  if (leader === ORKMASTER) return { name: "Orkmaster", head: orkHeadOf(), race: "", g: null };
  const g = partiesAll().find((x) => x.slug === leader) || null;
  return { name: g ? nameOf(g) : leader, head: g?.leader?.head || null, race: g ? raceOf(g) : "", g };
}

/** A leader's head. */
export const HeadOf = ({ w, size = "" }) => (w.head ? html`<${Head} race=${w.head.race} tier=${w.head.tier} size=${size} />` : null);

/** A post's head: the leader's round head, its name, the line under it (when, what kind), the dots. */
export function PostHead({ leader, sub }) {
  const w = whoOf(leader);
  return html`<header class="post-card__who"><span class="post-card__av"><${HeadOf} w=${w} /></span>
    <span class="post-card__by"><b class="post-card__name">${w.name}</b>${sub && html`<small class="post-card__sub">${sub}</small>`}</span><span class="post-card__dots" aria-hidden="true"><${Icon} name="more-horizontal" /></span></header>`;
}

/** A goal named in a post: its rune and short name, a press is `onPick(slug)`; words alone when the Board no longer has it or nothing picks. `small`: under a post's words. */
export function GoalLine({ slug, name, onPick, sign = "", small = false }) {
  const n = (mapData.value?.nodes || []).find((x) => x.slug === slug);
  const face = html`<${Elem} name=${n?.element || ""} hue=${n?.hue || ""} dim=${!n?.element} />${sign && html`<${Sign} name=${sign} />`}<span class="post-card__gname">${name || n?.short || n?.title || slug}</span>`;
  if (!n || !onPick) return html`<p class=${cls("post-card__goal is-gone", { "is-small": small })}>${face}</p>`;
  return html`<button type="button" class=${cls("post-card__goal", { "is-small": small })} data-goal=${slug} onClick=${() => onPick(slug)}>${face}</button>`;
}

/** A post's body: its words, the alert sign before a concern's, the goal it is about. */
export function PostBody({ p, onPick }) {
  return html`<p class="post-card__text" data-kind=${p.kind}>${p.kind === "concern" && html`<${Sign} name="alert" />`}<span>${p.text}</span></p>
    ${p.goal && html`<${GoalLine} slug=${p.goal} onPick=${onPick} small=${true} />`}`;
}

/** The card a post lies on: orkUI's, its party's colour its top edge; reached by the keys (`tabindex`), said by `label`. `kind`: its modifier (news, wait, work, seen). */
export function PostCard({ leader, kind, label, stacked = false, data = {}, children }) {
  const w = whoOf(leader);
  return html`<article class=${cls(`ork-card post-card post-card--${kind}`, { "is-stacked": stacked })} data-leader=${leader} data-race=${w.race || undefined} tabindex="0" aria-label=${label} ...${data}>${children}</article>`;
}

const subOf = (p) => [KINDS[p.kind] || KINDS.news, when(p.at)].filter(Boolean).join(" · ");

/** One post, read whole. */
export const Post = ({ p, onPick }) => html`<${PostCard} leader=${p.leader} kind="news" label=${`${whoOf(p.leader).name}: ${p.text}`}><${PostHead} leader=${p.leader} sub=${subOf(p)} /><${PostBody} p=${p} onPick=${onPick} /></${PostCard}>`;

/** One leader's posts in a row (`{leader, post, more}`): its newest post, the edges of the rest under its card until *More from <leader>* opens them. */
export function Stack({ s, onPick }) {
  const [open, setOpen] = useState(false), more = s.more || [], w = whoOf(s.leader);
  return html`<${PostCard} leader=${s.leader} kind="news" stacked=${more.length > 0 && !open} label=${`${w.name}: ${s.post.text}`}>
    <${PostHead} leader=${s.leader} sub=${subOf(s.post)} />
    <${PostBody} p=${s.post} onPick=${onPick} />
    ${open && more.map((p, i) => html`<div key=${i} class="post-card__more"><small class="post-card__sub">${subOf(p)}</small><${PostBody} p=${p} onPick=${onPick} /></div>`)}
    ${more.length > 0 && html`<button type="button" class="post-card__open" aria-expanded=${String(open)} onClick=${() => setOpen(!open)}><${Icon} name=${open ? "chevron-up" : "chevron-down"} /><span>${open ? `Less from ${w.name}` : `More from ${w.name}`}</span></button>`}
  </${PostCard}>`;
}

/** What waits for the person (the reader's `waits`): a spec that starts by itself at a clock time, a goal done and waiting for main; only its own acts, each the command the reader names. `onDone()`: after an act was sent. */
export function Wait({ w, onPick, onDone = () => {} }) {
  const [writing, setWriting] = useState(false), [text, setText] = useState(""), [busy, setBusy] = useState(false), field = useRef();
  const acts = w.acts || [], change = acts.find((a) => a.act === "change_spec"), main = w.kind === "main", ready = w.main_ready !== false;
  useEffect(() => { if (writing) field.current?.focus(); }, [writing]);
  const run = async (a, args = a.args) => {
    if (busy) return;
    setBusy(true);
    try { await command(a.command, args); setWriting(false); setText(""); } catch { /* the host's words are in a toast */ }
    setBusy(false);
    onDone();
  };
  return html`<${PostCard} leader=${w.leader} kind="wait" data=${{ "data-wait": w.kind, "data-goal": w.goal }} label=${`${whoOf(w.leader).name}: ${w.short}${main ? ", waits for main" : ""}`}>
    <${PostHead} leader=${w.leader} sub=${main ? "done · waits for main" : "the plan"} />
    <${GoalLine} slug=${w.goal} name=${w.short} sign=${main ? "check" : ""} onPick=${onPick} />
    ${w.kind === "starts" && w.at && html`<p class="post-card__clock"><${Icon} name="clock" /><span>Starts by itself at ${when(w.at)}</span></p>`}
    ${main && !ready && w.main_reason && html`<p class="post-card__sub">${w.main_reason}</p>`}
    <div class="post-card__acts">${acts.map((a) => (a === change
      ? html`<button key=${a.act} type="button" class="ork-btn" data-act=${a.act} aria-expanded=${String(writing)} onClick=${() => setWriting(!writing)}><${Icon} name="pencil" /><span>${ACTS[a.act]}</span></button>`
      : a.act === "to_main" ? html`<button key=${a.act} type="button" class="ork-btn primary" data-act=${a.act} disabled=${busy || !ready} onClick=${() => run(a)}><${Icon} name="git-merge" /><span>${ACTS[a.act]}</span></button>`
      : html`<button key=${a.act} type="button" class="post-card__link" data-act=${a.act} disabled=${busy} onClick=${() => run(a)}>${ACTS[a.act] || a.act}</button>`))}</div>
    ${writing && change && html`<div class="post-card__write"><textarea ref=${field} class="ork-field" rows="3" aria-label="What to change in the spec" value=${text} onInput=${(e) => setText(e.currentTarget.value)}></textarea>
      <button type="button" class="ork-btn primary" data-act="send" disabled=${busy || !text.trim()} onClick=${() => run(change, { ...change.args, text: text.trim() })}>Send</button></div>`}
  </${PostCard}>`;
}
