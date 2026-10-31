// Product's map: the opportunity solution tree (docs/specs/102-the-other-maps-and-picking-on-them.md §8.4, decisions §172, §175.1; mockup docs/mockups/s3/ state 2). The outcome as a banner at the top (**Edit**); under it
// the jobs as columns, each its sentence *When …, I want to …, so I can …* (the three keywords muted) and its segment (**Edit**); under a job the goals that serve it as the Board's goal cards (the element at the left, the
// name in the body face, the type's two-tone sign, its place: *In line*, *At work*, *Done*), a press picking the goal (frame/state.js `pick`), and under a goal the experiments that test it. A job no goal serves says
// *No goal serves this yet* with a **+** that opens the + card's field addressed to Product with the job noted as a mark (hand/state.js `fieldOpen`, table/picking.js `marks`: the field is Product's tab's own, the mark is
// read into the goal's route as any picked part of a map is). With nothing kept, **Propose** (`ideas.tree_propose`: one call of Product's leader, never made unasked). Every job and goal card is wrapped in `Pickable`
// (map `product`; a job's id is its own, its name its want). Under a job, before its goals, its hypotheses (docs/specs/116-hypotheses-on-products-tree.md §6.1, decisions §194; `ideas.hypotheses`, read beside the tree) as
// small cards — *We believe* then the text, *We'll know when* then the signal (both keywords muted), the state as an orkUI chip (*Proposed* dashed, *Open*, *Testing*, *Held*, *Refuted*), the head of the leader that
// proposed it with *Proposed by …* —; a proposed one has **Keep** and **Drop**, an open one **Test it** (the + card's field addressed to Product, the type *Try an experiment* and the hypothesis as a mark: the host
// attaches the goal it makes as the hypothesis's test, `ideas.add`), and **+ Hypothesis** at the end of a job's opens a small field. Those of no job lie in a row under the outcome, where **Propose hypotheses**
// (`ideas.hypotheses_propose`: one call of Product's leader, never made unasked) stands while none is kept. Each is `Pickable` (id `hyp:<id>`, group `hypotheses`, name its text). No count of them anywhere.
// At the narrow width the columns stack. Registered with maps.js for the craft `product`; the sheet is tree.css.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Elem, Head, Icon, Sign } from "../orkui.js";
import { command, toast } from "../link.js";
import { pick, picked, tab } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { fieldOff, fieldOpen, fieldType } from "../hand/state.js";
import { nameOf, partiesAll } from "./data.js";
import { Pickable, mapFor } from "./maps.js";
import { MapFrame, Nothing, Win, countWords, useRead } from "./mapkit.js";
import { marks, pickOff } from "./picking.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./tree.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const MAP = "product";
const NONE_WHAT = "the outcome and the users' jobs", POLL_MS = 2500, MAX_OUTCOMES = 2;
const PLACES = { line: ["before", "In line"], work: ["work", "At work"], done: ["check", "Done"] };

/** The jobs in rows of equal columns: up to five a row, else two rows (6 → 3 and 3, 7 → 4 and 3). */
export function rowsOf(jobs) {
  const k = jobs.length <= 5 ? jobs.length : Math.ceil(jobs.length / 2), rows = [];
  for (let i = 0; i < jobs.length; i += k) rows.push(jobs.slice(i, i + k));
  return { k: Math.max(k, 1), rows };
}

/** The goal's own type's sign while the Board still holds it, else `fallback`. */
const signOf = (slug, fallback) => (mapData.value?.nodes || []).find((n) => n.slug === slug)?.type?.sign || fallback;

// -- the goals under a job -------------------------------------------------------------------------------------------------------------------------------

