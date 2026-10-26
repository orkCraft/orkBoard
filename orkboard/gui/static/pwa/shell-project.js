// The project's level on the phone (docs/specs/70-orkmaster-and-the-project.md §2.1, §2.4, §3, §4; decisions §85): the Orkmaster is the project's ork; a row at the top of the parties' sheet (shell-where.js) opens
// **The project**, a full sheet: the Orkmaster's head, its **two rows** (docs/specs/91-the-owners-list.md §8, one under the other, every target 44 px at least) — **Parties**: a strip of *New party* (a dashed card) and two
// or three ready parties that suit this kind of project, in `ideas.map`'s `project.deal` order (the Orkmaster's proposals first when the host proposes, spec 75 §5.3), each with its leader's head, its name, who and what for
// and **Add**, which opens New party on it; **New goal**: one line, **for <party>** (the Orkmaster's guess, `ideas.party_for` of the kind the line says; the person's pick stays), **Add goal** and under them
// *<Party>'s kinds:* (three at most, the guessed one marked *· guessed* once a line is typed: `ideas.kind_for`, words, no model) and **More kinds…**, which opens today's New goal form (shell-ideas.js `openProject`) with the
// line carried over —, then a section for each party (its leader's head, its name, *k/n*, **Open <party>**; under it its goals as rows: Planning and At work, Waits for main and Flags folded; a row opens the goal's
// screen). A host without `project` has none of it. *Add goal* sends what New goal sends (`ideas.add`, delivered as it is: kept when there is no signal).
// After the parties comes a section **Assets** (spec 88 §7; shell-assets.js): the project's files by kind as tokens, a token's own screen, the changes since this device's last look.
// Pure words here too: `whyWords`, `fitWords`, `dealOf`.
import { h, head, sheet } from "./util.js";
import { elem, sign, typeTone } from "./shell-marks.js";
import { raceOf, whoHead } from "./shell-who.js";
import { chipsOf, modelOf } from "./shell-arena-words.js";
import { flagTally, goalsOf } from "./shell-goals-words.js";
import { PROPOSAL, STANDARD, loadProposals, proposes } from "./shell-proposals.js";
import { makeAssets } from "./shell-assets.js";

const READY = 3, KINDS_SHOWN = 3, GUESS_MS = 250;         // ready parties offered; kinds shown; the line rests this long before its kind is guessed
const ROWS = { parties: "Parties", partiesCap: "who works on this project", newParty: "New party", add: "Add", goal: "New goal", goalCap: "say it in a line: the Orkmaster picks its kind",
  addGoal: "Add goal", more: "More kinds…", guessed: "guessed", placeholder: "Say it in a line, in your own words" };

export const PROJECT = "@project";                   // `ideas.shown`'s party for the project's level
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;

/** The project block of `ideas.map` (null for a host older than spec 70). */
export const projectOf = (core) => core.st.map?.project || null;

/** Why the Orkmaster deals a party first (or last): `d` is a `project.deal` entry. */
export function whyWords(d) {
  if (d?.why === "flags_wait") return `${plural(d.n || 0, "flag")} ${d.n === 1 ? "waits" : "wait"} and no party releases ${d.n === 1 ? "it" : "them"}`;
  if (d?.why === "no_pitches") return "No party judges small ideas yet";
  if (d?.why === "have") return "You have one";
  return "";
}

/** The deal as a map: preset id → {i, why, n, words}; empty for a host with no `project`. */
export function dealOf(core) {
  return new Map((projectOf(core)?.deal || []).map((d, i) => [d.id, { i, why: d.why || "", n: d.n || 0, words: whyWords(d) }]));
}

/** How a party fits a goal's type, as `ideas.party_for` says it: *takes it whole* · *needs Artist* · *no one there does it* (a pitch in Ideation, no type). */
export function fitWords(p) {
  if (p.fits === "whole") return "takes it whole";
  if (p.fits === "missing") return `needs ${(p.missing || []).map((m) => m.name || m.agent).join(", ")}`;
  if (p.fits === "none") return "no one there does it";
  if (p.fits === "pitch") return "a pitch there";
  return "";
}

