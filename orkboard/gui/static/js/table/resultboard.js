// The result tables of a goal done (docs/specs/168-the-window-played-as-a-card-games-table.md G2, decisions §283.16.10, §283.16.11): a goal done and picked shows what the spec planned against what was built, each leader's problems lit.
//  - **Through the Orkmaster** (`ResultTable`): the Orkmaster's lanes, a lane a leader of the goal. In a leader's lane a big card (144 x 202) says what its section planned against what was built (the parts and the *Done when* lines, in the honest words of
//    realm/goal_result.py: *as promised* only where it was met, else *not checked*, *not met*, *landed, not compared*), and under it that leader's problems lit: a small card (56 x 78, danger or alert frame, its count in the middle) for each kind of problem and
//    a line for each problem (a *Done when* line not met or not checked, a failed or sent-back task, a red test, a finding left). A card pressed picks the goal at that leader's tab.
//  - **Through a leader** (`ResultScheme`, `BeforeAfter`, `Errors`, laid by goalview.js under its cards): the leader's map with each part of the goal marked, planned (outlined) against built (filled); the work **before and after** where the code keeps both
//    (Tech's System at the commit before the goal and at its last, Design's picture of a screen before and after); and every error of the goal's work at this leader as a line.
// The data is `ideas.goal_result` (goalmap.js `useResult`): `parties`, `errors`, `before_after`. Two card sizes only: 144 x 202 and 56 x 78. Layout is resultboard.css.
import { html, cls } from "../html.js";
import { Elem, Sign } from "../orkui.js";
import { CornerFoot, CornerTop } from "./corners.js";
import { SmallCard } from "./smallcard.js";
import { Lanes } from "./stagelanes.js";
import { leadersOf, open } from "./stageboard.js";
import { partiesNow, nameOf } from "./data.js";
import { useResult } from "./goalmap.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./resultboard.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const VERDICT = { ok: ["✓", "As promised"], landed: ["○", "Landed, not compared"], differs: ["≠", "Not quite"], extra: ["+", "More than promised"], missing: ["✗", "Not done"] };
/** The kinds of problem, in the order they are laid: their words and the frame they light (a card that failed or was not met: danger; one that waits for a look: alert). */
export const PROBLEMS = { not_met: ["Not met", "danger"], failed: ["Failed", "danger"], test: ["Red test", "danger"], not_checked: ["Not checked", "alert"], finding: ["Finding", "alert"], sent_back: ["Sent back", "alert"] };

/** The problems of one leader: its *Done when* lines not met or not checked, then the errors of its work (realm/goal_errors.py). `[{kind, text, task?}]` */
export function problemsOf(row, errors = []) {
  const out = [];
  for (const x of row?.done_when || []) if (x.state !== "ok") out.push({ kind: x.state === "unmet" ? "not_met" : "not_checked", text: x.text });
  for (const e of errors) out.push({ kind: e.kind, task: e.task, text: e.kind === "test" ? `${e.line} · ${e.title}` : e.kind === "finding" ? e.line : `${e.title}: ${e.line}` });
  return out;
}

/** What a leader's section planned against what was built: `{planned, built, by: {verdict: n}, met, unmet, unchecked}`. A part nothing promised (*More than promised*) is not planned; built is a promised part that is *as promised* or *landed*. */
export function summaryOf(row) {
  const parts = row?.parts || [], by = {}, dones = row?.done_when || [];
  parts.forEach((p) => { by[p.verdict] = (by[p.verdict] || 0) + 1; });
  const promised = parts.filter((p) => p.verdict !== "extra");
  return { planned: promised.length, built: promised.filter((p) => p.verdict === "ok" || p.verdict === "landed").length, by, met: dones.filter((x) => x.state === "ok").length, unmet: dones.filter((x) => x.state === "unmet").length, unchecked: dones.filter((x) => x.state !== "ok" && x.state !== "unmet").length };
}

const lit = (problems) => (problems.some((p) => PROBLEMS[p.kind]?.[1] === "danger") ? "danger" : problems.length ? "alert" : "");