/** A goal as the Board's card (the face of mapkit.js `MapCard`, but a press picks the goal instead of lifting a card that has no back). `g`: `{goal, title, element, place}`. */
function GoalCard({ g, group, groupName, test = false }) {
  const on = picked.value === g.goal, [sign, word] = PLACES[g.place] || PLACES.line;
  return html`<${Pickable} map=${MAP} id=${g.goal} name=${g.title} group=${group} groupName=${groupName}>
    <article class=${cls("ork-card ork-leans mp-card tr-goal", { "is-lit": on, "is-test": test })} data-id=${g.goal} data-place=${g.place} data-test=${test ? "1" : undefined} onClick=${() => pick(g.goal)}>
      <h3 class="mp-card__head">${g.element && html`<${Elem} name=${g.element} />`}<button type="button" class="mp-card__nm" aria-pressed=${String(on)} title=${g.title}>${g.title}</button></h3>
      <${Win} tone=${g.element || ""}><${Sign} name=${signOf(g.goal, test ? "abtest" : "feature")} big=${true} /></${Win}>
      <div class="mp-card__row"><span class="mp-card__l tr-place"><${Sign} name=${sign} />${word}</span></div>
    </article>
  </${Pickable}>`;
}

/** A job no goal serves: a ghost with a **+** that writes a goal for it (the + card's field, addressed to Product, with the job noted). */
function NoGoal({ job, write }) {
  return html`<div class="ork-card mp-card is-ghost tr-nogoal" data-job=${job.id}>
    <p class="mp-cap">No goal serves this yet</p>
    <button type="button" class="ork-btn tr-write" aria-label="Write a goal for this job" title="Write a goal for this job" onClick=${() => write(job)}><${Icon} name="plus" /></button>
  </div>`;
}

// -- a job, and its form ---------------------------------------------------------------------------------------------------------------------------------

const KEYS = [["when", "When", "I start a game night"], ["want", "I want to", "get everyone into the lobby fast"], ["so", "So I can", "begin before people drift off"]];

/** The form of a job (or of the outcome): its fields, **Save**, **Cancel**; `onSave(form)` throws a plain message when the host refuses. */
function JobForm({ job, onSave, onCancel }) {
  const [form, setForm] = useState({ segment: job.segment || "", when: job.when, want: job.want, so: job.so }), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const save = async () => {
    setBusy(true);
    setErr("");
    try { await onSave({ segment: form.segment.trim(), when: form.when.trim(), want: form.want.trim(), so: form.so.trim() }); } catch (e) { setErr(e.message || "The tree could not be kept"); setBusy(false); }
  };
  return html`<form class="mp-form tr-form" onSubmit=${(e) => { e.preventDefault(); save(); }}>
    <label class="mp-sec"><span class="ork-label">Segment</span><input class="ork-field" name="segment" maxlength="40" value=${form.segment} onInput=${set("segment")} placeholder="Hosts" /></label>
    ${KEYS.map(([k, label, ph]) => html`<label key=${k} class="mp-sec"><span class="ork-label">${label}</span><textarea class="ork-field" name=${k} maxlength="90" rows="2" value=${form[k]} onInput=${set(k)} placeholder=${ph} required></textarea></label>`)}
    ${err && html`<p class="mp-err" role="alert">${err}</p>`}
    <div class="mp-acts"><button type="submit" class="ork-btn primary" disabled=${busy || !form.when.trim() || !form.want.trim() || !form.so.trim()}>Save</button>
      <button type="button" class="ork-btn" onClick=${onCancel}>Cancel</button></div>
  </form>`;
}

/** A job: its segment and **Edit** at the top, its sentence under them (the three keywords muted). Pickable: its want is its name. */
function Job({ job, edit, save }) {
  const [editing, setEditing] = useState(false);
  return html`<${Pickable} map=${MAP} id=${job.id} name=${job.want}>
    <article class="ork-card mp-card tr-job" data-job=${job.id}>
      ${editing ? html`<${JobForm} job=${job} onCancel=${() => setEditing(false)} onSave=${async (f) => { await save(job.id, f); setEditing(false); }} />`
        : html`<div class="mp-card__row tr-job__top"><span class="mp-card__l tr-segment">${job.segment}</span>
            <button type="button" class="ork-btn quiet" aria-label=${`Edit the job: ${job.want}`} onClick=${() => setEditing(true)}>Edit</button></div>
          <p class="tr-job__s"><span class="tr-k">When</span> ${job.when}, <span class="tr-k">I want to</span> ${job.want}, <span class="tr-k">so I can</span> ${job.so}.</p>`}
    </article>
  </${Pickable}>`;
}

