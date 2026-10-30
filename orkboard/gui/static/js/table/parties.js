// The one place of the parties, over the pane (docs/specs/100-a-goals-way-as-cards.md §4, decisions §122.5, §137.1, §151.5, §164; spec 99 §1): kind `parties`, from the first start, the tabs' **+** and a party's **…** *Edit*
// (they call `openParties(props)`: `{party}` opens that party at the right, `{first}` is the first start). **At the left**, *Read from the project: <kind>* (a list of the kinds, to correct it: `ideas.project_kind_set`), the parties under the stages' headings *Idea*, *Being made* and
// *Live* — the stage the project is at is picked on its heading (*The project is here*: `ideas.stage_set`), the parties of the stages reached come ticked — and **Release** under *In every project*, ticked and locked (*the
// one way into main*); each party a row with its leader's head, ticked or not, pressed to open it at the right (partyseats2.js). **At the foot**, what the ticked parties cost together and **Start** (the first time: it makes
// them, then `ideas.project_ask`) or **Save** (*From the next task*). A made party is ticked for good here (it is removed from its tab's menu); a party that is not made yet is made by Start or Save with the squad and the
// size on the screen (`ideas.goal_save`: its `preset`, `leader`, `team`, `size`); a made party that changed is saved as it is (`slug`, `team`, `leader`, `size`). At the narrow width the left is a screen and the right the next.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command } from "../link.js";
import { Head, Icon, Sign } from "../orkui.js";
import { ask, board } from "../board/store.js";
import { currentProject } from "../shell/projects.js";
import { mapData, refreshShell } from "../shell/store.js";
import { useTools } from "../shell/toolpick.js";
import { drawn } from "../frame/kinds.js";
import { openOver, over, tab } from "../frame/state.js";
import { costOf } from "../hand/cost.js";
import { mapName, partiesAll } from "./data.js";
import { PartyRight, SIZES, Tick, headOf } from "./partyseats2.js";
import { SeatPop } from "./seatpop.js";

