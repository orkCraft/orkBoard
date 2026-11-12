// The one place of the parties (docs/specs/130-the-first-open-is-the-orkmasters.md C.1–C.3, decisions §232.2, §232.6, §122.5, §137.1; spec 100 §4; mockup docs/mockups/setup/ #parties): **the Orkmaster's large card on the table**, dealt from its head: the same card the first time, from the empty chair and from a party's *Edit* (they call `openParties(props)`). At its top
// **The project is** and the kinds' list, with what it was read from (`ideas.project_kind_set`); under it the stages (*Idea*, *Being made*, *Live*), the stage the project is at marked *The project is here* and set by a press on another's heading (`ideas.stage_set`); each party of a stage reached one line and its heads (partyseats2.js), the stages not reached in one line of heads and names. A head or a mark pressed opens its seat (seatpop.js).
// **At its foot** what the ticked parties cost together, said plainly, and **Start** the first time (it makes them by `ideas.goal_save`, then `ideas.project_ask`: the table is laid, laying.js) or **Save** (*From the next task*). A made party is ticked for good here (it is removed from its tab's menu); nothing is saved until Start or Save. It is about 620 px at the wide width and never covers the potions; at the narrow width the card is the screen, one party a block.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command, town } from "../link.js";
import { ask, board } from "../board/store.js";
import { currentProject } from "../shell/projects.js";
import { mapData, refreshShell } from "../shell/store.js";
import { useTools } from "../shell/toolpick.js";
import { drawn } from "../frame/kinds.js";
import { lifted, openOver, over, tab } from "../frame/state.js";
import { setupNow } from "../hand/setupcards.js";
import { isToolKey, stopKeyOf } from "../hand/state.js";
import { mapName, partiesAll } from "./data.js";
import { LaterRow, PartyRow, SIZES, usdWords } from "./partyseats2.js";
import { SeatDraft } from "./seatpop.js";