function Column({ job, d, save, write, hyps }) {
  const goals = (d.serves || []).filter((s) => s.job === job.id);
  return html`<div class="tr-col" data-job=${job.id}>
    <${Job} job=${job} save=${save} />
    <${Hyps} items=${hyps.of(job.id)} on=${job.id} h=${hyps} />
    <div class="tr-goals">
      ${goals.length ? goals.map((g) => {
        const tests = (d.tests || []).filter((t) => t.goal === g.goal);
        return html`<div key=${g.goal} class="tr-branch">
          <${GoalCard} g=${g} group=${job.id} groupName=${job.want} />
          ${tests.length > 0 && html`<div class="tr-tests" aria-label="Experiments">${tests.map((t) => html`<${GoalCard} key=${t.experiment} g=${{ ...t, goal: t.experiment }} group=${job.id} groupName=${job.want} test=${true} />`)}</div>`}
        </div>`;
      }) : html`<${NoGoal} job=${job} write=${write} />`}
    </div>
  </div>`;
}

// -- the hypotheses ---------------------------------------------------------------------------------------------------------------------------------------

/** `ideas.hypotheses`, read again when the Board changes. Unlike `useRead`, an `error` in the answer is the last proposal's, with the items beside it: `[{data}, reload]`. A read that fails leaves what was read. */
function useHypotheses() {
  const [data, set] = useState(null), [tick, setTick] = useState(0), rev = mapData.value?.rev;
  useEffect(() => {
    let live = true;
    command("ideas.hypotheses", {}, true).then((r) => { if (live) set(r && typeof r === "object" ? r : {}); }).catch(() => {});
    return () => { live = false; };
  }, [rev, tick]);
  return [{ data }, () => setTick((n) => n + 1)];
}

const STATES = { proposed: "Proposed", open: "Open", testing: "Testing", held: "Held", refuted: "Refuted" };
const TEST_TYPE = { id: "experiment", name: "Try an experiment", sign: "flask" };

/** The leader of the party that proposed a hypothesis, as the page shows leaders (`{name, head}`); null for the person's own. */
function proposer(h) {
  if (h.by !== "leader") return null;
  const g = partiesAll().find((x) => x.slug === h.party);
  return { name: g?.leader?.name || nameOf(g) || "a leader", head: g?.leader?.head || null };
}

/** A hypothesis as a small card (the Board's card, but a press on it picks nothing: only picking on the map does). `h.act(name, args)` runs one of its commands, `h.test(item)` opens the field to test it. */
function HypCard({ x, h }) {
  const by = proposer(x), state = STATES[x.state] ? x.state : "open";
  return html`<${Pickable} map=${MAP} id=${`hyp:${x.id}`} name=${x.text} group="hypotheses" groupName="Hypotheses">
    <article class="ork-card mp-card hy-card" data-hyp=${x.id} data-state=${state}>
      <div class="mp-card__row hy-card__top"><span class=${cls("ork-chip hy-chip", `is-${state}`)}>${STATES[state]}</span>
        ${by && html`<span class="hy-by">${by.head && html`<${Head} race=${by.head.race} tier=${by.head.tier} />`}<span class="mp-cap">Proposed by ${by.name}</span></span>`}</div>
      <p class="hy-line"><span class="tr-k">We believe</span> ${x.text}</p>
      <p class="hy-line"><span class="tr-k">We'll know when</span> ${x.signal}</p>
      ${(state === "proposed" || state === "open") && html`<div class="mp-acts hy-acts">
        ${state === "proposed" && html`<button type="button" class="ork-btn primary" aria-label=${`Keep the hypothesis: ${x.text}`} onClick=${() => h.act("ideas.hypothesis_keep", { id: x.id })}>Keep</button>
          <button type="button" class="ork-btn" aria-label=${`Drop the hypothesis: ${x.text}`} onClick=${() => h.act("ideas.hypothesis_drop", { id: x.id })}>Drop</button>`}
        ${state === "open" && html`<button type="button" class="ork-btn" aria-label=${`Test it: ${x.text}`} title="Write an experiment that tests it" onClick=${() => h.test(x)}>Test it</button>`}
      </div>`}
    </article>
  </${Pickable}>`;
}