/** The problems as a line each, a tag first. */
function Lines({ problems }) {
  return html`<ul class="rb-lines" aria-label="Problems">${problems.map((p, i) => html`<li key=${i} data-problem=${p.kind} data-task=${p.task || undefined}><b class=${cls("rb-tag", `is-${PROBLEMS[p.kind]?.[1]}`)}>${PROBLEMS[p.kind]?.[0] || p.kind}</b> ${p.text}</li>`)}</ul>`;
}

/** A leader's section as a big card: its name, what it planned against what was built, its *Done when* lines; its frame lit by its problems. */
function PlanCard({ n, g, row, signal }) {
  const s = summaryOf(row), kind = n.type?.sign || "", marks = ["ok", "landed", "differs", "missing", "extra"].filter((v) => s.by[v]).map((v) => `${VERDICT[v][0]} ${s.by[v]}`).join(" · ");
  const dones = [s.met && `${s.met} met`, s.unmet && `${s.unmet} not met`, s.unchecked && `${s.unchecked} not checked`].filter(Boolean).join(" · ");
  return html`<button type="button" class=${cls("ork-card ork-leans table-card sb-spec rb-card", signal && `is-${signal}`, { [`el-${n.hue || n.element}`]: !!(n.hue || n.element) })} data-result-card=${g.slug} data-signal=${signal || undefined} data-goal=${n.slug}
    aria-label=${`${nameOf(g)}: planned ${s.planned}, built ${s.built}${dones ? `, ${dones}` : ""}`} onClick=${() => open(n.slug, g.slug)}>
    <${CornerTop} rune=${{ name: n.element, hue: n.hue, dim: !n.element, still: true }} kind=${kind} signal=${signal} />
    <span class="table-card__head"><span class="table-card__nm">${nameOf(g)}'s part</span></span>
    <span class="table-card__win is-window sb-spec__win"><span class="body sb-spec__lines rb-card__lines">
      <span data-line="built">Planned ${s.planned} · built ${s.built}</span>${marks && html`<span data-line="marks">${marks}</span>`}${dones && html`<span data-line="done">Done when: ${dones}</span>`}
      ${!s.planned && !dones && html`<span data-line="none">Nothing planned here</span>`}</span></span>
    <${CornerFoot} who=${g.leader?.head ? { heads: [g.leader.head] } : null} />
  </button>`;
}

/** A small card for each kind of problem of a leader: its count in the middle, the frame of its kind. */
function Smalls({ n, g, problems }) {
  const kinds = Object.keys(PROBLEMS).filter((k) => problems.some((p) => p.kind === k));
  if (!kinds.length) return null;
  return html`<div class="rb-smalls">${kinds.map((k) => {
    const count = problems.filter((p) => p.kind === k).length;
    return html`<${SmallCard} key=${k} n=${{ ...n, title: `${PROBLEMS[k][0]}: ${count}` }} parties=${[]} signal=${PROBLEMS[k][1]} preview=${false} onPress=${() => open(n.slug, g.slug)}
      picture=${html`<b class="rb-count">${count}</b>`} extra=${{ "data-problem": k, "data-party": g.slug, title: `${PROBLEMS[k][0]}: ${count}` }} />`;
  })}</div>`;
}

/** The leaders of the goal done, in the route's order, then any other the result names; only those that stand in a lane. */
const leadersOfResult = (n, res) => {
  const lanes = new Set(partiesNow().map((g) => g.slug)), out = [...leadersOf(n)];
  (res?.parties || []).forEach((p) => { if (lanes.has(p.party) && !out.includes(p.party)) out.push(p.party); });
  (res?.errors || []).forEach((e) => { if (lanes.has(e.party) && !out.includes(e.party)) out.push(e.party); });
  return out;
};

