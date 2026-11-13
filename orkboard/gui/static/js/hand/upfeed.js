// The project's feed on the phone (goal 169 F, decisions §291.5–§291.9; the mockup docs/mockups/phone/feed.html v3, screens 1, 2, 3 and 6): the phone's middle when no goal is picked (uplook.js), in place of §223's tabs. It draws the host's reader
// (`ideas.feed`, realm/board_feed.py) in its order and keeps none of its own: **the heads row** on top (the reader's `heads`, the Orkmaster then the leaders, each a 44 px button: a ring and the post sign beside it for news since the last look, the yellow ring and **!** for
// asking, never a number, its name 14 px under it); **what waits for you** (`waits`); **the news** (`posts`, newest first, one leader's posts in a row one stack); the goals at work as sideways cards with a button each way (the Orkmaster's block, after the news); **the seen
// line** (*You have seen everything since <time>*, its small heads; pressed it spreads its cards, each card's head showing). A post, a stack and a wait are table/post.js's, the part the desktop's lanes draw too (goal 170). **A head pressed** is `aria-pressed`, the others faint,
// a line says the feed shows only it, the feed narrowed to its posts (a party's: its goals at work and its concerns above them, upparty.js); pressed again the whole feed and no line. A party picked in the crown's menu is the same narrowed feed (`tab` its slug); the
// Orkmaster's narrowing is `onlyOrk`. **The last look** is this device's own (js/linkpaired.js `looked`, by the project's path), asked as `since`, again when the Board's snapshot changes, and written when the person leaves the feed (a goal picked, the project switched, the
// page hidden), never on its first draw. **A goal's feed** (`GoalFeed`, goal 169 G, screen 4) is the same reader cut to the goal's route, drawn in uplook.js's goal screen. No count anywhere. Layout only (upfeed.css, table/post.css); every colour, face and corner is orkUI's.
import { useEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { command, looked, town } from "../link.js";
import { ORKMASTER, openTab, picked, tab } from "../frame/state.js";
import { currentProject } from "../shell/projects.js";
import { nameOf, partiesAll } from "../table/data.js";
import { raceOf } from "../table/felt.js";
import { HeadOf, PostBody, PostCard, PostHead, Stack, Wait, when, whoOf } from "../table/post.js";
import { pickGoal } from "./entries.js";
import { workOf } from "./upmenu.js";
import { Concerns } from "./upparty.js";
import { PhoneCards } from "../cards/phone.js";           // the feed in cards (goal 170 P)

export const FEED = "ideas.feed";
export const onlyOrk = signal(false);                        // the Orkmaster's head pressed: the feed narrowed to its posts (a party's head narrows by `tab`)

/** The goals at work, each party's in the Board's order: `[{slug, name, element, hue, sign, phase, g}]`; one party's only when `g` is given. */
export const atWork = (g = null) => (g ? [g] : partiesAll()).flatMap((p) => workOf(p).map((r) => ({ ...r, g: p })));

/** The reader's answer, asked again when `since` or the Board's snapshot changes: `[feed | null, reload]`; a refusal keeps what was drawn. */
function useFeed(project, since, route = "") {
  const [got, setGot] = useState(null), n = useRef(0), snap = town.value;
  const load = () => {
    const k = ++n.current, args = { ...(since == null ? {} : { since }), ...(route ? { route } : {}) };
    command(FEED, args, true).then((r) => { if (k === n.current) setGot(r || {}); }).catch(() => { if (k === n.current) setGot((x) => x || {}); });
  };
  useEffect(() => { load(); }, [project, since, snap, route]);
  return [got, load];
}

/** This device's last look at the project, read on the feed's first draw and written when the person leaves it (never on its first draw). */
const drawn = new Map();                                       // the look each project's feed was last drawn with, by its path: a goal's feed reads it (the look is written when the person leaves the feed)
function useLook(project) {
  const [since, setSince] = useState(() => looked.get(project));
  useEffect(() => {
    setSince(looked.get(project));
    drawn.set(project, looked.get(project));
    if (!project) return undefined;
    const hide = () => { if (document.visibilityState === "hidden") looked.set(project); };
    document.addEventListener("visibilitychange", hide);
    return () => { document.removeEventListener("visibilitychange", hide); looked.set(project); };
  }, [project]);
  return since;
}

/** Goals laid as sideways cards, a button each way (44 px) beside the row that scrolls; a press on a card picks its goal. */
function Work({ goals, onPick, leader }) {
  const row = useRef(), [ends, setEnds] = useState({ l: false, r: goals.length > 1 });
  const edge = () => { const e = row.current; if (e) setEnds({ l: e.scrollLeft > 2, r: e.scrollLeft + e.clientWidth < e.scrollWidth - 2 }); };
  useEffect(edge, [goals.length]);
  const by = (dir) => {
    const e = row.current, c = e?.querySelector(".up-fd__gc");
    if (!e) return;
    const still = matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    e.scrollBy({ left: dir * ((c?.offsetWidth || 150) + 8), behavior: still ? "auto" : "smooth" });
  };
  return html`<${PostCard} leader=${leader} kind="work" label=${`${whoOf(leader).name}: goals at work`}>
    <${PostHead} leader=${leader} sub="at work" />
    <div class="up-fd__car" ref=${row} role="group" aria-label="Goals at work" onScroll=${edge}>${goals.map((r) => html`<button key=${r.slug} type="button" class="ork-card up-fd__gc" data-goal=${r.slug} data-race=${raceOf(r.g) || undefined}
        aria-label=${`${r.name}: ${r.phase}, ${nameOf(r.g)}`} onClick=${() => onPick(r.slug)}>
      <span class="up-fd__gtop"><${Elem} name=${r.element} hue=${r.hue} dim=${!r.element} />${r.sign && html`<${Sign} name=${r.sign} />`}</span><span class="up-fd__gcn">${r.name}</span>
      <span class="up-fd__gfoot">${r.g?.leader?.head && html`<${Head} race=${r.g.leader.head.race} tier=${r.g.leader.head.tier} />`}<span>${r.phase}</span></span></button>`)}</div>
    ${goals.length > 1 && html`<div class="up-fd__arrows"><button type="button" class="ork-btn up-fd__arrow" aria-label="Previous goals" disabled=${!ends.l} onClick=${() => by(-1)}><${Icon} name="chevron-left" /></button>
      <button type="button" class="ork-btn up-fd__arrow" aria-label="Next goals" disabled=${!ends.r} onClick=${() => by(1)}><${Icon} name="chevron-right" /></button></div>`}
  </${PostCard}>`;
}

/** The one seen line: what came before the last look, its heads small; pressed it spreads its cards, each card's head showing. */
function Seen({ seen, onPick }) {
  const [open, setOpen] = useState(false), at = when(seen.since);
  return html`<section class="up-fd__seen" aria-label="What you have seen">
    <button type="button" class="up-fd__seenline" aria-expanded=${String(open)} onClick=${() => setOpen(!open)}>
      <span class="up-fd__caught"><${Icon} name="check" /><span class="up-fd__seenwords">${at ? `You have seen everything since ${at}` : "You have seen everything"}</span></span>
      <span class="up-fd__seenrow"><span class="up-fd__smalls" aria-hidden="true">${seen.leaders.map((l) => html`<span key=${l} class="up-fd__small"><${HeadOf} w=${whoOf(l)} /></span>`)}</span>
        <span class="up-fd__seenwhat">${open ? "Fold what you have seen" : "What you have seen"}</span><${Icon} name=${open ? "chevron-up" : "chevron-down"} /></span></button>
    ${open && html`<div class="up-fd__spread">${seen.posts.map((p, i) => html`<${PostCard} key=${i} leader=${p.leader} kind="seen" label=${`${whoOf(p.leader).name}: ${p.text}`}>
      <${PostHead} leader=${p.leader} sub=${when(p.at)} /><${PostBody} p=${p} onPick=${onPick} /></${PostCard}>`)}</div>`}
  </section>`;
}

/** The heads row: the reader's heads in its order; the one the feed is narrowed to pressed, the others faint. */
function Heads({ heads, only, press }) {
  return html`<div class="up-fh" role="group" aria-label="The Orkmaster and the leaders">${heads.map((h) => {
    const w = whoOf(h.leader), on = only === h.leader, said = `${w.name}${h.asks ? ": asks you" : h.news ? ": news since your last look" : ""}`;
    return html`<button key=${h.leader} type="button" class=${cls("up-fh__head", { "is-news": !!h.news, "is-asks": !!h.asks, "is-faint": !!only && !on })} data-leader=${h.leader} data-race=${w.race || undefined}
        aria-pressed=${String(on)} aria-label=${said} title=${said} onClick=${() => press(h.leader)}>
      <span class="up-fh__ring"><span class="up-fh__gap"><span class="up-fh__disc"><${HeadOf} w=${w} size="mid" /></span></span></span>
      ${h.asks ? html`<span class="up-fh__ask" aria-hidden="true">!</span>` : h.news ? html`<span class="up-fh__news" aria-hidden="true"><${Sign} name="post" /></span>` : null}
      <span class="up-fh__name">${w.name}</span></button>`;
  })}</div>`;
}

/** The narrowing a head's press makes: the same head again lets it go; the Orkmaster's by `onlyOrk`, a party's by its tab (the crown's menu picks it the same way). */
export function pressHead(leader, only) {
  if (leader === only) { onlyOrk.value = false; if (tab.value !== ORKMASTER) openTab(ORKMASTER); return; }
  picked.value = "";
  onlyOrk.value = leader === ORKMASTER;
  openTab(leader === ORKMASTER ? ORKMASTER : leader);
}

/** The feed. `g`: the party it is narrowed to (a party picked in the menu or its head pressed), null for none; `entries`: the hand's, so a goal with a card is picked as that card. */
export function Feed({ g, entries }) {
  const project = currentProject.value?.path || "", since = useLook(project), [feed, reload] = useFeed(project, since), onPick = (slug) => pickGoal(entries, slug);
  useEffect(() => () => { onlyOrk.value = false; }, []);                                  // left: the whole feed next time
  const only = g ? g.slug : onlyOrk.value ? ORKMASTER : "", mine = (x) => !only || x.leader === only;
  const heads = feed?.heads || [], waits = (feed?.waits || []).filter(mine), stacks = (feed?.posts || []).filter(mine);
  const old = feed?.seen ? (feed.seen.posts || []).filter(mine) : [], seen = old.length ? { ...feed.seen, posts: old, leaders: (feed.seen.leaders || []).filter((l) => !only || l === only) } : null;
  const work = only && only !== ORKMASTER ? [] : atWork(), mineWork = g ? atWork(g) : [];
  const news = feed?.since ? `New since your last look · ${when(feed.since)}` : "News";
  const empty = feed && !waits.length && !stacks.length && !work.length && !mineWork.length && !seen;
  return html`<${PhoneCards} only=${only} party=${g ? g.slug : ""} heads=${html`<${Heads} heads=${heads} only=${only} press=${(l) => pressHead(l, only)} />`} waits=${waits} stacks=${stacks}
    news=${news} seen=${seen && html`<${Seen} seen=${seen} onPick=${onPick} />`} empty=${empty} onPick=${onPick} reload=${reload} concerns=${g && html`<${ConcernsBlock} g=${g} />`} />`;
}

/** A party's concerns as a block of its leader's, in the feed narrowed to it. */
const ConcernsBlock = ({ g }) => html`<div class="up-fd__concerns" data-leader=${g.slug}><${Concerns} slug=${g.slug} /></div>`;

/** A goal's feed (goal 169 G; feed.html v3 screen 4): the same reader cut to the goal's route (`ideas.feed` with `{since, route}`), drawn under the goal's header, its card and its phases (uplook.js): the heads row the reader's heads for the route (the Orkmaster, then the
 *  route's leaders in route order), then the goal's waits and posts in the reader's order and the seen line; it keeps no order of its own. A head pressed narrows to its posts, the goal staying picked; pressed again the whole goal's feed. Its `since` is the look the
 *  project's feed was drawn with this visit (written when the person left it), else this device's last look; it writes none. `entries`: the hand's, so a goal named in a post is picked as its card. */
export function GoalFeed({ slug, entries }) {
  const project = currentProject.value?.path || "", since = drawn.has(project) ? drawn.get(project) : looked.get(project);
  const [feed, reload] = useFeed(project, since, slug), [only, setOnly] = useState(""), onPick = (s) => pickGoal(entries, s);
  const mine = (x) => !only || x.leader === only, heads = feed?.heads || [], waits = (feed?.waits || []).filter(mine), stacks = (feed?.posts || []).filter(mine);
  const old = feed?.seen ? (feed.seen.posts || []).filter(mine) : [], seen = old.length ? { ...feed.seen, posts: old, leaders: (feed.seen.leaders || []).filter((l) => !only || l === only) } : null;
  const news = feed?.since ? `New since your last look · ${when(feed.since)}` : "News";
  if (!heads.length && !waits.length && !stacks.length && !seen) return null;
  return html`<section class="up-feed up-gfeed" data-route=${slug} data-only=${only || undefined} aria-label="Its feed">
    <${Heads} heads=${heads} only=${only} press=${(l) => setOnly(l === only ? "" : l)} />
    ${only && html`<p class="up-fd__only" role="status">The feed shows only ${whoOf(only).name}</p>`}
    ${waits.length > 0 && html`<p class="up-lab up-fd__lab">Waits for you</p>${waits.map((w) => html`<${Wait} key=${`${w.kind}:${w.goal}`} w=${w} onPick=${onPick} onDone=${reload} />`)}`}
    ${stacks.length > 0 && html`<p class="up-lab up-fd__lab">${news}</p>${stacks.map((s, i) => html`<${Stack} key=${`${s.leader}:${s.post.at}:${i}`} s=${s} onPick=${onPick} />`)}`}
    ${seen && html`<${Seen} seen=${seen} onPick=${onPick} />`}
  </section>`;
}
