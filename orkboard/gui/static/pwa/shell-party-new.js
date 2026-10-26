// New party on the phone (docs/specs/91-the-owners-list.md §7, decisions §107.5; docs/specs/41-phone-round-3.md §6, spec 50 §0): one sheet, the two halves of the desktop's dialog one step under the other.
// **Presets** first (shell-party-presets.js): *By stage of the project* (Ideation, Concept, Build, Release, LiveOps, fitted to what the project is), *By craft* (Tech, Design, Data, Marketing, Product, Art
// and sound) and *Your own party* (the Taskmaster alone), and the person's saved parties. Then the name and *What it is for*, the priority, and the team (shell-party-seats.js): **Size** — Lean ·
// Standard · Full: the seats and their tiers change at once — with the party's **Its AI tool**, and the bands **Leads**, **Does**, **Checks** by seats, each seat with its own AI tool (a sheet that says which tools
// can do what the role needs and why the others cannot) and a dashed free seat that opens a short list of roles. Under them what the party costs a goal and its checks on every goal; Save party is pinned at
// the foot with how many agents the party has and who takes a task (the Grunt fills in). *Save party* sends `ideas.goal_save` with `about`, `title`, `craft`, `leader`, `team`, `every`, `priority`, `size`, the
// party's `tool`, `tools` (the seats whose tool is not the party's), `party` (a party of the person's that was picked), `proposal` and `preset`. The party's heads gather into its deck (spec 63 §4).
import { h, head, sheet } from "./util.js";
import { field, foot, prioritySwitch } from "./shell-forms.js";
import { limitsNote } from "./shell-limits.js";
import { motionOn, gather } from "./shell-motion.js";
import { makeReleasesFrom } from "./shell-release.js";
import { PROPOSAL, STANDARD, loadProposals, proposes } from "./shell-proposals.js";
import { loadTools } from "./shell-party-tool.js";
import { raceOf } from "./shell-who.js";
import { say } from "./shell-words.js";
import { makePrice } from "./shell-party-price.js";
import { TASKMASTER, agentOf, bandOf, libraryPreset, loadPresets } from "./shell-party-model.js";
import { makePresets } from "./shell-party-presets.js";
import { makeSeats } from "./shell-party-seats.js";
import { makeRoutines, teamNote } from "./shell-party-run.js";

const GATHER_HEADS = 6;                                        // the heads that gather into the deck, the leader's first (spec 63 §4.1)

/** A proposal of the deal that the list does not hold, as a preset: its leader and its seats at Full, builders and checkers apart. */
function fromProposal(core, p) {
  const full = p.sizes?.full || p.sizes?.standard || {}, team = full.team || [];
  return { id: p.id, name: p.name, line: p.line, group: "stage", stage: "", recipe: p.id, whole: false, leader: full.leader, build: team.filter((s) => bandOf(core, s) === "build"), check: team.filter((s) => bandOf(core, s) === "check") };
}

