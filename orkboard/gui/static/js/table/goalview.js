// A goal picked, at a leader's tab (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md F.2–F.3, decisions §206.4, §206.8; mockup docs/mockups/goal-card/ `changeHtml`, `resultHtml`, `sideHtml`): the pane shows **another view** in place of the leader's map.
// **A goal agreed or at work: what it will change** at this leader's level — the parts of its map the goal touches (the *Will be* lines of the leader's section of the spec, §104), each a card with its name, *New*, *Changes* or *Read only* and its lines
// (+ added, ~ changed); Tech's *Contract* as a diff of those lines; Design's screens *Now* → *Will be*. **A goal done: what it changed against what its spec promised**, each part ✓ *As promised*, ≠ *Not quite*, + *More than promised* or ✗ *Not done*
// (realm/goal_result.py), and its *Done when*, checked where the host can say so. Beside it, a small whole map with the parts lit, the section's *Done when* and the goal's tasks at this leader. A part pressed opens this leader's bubble about it (ask.js `openAsk`,
// spec 128 E). Nothing here changes the goal; Esc or the × in the pane's title picks nothing and the leader's map is back. The data is goalmap.js's; the sheet goalview.css.
import { html, cls } from "../html.js";
import { Elem, Icon } from "../orkui.js";
import { usePicture } from "./screenparts.js";
import { usePage, readSpec } from "./specpage.js";
import { leadsSystem, nameOf, partiesAll } from "./data.js";
import { openAsk } from "./ask.js";
import { partFor, partsOf, useMap, useResult, names } from "./goalmap.js";
import { TASK_STATE } from "../board/maplayout.js";
import { BeforeAfter, Errors, ResultScheme, VERDICT } from "./resultboard.js";

export const KIND_WORDS = { new: "New", changed: "Changes", read: "Read only", gone: "Goes" };
export { VERDICT };                                                     // the verdicts' marks and words are resultboard.js' (spec 168 G2)
const SIGN_OF = (l) => (l.startsWith("+") ? "is-add" : l.startsWith("~") ? "is-chg" : l.startsWith("-") ? "is-del" : l.startsWith("≠") ? "is-dif" : "");

const Lines = ({ lines }) => html`<ul class="gv-lines">${lines.map((l, i) => html`<li key=${i} class=${SIGN_OF(l)}>${l}</li>`)}</ul>`;

/** Design's screen, now and as it will be: the picture of the screen as it is (none for a new one), then a wireframe for the one that will be. */
export function Pair({ part, info }) {
  const p = partFor(info, part.id), src = usePicture(p?.picture || null);
  return html`<div class="gv-pair"><figure><span class=${cls("gv-ph", { "is-none": !src })}>${src ? html`<img src=${src} alt=${`${part.name}, as it is now`} draggable="false" />` : html`<em>${part.kind === "new" ? "none" : "no picture yet"}</em>`}</span><figcaption>Now</figcaption></figure>
    <span class="gv-pair__arrow"><${Icon} name="arrow-right" /></span>
    <figure><span class="gv-ph is-will" aria-hidden="true"><i></i><b></b><i class="s"></i><i></i></span><figcaption>Will be</figcaption></figure></div>`;
}

/** A part of the map as a card. A card of what will change is pressable: it opens the leader's bubble with the part as its mark (ask.js). */
function PartCard({ g, part, info, done = false }) {
  const press = () => openAsk(g.slug, { id: part.id, name: part.name }), v = VERDICT[part.verdict];
  const keys = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); press(); } };
  const screens = info?.kind === "screens" && !done && part.kind !== "read";
  return html`<div class=${cls("ork-card gv-card", done && `is-${part.verdict}`, !done && `is-${part.kind}`)} role="button" tabindex="0" data-part=${part.id} data-kind=${done ? part.verdict : part.kind} onClick=${press} onKeyDown=${keys}
    aria-label=${`${part.name}: ${done ? v[1] : KIND_WORDS[part.kind]}. Ask ${nameOf(g)} about it`}>
    <div class="gv-card__hd"><b class="gv-card__nm">${part.name}</b><span class=${cls("gv-kind", done ? `k-${part.verdict}` : `k-${part.kind}`)}>${done ? `${v[0]} ${v[1]}` : KIND_WORDS[part.kind]}</span></div>
    ${screens && html`<${Pair} part=${part} info=${info} />`}
    <${Lines} lines=${part.lines} />
    <span class="gv-ask"><${Icon} name="arrow-right" />Ask ${nameOf(g)} about it</span>
  </div>`;
}

/** Tech's contract as a diff: the lines of the section's *Will be*, one a line (+ new, ~ changed, − gone), with their notes. */
function Contract({ will }) {
  const rows = will.filter((w) => w.id && w.kind);
  if (!rows.length) return null;
  const sign = { new: "+", changed: "~", gone: "-" };
  return html`<section class="gv-sec" aria-label="Contract"><h3 class="ork-label">Contract</h3>
    <pre class="gv-diff">${rows.map((w, i) => html`<span key=${i} class=${w.kind === "new" ? "add" : w.kind === "gone" ? "del" : "ctx"}>${`${sign[w.kind]} ${w.id}${w.note ? ` — ${w.note}` : ""}`}${"\n"}</span>`)}</pre></section>`;
}