/** The Orkmaster's table of a goal done: a lane a leader, its planned against built and its problems lit. */
export function ResultTable({ n }) {
  const res = useResult(n.slug, true), leaders = leadersOfResult(n, res), all = res ? (res.parties || []).flatMap((p) => problemsOf(p, (res.errors || []).filter((e) => e.party === p.party))) : [];
  return html`<div class="sb sb--result" data-stage="result" data-goal=${n.slug}>
    <section class="sb-plate ork-plate rb-plate" data-view="result" aria-label=${`${n.title}: what it changed against what its spec planned`}>
      <${Elem} name=${n.element} hue=${n.hue} dim=${!n.element} />
      <b class="rb-plate__nm">${n.title}</b><span class="body">What it built against what its spec planned</span>
      <span class="table-grow"></span>
      ${res === undefined ? html`<span class="cap" data-state="loading">Reading the result…</span>` : res === null ? html`<span class="cap" data-state="none">The result cannot be read.</span>`
        : html`<span class="cap rb-plate__count" data-problems=${all.length}>${all.length ? `${all.length} to look at` : "Nothing lit"}</span>`}
    </section>
    <${Lanes} n=${n} stage="result" leaders=${leaders}>${(g) => {
      const row = res?.parties?.find((p) => p.party === g.slug) || null, errors = (res?.errors || []).filter((e) => e.party === g.slug), problems = problemsOf(row, errors);
      return html`<div class="rb-lane" data-leader=${g.slug} data-lit=${lit(problems) || undefined}>
        ${row ? html`<div class="sb-slot"><${PlanCard} n=${n} g=${g} row=${row} signal=${lit(problems)} /></div>` : res && html`<p class="rb-none" data-none=${g.slug}>Nothing of it was planned at ${nameOf(g)}</p>`}
        <${Smalls} n=${n} g=${g} problems=${problems} />
        ${problems.length > 0 && html`<${Lines} problems=${problems} />`}
      </div>`;
    }}<//>
  </div>`;
}

// -- through a leader ------------------------------------------------------------------------------------------------------------

/** The leader's map with each part of the goal marked: planned (outlined) and built (filled, by the verdict). `info`: goalmap.js `useMap`; `cards`: the leader's parts judged (`id`, `name`, `kind`, `verdict`). Null for a craft with no map. */
export function ResultScheme({ info, cards }) {
  if (!info || !cards.length) return null;
  const by = new Map(cards.map((c) => [c.id, c])), find = (p) => cards.find((c) => c.id === p.id || (info.kind === "parts" ? c.id.startsWith(`${p.id}/`) || p.id.startsWith(`${c.id}/`) : [p.name, p.path].includes(c.id) || [p.name, p.path].includes(c.name)));
  const marks = (p) => by.get(p.id) || find(p) || null, made = cards.filter((c) => !info.parts.some((p) => marks(p) === c));
  const chip = (id, name, c) => html`<li key=${id} class=${cls("rb-chip", { "is-planned": !!c && !!c.kind && c.kind !== "read", [`is-${c?.verdict}`]: !!c?.verdict })} data-id=${id} data-planned=${c && c.kind && c.verdict !== "extra" ? "1" : undefined} data-verdict=${c?.verdict || undefined}
    title=${c ? `${name}: ${VERDICT[c.verdict]?.[1] || c.verdict}` : name}>${c?.verdict ? `${VERDICT[c.verdict][0]} ` : ""}${name}</li>`;
  return html`<section class="gv-sec rb-scheme" aria-label="Planned and built" data-kind=${info.kind}>
    <h3 class="ork-label">Planned and built, on its table</h3>
    <div class="rb-scheme__cols">${info.groups.map((grp, i) => html`<ul key=${i} class="rb-scheme__col">${grp.ids.map((id) => { const p = info.parts.find((x) => x.id === id); return p && chip(p.id, p.name, marks(p)); })}</ul>`)}
      ${made.length > 0 && html`<ul class="rb-scheme__col">${made.map((c) => chip(c.id, c.name, c))}</ul>`}</div>
    <p class="cap rb-scheme__key"><i class="rb-key is-planned"></i> planned <i class="rb-key is-built"></i> built</p>
  </section>`;
}