/** The small field of a new hypothesis: *We believe*, *We'll know when*, **Save**, **Cancel**; `onSave(form)` throws a plain message when the host refuses. */
function HypForm({ onSave, onCancel }) {
  const [form, setForm] = useState({ text: "", signal: "" }), [err, setErr] = useState(""), [busy, setBusy] = useState(false), first = useRef();
  useEffect(() => { first.current?.focus({ preventScroll: true }); }, []);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const save = async () => {
    setBusy(true);
    setErr("");
    try { await onSave({ text: form.text.trim(), signal: form.signal.trim() }); } catch (e) { setErr(e.message || "The hypothesis could not be kept"); setBusy(false); }
  };
  return html`<form class="mp-form hy-form" onSubmit=${(e) => { e.preventDefault(); save(); }}>
    <label class="mp-sec"><span class="ork-label">We believe</span><textarea ref=${first} class="ork-field" name="text" maxlength="200" rows="2" value=${form.text} onInput=${set("text")} required></textarea></label>
    <label class="mp-sec"><span class="ork-label">We'll know when</span><textarea class="ork-field" name="signal" maxlength="200" rows="2" value=${form.signal} onInput=${set("signal")} required></textarea></label>
    ${err && html`<p class="mp-err" role="alert">${err}</p>`}
    <div class="mp-acts"><button type="submit" class="ork-btn primary" disabled=${busy || !form.text.trim() || !form.signal.trim()}>Save</button>
      <button type="button" class="ork-btn" onClick=${onCancel}>Cancel</button></div>
  </form>`;
}

/** The hypotheses of one place — a job's, or (`outcome`) those of no job — as cards, then **+ Hypothesis**; `extra`: what stands beside that button (the row under the outcome's **Propose hypotheses**). `h`: `{act, test, add}`. */
function Hyps({ items, on = "", outcome = false, h, extra = null }) {
  const [adding, setAdding] = useState(false);
  return html`<div class=${cls("tr-hyps", { "tr-hyps--outcome": outcome })} data-on=${on || undefined} role="group" aria-label="Hypotheses">
    ${items.map((x) => html`<${HypCard} key=${x.id} x=${x} h=${h} />`)}
    ${adding ? html`<${HypForm} onCancel=${() => setAdding(false)} onSave=${async (f) => { await h.add({ ...f, ...(on ? { on } : {}) }); setAdding(false); }} />`
      : html`<div class="mp-acts hy-add"><button type="button" class="ork-btn quiet tr-addhyp" onClick=${() => setAdding(true)}>+ Hypothesis</button>${extra}</div>`}
  </div>`;
}

// -- the outcome ---------------------------------------------------------------------------------------------------------------------------------------------