/** The small whole map: its parts as blocks by group, the goal's lit (`lit`: ids), the ones read only half-lit. */
function Mini({ info, will, read }) {
  if (!info) return null;
  const lit = new Set(info.parts.filter((p) => will.some((w) => names(info, w.id, p))).map((p) => p.id)), half = new Set(read.map((p) => p.id)), made = will.filter((w) => w.kind === "new" && !partFor(info, w.id));
  return html`<div class="gv-mini" role="img" aria-label=${`The whole table, with ${lit.size + made.length} ${lit.size + made.length === 1 ? "part" : "parts"} lit`} data-kind=${info.kind}>
    ${info.groups.map((c, i) => html`<div key=${i} class="gv-mini__col">${c.ids.map((id) => html`<i key=${id} class=${cls("gv-mini__b", { "is-lit": lit.has(id), "is-read": half.has(id) })} data-id=${id}></i>`)}</div>`)}
    ${made.length > 0 && html`<div class="gv-mini__col">${made.map((w) => html`<i key=${w.id} class="gv-mini__b is-lit is-new" data-id=${w.id}></i>`)}</div>`}
  </div>`;
}

/** The side: the small map (a goal done: the map with its parts planned and built, resultboard.js), the leader's *Done when* (checked once the goal is done and the host can say it), the goal's tasks here. */
function Side({ g, n, info, will, read, dones, tasks, done, cards }) {
  return html`<aside class="gv-side" aria-label="Where it lies">
    ${done ? html`<${ResultScheme} info=${info} cards=${cards} />` : info && html`<div class="gv-side__map"><span class="ork-label">Where, on the whole table</span><${Mini} info=${info} will=${will} read=${read} /></div>`}
    ${dones.length > 0 && html`<section class="gv-sec" aria-label="Done when"><h3 class="ork-label">${done ? "Done when, checked" : "Done when"}</h3>
      <ul class="gv-lines gv-done">${dones.map((x, i) => html`<li key=${i} class=${cls({ "is-ok": x.state === "ok" })} data-state=${x.state || undefined}>${x.state === "ok" ? "✓ " : ""}${x.text}${x.word ? html` <span class="cap gv-word">· ${x.word}</span>` : ""}</li>`)}</ul></section>`}
    <section class="gv-sec" aria-label="Its tasks here"><h3 class="ork-label">Its tasks here</h3>
      ${tasks.length ? html`<ul class="gv-lines gv-tasks">${tasks.map((t) => html`<li key=${t.id} data-task=${t.id} data-state=${t.state}>${t.short || t.title} · ${t.state === "merged" ? "done" : TASK_STATE[t.state] || t.state}</li>`)}</ul>`
        : html`<p class="cap">None for ${nameOf(g)}.</p>`}</section>
  </aside>`;
}

/** The view of the goal `n` at the leader `g`'s tab. */
export function GoalView({ g, n }) {
  const done = n.state === "done", page = usePage(done ? "" : n.slug), res = useResult(n.slug, done), info = useMap(g);
  const parties = partiesAll(), spec = !done && page ? readSpec(page, parties, parties.find((x) => x.slug === n.goal) || null).sections.find((s) => s.party?.slug === g.slug) || null : null;
  const tasks = (n.tasks || []).filter((t) => t.state !== "dropped" && (t.party || n.goal) === g.slug);
  const will = spec?.will || [], mine = done ? res?.parties?.find((p) => p.party === g.slug) || null : null;
  const cards = done ? (mine?.parts || []).map((p) => ({ ...p, name: partFor(info, p.id)?.name || p.id.split("/").pop() || p.id, lines: [p.verdict === "ok" ? p.line : `${VERDICT[p.verdict][0]} ${p.line}`], kind: p.kind })) : partsOf(will, info);
  const dones = done ? mine?.done_when || [] : (spec?.done || []).map((text) => ({ text, state: "" }));
  const loading = done ? res === undefined : page === undefined;
  const lit = will.filter((w) => w.id && w.kind), read = cards.filter((c) => c.kind === "read").map((c) => ({ id: c.id }));
  const says = done ? `What it changed at ${nameOf(g)}’s level, against what its spec promised` : `What it will change, at ${nameOf(g)}’s level${n.state === "working" ? "" : " · its spec is ready"}`;
  const empty = !loading && !cards.length && !dones.length && !tasks.length;
  return html`<section class="gv" data-goal=${n.slug} data-party=${g.slug} data-view=${done ? "changed" : "will"} data-elem=${n.hue || n.element || undefined} aria-label=${`${n.title}: ${says}`}>
    <div class="gv-main">
      <header class="gv-title"><${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} big=${true} /><div><b>${n.title}</b><span>${says}</span></div></header>
      ${loading ? html`<p class="gv-empty" data-state="loading">Reading the spec…</p>`
        : empty ? html`<p class="gv-empty" data-state="none">${n.short || n.title}: nothing of it ${done ? "was" : "is"} on ${nameOf(g)}’s table. Its work is at the other leaders.</p>`
        : html`${cards.length > 0 ? html`<div class="gv-grid">${cards.map((c) => html`<${PartCard} key=${`${c.id}:${c.verdict || c.kind}`} g=${g} part=${c} info=${info} done=${done} />`)}</div>`
          : html`<p class="gv-empty" data-state="no-parts">${nameOf(g)}’s part of the spec does not name a part of its table.</p>`}
          ${!done && leadsSystem(g) && html`<${Contract} will=${will} />`}
          ${done && html`<${BeforeAfter} data=${res?.before_after?.[g.slug] || null} /><${Errors} errors=${(res?.errors || []).filter((e) => e.party === g.slug)} g=${g} />`}
          ${done && html`<p class="cap gv-play">The die in your hand wears its rune: press it to play the product with this goal in it.</p>`}`}
    </div>
    <${Side} g=${g} n=${n} info=${info} will=${lit} read=${read} dones=${dones} tasks=${tasks} done=${done} cards=${cards} />
  </section>`;
}