const FILES = (c) => `${c} file${c === 1 ? "" : "s"}`;
const CHANGE = { new: "New", gone: "Gone", changed: "Changed", same: "Same" };

/** Tech's System before the goal and after it, a row for each part its files are in. */
function SystemPair({ data }) {
  const has = data.parts.length > 0;
  return html`<div class="rb-sys" data-kind="parts">
    <div class="rb-sys__hd"><span data-side="before">Before${data.before ? html` · <code>${data.before.short}</code>` : ""}</span><span></span><span data-side="after">After${data.after ? html` · <code>${data.after.short}</code>` : ""}</span></div>
    ${data.parts.map((r) => html`<div key=${r.path} class="rb-sys__row" data-part=${r.path} data-change=${r.change}>
      <span class="rb-sys__cell" data-side="before">${r.before ? html`<b>${r.name}</b> · ${FILES(r.before.count)}` : html`<em>not there</em>`}</span>
      <span class=${cls("rb-sys__chg", `is-${r.change}`)}>${CHANGE[r.change]}</span>
      <span class="rb-sys__cell" data-side="after">${r.after ? html`<b>${r.name}</b> · ${FILES(r.after.count)}${r.uses_new.map((u) => html`<span key=${u} class="rb-use is-add">+ uses ${u.split("/").pop()}</span>`)}${r.uses_gone.map((u) => html`<span key=${u} class="rb-use is-del">− uses ${u.split("/").pop()}</span>`)}` : html`<em>gone</em>`}</span>
    </div>`)}
    ${!has && html`<p class="cap rb-none" data-state="none">${data.none || "No part of the System changed."}</p>`}
    ${has && data.none && html`<p class="cap rb-none" data-state="partial">${data.none[0].toUpperCase() + data.none.slice(1)}: nothing is compared.</p>`}
  </div>`;
}

/** A picture of a screen at its card size (144 x 202), or the card that says none was kept. */
function Shot({ pic, side, name }) {
  return pic ? html`<figure class="ork-card rb-shot" data-side=${side}><img src=${pic.url} alt=${`${name}, ${side === "before" ? "before" : "after"} the goal`} draggable="false" /><figcaption>${side === "before" ? "Before" : "After"}</figcaption></figure>`
    : html`<figure class="ork-card rb-shot is-none" data-side=${side}><span><${Sign} name="screen" big=${true} /></span><figcaption>${side === "before" ? "Before" : "After"}: no picture kept</figcaption></figure>`;
}

/** Design's screens the goal changed, a row each: the picture before and the picture after. */
function ShotsPair({ data }) {
  return html`<div class="rb-shots" data-kind="screens">${data.screens.map((s) => html`<div key=${s.screen} class="rb-shots__row" data-screen=${s.screen}>
    <b class="rb-shots__nm">${s.name} <span class="cap">${s.path}</span></b><div class="rb-shots__pair"><${Shot} pic=${s.before} side="before" name=${s.name} /><${Shot} pic=${s.after} side="after" name=${s.name} /></div></div>`)}
    ${!data.screens.length && html`<p class="cap rb-none" data-state="none">No screen of the app changed.</p>`}</div>`;
}

/** The work before and after, where the code keeps both: `data` is the party's `before_after` of the result; nothing for a craft that keeps none. */
export function BeforeAfter({ data }) {
  if (!data) return null;
  return html`<section class="gv-sec rb-ba" aria-label="Before and after" data-kind=${data.kind}><h3 class="ork-label">Before and after</h3>
    ${data.kind === "screens" ? html`<${ShotsPair} data=${data} />` : html`<${SystemPair} data=${data} />`}</section>`;
}

/** Every error of the goal's work at this leader, a line each. */
export function Errors({ errors, g }) {
  const problems = problemsOf(null, errors);
  return html`<section class="gv-sec rb-errors" aria-label="Errors of its work"><h3 class="ork-label">Errors of its work</h3>
    ${problems.length ? html`<${Lines} problems=${problems} />` : html`<p class="cap" data-state="clean">No failed task, red test or finding was kept for ${nameOf(g)}.</p>`}</section>`;
}
