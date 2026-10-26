// The team of New party on the phone (docs/specs/91-the-owners-list.md §7, decisions §107.5), one step under the presets: **Size** — Lean · Standard · Full, a press changes the seats and their tiers at once —
// with the party's **Its AI tool**, then the bands **Leads**, **Does**, **Checks**, each with *k of n seats*. A seat is a card: its head (race by craft, gear by tier), its role in semibold, *<Tier> <race> ·
// what it does*, a chip when the role needs something its AI tool must make (*needs pictures*), **Its AI tool** (a 44 px button showing the tool's mark and name, the party's by default: it opens the sheet of
// shell-seat-tool.js) and × (*Remove … from the party*). A free seat is a dashed row, *Add a member* · *Add a checker* · *Choose a leader*, that opens a sheet of the library's roles for that band. Ideation's
// seats stay as they are. The desktop's twin is js/shell/partyseats.js and partydraft.js; this keeps the same state: the leader, the team, the size, the candidates (`rec`: the builders and the checkers
// most needed first; a size seats the first of each), `pool` (the preset's own, which a free seat's list offers first), the party's tool and each seat's.
import { h, head, icon, sheet } from "./util.js";
import { RACE_WORDS, TIER_WORDS, raceOf } from "./shell-who.js";
import { proposes, sizeSwitch } from "./shell-proposals.js";
import { runsOwn, toolPick, toolRow } from "./shell-party-tool.js";
import { makeSeatTool, toolMark } from "./shell-seat-tool.js";
import { IDEATION_WHOLE } from "./shell-goal-new.js";
import { TASKMASTER, agentOf, bandOf, library, recOf, seatsOf, sizeWords, sizedTeam, stageWord, tierOf, tiersFor } from "./shell-party-model.js";

const BANDS = [["lead", "Leads", "plans the party's goals"], ["build", "Does", "does the work"], ["check", "Checks", "checks before it lands"]];
const PITCH = { lead: "decides on each pitch", build: "each reads every pitch, alone", check: "makes the case against" };
const ADD = { lead: "Choose a leader", build: "Add a member", check: "Add a checker" };
const SHOWN = 6;                                              // the roles a sheet lists before *More roles*
const tag = (img, id) => { img.dataset.agent = id; return img; };