if (typeof document !== "undefined") {
  const href = new URL("./parties.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const STAGES = ["idea", "being_made", "live"];
const STAGE_WORDS = { idea: "Idea", being_made: "Being made", live: "Live" };
const NARROW = "(max-width: 759px)";                                              // spec 94: the phone's width is the narrow one

/** Opens the one place of the parties over the pane (`props.party`: a party's slug to open at the right; `props.first`: the first start, whatever the Board holds). It says it came from the map that was shown. */
export function openParties(props = {}, from = over.peek()?.from || { title: mapName(tab.value, partiesAll()), key: "" }) {
  openOver("parties", props, from, "Parties");
}

const offered = new Set();                                                          // the projects whose first start was opened by itself, this page load

/** The first start (decisions §169.4): the project read and no party but General — the empty Board — opens the one place at once, once per project per page load, as soon as the map has answered (an earlier open
 *  fires before the map is there). ← or Esc leaves it to the empty Board, which keeps *Choose the parties* to open it again. Nothing is opened over a thing already open. */
export function useFirstStart(parties) {
  const project = currentProject.value?.path || "", read = !!mapData.value && !!board.value;
  useEffect(() => {
    if (!read || parties.length || over.peek() || offered.has(project)) return;
    offered.add(project);
    openParties({ first: true });
  }, [read, project, parties.length]);
}

/** The kinds a project can be (realm/project_kind.py `KINDS`, in its order) and how the interface says each. A kind the host names that is not here is listed with the host's words. */
const KINDS = [["empty", "an empty folder"], ["mobile", "a mobile app"], ["game", "a game"], ["web", "a web app"], ["backend", "a backend"], ["data", "data work"], ["wiki", "a team's wiki"],
  ["design", "a designer's folder"], ["texts", "texts"], ["code", "code"]];

function useNarrow() {
  const [narrow, set] = useState(() => typeof matchMedia === "function" && matchMedia(NARROW).matches);
  useEffect(() => {
    if (typeof matchMedia !== "function") return undefined;
    const mq = matchMedia(NARROW), on = () => set(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return narrow;
}

/** What the host says to start from: the stage (`ideas.stage`) and the parties of the project's kind (`ideas.party_presets`); null while asked. */
function useBeginning() {
  const [got, setGot] = useState(null), live = useRef(true);
  const load = () => Promise.all([ask("ideas.stage"), ask("ideas.party_presets")]).then(([stage, presets]) => {
    if (live.current) setGot({ stage: stage || { stage: "idea", read: "idea" }, presets: (presets?.presets || []).filter((p) => p.group === "stage"), kind: presets?.kind || null });
  });
  useEffect(() => { live.current = true; load(); return () => { live.current = false; }; }, []);
  return [got, setGot, load];
}

/** The party the Board has of a preset: the one made from its recipe, else (a party made before recipes were kept) the one its leader leads. */
const madeFrom = (p, tracks) => tracks.find((t) => t.recipe === p.id) || tracks.find((t) => !t.recipe && t.leader?.slug === p.leader && !tracks.some((o) => o.recipe === p.id)) || null;

/** One party as the screen has it: ticked or not, its size, its squad (the person's changes are `edit`). */
function viewOf(p, tracks, edit, stage) {
  const track = madeFrom(p, tracks), e = edit[p.id] || {};
  const reached = STAGES.indexOf(p.stage) <= STAGES.indexOf(stage);
  return { p, track, made: !!track, on: p.locked || !!track || (e.on ?? reached), size: p.locked ? "lean" : e.size ?? (track?.size || p.size), squad: e.squad ?? (track ? track.team : p.squad) };
}

const same = (a, b) => JSON.stringify([...a].sort()) === JSON.stringify([...b].sort());

/** What Start or Save would send, party by party: a made party that changed, a party ticked that is not made. */
function changesOf(views) {
  return views.filter((v) => v.on).flatMap((v) => {
    if (!v.made) return [{ v, args: { title: v.p.name, about: v.p.line, leader: v.p.leader, team: v.squad, every: [], size: v.size, preset: v.p.id } }];
    const t = v.track, args = { slug: t.slug };
    if (!same(v.squad, t.team || [])) Object.assign(args, { leader: t.leader?.slug || v.p.leader, team: v.squad, every: (t.every || []).filter((s) => v.squad.includes(s)) });
    if (v.size !== (t.size || v.p.size)) args.size = v.size;
    return Object.keys(args).length > 1 ? [{ v, args }] : [];
  });
}

/** `ideas.party_price` for every size of the open party and for each ticked party at its size, asked once each: `price(party, size)` → `{low, high}` or null. */
function usePrices(views, open) {
  const [prices, setPrices] = useState({}), asked = useRef(new Set()), mounted = useRef(true);
  useEffect(() => () => { mounted.current = false; }, []);
  const wants = views.filter((v) => v.on || v.p.id === open).flatMap((v) => (v.p.id === open ? SIZES.map(([s]) => s) : [v.size]).map((size) => [v, size]));
  const key = (v, size) => JSON.stringify([v.p.leader, v.squad, size]);
  const sig = wants.map(([v, s]) => key(v, s)).join("|");
  useEffect(() => {
    for (const [v, size] of wants) {
      const k = key(v, size);
      if (asked.current.has(k)) continue;
      asked.current.add(k);
      command("ideas.party_price", { leader: v.p.leader, team: v.squad, every: [], size }, true)
        .then((a) => { if (mounted.current && a && !a.error) setPrices((was) => ({ ...was, [k]: { low: a.low, high: a.high } })); }).catch(() => asked.current.delete(k));
    }
  }, [sig]);
  return (v, size) => prices[key(v, size)] || null;
}

// -- the left ------------------------------------------------------------------------------------------------------------------------------

function PartyRow({ v, open, onTick, onOpen }) {
  const { p } = v, stuck = p.locked || v.made, head = headOf(v, p.leader, v.size, true);
  return html`<div class=${cls("parties__row", { "is-on": open })} data-party=${p.id} data-on=${String(v.on)} data-locked=${String(p.locked)}>
    <button type="button" class="parties__tickbtn" role="checkbox" aria-checked=${String(v.on)} aria-label=${`In the project: ${p.name}`} aria-disabled=${stuck ? "true" : undefined}
      title=${p.locked ? "The one way into main" : v.made ? "It is made: remove it from its tab's menu" : undefined} onClick=${() => !stuck && onTick(p.id)}><${Tick} on=${v.on} locked=${stuck} /></button>
    <button type="button" class=${cls("ork-row parties__open", { "is-on": open })} aria-current=${open ? "true" : undefined} onClick=${() => onOpen(p.id)}>
      <${Head} race=${head.race} tier=${head.tier} /><span class="parties__row-nm">${p.name}</span>
      ${p.locked && html`<span class="parties__muted">the one way into main</span>`}</button></div>`;
}

function Left({ got, views, open, onTick, onOpen, onStage, onKind }) {
  const stage = got.stage.stage, row = (v) => html`<${PartyRow} key=${v.p.id} v=${v} open=${open === v.p.id} onTick=${onTick} onOpen=${onOpen} />`;
  const kind = got.kind?.id || "", kinds = KINDS.some(([id]) => id === kind) || !kind ? KINDS : [[kind, got.kind.words || kind], ...KINDS];
  return html`<div class="parties__left">
    <label class="parties__kind"><span class="ork-label">Read from the project</span>
      <span class="ork-select"><select class="ork-field" value=${kind} aria-label="The project's kind, read from the project; change it if it is wrong" onChange=${(e) => onKind(e.target.value)}>
        ${kinds.map(([id, words]) => html`<option key=${id} value=${id} selected=${id === kind}>${words}</option>`)}</select></span></label>
    ${STAGES.map((s) => html`<section key=${s} class="parties__stage" data-stage=${s} aria-label=${STAGE_WORDS[s]}>
      <button type="button" class=${cls("ork-row parties__stage-h", { "is-on": stage === s })} aria-pressed=${String(stage === s)} onClick=${() => stage !== s && onStage(s)}>
        <span class="ork-label">${STAGE_WORDS[s]}</span>${stage === s && html`<span class="parties__here">The project is here</span>`}</button>
      ${views.filter((v) => !v.p.locked && v.p.stage === s).map(row)}</section>`)}
    <section class="parties__stage" data-stage="every" aria-label="In every project">
      <div class="parties__stage-h is-plain"><span class="ork-label">In every project</span></div>
      ${views.filter((v) => v.p.locked).map(row)}</section></div>`;
}

// -- the page --------------------------------------------------------------------------------------------------------------------------------

export function Parties({ props = {}, close }) {
  const [got, setGot, reload] = useBeginning(), tools = useTools(), narrow = useNarrow();
  const [edit, setEdit] = useState({}), [screen, setScreen] = useState(props.party ? "right" : "left"), [pop, setPop] = useState(""), [open, setOpen] = useState(""), [busy, setBusy] = useState(false);
  const tracks = (board.value?.tracks || []).filter((t) => t.slug !== "general");
  const presets = got?.presets || [], stage = got?.stage.stage || "idea";
  const views = presets.map((p) => viewOf(p, tracks, edit, stage));
  const price = usePrices(views, open);
  const first = props.first ?? tracks.length === 0;
  useEffect(() => {                                                                                      // the party asked for, else the first of the stages
    if (!got || open) return;
    const asked = props.party && tracks.find((t) => t.slug === props.party), mine = asked && presets.find((p) => madeFrom(p, [asked]) === asked);
    setOpen((mine || presets.find((p) => !p.locked) || presets[0] || {}).id || "");
  }, [got]);
  useLayoutEffect(() => {                                                                                    // Esc lowers the popover first: the table's own Esc would take the whole place away with it
    if (!pop) return undefined;
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); setPop(""); } };
    addEventListener("keydown", esc, true);
    return () => removeEventListener("keydown", esc, true);
  }, [pop]);
  if (!got) return html`<div class="parties" data-kind="parties"><p class="ok-tone-muted parties__wait">Reading the project…</p></div>`;
  const v = views.find((x) => x.p.id === open), g = v?.track && (mapData.value?.goals || []).find((x) => x.slug === v.track.slug);
  const change = (id, more) => setEdit((was) => ({ ...was, [id]: { ...was[id], ...more } }));
  const todo = changesOf(views), ticked = views.filter((x) => x.on);
  const sum = ticked.map((x) => price(x, x.size)).filter(Boolean), cost = sum.length && costOf({ kind: "change", row: { usd_low: sum.reduce((a, b) => a + b.low, 0), usd_high: sum.reduce((a, b) => a + b.high, 0) } });
  const setStage = async (s) => {
    const r = await ask("ideas.stage_set", { stage: s });
    if (r) setGot((was) => ({ ...was, stage: r }));
  };
  const commit = async () => {
    setBusy(true);
    let failed = false;
    for (const { args } of todo) {
      if (!(await ask("ideas.goal_save", args))) { failed = true; break; }
    }
    await refreshShell();
    if (!failed && first) await ask("ideas.project_ask", {});
    setBusy(false);
    if (!failed) close?.();
  };
  const onOpen = (id) => { setOpen(id); setPop(""); setScreen("right"); };
  const seatPress = (slug) => setPop(pop === slug ? "" : slug);
  const setKind = async (id) => {                                                                          // the person's correction: the parties fitted to it are asked again
    if (id !== got.kind?.id && (await ask("ideas.project_kind_set", { kind: id }))) await reload();
  };
  return html`<div class="parties" data-kind="parties" data-screen=${screen} data-first=${String(first)}>
    <div class="parties__body">
      <${Left} got=${got} views=${views} open=${open} onTick=${(id) => change(id, { on: !views.find((x) => x.p.id === id).on })} onOpen=${onOpen} onStage=${setStage} onKind=${setKind} />
      <div class="parties__right">
        ${narrow && html`<button type="button" class="ork-btn quiet parties__back" onClick=${() => { setScreen("left"); setPop(""); }}><${Icon} name="arrow-left" /> Parties</button>`}
        ${v ? html`<${PartyRight} v=${v} size=${v.size} setSize=${(size) => change(v.p.id, { size })} setSquad=${(squad) => change(v.p.id, { squad })} prices=${Object.fromEntries(SIZES.map(([s]) => [s, price(v, s)]))}
          tools=${tools} g=${g} onOpen=${seatPress} open=${pop} />` : null}
        ${pop && g && html`<${SeatPop} g=${g} slug=${pop} from=${over.peek()?.from || null} onClose=${() => setPop("")} />`}
      </div></div>
    <footer class="parties__foot">
      <span class="parties__total" data-total>${cost ? `These parties: ${cost.words} a goal` : "These parties: no price yet"}</span>
      <span class="parties__grow"></span>
      ${!first && html`<span class="parties__muted">From the next task</span>`}
      <button type="button" class="ork-btn primary" data-act=${first ? "start" : "save"} disabled=${busy || (!first && todo.length === 0)} onClick=${commit}>${first ? "Start" : "Save"}</button>
    </footer></div>`;
}

drawn("parties", ({ props, close }) => html`<${Parties} props=${props} close=${close} />`);