/** The ready parties of the *Parties* row: the Orkmaster's proposals the deal names or lacks first, then the library's in the deal's order, those the project has left out, the first three; each
 *  `{id, name, line, why, lead: {race, tier, name}, size, open: {proposal} | {preset}}`. `proposals`: `ideas.proposals`'. */
export function readyOf(core, proposals = []) {
  const deal = dealOf(core), lib = core.st.roles?.library || [], presets = core.st.roles?.presets || [], byId = new Map(proposals.map((p) => [p.id, p])), seen = new Set(), out = [];
  const ofProposal = (p) => {
    const std = p.sizes?.[STANDARD] || Object.values(p.sizes || {})[0], lead = std?.heads?.[0];
    return { id: p.id, name: p.name, line: p.line || "", why: p.why || "", have: Boolean(p.have), lead: lead ? { race: lead.race || "peon", tier: lead.tier || "warrior", name: lib.find((a) => a.id === std.leader)?.name || "" } : null,
      size: std ? Math.max(0, (std.agents ?? 1 + (std.team || []).length) - 1) : 0, open: { proposal: p.id } };
  };
  const ofPreset = (p, d) => {
    const lead = lib.find((a) => a.id === p.lead);
    return { id: p.id, name: p.name, line: p.line || "", why: d?.words || "", have: d?.why === "have", lead: lead ? { race: raceOf(lead), tier: lead.tier || "warrior", name: lead.name } : null,
      size: (p.build || []).length + (p.check || []).length, open: { preset: p.id } };
  };
  for (const p of proposals) if (!deal.has(p.id)) { out.push(ofProposal(p)); seen.add(p.id); }
  for (const id of deal.keys()) {
    if (seen.has(id)) continue;
    seen.add(id);
    if (byId.has(id)) out.push(ofProposal(byId.get(id)));
    else if (presets.some((p) => p.id === id)) out.push(ofPreset(presets.find((p) => p.id === id), deal.get(id)));
  }
  return out.filter((c) => !c.have).slice(0, READY);
}

/** The Orkmaster's two rows (docs/specs/91-the-owners-list.md §8), stacked: **Parties** and **New goal**. `act`: {deliver, flash}; `close`: puts the project's sheet away. Returns {el, draw(), load(), reset()}:
 *  `reset` clears the line and what was picked, `load` asks the host for the proposals, the Orkmaster's party and the line's kind. */