/** `core`: the board's frame. Returns {el, open(after, presetId)}; `after(slug)` instead of opening the party's screen. */
export function makeNewGoal(core) {
  let then = null, opened = 0, priced = "", firstAnswer = false;
  const name = h("input", { class: "ork-field", type: "text", "aria-label": "Name", placeholder: "Its name, in a few words", maxlength: "120" });
  const about = h("textarea", { class: "ork-field", rows: "3", "aria-label": "What it is for", placeholder: "A few lines: what it is for", maxlength: "20000" });
  const priority = prioritySwitch("new-goal-priority");
  const presets = makePresets(core, { pick: (p) => press(p), own: (p) => seats.own(p) });
  const seats = makeSeats(core, { onChange: () => sync() });
  const price = h("div", { class: "party-pricebox" });
  const checks = h("div", { class: "party-checks", "data-sec": "checks" });
  const pr = makePrice(core, { current: priceOf, redraw: () => drawPrice() });             // what the party costs and can take (shell-party-price.js)
  const releasesFrom = makeReleasesFrom(core);       // the Release party takes its goals from the project's other parties: ticked so (spec 68 §7.6)
  const routines = makeRoutines();                   // the recurring goals a running party proposes, ticked (spec 92 §2)
  const about_team = teamNote();                     // Team has no seats: what it is, in their place (spec 92 §3)
  const left = h("div", {});
  const line = h("p", { class: "cap foot-line", "data-foot": "agents" });
  const save = h("button", { class: "ork-btn primary big", type: "button", disabled: true }, "Save party");
  const body = h("div", { class: "goal-steps one-sheet" });
  const sh = sheet("New party", body, foot(line, save));
  let releaseOn = false;

  name.addEventListener("input", () => sync());
  about.addEventListener("input", () => sync());

  function press(p) {
    seats.preset(p);
    presets.picked("");
    sync();
  }

  /** The pressed preset's name: the name the party is saved under when the person says neither a name nor what it is for (the placeholder of Name). */
  const suggest = () => seats.get().row?.name || "";

  /** What `ideas.party_price` is asked: the party as it stands, its craft, and its size's Target when the host sizes. */
  function priceOf() {
    const p = seats.get();
    return { leader: p.leader, team: p.team, every: p.every.filter((id) => p.team.includes(id)), ...(p.craft ? { craft: p.craft } : {}), ...(p.size && proposes(core) ? { size: p.size } : {}) };
  }

  /** What the party costs a goal and what it can take; a tool with no tiers of its own says its price is its own. */
  function drawPrice() {
    const own = seats.runsOwn() && proposes(core);
    price.replaceChildren(...[own ? h("p", { class: "party-price muted" }, "Runs its own model: its price is its own.") : pr.line(), own ? null : pr.takes()].filter(Boolean));
    pr.fit();
    drawChecks(seats.get());
  }

  /** The party's checks: each checker's, what it adds to a goal, and *Every goal* (how deep each goal is worked). */
  function drawChecks(p) {
    const checkers = p.team.map((id) => agentOf(core, id)).filter((a) => a?.check);
    if (agentOf(core, p.leader)?.pitch) { checks.replaceChildren(); return; }
    checks.replaceChildren(...[h("h4", {}, "Checks on every goal"), ...(checkers.length ? [h("div", { class: "checks-block", role: "group", "aria-label": "Checks" },
      h("p", { class: "muted" }, "How deep each goal is worked: every check adds a line to its Done when and a task to its plan."),
      ...checkers.map((a) => {
        const box = h("input", { type: "checkbox", "aria-label": `Every goal: ${a.name}`, ...(p.every.includes(a.id) ? { checked: true } : {}) });
        box.addEventListener("change", () => seats.setEvery(box.checked ? [...p.every, a.id] : p.every.filter((x) => x !== a.id)));
        return h("div", { class: "check-row" }, head(raceOf(a), a.tier || "warrior", { small: true }),
          h("span", { class: "check-text" }, h("b", {}, a.name), h("small", { class: "muted" }, say(`${a.check.done} · applies ${a.check.applies}`) + pr.adds(a.id))),
          h("label", { class: "check-every" }, box, h("span", {}, "Every goal")));
      }))] : [h("p", { class: "muted" }, "No checker in the party: a goal is done when its own Done when lines are.")])].filter(Boolean));
  }

  function sync() {
    const p = seats.get();
    presets.lit(p.lit);
    presets.picked(p.partyId);
    name.placeholder = suggest() || "Its name, in a few words";
    save.disabled = !(name.value.trim() || about.value.trim() || suggest()) || !seats.fits();
    const n = seats.agents(), team = Boolean(p.row?.ops);
    routines.set(p.row);
    for (const part of [seats.el, price, checks, releasesFrom.el]) part.hidden = team;
    about_team.hidden = !team;
    line.textContent = team ? "Your Operations stay yours: Team only shows them here" : `${n} ${n === 1 ? "agent" : "agents"} · a task goes to the one who does its kind of work, the Grunt fills in`;
    const key = JSON.stringify([p.leader, p.team, p.every, p.size, p.craft, seats.runsOwn()]);
    if (key !== priced && (p.lit || p.moved || p.partyId)) { const first = !priced; priced = key; pr.ask(first && firstAnswer, !(first && firstAnswer)); firstAnswer = false; }       // a party is on the seats: its price is asked (the opening's answer lights nothing)
    drawPrice();
    const on = p.leader === "release-manager";
    if (on !== releaseOn) { releaseOn = on; releasesFrom.set({ self: "", saved: [], leads: true, offers: on }); }
  }

  /** The craft the goal is given: its leader's, else (a Taskmaster's party) its members' most, the first on a tie, else the preset's. */
  const craftOf = (p) => {
    const lead = p.leader !== TASKMASTER && agentOf(core, p.leader)?.craft, crafts = p.team.map((id) => agentOf(core, id)?.craft).filter(Boolean);
    return lead || crafts.sort((a, b) => crafts.filter((x) => x === b).length - crafts.filter((x) => x === a).length)[0] || (p.row?.craft !== "mixed" && p.row?.craft) || "engineering";
  };

  /** Where the sheet shows the party's heads at the press (spec 63 §4.1), the leader's first, six at most: [{race, tier, box}]. A head that is not on screen starts from Save party. */
  function gatherFrom() {
    const view = sh.el.getBoundingClientRect(), floor = save.parentElement.getBoundingClientRect().top, mine = save.getBoundingClientRect(), p = seats.get();
    const shown = (b) => b.width > 0 && b.top >= view.top && b.bottom <= floor && b.left >= 0 && b.right <= innerWidth;
    const from = { left: mine.left + mine.width / 2 - 12, top: mine.top + mine.height / 2 - 11, width: 24, height: 22 };
    const ids = [p.leader, ...p.team.filter((s) => bandOf(core, s) === "build"), ...p.team.filter((s) => bandOf(core, s) === "check")];
    return ids.filter((id) => agentOf(core, id)).slice(0, GATHER_HEADS).map((id) => {
      const a = agentOf(core, id), b = [sh.el.querySelector(`.pseat img[data-agent="${CSS.escape(id)}"]`)?.getBoundingClientRect()].find((r) => r && shown(r)) || from;
      return { race: raceOf(a), tier: p.tiers[id] || a.tier || "warrior", box: { left: b.left, top: b.top, width: b.width, height: b.height } };
    });
  }

  /** The party is made: the sheet closes, the heads gather into the deck (spec 63 §4), the party's screen opens (or `after` is told). */
  async function made(got, heads) {
    for (const note of got.notes || []) core.flash(note);       // an agent of the project's own that the party carries stays as it was
    const after = then;
    then = null;
    if (!after) gather.wait(got.slug, heads);                   // New goal opening right after is what the person looks at: the heads gather only into a party they are shown
    sh.close();
    core.st.track = got.slug;
    await core.refresh();
    if (after) after(got.slug);
    else if (heads.length) setTimeout(() => core.open({ kind: "goal", slug: got.slug }), gather.ms(heads.length));     // the party's screen covers the deck: it opens once the heads have gathered and the deck is lit
    else core.open({ kind: "goal", slug: got.slug });
  }

  save.addEventListener("click", async () => {
    if (save.disabled) return;
    save.disabled = true;
    const p = seats.get(), tools = seats.seatTools(), sized = proposes(core), from = releasesFrom.get();
    const heads = motionOn() ? gatherFrom() : [];                // read at the press, before the sheet closes
    const library = !p.partyId && p.lit && (core.st.roles?.presets || []).some((x) => x.id === p.lit);
    const got = await core.call("ideas.goal_save", { ...(name.value.trim() || (!about.value.trim() && suggest()) ? { title: name.value.trim() || suggest() } : {}), about: about.value.trim(), craft: craftOf(p), leader: p.leader, team: p.team,
      every: p.every.filter((id) => p.team.includes(id)), priority: priority.get(), ...(p.partyId ? { party: p.partyId } : {}), ...(library ? { preset: p.lit } : {}),
      ...(sized && !p.partyId && p.lit && p.row?.recipe ? { proposal: p.row.recipe } : {}), ...(routines.kept().length ? { routines: routines.kept() } : {}), ...(from ? { releases_from: from } : {}), ...(sized && p.size ? { size: p.size } : {}),
      ...(sized && p.tool ? { tool: p.tool } : {}), ...(sized && Object.keys(tools).length ? { tools } : {}) });
    sync();
    if (!got?.slug) { gather.drop(); return; }
    await made(got, heads);
  });

  sh.el.addEventListener("close", () => { then = null; });

  body.replaceChildren(
    presets.el,
    h("section", { class: "new-goal-for", "aria-label": "About the party" }, field("Name", name), field("What it is for", about), h("div", { class: "field" }, h("span", { class: "field-label" }, "Priority"), priority.el)),
    seats.el, about_team, routines.el, price, checks, releasesFrom.el,
    h("p", { class: "muted hint" }, "The leader reads it and writes the title and the summary."), left);

  /** The preset to open on: the one asked for by id, a proposal of the deal (`proposal:<id>`), else the project's Build (a craft's Tech for an older host). */
  async function opening(presetId) {
    const wanted = presetId.startsWith(PROPOSAL) ? presetId.slice(PROPOSAL.length) : "", ask = wanted || presetId, list = core.st.partyPresets.presets;
    let pick = list.find((p) => p.id === ask || (wanted && p.recipe === wanted)) || (presetId && !wanted ? libraryPreset(core, presetId) : null);
    if (!pick && wanted) { const got = core.st.proposed || await loadProposals(core); const p = got?.proposals?.find((x) => x.id === wanted); pick = p ? fromProposal(core, p) : null; }
    return pick || list.find((p) => p.stage === "build") || list.find((p) => p.id === "engineering") || null;
  }

  return {
    el: sh.el,
    /** `presetId`: a party of the library picked at once (a pitch sent to a party the project lacks, spec 65 §5), or `proposal:<id>` (a proposal of the deal, spec 75 §5.3). */
    async open(after = null, presetId = "") {
      then = after;
      opened += 1;
      const mine = opened;
      priced = "";
      firstAnswer = true;
      pr.reset();
      name.value = "";
      about.value = "";
      save.disabled = true;
      priority.set("normal");
      price.replaceChildren();
      releaseOn = false;
      releasesFrom.set({ offers: false });
      seats.reset(proposes(core) ? STANDARD : "");
      presets.lit("");
      left.replaceChildren(limitsNote(core.st.snap) || "");
      sh.open();
      if (proposes(core)) loadTools(core).then(() => seats.draw());
      await loadPresets(core);
      if (mine !== opened) return;
      presets.draw();
      presets.load();
      const pick = await opening(presetId);
      if (mine === opened && pick) press(pick);
      sync();
    },
  };
}
