// Product's table: jobs to be done (docs/mockups/frameworks/, ?f=jtbd): who (a pile of personas, spread on press), the job (when, I want, so)
// with the forces that push and pull and the ones that hold back, its smaller jobs as a pile, hired and fired. What the Board keeps is what lies here
// (`ideas.tables`, gui/ideas_mats.py): a zone nothing fills yet lies empty and says who fills it (`data.fills`), never an example; the person turns a
// card over, spreads a pile, puts a token.
import { useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { Icon } from "../../orkui.js";
import { TBack, TCard, TPile } from "./parts.js";

const Force = ({ f }) => html`<span class=${cls("tb-force", `is-${f.dir}`)} data-force=${f.kind.toLowerCase()}><b>${f.kind}</b>${f.text}</span>`;

/** A zone nothing fills yet: its words say who fills it (`fills[zone]`, the host's) where its cards would lie. */
const Empty = ({ zone, fills }) => html`<p class="tb-empty" data-empty=${zone}>${fills?.[zone] || "Nothing is laid here yet"}</p>`;

/** Product's table. `ctx`: {party, framework, race, leader}; `data`: the jobs the Board keeps ({personas, job, forces, jobs, hired, fired, fills}); a part it lacks lies empty. */
export function Jobs({ ctx, data }) {
  const [open, setOpen] = useState({}), [turned, setTurned] = useState({}), flip = (id) => setOpen({ ...open, [id]: !open[id] });
  const { job, hired, fills } = data, personas = data.personas || [], forces = data.forces || [], jobs = data.jobs || [], fired = data.fired || [];
  const who = job ? personas.find((p) => p.id === job.persona) || personas[0] || { title: job.persona || "The job" } : null;
  const jobFace = job && html`<span class="tb-jt"><b>When</b> ${job.when}, <b>I want</b> ${job.want}, <b>so</b> ${job.so}.</span>`;
  return html`<div class="tb-jtbd">
    <div class="tb-fc"><p class="tb-colh">Who ${personas.length > 0 && html`<i>· pressed, the pile spreads</i>`}</p>
      ${personas.length ? html`<${TPile} ctx=${ctx} id=${`pile:${personas[0].id}`} title=${personas[0].title} line=${personas[0].line} sign="character" n=${personas.length + 1} size="xl" open=${!!open.personas} onSpread=${() => flip("personas")} count=${`${personas.length} personas`} />
      <button type="button" class="ork-btn" data-spread-of="personas" onClick=${() => flip("personas")}><${Icon} name=${open.personas ? "chevron-up" : "chevron-down"} /><span>${open.personas ? "Close the personas" : "Spread the personas"}</span></button>
      ${open.personas && html`<div class="tb-fan is-col" data-spread="personas">${personas.map((p, i) => html`<${TCard} key=${p.id} ctx=${ctx} id=${p.id} title=${p.title} line=${p.line} sign="character" size="lg" tilt=${i % 2 ? 2 : -2}
        back=${[job && p.id === who.id ? "its main job is the one beside" : "a job of its own, not laid yet"]} tokens=${[]} />`)}</div>`}`
        : html`<${Empty} zone="personas" fills=${fills} />`}
    </div>
    <div class="tb-fc is-mid"><p class="tb-colh">The job ${job && html`<i>· when, I want, so</i>`}</p>
      ${forces.length > 0 && html`<div class="tb-forces is-top">${forces.filter((f) => f.dir === "in").map((f) => html`<${Force} key=${f.kind} f=${f} />`)}</div>`}
      ${job ? html`<${TCard} ctx=${ctx} id=${job.id} title=${who.title} line="" face=${jobFace} sign="target" size="job" kind="job" back=${[`The main job of ${who.title}.`, "Pressed again, it turns back."]} />`
        : html`<${Empty} zone="job" fills=${fills} />`}
      ${forces.length > 0 && html`<div class="tb-forces is-bot">${forces.filter((f) => f.dir === "out").map((f) => html`<${Force} key=${f.kind} f=${f} />`)}</div>`}
      <p class="tb-colh">Its smaller jobs ${jobs.length > 0 && html`<i>· ${open.jobs ? "the pile spread" : "pressed, the pile spreads"}</i>`}</p>
      ${!jobs.length ? html`<${Empty} zone="jobs" fills=${fills} />`
        : open.jobs ? html`<div class="tb-fan" data-spread="jobs">${jobs.map((j, i) => html`<${TCard} key=${j.id} ctx=${ctx} id=${j.id} title=${j.title} line=${j.line} sign="target" size="md" tilt=${[-4, 0, 4][i % 3]} back=${["A job inside the main one.", `no. ${i + 1} of ${jobs.length}`]} />`)}</div>
        <button type="button" class="ork-btn" data-spread-of="jobs" onClick=${() => flip("jobs")}><${Icon} name="chevron-up" /><span>Close the smaller jobs</span></button>`
          : html`<${TPile} ctx=${ctx} id="pile:jobs" title=${jobs[0].title} line=${jobs[0].line} sign="target" n=${jobs.length} size="md" open=${false} onSpread=${() => flip("jobs")} count=${`${jobs.length} smaller jobs`} />`}
    </div>
    <div class="tb-fc"><p class="tb-colh">Hired</p>
      ${hired ? html`<${TCard} ctx=${ctx} id=${hired.id} title=${hired.title} line=${hired.line} sign="logo" size="xl" kind="hired" back=${["What they hire it for: the main job."]} />` : html`<${Empty} zone="hired" fills=${fills} />`}
      <p class="tb-colh">Fired ${fired.length > 0 && html`<i>· one turned over</i>`}</p>
      ${fired.length ? html`<div class="tb-row">${fired.map((f, i) => (i === 0 || turned[f.id] ? html`<${TCard} key=${f.id} ctx=${ctx} id=${f.id} title=${f.title} line=${f.line} sign="cross" size="md" kind="fired" tilt=${i ? -3 : 3} back=${["What they use now, and drop for it."]} />`
        : html`<${TBack} key=${f.id} name="A card" onTurn=${() => setTurned({ ...turned, [f.id]: true })} />`))}</div>` : html`<${Empty} zone="fired" fills=${fills} />`}
    </div>
  </div>`;
}