if (typeof document !== "undefined") {
  const href = new URL("./parties.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

export const STAGES = ["idea", "being_made", "live"];
export const STAGE_WORDS = { idea: "Idea", being_made: "Being made", live: "Live" };

/** Opens the one place of the parties over the pane (`props.party`: the party it came from; `props.first`: the first start, whatever the Board holds). It says it came from the map that was shown. */
export function openParties(props = {}, from = over.peek()?.from || { title: mapName(tab.value, partiesAll()), key: "" }) {
  openOver("parties", props, from, "Parties");
}

const offered = new Set();                                                          // the projects whose first start was opened by itself, this page load

/** The first start (decisions §169.4, §232): no party but General opens the card once, once per project per page load, as soon as the map has answered and the Orkmaster has come to it. Nothing is opened over a thing already open. */
export function useFirstStart(parties) {
  const project = currentProject.value?.path || "", read = !!mapData.value && !!board.value, asks = setupNow.value?.step || "", talk = !!town.value?.tools, adding = isToolKey(stopKeyOf(lifted.value));      // the Orkmaster asks its questions first (spec 130 A.4): the parties' place comes at its step, once the adding card is put away
  useEffect(() => {
    if (!read || parties.length || over.peek() || offered.has(project) || (talk && asks !== "parties") || adding) return;
    offered.add(project);
    openParties({ first: true });
  }, [read, project, parties.length, asks, adding]);
}

/** The kinds a project can be (realm/project_kind.py `KINDS`, in its order) and how the interface says each. A kind the host names that is not here is listed with the host's words. */
export const KINDS = [["empty", "an empty folder"], ["mobile", "a mobile app"], ["game", "a game"], ["web", "a web app"], ["backend", "a backend"], ["data", "data work"], ["wiki", "a team's wiki"],
  ["design", "a designer's folder"], ["texts", "texts"], ["code", "code"]];

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
export const madeFrom = (p, tracks) => tracks.find((t) => t.recipe === p.id) || tracks.find((t) => !t.recipe && t.leader?.slug === p.leader && !tracks.some((o) => o.recipe === p.id)) || null;

/** One party as the card has it: ticked or not, its size, its squad, its AI tool, each seat's own and the levels set by hand (the person's changes are `edit`). */
function viewOf(p, tracks, edit, stage) {
  const track = madeFrom(p, tracks), e = edit[p.id] || {}, reached = STAGES.indexOf(p.stage) <= STAGES.indexOf(stage);
  return { p, track, made: !!track, reached, on: p.locked || !!track || (e.on ?? reached), size: p.locked ? "lean" : e.size ?? (track?.size || p.size), squad: e.squad ?? (track ? track.team : p.squad),
    tool: e.tool ?? (track?.tool || ""), tools: e.tools ?? (track?.tools || {}), tiers: e.tiers ?? {} };
}

const same = (a, b) => JSON.stringify([...a].sort()) === JSON.stringify([...b].sort());
const sameTools = (a, b) => JSON.stringify(Object.entries(a).sort()) === JSON.stringify(Object.entries(b).sort());

/** What Start or Save would send, party by party: a made party that changed, a party ticked that is not made. */
function changesOf(views) {
  return views.filter((v) => v.on).flatMap((v) => {
    const own = { ...(v.tool ? { tool: v.tool } : {}), ...(Object.keys(v.tools).length ? { tools: v.tools } : {}), ...(Object.keys(v.tiers).length ? { tiers: v.tiers } : {}) };
    if (!v.made) return [{ v, args: { title: v.p.name, about: v.p.line, leader: v.p.leader, team: v.squad, every: [], size: v.size, preset: v.p.id, ...own } }];
    const t = v.track, args = { slug: t.slug };
    if (!same(v.squad, t.team || [])) Object.assign(args, { leader: t.leader?.slug || v.p.leader, team: v.squad, every: (t.every || []).filter((s) => v.squad.includes(s)) });
    if (v.size !== (t.size || v.p.size)) args.size = v.size;
    if (v.tool !== (t.tool || "")) args.tool = v.tool;
    if (!sameTools(v.tools, t.tools || {})) args.tools = v.tools;
    if (Object.keys(v.tiers).length) args.tiers = v.tiers;
    return Object.keys(args).length > 1 ? [{ v, args }] : [];
  });
}

/** `ideas.party_price` for every size of each party on the card, asked once each: `price(v, size)` → `{low, high}` or null. */
function usePrices(views) {
  const [prices, setPrices] = useState({}), asked = useRef(new Set()), mounted = useRef(true);
  useEffect(() => () => { mounted.current = false; }, []);
  const key = (v, size) => JSON.stringify([v.p.leader, v.squad, size]);
  const wants = views.filter((v) => v.on).flatMap((v) => SIZES.map(([s]) => [v, s]));
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

function StageHead({ id, here, onSet }) {
  return html`<button type="button" class=${cls("pc-stage", { "is-here": here })} data-stage-head=${id} aria-pressed=${String(here)} aria-label=${here ? `${STAGE_WORDS[id]}: the project is here` : `${STAGE_WORDS[id]}: set the project here`} onClick=${() => !here && onSet(id)}>
    <span class="pc-stage__t">${STAGE_WORDS[id]}</span>${here ? html`<span class="parties__here">The project is here</span>` : html`<span class="pc-stage__set">Set the project here</span>`}</button>`;
}

export function Parties({ props = {}, close }) {
  const [got, setGot, reload] = useBeginning(), tools = useTools(), [edit, setEdit] = useState({}), [seat, setSeat] = useState(null), [busy, setBusy] = useState(false);
  const tracks = (board.value?.tracks || []).filter((t) => t.slug !== "general");
  const presets = (got?.presets || []).filter((p) => !p.waits || madeFrom(p, tracks)), stage = got?.stage.stage || "idea", views = presets.map((p) => viewOf(p, tracks, edit, stage)), price = usePrices(views);
  const first = props.first ?? tracks.length === 0, name = currentProject.value?.name || "the project";
  useLayoutEffect(() => {                                                                                    // Esc lowers the seat first: the table's own Esc would take the whole card away with it
    if (!seat) return undefined;
    const esc = (e) => { if (e.key === "Escape" && !e.defaultPrevented) { e.preventDefault(); setSeat(null); } };
    addEventListener("keydown", esc, true);
    return () => removeEventListener("keydown", esc, true);
  }, [seat?.slug]);
  if (!got) return html`<div class="parties" data-kind="parties"><p class="ok-tone-muted parties__wait">Reading the project…</p></div>`;
  const change = (id, more) => setEdit((was) => ({ ...was, [id]: { ...was[id], ...more } }));
  const todo = changesOf(views), ticked = views.filter((x) => x.on), sum = ticked.map((x) => price(x, x.size)).filter(Boolean);
  const total = sum.length ? { low: sum.reduce((a, b) => a + b.low, 0), high: sum.reduce((a, b) => a + b.high, 0) } : null;
  const setStage = async (s) => { const r = await ask("ideas.stage_set", { stage: s }); if (r) setGot((was) => ({ ...was, stage: r })); };
  const commit = async () => {
    const mine = over.peek();                                                        // what was over the pane when Start or Save was pressed: only that is closed at the end
    setBusy(true);
    if (first) offered.add(currentProject.value?.path || "");                       // Start lays the table: its mount must not offer the first start again while the snapshot still has no party (useFirstStart)
    let failed = false;
    for (const { args } of todo) {
      if (!(await ask("ideas.goal_save", args))) { failed = true; break; }
    }
    await refreshShell();
    if (!failed && first) await ask("ideas.project_ask", {});
    setBusy(false);
    if (!failed && over.peek() === mine) close?.();                                 // the person may have opened the card again meanwhile (the project's questions take a while): that one stays
  };
  const setKind = async (id) => { if (id !== got.kind?.id && (await ask("ideas.project_kind_set", { kind: id }))) await reload(); };      // the person's correction: the parties fitted to it are asked again
  const kind = got.kind?.id || "", kinds = KINDS.some(([id]) => id === kind) || !kind ? KINDS : [[kind, got.kind.words || kind], ...KINDS];
  const onTick = (id) => change(id, { on: !views.find((x) => x.p.id === id).on });
  const row = (v) => html`<${PartyRow} key=${v.p.id} v=${v} main=${tools?.main || ""} prices=${Object.fromEntries(SIZES.map(([s]) => [s, price(v, s)]))} open=${seat?.party === v.p.id ? seat.slug : ""} onTick=${onTick} onSize=${(size) => change(v.p.id, { size })}
    onSeat=${(slug) => setSeat(seat?.party === v.p.id && seat.slug === slug ? null : { party: v.p.id, slug })} />`;
  const open = seat && views.find((x) => x.p.id === seat.party);
  return html`<div class="parties-wrap"><article class="ork-card parties ork-deal" data-kind="parties" data-first=${String(first)} aria-label=${`The parties for ${name}`}>
    <h2 class="pc-title">The parties for ${name}</h2>
    <label class="pc-kind"><span class="ork-label">The project is</span>
      <span class="ork-select"><select class="ork-field" value=${kind} aria-label="The project is; change it if it was read wrong" onChange=${(e) => setKind(e.target.value)}>
        ${kinds.map(([id, words]) => html`<option key=${id} value=${id} selected=${id === kind}>${words}</option>`)}</select></span>
      ${got.kind?.how && html`<span class="pc-muted" data-how="1">read from ${got.kind.how}</span>`}</label>
    ${STAGES.map((s) => {
      const here = views.filter((v) => v.p.stage === s), reached = STAGES.indexOf(s) <= STAGES.indexOf(stage), later = reached ? [] : here.filter((v) => !v.on && !v.made), full = reached ? here : here.filter((v) => v.on || v.made);
      return html`<section key=${s} class="pc-sec" data-stage=${s} aria-label=${STAGE_WORDS[s]}>
        <${StageHead} id=${s} here=${stage === s} onSet=${setStage} />
        ${full.map(row)}
        ${later.length > 0 && html`<${LaterRow} views=${later} words=${`offered when the project is ${STAGE_WORDS[s].toLowerCase()}`} onTick=${onTick} />`}</section>`;
    })}
    <footer class="pc-foot">
      <span class="pc-total" data-total>${total ? html`Together <b>≈ ${usdWords(total)} a goal</b> at the API's prices. On a subscription it is taken from its limits instead.` : "Together: no price yet."}</span>
      ${!first && html`<span class="pc-muted">From the next task</span>`}
      <button type="button" class="ork-btn primary" data-act=${first ? "start" : "save"} disabled=${busy || (!first && todo.length === 0)} onClick=${commit}>${first ? "Start" : "Save"}</button>
    </footer></article>
    ${open && html`<${SeatDraft} key=${seat.slug} v=${open} slug=${seat.slug} tools=${tools} hand=${town.value?.tools?.hand || null} onChange=${(more) => change(open.p.id, more)} onClose=${() => setSeat(null)} from=${over.peek()?.from || null} />`}
  </div>`;
}

drawn("parties", ({ props, close }) => html`<${Parties} props=${props} close=${close} />`);