function makeRows(core, act, close) {
  const st = core.st;
  let proposing = [], parties = [], suggested = "", mineParty = "", kind = "", own = "", mine, busy = false, seq = 0, timer = 0, menuOn = false;       // `mine`: the kind the person picked (undefined: the guessed one)
  const goalOf = (slug) => (st.map?.goals || []).find((g) => g.slug === slug);
  const typesOf = (slug) => (goalOf(slug)?.ideation ? [] : goalOf(slug)?.types || []);
  const picked = () => (parties.some((p) => p.party === mineParty) ? mineParty : suggested);
  const nameOf = (slug) => parties.find((p) => p.party === slug)?.name || goalOf(slug)?.short || goalOf(slug)?.title || "";

  const strip = h("div", { class: "orow__strip", role: "group", "aria-label": ROWS.parties });
  const text = h("input", { class: "ork-field orow__text", type: "text", enterkeyhint: "done", maxlength: "2000", autocomplete: "off", "aria-label": ROWS.goal, placeholder: ROWS.placeholder });
  const forBtn = h("button", { class: "ork-btn orow__for", type: "button", "aria-haspopup": "listbox", "aria-expanded": "false", "data-act": "for-party" });
  const menu = h("div", { class: "orow__menu", role: "listbox", "aria-label": "Its party", hidden: true });
  const add = h("button", { class: "ork-btn primary orow__add", type: "button", "data-act": "add-goal", disabled: true }, ROWS.addGoal);
  const kinds = h("div", { class: "okinds", role: "group" });
  const el = h("section", { class: "orows", "aria-label": "Parties and goals" },
    h("div", { class: "orow", "data-row": "parties" }, h("div", { class: "orow__lab" }, h("b", {}, ROWS.parties), h("small", { class: "muted" }, ROWS.partiesCap)), strip),
    h("div", { class: "orow", "data-row": "goal" }, h("div", { class: "orow__lab" }, h("b", {}, ROWS.goal), h("small", { class: "muted" }, ROWS.goalCap)),
      text, h("div", { class: "orow__go" }, forBtn, add), menu, kinds));

  const line = () => text.value.trim();
  /** The kind in force: the person's pick ("" none), else the guessed one, only when the party picked offers it. */
  function chosen() {
    const ids = typesOf(picked()).map((t) => t.id), want = mine !== undefined ? mine : line() ? own : "";
    return ids.includes(want) ? want : "";
  }

  function cards() {
    const ready = readyOf(core, proposing);
    const newParty = h("button", { class: "ocard ocard--new", type: "button", "data-act": "project-new-party", "aria-haspopup": "dialog", onclick: () => { close(); core.editGoal(""); } },
      h("b", {}, `+ ${ROWS.newParty}`));
    return [newParty, ...ready.map((c) => h("article", { class: "ocard", "data-preset": c.id, "data-proposal": c.open.proposal || "", "aria-label": c.name },
      h("div", { class: "ocard__top" }, c.lead ? head(c.lead.race, c.lead.tier) : h("span", { class: "ocard__nohead" }), h("b", { class: "ocard__name" }, c.name)),
      h("p", { class: "ocard__cap muted" }, c.lead?.name ? h("span", { class: "ocard__who" }, `${c.lead.name}${c.size ? ` + ${c.size}` : ""}`) : null, c.lead?.name && c.line ? " · " : null, c.line),
      c.why ? h("small", { class: "ocard__why" }, c.why) : null,
      h("button", { class: "ork-btn ocard__add", type: "button", "aria-label": `${ROWS.add} ${c.name}`, onclick: () => { close(); if (c.open.proposal) core.newParty(`${PROPOSAL}${c.open.proposal}`); else core.newParty(c.open.preset); } }, ROWS.add)))];
  }

  function chipsOf() {
    const party = picked(), all = typesOf(party), guessed = line() && all.some((t) => t.id === own) ? own : "";
    const order = guessed ? [all.find((t) => t.id === guessed), ...all.filter((t) => t.id !== guessed)] : all, now = chosen();
    const label = `${nameOf(party)}'s kinds:`;
    kinds.setAttribute("aria-label", label);
    if (goalOf(party)?.ideation) { kinds.replaceChildren(h("small", { class: "muted" }, `${nameOf(party)} takes it as a pitch: no kind`)); return; }
    kinds.replaceChildren(h("span", { class: "okinds__label muted" }, label),
      ...order.slice(0, KINDS_SHOWN).map((t) => h("button", { class: `ork-btn okind${t.id === now ? " is-picked" : ""}`, type: "button", "data-type": t.id, "data-guessed": String(t.id === guessed), "aria-pressed": String(t.id === now), title: t.line || "",
        onclick: () => { mine = t.id === now ? "" : t.id; draw(); } }, sign(t.sign), h("span", {}, t.id === guessed ? `${t.name} · ${ROWS.guessed}` : t.name))),
      h("button", { class: "ork-btn quiet okinds__more", type: "button", "data-act": "more-kinds", onclick: () => { close(); core.newIdea("", PROJECT, { text: text.value, party: mineParty }); } }, ROWS.more));
  }

  function menuItems() {
    menu.replaceChildren(...parties.map((p) => h("button", { class: `orow__opt${p.party === picked() ? " is-on" : ""}`, type: "button", role: "option", "aria-selected": String(p.party === picked()), "data-party": p.party,
      onclick: () => { mineParty = p.party; mine = undefined; menuOn = false; draw(); refreshOwn().then(draw); forBtn.focus(); } }, h("b", {}, p.name), fitWords(p) ? h("small", { class: "muted" }, fitWords(p)) : null,
    p.party === picked() ? sign("check", "Picked") : null)));
  }

  function draw() {
    strip.replaceChildren(...cards());
    forBtn.replaceChildren(h("span", {}, `for ${nameOf(picked()) || "…"}`), h("i", { class: `ork-chev${menuOn ? " up" : ""}`, "aria-hidden": "true" }));
    forBtn.setAttribute("aria-expanded", String(menuOn));
    forBtn.disabled = !parties.length;
    menu.hidden = !menuOn;
    if (menuOn) menuItems();
    chipsOf();
    add.disabled = !line() || !picked() || busy;
  }

  /** The kind among the party picked's (the line's kind over every kind when the party offers it, else asked of the host for this party). */
  async function refreshOwn(n = ++seq) {
    const party = picked(), t = line();
    if (!t || !party) { own = ""; return; }
    if (!kind || typesOf(party).some((x) => x.id === kind)) { own = kind; return; }
    const got = await core.call("ideas.kind_for", { text: t, party }, () => {});
    if (n === seq) own = got?.type || "";
  }

  /** The line has rested: its kind, then the Orkmaster's party for that kind, then the kind among that party's. */
  async function guess() {
    const n = ++seq, t = line();
    if (t) {
      const got = await core.call("ideas.kind_for", { text: t }, () => {});
      if (n !== seq) return;
      kind = got?.type || "";
    } else kind = own = "";
    const got = await core.call("ideas.party_for", kind ? { type: kind } : {}, () => {});
    if (n !== seq) return;
    const fromMap = (st.map?.goals || []).filter((g) => g.slug !== "general" && !g.ops).map((g) => ({ party: g.slug, name: g.short || g.title, fits: g.ideation ? "pitch" : "", missing: [] }));
    parties = got && Array.isArray(got.parties) ? got.parties : fromMap;
    suggested = (got && got.suggested) || parties.find((p) => p.fits !== "pitch")?.party || parties[0]?.party || "";
    await refreshOwn(n);
    if (n === seq) draw();
  }

  text.addEventListener("input", () => { add.disabled = !line() || !picked() || busy; clearTimeout(timer); timer = setTimeout(guess, GUESS_MS); });
  text.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); send(); } });
  forBtn.addEventListener("click", () => { menuOn = !menuOn; draw(); });
  menu.addEventListener("keydown", (e) => { if (e.key === "Escape" && menuOn) { e.preventDefault(); e.stopPropagation(); menuOn = false; draw(); forBtn.focus(); } });
  add.addEventListener("click", () => send());

  /** *Add goal*: `ideas.add` as New goal sends it: the line, the party, its priority and the kind, if any (a pitch has none). */
  async function send() {
    const body = line(), party = picked();
    if (!body || !party || busy) return;
    const g = goalOf(party), track = (st.board?.tracks || []).find((t) => t.slug === party), pitch = Boolean(g?.ideation);
    const priority = pitch ? (track?.priority === "high" ? "high" : "normal") : track?.priority || "normal", type = pitch ? "" : chosen();
    busy = true;
    draw();
    const short = body.length > 40 ? `${body.slice(0, 40)}…` : body;
    const r = await act.deliver("ideas.add", { text: body, track: party, priority, ...(type ? { type } : {}) }, `the goal “${short}”`);
    busy = false;
    if (!r.ok || r.result?.error) { act.flash(r.error || r.result?.error); draw(); return; }
    text.value = "";
    mine = undefined;
    kind = own = "";
    act.flash(r.kept ? "No signal: the goal is kept and goes when the town answers." : `Added to ${nameOf(party)}: the Taskmaster drafts it now.`);
    if (priority === "low" && !pitch && !r.kept && core.nightUnset()) core.askNight();           // the first Low goal asks whether Low work may run at night (spec 83 §3)
    if (!r.kept) core.refresh();
    draw();
  }

  return {
    el,
    draw,
    reset() { text.value = ""; clearTimeout(timer); mineParty = ""; mine = undefined; kind = own = ""; menuOn = false; busy = false; },
    async load() {
      proposing = [];
      const asked = proposes(core) ? loadProposals(core) : null;
      await guess();
      if (asked) { proposing = (await asked)?.proposals || []; draw(); }
    },
  };
}