/** The banner: the outcome (one or two), **Edit** keeping them through `ideas.tree_set`; a field left empty drops that outcome. */
function Banner({ outcomes, save }) {
  const [editing, setEditing] = useState(false), [texts, setTexts] = useState([]), [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const start = () => { setTexts(outcomes.map((o) => o.text)); setErr(""); setBusy(false); setEditing(true); };
  const keep = async () => {
    setBusy(true);
    setErr("");
    try {
      await save(texts.map((t, i) => ({ ...(outcomes[i] ? { id: outcomes[i].id } : {}), text: t.trim() })).filter((o) => o.text));
      setEditing(false);
    } catch (e) { setErr(e.message || "The outcome could not be kept"); }
    setBusy(false);
  };
  if (editing) {
    return html`<form class="ork-frame tr-banner is-editing" onSubmit=${(e) => { e.preventDefault(); keep(); }}>
      <div class="tr-banner__body">
        <span class="ork-label">Outcome</span>
        ${texts.map((t, i) => html`<textarea key=${i} class="ork-field" name=${`outcome-${i}`} aria-label=${`Outcome ${i + 1}`} maxlength="160" rows="2" value=${t}
          onInput=${(e) => setTexts(texts.map((x, k) => (k === i ? e.target.value : x)))}></textarea>`)}
        ${texts.length < MAX_OUTCOMES && html`<button type="button" class="ork-btn quiet tr-add" onClick=${() => setTexts([...texts, ""])}>Add a second outcome</button>`}
        ${err && html`<p class="mp-err" role="alert">${err}</p>`}
        <div class="mp-acts"><button type="submit" class="ork-btn primary" disabled=${busy || !texts.some((t) => t.trim())}>Save</button>
          <button type="button" class="ork-btn" onClick=${() => setEditing(false)}>Cancel</button></div>
      </div>
    </form>`;
  }
  return html`<div class="ork-frame tr-banner">
    <div class="tr-banner__body"><span class="ork-label">${outcomes.length > 1 ? "Outcomes" : "Outcome"}</span>${outcomes.map((o) => html`<p key=${o.id} class="tr-banner__t">${o.text}</p>`)}</div>
    <button type="button" class="ork-btn quiet" aria-label="Edit the outcome" onClick=${start}>Edit</button>
  </div>`;
}

// -- the map -------------------------------------------------------------------------------------------------------------------------------------------------

/** The + card's field opens addressed to Product (this tab; the address taken off is put back), `mark` noted so Product's picking shows it, a goal type `type` taken when given. */
function openField(mark, type = null) {
  fieldOff.value = fieldOff.value === tab.value ? "" : fieldOff.value;
  pickOff.value = pickOff.value === MAP ? "" : pickOff.value;
  if (!marks.value.some((m) => m.map === MAP && m.id === mark.id)) marks.value = [...marks.value, { map: MAP, ...mark }];
  if (type) fieldType.value = type;
  fieldOpen.value = true;
}

/** **+** on an empty job: the field opens with the job noted as a mark. */
const write = (job) => openField({ id: job.id, name: job.want });

export function TreeMap({ g, narrow }) {
  const host = useRef(), [rd, reloadTree] = useRead("ideas.tree"), [hr, reloadHyps] = useHypotheses(), d = rd.data, [asked, setAsked] = useState(""), [busy, setBusy] = useState(false), who = nameOf(g);
  const [hasked, setHasked] = useState(""), [hbusy, setHbusy] = useState(false), hd = hr.data || {}, items = Array.isArray(hd.items) ? hd.items : [], hproposing = !!hd.proposing;
  const reload = () => { reloadTree(); reloadHyps(); };                         // the tree and its hypotheses change together
  const outcomes = d?.outcomes || [], jobs = d?.jobs || [], proposing = !!d?.proposing, empty = !!d && outcomes.length === 0 && jobs.length === 0;
  useEffect(() => {                                                            // a proposal being made: look again until it is kept
    if (!proposing) return undefined;
    const t = setInterval(reload, POLL_MS);
    return () => clearInterval(t);
  }, [proposing]);
  useEffect(() => {                                                            // hypotheses being proposed: the same
    if (!hproposing) return undefined;
    const t = setInterval(reloadHyps, POLL_MS);
    return () => clearInterval(t);
  }, [hproposing]);
  const propose = async () => {
    setBusy(true);
    setAsked("");
    try {
      const got = await command("ideas.tree_propose", {}, true);
      if (got && got.asked === false) setAsked(got.why || `${who} could not be asked now`);
    } catch (e) { setAsked(e.message || `${who} could not be asked now`); }
    setBusy(false);
    reload();
  };
  const saveJob = async (id, f) => {                                           // the jobs are kept whole: the one edited, the others as they are
    await command("ideas.tree_set", { jobs: jobs.map((j) => ({ id: j.id, when: j.when, want: j.want, so: j.so, segment: j.segment || "", ...(j.id === id ? f : {}) })) }, true);
    reload();
  };
  const saveOutcomes = async (list) => {
    const got = await command("ideas.tree_set", { outcomes: list }, true);
    if (got && got.ok === false) toast("The outcome could not be kept", "warning");
    reload();
  };
  const proposeHyps = async () => {
    setHbusy(true);
    setHasked("");
    try {
      const got = await command("ideas.hypotheses_propose", {}, true);
      if (got && got.asked === false) setHasked(got.why || `${who} could not be asked now`);
    } catch (e) { setHasked(e.message || `${who} could not be asked now`); }
    setHbusy(false);
    reloadHyps();
  };
  const hyps = {                                                               // what the hypotheses' cards do
    of: (id) => items.filter((x) => x.on === id),
    act: async (name, args) => {
      try { await command(name, args, true); } catch (e) { toast(e.message || "The hypothesis could not be changed", "warning"); }
      reloadHyps();
    },
    add: async (f) => { await command("ideas.hypothesis_set", f, true); reloadHyps(); },
    test: (x) => openField({ id: `hyp:${x.id}`, name: x.text }, { ...TEST_TYPE, party: g.slug }),
  };
  const loose = items.filter((x) => !jobs.some((j) => j.id === x.on));         // those on the outcome, or on a job that is gone: a row under the outcome
  const bare = jobs.filter((j) => !(d?.serves || []).some((s) => s.job === j.id)).length, { k, rows } = rowsOf(jobs);
  return html`<${MapFrame} map=${MAP} host=${host} className=${cls("mp--tree tr", { "is-narrow": narrow })}>
    ${d && !empty && html`<div class="tr-tree" style=${`--cols:${k}`}>
      ${bare > 0 && html`<p class="mp-cap tr-note">${countWords(bare, "job", "jobs")} no goal serves</p>`}
      ${outcomes.length > 0 && html`<${Banner} outcomes=${outcomes} save=${saveOutcomes} />`}
      ${outcomes.length > 0 && html`<${Hyps} items=${loose} on=${outcomes[0].id} outcome=${true} h=${hyps} extra=${items.length === 0 && html`<button type="button" class="ork-btn" disabled=${hbusy || hproposing} onClick=${proposeHyps}>${hbusy || hproposing ? "Proposing…" : "Propose hypotheses"}</button>
        ${hbusy || hproposing ? html`<span class="ork-busy" role="status" aria-label="Proposing"></span>` : html`<span class="mp-cap">${who} proposes the riskiest, in one short call</span>`}
        ${(hasked || hd.error) && html`<p class="mp-err" role="alert">${hasked || hd.error}</p>`}`} />`}
      ${rows.map((row, i) => html`<div key=${i} class="tr-tier"><i class="tr-stub" aria-hidden="true"></i>
        <div class="tr-row">${row.map((j) => html`<${Column} key=${j.id} job=${j} d=${d} save=${saveJob} write=${write} hyps=${hyps} />`)}</div></div>`)}
    </div>`}
    ${empty && html`<div class="mp-propose">
      <${Nothing} what=${NONE_WHAT} />
      <div class="mp-acts"><button type="button" class="ork-btn primary" disabled=${busy || proposing} onClick=${propose}>${proposing ? "Proposing…" : "Propose"}</button>
        <span class="mp-cap">${who} reads the project's files and proposes the outcome and the jobs, in one short call</span></div>
      ${(asked || d.error) && html`<p class="mp-err" role="alert">${asked || d.error}</p>`}
    </div>`}
    ${!d && rd.err && html`<p class="mp-err" role="alert">${rd.err}</p>`}
  </${MapFrame}>`;
}

mapFor(MAP, TreeMap);
