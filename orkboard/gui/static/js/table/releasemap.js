// Release's map: dev and main (docs/specs/102-the-other-maps-and-picking-on-them.md §3.2, §5.5; decisions §137.3, §171.1; mockup docs/mockups/s3/ state 5). A card is a goal that is in dev and not in main — its element, its name, its sign,
// its commit in the label row and, at its right, the tick of the goal being in the merge —; under them, **To main** at the map's foot with the gate's words (what the merge takes, and a refusal in the gate's own words); *Since <version>*
// faint under that. (The past is no line of this lens any more: the lich in the table's edge opens it through the open tab, spec 150 E2.2.) **To main** is today's merge (`ideas.gate_merge`, as the discard's does it): it takes dev whole, so the tick is the data's (`ticked`), not a choice made here. Registered with maps.js for the craft `release`.
import { useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Sign } from "../orkui.js";
import { command, toast } from "../link.js";
import { pick, picked } from "../frame/state.js";
import { mapData, refreshShell } from "../shell/store.js";
import { flagDay } from "../arena/goalwords.js";
import { mapFor } from "./maps.js";
import { MapBack, MapCard, MapFrame, Sec, Win, countWords, useLifted, useRead } from "./mapkit.js";

const MAP = "release", SHORT = 7, BATCH = 8;   // past the eighth car the batch is big (spec 165 Q, decisions §280.2)
const BATCH_WORDS = "Past here the batch is big: To main takes every goal in dev together";
const typeOf = (slug) => (mapData.value?.nodes || []).find((n) => n.slug === slug)?.type?.sign || "release";   // the goal's own type while the Board still holds it, else a release's sign

/** A goal's age in words (*3 days*), from the epoch seconds of its oldest commit main lacks; "" when unread. */
export function ageWords(at, now = Date.now() / 1000) {
  if (typeof at !== "number" || !isFinite(at)) return "";
  const s = Math.max(0, now - at);
  if (s < 3600) return "under an hour";
  if (s < 86400) return countWords(Math.floor(s / 3600), "hour", "hours");
  if (s < 14 * 86400) return countWords(Math.floor(s / 86400), "day", "days");
  return countWords(Math.floor(s / (7 * 86400)), "week", "weeks");
}

/** The goals oldest first; one whose age is unread keeps its place after those that have one. */
export const oldestFirst = (goals) => goals.map((g, i) => [g, i]).sort(([a, i], [b, j]) => ((a.at ?? Infinity) - (b.at ?? Infinity)) || i - j).map(([g]) => g);

function GoalCard({ g, group }) {
  return html`<${MapCard} map=${MAP} id=${g.idea} name=${g.title} element=${g.element || ""} hue=${g.hue || ""} group=${group} className=${cls("mp-goal", { "is-out": !g.ticked })} ghost=${!g.ticked}
    row=${String(g.commit || "").slice(0, SHORT)} rowCode=${true}
    foot=${ageWords(g.at) && html`<span class="mp-age mp-cap">${ageWords(g.at)}</span>`}
    mark=${html`<span class=${cls("mp-tick", { "is-off": !g.ticked })} role="img" aria-label=${g.ticked ? "In the merge" : "Not in the merge"}><${Sign} name="check" /></span>`}>
    <${Win} tone=${g.hue || g.element || ""}><${Sign} name=${typeOf(g.idea)} big=${true} /></${Win}>
  </${MapCard}>`;
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
      const got = await command("ideas.gate_merge", { sealed: true }, true);
      if (got?.note) toast(got.note, "warning");
      await refreshShell();
      reload();
    } catch (e) { setRefused(e.message || "The merge failed"); }
    setBusy(false);
  };
  const cars = oldestFirst(goals), goal = goals.find((x) => x.idea === at);
  const back = goal ? html`<${MapBack} host=${host} name=${goal.title} narrow=${narrow}><${Back} key=${goal.idea} g=${goal} into=${into} main=${main} /></${MapBack}>` : null;
  const waits = !!d && !d.same && (d.commits > 0 || goals.length > 0);
  return html`<${MapFrame} map=${MAP} host=${host} back=${back} className="mp--release">
    ${d && html`<div class="mp-dev">
      <header class="mp-dev__head"><span class="ork-label">${`${into[0].toUpperCase()}${into.slice(1)}, not in ${main} yet`}</span>
        ${goals.length > 0 && html`<span class="mp-cap">${countWords(goals.length, "goal", "goals")} · ${ticked} ticked</span>`}</header>
      ${goals.length > 0 ? html`<div class="mp-goals mp-cars">${cars.flatMap((x, i) => [
          i === BATCH ? html`<span key="batch" class="mp-batch" role="img" aria-label=${BATCH_WORDS} title=${BATCH_WORDS}><${Sign} name="flag" /></span>` : null,
          html`<${GoalCard} key=${x.idea} g=${x} group=${into} />`])}</div>`
        : html`<p class="mp-quiet">${d.same ? `${into} and ${main} are one branch here: nothing waits for ${main}.` : waits ? `The ${countWords(d.commits, "commit", "commits")} waiting for ${main} belong to no goal.` : `Nothing in ${into} waits for ${main}.`}</p>`}
      <div class="mp-foot">
        ${!d.same && html`<section class="mp-tomain" aria-label=${`Into ${main}`}>
          <span class="ork-label"><${Sign} name="flag" /> Into ${main}</span>
          <div class="ork-frame mp-tomain__box">
            <div class="mp-tomain__go"><button type="button" class="ork-btn primary" disabled=${busy || !waits} onClick=${merge}>To ${main}</button>
              <span class="mp-cap" role=${busy ? "status" : undefined}>${busy ? "Running the tests…" : waits ? `Merges ${into} into ${main} whole: ${countWords(goals.length, "goal", "goals")}, nothing reaches ${main} without you` : `Nothing to take to ${main}`}</span></div>
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