/** `core`: the board's frame; `act`: {openParty(slug), deliver, flash}. Returns {el, open(), draw(), isOpen()}. */
export function makeProject(core, act) {
  const st = core.st;
  const body = h("div", { class: "project" });
  const top = h("div", { class: "pj-top" });                  // the Orkmaster's head, then the rows, then the parties: the head and the rows are drawn once and stay
  const sh = sheet("The project", body);
  sh.el.classList.add("full", "project-sheet");
  const rows = makeRows(core, act, () => sh.close());       // the Orkmaster's two rows (spec 91 §8)
  const assets = makeAssets(core);            // the section *Assets* (spec 88 §7): drawn after the parties; its look is kept when the sheet is put away
  sh.el.addEventListener("close", () => assets.leave());
  const folded = new Set();                          // the folds opened: `<party>:waits`, `<party>:flags`

  /** A goal's row: its element, its type's sign and title, its state's words, its mark; a tap opens the goal's screen. */
  const row = (r) => h("button", { class: "pj-row", type: "button", "data-idea": r.slug, title: `${r.title} · ${r.line}`, onclick: () => { sh.close(); core.open(r.open, "map"); } },
    elem(r.element, { dim: r.raw }) || h("span", { class: "pj-row__none" }),
    h("span", { class: "pj-row__body" }, h("span", { class: "pj-row__title" }, r.type ? h("span", { class: `dk__type ${typeTone(r.element, r.raw)}`, "data-type": r.type.id }, sign(r.type.sign, r.type.name)) : null, r.title),
      h("span", { class: "pj-row__line" }, r.line)),
    r.mark ? h("span", { class: "dk__mark" }, sign(r.mark, r.markTip)) : null, h("i", { class: "ork-chev right", "aria-hidden": "true" }));
  const flagRow = (f) => row({ slug: f.slug, title: f.short, element: f.element, raw: false, type: null, line: flagTally(f), mark: "flag", markTip: "flag", open: { kind: "idea", slug: f.slug } });

  /** A fold shut by default: a 44 px button, its count, then its rows. */
  function fold(c, key, words, rows, count = true) {
    if (!rows.length) return null;
    const id = `${c.slug}:${key}`, on = folded.has(id);
    return h("div", { class: `pj-fold${on ? " is-open" : ""}`, "data-fold": key },
      h("button", { class: "pj-fold__head", type: "button", "aria-expanded": String(on), onclick: () => { if (on) folded.delete(id); else folded.add(id); draw(); } },
        h("span", {}, words), count ? h("small", { class: "muted" }, String(rows.length)) : null, h("i", { class: `ork-chev${on ? " up" : ""}`, "aria-hidden": "true" })),
      on ? h("div", { class: "pj-rows" }, ...rows) : null);
  }

  /** A party's section: its leader's head, name and *k/n*, **Open <party>**, then its goals. */
  function section(c) {
    const m = modelOf(st, c.slug);
    const list = m ? goalsOf(st, m) : { atWork: [], planning: [], waits: [], flags: [] };
    const g = (st.map?.goals || []).find((x) => x.slug === c.slug);
    const empty = !list.atWork.length && !list.planning.length && !list.waits.length && !list.flags.length;
    const group = (words, rows) => (rows.length ? [h("h4", { class: "pj-group" }, words), h("div", { class: "pj-rows" }, ...rows.map(row))] : []);
    return h("section", { class: "pj-party", "data-goal": c.slug, "aria-label": c.title },
      h("div", { class: "pj-party__head" },
        c.head ? whoHead(c.head, false) : h("span", { class: "where-row__head" }),
        h("span", { class: "pj-party__name", title: c.title }, h("b", {}, c.short), h("small", { class: "muted" }, g?.ideation ? `${g.ideas ?? 0}` : `${g?.done ?? 0}/${g?.ideas ?? 0}`)),
        h("button", { class: "ork-btn quiet pj-party__open", type: "button", "data-act": "open-party", "aria-label": `Open ${c.short}`, onclick: () => { sh.close(); act.openParty(c.slug); } }, `Open ${c.short}`)),
      empty ? h("p", { class: "cap pj-empty" }, `Nothing in ${c.short} yet`) : null,
      ...group("Planning", list.planning), ...group("At work", list.atWork),
      fold(c, "waits", "Waits for main", list.waits.map(row)),
      fold(c, "flags", `Flags (${list.flags.length})`, list.flags.map(flagRow), false));
  }

  function draw() {
    const project = projectOf(core);
    if (!project) { body.replaceChildren(); return; }
    const o = project.orkmaster || { race: "peon", tier: "crown", name: "Orkmaster" };
    const parties = chipsOf(st).filter((c) => c.slug !== "general" && !c.ops);
    rows.draw();
    top.replaceChildren(head(o.race, o.tier, { title: "Orkmaster" }), h("span", { class: "pj-top__name" }, h("b", {}, "Orkmaster"), h("small", { class: "muted" }, "The parties, their goals")));
    if (body.firstChild !== top || top.nextSibling !== rows.el) body.replaceChildren(top, rows.el);
    while (rows.el.nextSibling) rows.el.nextSibling.remove();                           // the rows stay where they are while the Board is drawn again: the line being typed keeps its focus
    body.append(...[...parties.map(section), parties.length ? null : h("p", { class: "muted" }, "No parties yet."), assets.el].filter(Boolean));
  }

  return {
    el: sh.el,
    isOpen: () => sh.el.open,
    open() { rows.reset(); draw(); sh.open(); if (projectOf(core)) { assets.load(); rows.load(); } },
    /** The sheet drawn again with the Board while it is open. */
    draw() { if (sh.el.open) draw(); },
  };
}

