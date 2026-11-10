// A goal of the discard as a post (goal 170 B, decisions §293.4): the one post of post.js (round, its party's top edge, the leader's round head, its name, *when*, ···) for a goal ready for main, done and not yet seen, or waiting for dev. The discard's parts keep what they were
// (lane.js lays the piles, plates.js the plates, discard.js the face of the narrow pile); this file only says how a goal there looks and what its acts are: the goal's name pressed picks it (or plays it, in the lower pile), and **To main** on the goal ready for main sends it the
// way it went before (portal.js `toMain`: its plan, its checks, then `ideas.to_main`). No count anywhere. A post picked, taken along by the portal, going in or dissolving into the ring says so in its data (discard.css).
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { Icon, Sign } from "../orkui.js";
import { GoalLine, PostCard, PostHead, whoOf } from "./post.js";
import { alongOf, chosenSlug, dissolving, going, toMain } from "./portal.js";
import { redOf } from "./checks.js";

const ORKMASTER = "orkmaster";

/** One goal of the discard as a post. `g`: the goal (`slug`, `title`, `party` or `goal`); `kind`: "ready" (the one ready for main), "ready-more", "done", "lower"; `sub`: the line under the leader's name; `line`: a caption under the goal. `onPick(slug)`: the goal's name, or the post, pressed.
 *  `toMainWord`: given (the branch's name), the post has the act *To main* (`onToMain()`); `busy`: the act waits. */
export function DonePost({ g, kind, sub, line = "", picked = false, along = false, dealing = "", moon = false, onPick, toMainWord = "", onToMain = null, busy = false, label = "" }) {
  const leader = g.party || g.goal || ORKMASTER, w = whoOf(leader), name = g.title || g.short || g.slug, melting = dissolving.value.includes(g.slug), gone = going.value === g.slug, ready = kind.startsWith("ready");
  const press = (e) => { if (!e.target.closest("button")) onPick(g.slug); };
  const data = { "data-slug": g.slug, "data-portal-card": ready ? g.slug : undefined, "data-picked": picked ? "true" : undefined, "data-along": along ? "1" : undefined, "data-melting": melting ? "1" : undefined, "data-going": gone ? "1" : undefined,
    "data-dealt": dealing || undefined, "data-moon": moon ? "1" : undefined, "data-portal": kind === "ready" ? "1" : undefined, onClick: press };
  return html`<${PostCard} leader=${leader} kind=${ready ? "main" : kind} data=${data} label=${label || `${w.name}: ${name}`}>
    <${PostHead} leader=${leader} sub=${sub} />
    <${GoalLine} slug=${g.slug} name=${name} sign="check" onPick=${onPick} />
    ${moon && html`<p class="post-card__sub post-card__moon"><${Sign} name="moon" label="Done in the night" /><span>Done in the night</span></p>`}
    ${line && html`<p class="post-card__sub">${line}</p>`}
    ${toMainWord && html`<div class="post-card__acts"><button type="button" class="ork-btn primary" data-act="to_main" disabled=${busy} title=${`Sends the goal through the portal to ${toMainWord}: its checks run first, nothing reaches ${toMainWord} without you`} onClick=${onToMain}><${Icon} name="git-merge" /><span>To ${toMainWord}</span></button></div>`}
  </${PostCard}>`;
}

/** The goals ready for main, each a post; with `ringed` the first is the one the portal rings and has *To main*. `on`: the goal picked; `onPress(slug)`: a post pressed (picked). */
export function ReadyPosts({ goals, main, on = "", onPress, ringed = false }) {
  const [busy, setBusy] = useState(false), held = chosenSlug() || on;
  const go = async (slug) => { setBusy(true); try { if (on !== slug) onPress(slug); await toMain(slug); } finally { setBusy(false); } };
  return html`<ul class="discard-posts" aria-label=${goals.some((g) => redOf(g.slug, g)) ? "Goals awaiting checks before main" : `Goals ready for ${main}`}>${goals.map((g, i) => {
    const red = redOf(g.slug, g), top = ringed && i === 0, along = !!held && held !== g.slug && alongOf(held).has(g.slug);
    return html`<li key=${g.slug}><${DonePost} g=${g} kind=${top ? "ready" : "ready-more"} sub=${red ? "checks failed" : "ready"} picked=${on === g.slug} along=${along} onPick=${onPress}
      toMainWord=${top ? main : ""} busy=${busy} onToMain=${() => go(g.slug)} label=${`${g.title}, ${red ? "checks failed" : `ready for ${main}`}`} /></li>`;
  })}</ul>`;
}
