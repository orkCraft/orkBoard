// Game design's map: the loops (docs/specs/107-what-the-owners-day-said.md §14, docs/specs/102-the-other-maps-and-picking-on-them.md §2, §5.3; decisions §112.8, §171.1, §182). The game's loops lie one in another as rings — the core
// inside, the meta outside, each ring tagged with its span and name — each step a small card on its ring (its name, its feeling and its intensity). A press lifts the step: its line, its feeling, its intensity, what it gives
// or takes and what it rests on, all editable in place (`ideas.loop_set`). At the right **the economy** (each currency: what gives it, it, what takes it), under the rings **the feeling** (a stepped line of the intensities of
// the session loop, else the core's), above **what the loop says** (one alert line a finding, by code). **Propose again** asks the party's leader once more (`ideas.loop_propose {again}`; the person's version is kept aside);
// with no loop kept, **Propose**. A pixel dot steps round the core ring while any task of the party is at work (spec 107 §7: what is alive moves; off under reduced motion). Under 640 px the loops lie as lists, the
// economy and the feeling under them. Registered with maps.js for the craft `game-design`; the parts it draws are loopparts.js's.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { command, toast } from "../link.js";
import { RUN } from "../arena/arenawords.js";
import { nameOf, nodesFor } from "./data.js";
import { mapFor } from "./maps.js";
import { FileLink, MapBack, MapFrame, Nothing, Sec, keyOf, useLifted, useRead, useWidth } from "./mapkit.js";
import { Economy, Feeling, FEELS, FEEL_HINT, INTENSITIES, MAP, Pips, RING_MIN, Says, StepCard, TIME, cap, curNames, feelingLoop, layout, orbitOf } from "./loopparts.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as treemap.js links its own
  const href = new URL("./rondel.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const NONE_WHAT = "the game's configs", POLL_MS = 2500, ECO_W = 280, SIDE_MIN = 900, GAP = 24;

/** What `ideas.loop_set` keeps, from what `ideas.loop` read: the shape without who kept each step and when. */
const plain = (d) => ({
  loops: d.loops.map((lp) => ({ span: lp.span, name: lp.name, line: lp.line, feeds: lp.feeds,
    steps: lp.steps.map((s) => ({ id: s.id, name: s.name, line: s.line, feel: s.feel, intensity: s.intensity, gives: s.gives, takes: s.takes, rests_on: s.rests_on || [] })) })),
  currencies: d.currencies.map((c) => ({ id: c.id, name: c.name, kind: c.kind, line: c.line })), hooks: d.hooks.map((h) => ({ when: h.when, line: h.line })),
});

/** Keeping one change: `save(edit)` gives `edit` the plain loops to change, sends them, and says what was left out; `err` is what the host refused with. */
function useSaver(d, reload) {
  const [err, setErr] = useState(""), [busy, setBusy] = useState(false);
  const save = async (edit) => {
    const next = plain(d);
    edit(next);
    setBusy(true);
    setErr("");
    let ok = false;
    try {
      const got = await command("ideas.loop_set", next, true);
      if (got?.dropped?.length) toast(`Not in the project, left out: ${got.dropped.map((x) => x.path || x).join(", ")}`, "warning");
      ok = true;
      reload();
    } catch (e) { setErr(e.message || "The loop could not be kept"); }
    setBusy(false);
    return ok;
  };
  return { save, err, busy };
}

const Keeper = ({ mine, g }) => html`<span class="mp-by">${!mine && g.leader?.head && html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} />`}<span>${mine ? "Yours" : `Proposed by ${nameOf(g)}`}</span></span>`;

/** The back of a step: its line, its feeling and intensity, what it gives and takes, who keeps it, what it rests on, **Edit**; while editing, the form for its name, line, feeling, intensity and files. */
function StepBack({ s, lp, d, g, reload }) {
  const [editing, setEditing] = useState(false), [form, setForm] = useState(null), { save, err, busy } = useSaver(d, reload);
  const key = keyOf(MAP, s.id), cur = (ids) => ids.map((id) => d.currencies.find((c) => c.id === id)?.name).filter(Boolean);
  const start = () => { setForm({ name: s.name, line: s.line, feel: s.feel, intensity: String(s.intensity), files: (s.rests_on || []).join("\n") }); setEditing(true); };
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const submit = async () => {
    const ok = await save((next) => {
      const at = next.loops.find((x) => x.span === lp.span).steps.find((x) => x.id === s.id);
      Object.assign(at, { name: form.name.trim(), line: form.line.trim(), feel: form.feel, intensity: Number(form.intensity), rests_on: form.files.split("\n").map((x) => x.trim()).filter(Boolean) });
    });
    if (ok) setEditing(false);
  };
  if (editing) {
    return html`<form class="mp-form" onSubmit=${(e) => { e.preventDefault(); submit(); }}>
      <label class="mp-sec"><span class="ork-label">Name</span><input class="ork-field" name="name" maxlength="40" value=${form.name} onInput=${set("name")} required /></label>
      <label class="mp-sec"><span class="ork-label">Line</span><textarea class="ork-field" name="line" maxlength="160" rows="3" value=${form.line} onInput=${set("line")} required></textarea></label>
      <label class="mp-sec"><span class="ork-label">Feeling</span><div class="ork-select"><select class="ork-field" name="feel" value=${form.feel} onChange=${set("feel")}>
        <option value="" selected=${form.feel === ""}>Not said</option>${FEELS.map(([f, hint]) => html`<option key=${f} value=${f} selected=${form.feel === f}>${cap(f)} · ${hint}</option>`)}</select></div></label>
      <label class="mp-sec"><span class="ork-label">Intensity</span><div class="ork-select"><select class="ork-field" name="intensity" value=${form.intensity} onChange=${set("intensity")}>
        ${INTENSITIES.map(([n, word]) => html`<option key=${n} value=${String(n)} selected=${form.intensity === String(n)}>${n} · ${word}</option>`)}</select></div></label>
      <label class="mp-sec"><span class="ork-label">Files</span><textarea class="ork-field mp-code" name="files" rows="3" value=${form.files} onInput=${set("files")} placeholder="config/balance.ts"></textarea>
        <span class="mp-cap">One file or folder of the project a line; one that is not there is left out</span></label>
      ${err && html`<p class="mp-err" role="alert">${err}</p>`}
      <div class="mp-acts"><button type="submit" class="ork-btn primary" disabled=${busy || !form.name.trim() || !form.line.trim()}>Save</button>
        <button type="button" class="ork-btn" onClick=${() => setEditing(false)}>Cancel</button></div>
    </form>`;
  }
  const gives = cur(s.gives), takes = cur(s.takes);
  return html`<span class="ork-label">${cap(lp.span)} loop · ${lp.name}</span>
    <h3 class="mp-back__nm">${s.name}</h3>
    <p class="mp-back__line">${s.line}</p>
    <${Sec} label="Feeling"><span class="mp-st__feel">${s.feel ? html`<b>${cap(s.feel)}</b> · ${FEEL_HINT[s.feel]}` : "Not said"}</span>
      <span class="mp-st__meta"><${Pips} n=${s.intensity} /><span>${INTENSITIES.find(([n]) => n === s.intensity)?.[1]}</span></span></${Sec}>
    <${Sec} label="Gives">${gives.length ? html`<span class="mp-back__cur">${gives.join(", ")}</span>` : html`<span class="mp-cap">It gives nothing</span>`}</${Sec}>
    <${Sec} label="Takes">${takes.length ? html`<span class="mp-back__cur">${takes.join(", ")}</span>` : html`<span class="mp-cap">It takes nothing</span>`}</${Sec}>
    <${Keeper} mine=${s.by === "person"} g=${g} />
    <${Sec} label="Rests on">${(s.rests_on || []).length
      ? html`<ul class="mp-list">${s.rests_on.map((p) => html`<li key=${p}><${FileLink} path=${p} from=${key} /></li>`)}</ul>`
      : html`<span class="mp-cap">It rests on no file yet</span>`}</${Sec}>
    <div class="mp-acts"><button type="button" class="ork-btn" onClick=${start}>Edit</button></div>`;
}

/** The back of a currency: its kind and line, what gives and takes it, **Edit** (its name). */
function CurrencyBack({ c, d, reload }) {
  const [editing, setEditing] = useState(false), [name, setName] = useState(""), { save, err, busy } = useSaver(d, reload);
  const steps = d.loops.flatMap((lp) => lp.steps), by = (k) => steps.filter((s) => s[k].includes(c.id)).map((s) => s.name).join(", ");
  const submit = async () => { if (await save((next) => { next.currencies.find((x) => x.id === c.id).name = name.trim(); })) setEditing(false); };
  if (editing) {
    return html`<form class="mp-form" onSubmit=${(e) => { e.preventDefault(); submit(); }}>
      <label class="mp-sec"><span class="ork-label">Name</span><input class="ork-field" name="name" maxlength="40" value=${name} onInput=${(e) => setName(e.target.value)} required /></label>
      ${err && html`<p class="mp-err" role="alert">${err}</p>`}
      <div class="mp-acts"><button type="submit" class="ork-btn primary" disabled=${busy || !name.trim()}>Save</button><button type="button" class="ork-btn" onClick=${() => setEditing(false)}>Cancel</button></div>
    </form>`;
  }
  return html`<span class="ork-label">Currency · ${c.kind}</span>
    <h3 class="mp-back__nm">${c.name}</h3>
    ${c.line && html`<p class="mp-back__line">${c.line}</p>`}
    <${Sec} label="Given by">${by("gives") ? html`<span class="mp-back__cur">${by("gives")}</span>` : html`<span class="mp-cap">Nothing gives it</span>`}</${Sec}>
    <${Sec} label="Taken by">${by("takes") ? html`<span class="mp-back__cur">${by("takes")}</span>` : html`<span class="mp-cap">Nothing takes it</span>`}</${Sec}>
    <div class="mp-acts"><button type="button" class="ork-btn" onClick=${() => { setName(c.name); setEditing(true); }}>Edit</button></div>`;
}

/** The loops as rings one in another, the core inside; each ring's tag says its span and name; the pixel dot steps round the core ring while the party's ork is at work. */
function Rings({ d, g, width, working }) {
  const L = layout(d.loops, width), head = g.leader?.head, cur = curNames(d), core = Math.max(0, d.loops.findIndex((lp) => lp.span === "core"));
  return html`<div class="mp-rings" style=${`height:${L.h}px`} data-loops=${d.loops.length}>
    <svg class="mp-rings__line" width=${width} height=${L.h} aria-hidden="true">${L.rings.map((r, i) => html`<ellipse key=${i} cx=${L.cx} cy=${L.cy} rx=${r.rx} ry=${r.ry} />`)}</svg>
    ${d.loops.map((lp, i) => {
      const r = L.rings[i];
      return html`<div key=${lp.span} class="mp-ring" data-span=${lp.span}>
        <div class=${cls("mp-ring__tag", { "is-mid": r.tag.mid })} style=${`left:${r.tag.x}px;top:${r.tag.y}px`} title=${[lp.line, lp.feeds && `feeds the ${lp.feeds} loop`].filter(Boolean).join(" · ") || undefined}>
          ${r.tag.mid && head && html`<${Head} race=${head.race} tier=${head.tier} />`}
          <span class="ork-label">${cap(lp.span)} · ${TIME[lp.span]}</span><span class="mp-ring__nm">${lp.name}</span>
        </div>
        ${r.places.map((p, j) => html`<i key=${`c${j}`} class=${`ork-chev ${p.dir} mp-ring__chev`} data-close=${j === r.places.length - 1 ? "" : undefined} style=${`left:${p.mx}px;top:${p.my}px`} aria-hidden="true"></i>`)}
        ${lp.steps.map((s, j) => html`<div key=${s.id} class="mp-slot" style=${`left:${r.places[j].x}px;top:${r.places[j].y}px;width:${L.cw}px`}><${StepCard} s=${s} narrow=${false} cur=${cur} /></div>`)}
      </div>`;
    })}
    ${working && html`<i class="mp-orbit" data-ring=${d.loops[core].span} style=${`offset-path:${orbitOf(L.cx, L.cy, L.rings[core].rx, L.rings[core].ry)}`} aria-hidden="true"></i>`}
  </div>`;
}

/** The loops as lists (under 640 px): each loop's tag, its line, its steps one under another. */
function Lists({ d }) {
  const cur = curNames(d);
  return html`<div class="mp-lists">${d.loops.map((lp) => html`<section key=${lp.span} class="mp-ll" data-span=${lp.span}>
    <span class="ork-label">${cap(lp.span)} · ${TIME[lp.span]}</span><h3 class="mp-ll__nm">${lp.name}</h3>
    <p class="mp-cap">${lp.line}${lp.feeds ? `${lp.line ? " · " : ""}feeds the ${lp.feeds} loop` : ""}</p>
    <div class="mp-ll__steps">${lp.steps.map((s) => html`<${StepCard} key=${s.id} s=${s} narrow=${true} cur=${cur} />`)}</div></section>`)}</div>`;
}

/** Whether any task of the party is at work (the page's own store of tasks, as the table reads it). */
const atWork = (g) => nodesFor(g).some((n) => (n.tasks || []).some((t) => RUN.includes(t.state)));

export function LoopMap({ g, narrow }) {
  const host = useRef(), wrap = useRef(), [rd, reload] = useRead("ideas.loop"), d = rd.data, width = useWidth(wrap);
  const [asked, setAsked] = useState(""), [busy, setBusy] = useState(false), at = useLifted(MAP), who = nameOf(g);
  const kept = !!d?.loops?.length, proposing = !!d?.proposing;
  useEffect(() => {                                                            // a proposal being made: look again until it is kept
    if (!proposing) return undefined;
    const t = setInterval(reload, POLL_MS);
    return () => clearInterval(t);
  }, [proposing]);
  const propose = async (again) => {
    setBusy(true);
    setAsked("");
    try {
      const got = await command("ideas.loop_propose", again ? { again: true } : {}, true);
      if (got && got.asked === false) setAsked(got.why || `${who} could not be asked now`);
    } catch (e) { setAsked(e.message || `${who} could not be asked now`); }
    setBusy(false);
    reload();
  };
  const steps = kept ? d.loops.flatMap((lp) => lp.steps.map((s) => [s, lp])) : [], hit = steps.find(([s]) => s.id === at), money = at.startsWith("cur:") && kept ? d.currencies.find((c) => `cur:${c.id}` === at) : null;
  const back = hit ? html`<${MapBack} host=${host} name=${hit[0].name} narrow=${narrow}><${StepBack} key=${hit[0].id} s=${hit[0]} lp=${hit[1]} d=${d} g=${g} reload=${reload} /></${MapBack}>`
    : money ? html`<${MapBack} host=${host} name=${money.name} narrow=${narrow}><${CurrencyBack} key=${money.id} c=${money} d=${d} reload=${reload} /></${MapBack}>` : null;
  const rung = !narrow && width >= RING_MIN, side = rung && width >= SIDE_MIN, ringW = side ? width - ECO_W - GAP : width;
  const ask = html`<div class="mp-bar"><span class="ork-label">The loop</span><div class="mp-bar__r">
    ${d?.was && html`<span class="mp-cap">Your version before this one is kept aside</span>`}
    <button type="button" class="ork-btn" disabled=${busy || proposing} onClick=${() => propose(true)} title=${`${who} reads the game's configs and proposes the loops again; the version kept now is kept aside`}>${proposing ? "Proposing…" : "Propose again"}</button></div></div>`;
  return html`<${MapFrame} map=${MAP} host=${host} back=${back} className="mp--loop">
    <div class="mp-loopwrap" ref=${wrap}>
      ${kept && html`${ask}
        ${(asked || d.error) && html`<p class="mp-err" role="alert">${asked || d.error}</p>`}
        <${Says} lines=${d.findings} />
        <div class=${cls("mp-loopbody", { "is-side": side })}>
          <div class="mp-loopmain">${rung ? html`<${Rings} d=${d} g=${g} width=${ringW} working=${atWork(g)} />` : html`<${Lists} d=${d} />`}
            ${!side && html`<${Economy} d=${d} />`}<${Feeling} loop=${feelingLoop(d.loops)} width=${side ? ringW : width} /></div>
          ${side && html`<div class="mp-loopside"><${Economy} d=${d} /></div>`}
        </div>`}
    </div>
    ${d && !kept && html`<div class="mp-propose">
      <${Nothing} what=${NONE_WHAT} />
      <div class="mp-acts"><button type="button" class="ork-btn primary" disabled=${busy || proposing} onClick=${() => propose(false)}>${proposing ? "Proposing…" : "Propose"}</button>
        <span class="mp-cap">${who} reads the game's configs and proposes the loops, the currencies and why a player comes back, in one short call</span></div>
      ${(asked || d.error) && html`<p class="mp-err" role="alert">${asked || d.error}</p>`}
    </div>`}
    ${!d && rd.err && html`<p class="mp-err" role="alert">${rd.err}</p>`}
  </${MapFrame}>`;
}

mapFor(MAP, LoopMap);