/** **Its party** in New goal from the project (shell-ideas.js): the parties as `ideas.party_for` answers them, the suggested one picked, a line *Orkmaster suggests Website · takes it whole*, the others as chips
 *  with their fit; without a type *Any party*. `pick(slug)` is told the party picked (and the suggestion, at first). Returns {el, ask(type), reset()}. */
export function makeItsParty(core, pick) {
  let list = [], suggested = "", picked = "", type = "", seq = 0, first = "";
  const line = h("p", { class: "itsparty__line", role: "status" });
  const chips = h("div", { class: "itsparty__chips", role: "radiogroup", "aria-label": "Its party" });
  const el = h("div", { class: "field itsparty", hidden: true }, h("span", { class: "field-label" }, "Its party"), line, chips);
  const nameOf = (slug) => list.find((p) => p.party === slug)?.name || slug;
  function draw() {
    const sug = list.find((p) => p.party === suggested);
    line.replaceChildren(...(type && sug ? [h("b", {}, `Orkmaster suggests ${sug.name}`), fitWords(sug) ? ` · ${fitWords(sug)}` : ""] : [h("b", {}, "Any party")]));
    chips.replaceChildren(...list.map((p) => h("button", { class: "itsparty__chip", type: "button", role: "radio", "aria-checked": String(p.party === picked), "data-goal": p.party, "data-fits": p.fits || "",
      onclick: () => { if (p.party === picked) return; picked = p.party; draw(); pick(picked); } },
    h("b", {}, p.name), fitWords(p) ? h("small", { class: "muted" }, fitWords(p)) : null, p.party === picked ? sign("check", "Picked") : null)));
  }
  return {
    el,
    nameOf,
    picked: () => picked,
    /** The party the person picked in the project's *New goal* row (spec 91 §8): picked at first, until another is ("" none: the Orkmaster's suggestion). */
    want(slug = "") { first = slug; },
    /** Asks the host for the parties of a goal of this type ("" none) and picks the one it suggests. */
    async ask(t = "") {
      const n = ++seq;
      type = t;
      const got = await core.call("ideas.party_for", t ? { type: t } : {});
      if (n !== seq || !got) return;
      list = got.parties || [];
      suggested = got.suggested || list[0]?.party || "";
      picked = list.some((p) => p.party === first) ? first : suggested;
      draw();
      if (picked) pick(picked);
    },
  };
}