/** `core`: the board's frame; `onChange()`: the party changed (the sheet asks its price again). Returns {el, preset(p), own(p), get(), agents(), tiers(), reset(size), fits(), draw(), setEvery(ids)}. */
export function makeSeats(core, { onChange = () => {} } = {}) {
  const blank = (size = "") => ({ leader: TASKMASTER, team: [], rec: { build: [], check: [] }, pool: { build: [], check: [] }, size, tool: "", seatTools: {}, lit: "", row: null, craft: "", partyId: "", every: [], moved: false });
  let d = blank();
  const sized = () => proposes(core);
  const toolSheet = makeSeatTool(core);
  const listBody = h("div", { class: "seat-list" });
  const listSheet = sheet("Add a member", listBody);
  const size = sizeSwitch({ label: "Size", onPick: (id) => pickSize(id) });
  const says = h("p", { class: "cap size-says" });
  const toolLib = toolPick(core, { onPick: (id) => { d.tool = id; draw(); } });
  const bandsEl = h("div", { class: "pbands", role: "group", "aria-label": "The team" });
  const sizeEl = h("div", { class: "field size-field", role: "group", "aria-label": "Size" }, h("span", { class: "field-label" }, "Size"), size.el, says, toolLib.el);
  const el = h("div", { class: "pteam" }, sizeEl, bandsEl);
  el.append(toolSheet.el, listSheet.el);
  const fixed = () => agentOf(core, d.leader)?.pitch === true;
  const tiers = () => tiersFor(core, d.leader, d.team, d.size);
  const set = (patch) => { d = { ...d, ...patch }; draw(); };
  const kept = (leader, team) => ({ every: d.every.filter((id) => team.includes(id)), seatTools: Object.fromEntries(Object.entries(d.seatTools).filter(([a]) => a === leader || team.includes(a))) });

  function pickSize(id) {
    const team = sizedTeam(d.rec, id, seatsOf(core, d.leader));
    set({ size: id, team, ...kept(d.leader, team), partyId: JSON.stringify(team) === JSON.stringify(d.team) ? d.partyId : "" });
  }
  function put(band, id) {
    if (band === "lead") { set({ leader: id, lit: "", row: null, partyId: "", moved: true }); return; }
    const team = [...d.team.filter((s) => s !== id), id];
    set({ team, rec: { ...d.rec, [band]: team.filter((s) => bandOf(core, s) === band) }, lit: "", row: null, partyId: "", moved: true });
  }
  function leave(id) {
    if (id === d.leader) { set({ leader: TASKMASTER, ...kept(TASKMASTER, d.team), lit: "", row: null, partyId: "", moved: true }); return; }
    const team = d.team.filter((s) => s !== id), band = bandOf(core, id);
    set({ team, rec: { ...d.rec, [band]: team.filter((s) => bandOf(core, s) === band) }, ...kept(d.leader, team), lit: "", row: null, partyId: "", moved: true });
  }
  function seatTool(id, tool) {
    const rest = Object.fromEntries(Object.entries(d.seatTools).filter(([a]) => a !== id));
    set({ seatTools: tool ? { ...rest, [id]: tool } : rest });
  }

  const caption = (a, tier) => `${TIER_WORDS[tier] || ""} ${RACE_WORDS[raceOf(a)] || ""}${a.line ? ` · ${a.line}` : ""}`.trim();
  const needs = (a) => ((a?.needs || []).length ? h("span", { class: "ork-chip pseat__needs", "data-needs": a.needs.join(" ") }, `needs ${a.needs.join(" and ")}`) : null);

  /** The roles a band's sheet offers, the most needed first: the preset's candidates, then the leader's craft, then the rest; none already in the party and none of Ideation's. */
  function candidates(band) {
    const taken = new Set([d.leader, ...d.team]), want = band === "lead" ? [] : d.pool[band] || [], craft = agentOf(core, d.leader)?.craft;
    const rank = (a) => (want.includes(a.id) ? want.indexOf(a.id) : a.craft === craft ? 100 : 200);
    return library(core).filter((a) => a.band === band && !a.pitch && !taken.has(a.id)).sort((x, y) => rank(x) - rank(y));
  }
  function openList(band) {
    const rows = candidates(band);
    const paint = (all) => {
      const shown = all ? rows : rows.slice(0, SHOWN);
      listBody.replaceChildren(...[...shown.map((a) => h("button", { class: "team-row", type: "button", "data-agent": a.id, onclick: () => { listSheet.close(); put(band, a.id); } },
        head(raceOf(a), a.tier || "warrior"), h("b", {}, a.name, a.check ? h("span", { class: "check-badge" }, "checks") : null), h("small", { class: "muted" }, caption(a, a.tier)), needs(a))),
      rows.length ? null : h("p", { class: "muted" }, "No other role of the library fits this seat."),
      !all && rows.length > SHOWN ? h("button", { class: "ork-btn", type: "button", "data-act": "more-roles", onclick: () => paint(true) }, `More roles (${rows.length - SHOWN})`) : null].filter(Boolean));
    };
    listSheet.title(ADD[band]);
    paint(false);
    listSheet.open();
  }

  function seat(id, band, over = false) {
    const a = agentOf(core, id) || { id, name: id, craft: "engineering", tier: "warrior", line: "" }, tier = tierOf(core, id, tiers());
    const away = id === TASKMASTER || fixed() ? null : h("button", { class: "ork-btn pseat__x", type: "button", "data-act": "remove", "aria-label": `Remove ${a.name} from the party`, onclick: () => leave(id) }, icon("close"));
    const party = toolRow(core, d.tool), mine = d.seatTools[id] ? core.st.tools?.tools?.find((t) => t.id === d.seatTools[id]) : null;
    const words = mine ? mine.name : `Party's tool · ${party?.name || "Claude Code"}`;
    const btn = id === TASKMASTER || !core.st.tools || !sized() ? null : h("button", { class: "ork-btn pseat__tool", type: "button", "data-seat-tool": id, "data-tool": d.seatTools[id] || "",
      "aria-label": `Its AI tool for ${a.name}: ${words}`, "aria-haspopup": "dialog", onclick: () => toolSheet.open({ role: a, tier, value: d.seatTools[id] || "", partyTool: d.tool, onPick: (t) => seatTool(id, t) }) },
    toolMark((mine || party)?.id), h("span", {}, words), h("i", { class: "ork-chev", "aria-hidden": "true" }));
    const hint = mine && mine.installed && !mine.signed_in ? h("small", { class: "muted pseat__hint" }, "Not signed in: sign in on the computer. The party's work waits for it.") : null;
    return h("div", { class: `pseat${band === "lead" ? " is-lead" : ""}`, "data-seat": id, "data-band": band },
      h("span", { class: `pseat__head${over ? " is-over" : ""}` }, tag(head(raceOf(a), tier), id)),
      h("div", { class: "pseat__who" }, h("b", {}, a.name, a.check ? h("span", { class: "check-badge" }, "checks") : null), h("small", { class: "muted" }, caption(a, tier))),
      away, needs(a), btn, hint);
  }

  function draw() {
    const seats = seatsOf(core, d.leader, d.team), pitch = fixed();
    bandsEl.replaceChildren(...[...BANDS.map(([band, words, what]) => {
      const mine = band === "lead" ? [d.leader] : d.team.filter((s) => bandOf(core, s) === band), real = band === "lead" ? mine.filter((x) => x !== TASKMASTER) : mine;
      const free = band === "lead" ? (d.leader === TASKMASTER ? 1 : 0) : Math.max(0, seats[band] - real.length);
      return h("section", { class: `pband band-${band}`, "aria-label": words, "data-band": band, "data-stage": stageWord(core, d.leader, band) },
        h("div", { class: "pband__head" }, h("h3", {}, words), h("small", { class: "muted" }, pitch ? PITCH[band] : what),
          h("small", { class: "muted pband__seats", "data-seats": band }, `${Math.max(real.length, band === "lead" ? 1 : 0)} of ${seats[band]} seats`)),
        ...mine.map((id, i) => seat(id, band, band !== "lead" && !pitch && i >= seats[band])),
        band !== "lead" && !pitch && real.length > seats[band] ? h("p", { class: "party-over", role: "alert" },
          `${stageWord(core, d.leader, band)} has ${seats[band]} ${seats[band] === 1 ? "seat" : "seats"} with ${agentOf(core, d.leader)?.name || "Taskmaster"}: take one out first.`) : null,
        ...(pitch ? [] : Array.from({ length: free }, () => h("button", { class: "pseat is-empty", type: "button", "data-free": band, "aria-haspopup": "dialog", onclick: () => openList(band) },
          h("span", { class: "team-seat is-empty" }), h("span", { class: "pseat__add" }, icon("plus"), ADD[band])))));
    }), pitch ? h("p", { class: "muted party-whole", "data-sec": "ideation" }, IDEATION_WHOLE) : null].filter(Boolean));
    sizeEl.hidden = !sized();
    size.set(d.size);
    says.textContent = d.size ? `${sizeWords(d.size, 1 + d.team.length)} · works as ${{ lean: "thrift", standard: "balance", full: "quality" }[d.size]}` : "";
    toolLib.set(d.tool);
    onChange();
  }

  return {
    el,
    /** A preset pressed: its leader and its candidates, the team of the size picked. */
    preset(p) {
      const leader = p.leader || TASKMASTER, rec = { build: [...(p.build || [])], check: [...(p.check || [])] };
      set({ leader, rec, pool: rec, team: sizedTeam(rec, d.size, agentOf(core, leader)?.pitch && !d.size ? { build: rec.build.length, check: rec.check.length } : seatsOf(core, leader)), every: [], seatTools: {}, lit: p.id, row: p, craft: p.craft || "", partyId: "" });
    },
    /** A saved party of the person's: its seats as they are, whatever the size. */
    own(p) {
      const leader = p.leader || TASKMASTER, team = [...p.team], rec = recOf(core, team);
      set({ leader, team, rec, pool: rec, every: [...p.every], seatTools: {}, lit: "", row: null, craft: p.craft || "", partyId: p.id });
    },
    /** A new party: no seats, the size `size` ("" for a host that does not size). */
    reset(sizeNow) { d = blank(sizeNow); draw(); },
    setEvery(every) { set({ every, lit: "", row: null, partyId: "" }); },
    get: () => ({ ...d, tiers: tiers() }),
    agents: () => 1 + d.team.length,
    tiers,
    /** Whether the party fits its leader's seats (a saved party made before is saved as it was). */
    fits: () => d.partyId !== "" || fixed() || ["build", "check"].every((b) => d.team.filter((s) => bandOf(core, s) === b).length <= seatsOf(core, d.leader)[b]),
    /** The seats whose AI tool is not the party's: {agent: tool}. */
    seatTools() { const main = core.st.tools?.main || "claude"; return Object.fromEntries(Object.entries(d.seatTools).filter(([a, t]) => t && t !== (d.tool || main) && (a === d.leader || d.team.includes(a)))); },
    runsOwn: () => runsOwn(core, d.tool),
    draw,
  };
}
