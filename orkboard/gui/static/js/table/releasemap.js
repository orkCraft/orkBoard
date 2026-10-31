// Release's map: dev and main (docs/specs/102-the-other-maps-and-picking-on-them.md §3.2, §5.5; decisions §137.3, §171.1; mockup docs/mockups/s3/ state 5). A card is a goal that is in dev and not in main — its element, its name, its sign,
// its commit in the label row and, at its right, the tick of the goal being in the merge —; under them, **To main** at the map's foot with the gate's words (what the merge takes, and a refusal in the gate's own words); *Since <version>*
// faint under that. As a train (docs/specs/117-each-lens-a-games-shape.md §9, sheet train.css): the goals are cars, oldest first (by `at`), coupled by a short line, each with its age under its title; before the car at `big_from` an upright dashed
// line says *From here the batch is big*; a car a hint calls stale (`data-heat`, the kit's) lies faint. **To main** is today's merge (`ideas.gate_merge`, as the discard's does it): it takes dev whole, so the tick is the data's (`ticked`), not a choice made here. Registered with maps.js for the craft `release`.
import { useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { command, toast } from "../link.js";
import { pick, picked } from "../frame/state.js";
import { mapData, refreshShell } from "../shell/store.js";
import { flagDay } from "../arena/goalwords.js";
import { mapFor } from "./maps.js";
import { MapBack, MapCard, MapFrame, Sec, Win, countWords, useLifted, useRead, useWidth } from "./mapkit.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as treemap.js links tree.css
  const href = new URL("./train.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const MAP = "release", SHORT = 7, DAY_S = 86400;
const typeOf = (slug) => (mapData.value?.nodes || []).find((n) => n.slug === slug)?.type?.sign || "release";   // the goal's own type while the Board still holds it, else a release's sign

/** A car's age from its commit's time in seconds: *today*, *1 day*, *3 days*; none while the time is not known. */
export function ageOf(at, now = Date.now() / 1000) {
  if (!(at > 0)) return "";
  const days = Math.max(0, Math.floor((now - at) / DAY_S));
  return days === 0 ? "today" : countWords(days, "day", "days");
}

function GoalCard({ g, group }) {
  const age = ageOf(g.at);
  return html`<${MapCard} map=${MAP} id=${g.idea} name=${g.title} element=${g.element || ""} group=${group} className=${cls("mp-goal", { "is-out": !g.ticked })} ghost=${!g.ticked}
    row=${String(g.commit || "").slice(0, SHORT)} rowCode=${true}
    mark=${html`<span class=${cls("mp-tick", { "is-off": !g.ticked })} role="img" aria-label=${g.ticked ? "In the merge" : "Not in the merge"}><${Sign} name="check" /></span>`}>
    ${age && html`<span class="mp-cap tr-age">${age}</span>`}
    <${Win} tone=${g.element || ""}><${Sign} name=${typeOf(g.idea)} big=${true} /></${Win}>
  </${MapCard}>`;
}

/** The cars in a row, the oldest first: a coupler joins each to the one before it, but not a car that starts a row (the width decides, so it is measured, and the attribute is set on the car beside the vnode's own). */
function Train({ goals, into, bigFrom }) {
  const host = useRef(), width = useWidth(host);
  useLayoutEffect(() => {
    let top = -1;
    for (const car of host.current?.children || []) {
      car.toggleAttribute("data-first", car.offsetTop > top);
      top = car.offsetTop;
    }
  }, [width, goals.length]);
  const cars = goals.map((x, i) => ({ x, i })).sort((a, b) => (a.x.at || 0) - (b.x.at || 0) || a.i - b.i).map((c) => c.x);        // oldest first; a time not known keeps the order the host gave
  return html`<div class="mp-goals tr-train" ref=${host}>${cars.map((x, n) => html`<div class="tr-car" key=${x.idea}>
    ${bigFrom > 0 && n + 1 === bigFrom && html`<span class="tr-big"><span class="mp-cap">From here the batch is big</span></span>`}
    <${GoalCard} g=${x} group=${into} />
  </div>`)}</div>`;
}

/** The back of a goal's card: when it is in dev and what pressing **To main** does with it. */
function Back({ g, into, main }) {
  const on = picked.value === g.idea;
  return html`<h3 class="mp-back__nm">${g.title}</h3>
    <${Sec} label="Commit"><span class="mp-code">${String(g.commit || "").slice(0, SHORT)}</span></${Sec}>
    <p class="mp-cap">${g.ticked ? `In ${into}, not in ${main} yet. It goes with the rest when you press To ${main}.` : `In ${into}, left out of the merge.`}</p>
    <div class="mp-acts"><button type="button" class="ork-btn quiet" aria-pressed=${String(on)} onClick=${() => pick(g.idea)}>${on ? "Picked: put it down" : "Pick this goal"}</button></div>`;
}

export function ReleaseMap({ g, narrow }) {
  const host = useRef(), [rd, reload] = useRead("ideas.release_map"), d = rd.data, at = useLifted(MAP), [busy, setBusy] = useState(false), [refused, setRefused] = useState("");
  const main = d?.main || "main", into = d?.into || "dev", goals = d?.goals || [], ticked = goals.filter((x) => x.ticked).length;
  const merge = async () => {
    setBusy(true);
    setRefused("");
    try {
      const got = await command("ideas.gate_merge", {}, true);
      if (got?.note) toast(got.note, "warning");
      await refreshShell();
      reload();
    } catch (e) { setRefused(e.message || "The merge failed"); }
    setBusy(false);
  };
  const goal = goals.find((x) => x.idea === at);
  const back = goal ? html`<${MapBack} host=${host} name=${goal.title} narrow=${narrow}><${Back} key=${goal.idea} g=${goal} into=${into} main=${main} /></${MapBack}>` : null;
  const waits = !!d && !d.same && (d.commits > 0 || goals.length > 0);
  return html`<${MapFrame} map=${MAP} host=${host} back=${back} className="mp--release">
    ${d && html`<div class="mp-dev">
      <header class="mp-dev__head"><span class="ork-label">${`${into[0].toUpperCase()}${into.slice(1)}, not in ${main} yet`}</span>
        ${goals.length > 0 && html`<span class="mp-cap">${countWords(goals.length, "goal", "goals")} · ${ticked} ticked</span>`}</header>
      ${goals.length > 0 ? html`<${Train} goals=${goals} into=${into} bigFrom=${d.big_from || 0} />`
        : html`<p class="mp-quiet">${d.same ? `${into} and ${main} are one branch here: nothing waits for ${main}.` : waits ? `The ${countWords(d.commits, "commit", "commits")} waiting for ${main} belong to no goal.` : `Nothing in ${into} waits for ${main}.`}</p>`}
      <div class="mp-foot">
        ${!d.same && html`<section class="mp-tomain" aria-label=${`Into ${main}`}>
          <span class="ork-label"><${Sign} name="flag" /> Into ${main}</span>
          <div class="ork-frame mp-tomain__box">
            <div class="mp-tomain__go"><button type="button" class="ork-btn primary" disabled=${busy || !waits} onClick=${merge}>To ${main}</button>
              <span class="mp-cap">${waits ? `Merges ${into} into ${main} whole: ${countWords(goals.length, "goal", "goals")}, nothing reaches ${main} without you` : `Nothing to take to ${main}`}</span></div>
            <ul class="mp-checks">
              ${waits && html`<li><span class="mp-ok"><${Sign} name="check" /></span>${countWords(d.commits, "commit", "commits")} to take, ${countWords(d.files, "file", "files")} changed</li>`}
              ${refused && html`<li class="mp-bad" role="alert"><${Sign} name="cross" />${refused}</li>`}
            </ul>
          </div>
        </section>`}
        <section class="mp-since" aria-label="Since the last version">
          ${d.since ? html`<span class="ork-label">Since ${d.since.version || "the last version"}</span><span class="mp-cap">Out ${flagDay(d.since.out)}</span>`
            : html`<span class="ork-label">No version is out yet</span>`}
        </section>
      </div>
    </div>`}
    ${!d && rd.err && html`<p class="mp-err" role="alert">${rd.err}</p>`}
  </${MapFrame}>`;
}

mapFor(MAP, ReleaseMap);
