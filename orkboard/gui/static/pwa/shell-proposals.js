// The Orkmaster's proposals on the phone (docs/specs/75-parties-fitted-to-the-project.md §4, §5; decisions §90): New party opens on **what the Orkmaster proposes for this project** — its head, *Orkmaster proposes*,
// *for this project* and what the project is (its kind's words and the signs it saw, muted) — and a card for each proposal: its name, its line, its why and **a three-way switch Lean · Standard · Full** (Standard
// picked; a radiogroup of orkUI's buttons), under it for the size picked the heads, *one agent* / *n agents* and *≈$a–b a goal*, and **Make it**. A proposal the project has is muted, *You have one*. An empty folder
// (`ask`) is asked one line, *What is this project for?*, and **Read it** draws the proposals of what the line says. Under the cards, **More: the library** opens today's tiles and seats (shell-goal-new.js).
// A host without `ideas.proposals` (its Map's `project` says no `kind`) keeps today's phone: `proposes(core)` is false and nothing here is drawn.
// Pure words here too: `priceWords`, `agentsWords`; `sizeSwitch` is the same switch in a party's *Its size* (shell-party.js, shell-goal.js) and in the library's seats.
import { h, head } from "./util.js";
import { field } from "./shell-forms.js";
import { pctRange } from "./shell-spend.js";

export const SIZES = [["lean", "Lean"], ["standard", "Standard"], ["full", "Full"]];
export const STANDARD = "standard";
export const PROPOSAL = "proposal:";                        // `core.newParty("proposal:<id>")`: New party opens on that proposal
const ABOUT_CHARS = 300;                                      // the empty folder's line (spec 75 §4.2)

/** Whether the host proposes: `ideas.map`'s `project` says what the project is (spec 75 §4.3). */
export const proposes = (core) => Boolean(core.st.map?.project?.kind);

/** *one agent* · *4 agents*. */
export const agentsWords = (n) => (n === 1 ? "one agent" : `${n} agents`);

/** *≈$0.40–1.20* (below $1, in cents) or, on the subscription, *≈3–8 % of 5h*; "" with no price. */
export function rangeWords(price) {
  if (!price || !Number.isFinite(Number(price.low)) || !Number.isFinite(Number(price.high))) return "";
  const { low, high } = price, pct = pctRange(low, high);
  if (pct) return `≈${pct}`;
  if (low < 1) return `≈$${low.toFixed(2)}–${high.toFixed(2)}`;
  const a = Math.round(low), b = Math.round(high);
  return a === b ? `≈$${a}` : `≈$${a}–${b}`;
}

/** *≈$0.40–1.20 a goal*. */
export function priceWords(price) {
  const range = rangeWords(price);
  return range ? `${range} a ${price.pitch ? "pitch" : "goal"}` : "";
}

/** The proposals as the host last said them (`core.st.proposed`); the party's sheets match a party to one by its leader. */
export const proposed = (core) => core.st.proposed?.proposals || [];

/** Asks `ideas.proposals` (no line) and keeps the answer; null (nothing said) when the host cannot. */
export async function loadProposals(core) {
  const got = await core.call("ideas.proposals", {}, () => {});
  if (!got || !Array.isArray(got.proposals)) return null;
  core.st.proposed = got;
  return got;
}

/** The proposal a party of this leader was made from, if one has the leader at its sizes: the prices of its three sizes. */
export const proposalOfLeader = (core, leader) => proposed(core).find((p) => Object.values(p.sizes || {}).some((s) => s.leader === leader)) || null;

/** The prices of a party's three sizes where the host's proposals know its leader: {lean: "≈$0.40–1.20", …}; empty for a party of one's own. */
export function sizePrices(core, leader) {
  const p = proposalOfLeader(core, leader);
  return Object.fromEntries(SIZES.map(([id]) => [id, rangeWords(p?.sizes?.[id]?.price)]).filter(([, words]) => words));
}

/** Lean · Standard · Full as a radiogroup of orkUI's buttons (arrows move the pick). `prices`: {size: words} under each word. Returns {el, set(size), get(), prices(map)}. */
export function sizeSwitch({ label = "Its size", onPick = null } = {}) {
  let now = "";
  const buttons = SIZES.map(([id, word]) => h("button", { class: "ork-btn size-pick", type: "button", role: "radio", "aria-checked": "false", tabindex: "-1", "data-size": id,
    onclick: () => { if (id === now) return; set(id); onPick?.(id); } }, h("span", { class: "size-pick__word" }, word)));
  const el = h("div", { class: "size-switch", role: "radiogroup", "aria-label": label }, ...buttons);
  function set(id) {
    now = id;
    buttons.forEach((b) => { const on = b.dataset.size === id; b.setAttribute("aria-checked", String(on)); b.tabIndex = on || (!id && b === buttons[0]) ? 0 : -1; });
  }
  el.addEventListener("keydown", (e) => {
    const step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (!step) return;
    e.preventDefault();
    const at = Math.max(0, SIZES.findIndex(([id]) => id === now)), next = SIZES[(at + step + SIZES.length) % SIZES.length][0];
    set(next);
    buttons.find((b) => b.dataset.size === next).focus();
    onPick?.(next);
  });
  set("");
  return {
    el,
    set,
    get: () => now,
    /** A line of words under each size's word ({lean: "≈$0.40–1.20", …}); none for a size with none. */
    prices(map = {}) {
      buttons.forEach((b) => {
        b.querySelector(".size-pick__price")?.remove();
        if (map[b.dataset.size]) b.append(h("small", { class: "size-pick__price" }, map[b.dataset.size]));
        b.classList.toggle("has-price", Boolean(map[b.dataset.size]));
      });
    },
  };
}

/** `core`: the board's frame; `act`: {make(proposal, size, card, button), library()}. Returns {el, load(pickedId) → Promise<boolean>, line(), about}: `load` asks the host and draws; false when it cannot. */
export function makeProposals(core, act) {
  const el = h("div", { class: "props" });
  const size = new Map();                                     // proposal id → the size picked on its card (Standard at first)
  let data = null, line = "", reading = false, note = "", pickedId = "", scrolled = false, hold = null;   // `hold`: the "What it is for" field, put under the Orkmaster's head

  const orkmaster = () => core.st.map?.project?.orkmaster || { race: "peon", tier: "crown" };

  function top() {
    const kind = data.kind || core.st.map?.project?.kind || {};
    const o = orkmaster();
    return h("div", { class: "props__top" }, head(o.race || "peon", o.tier || "crown"),
      h("div", { class: "props__who" }, h("b", {}, "Orkmaster proposes"),
        h("small", { class: "muted props__for" }, ["for this project", kind.words].filter(Boolean).join(" · ")),
        (kind.signs || []).length ? h("small", { class: "muted props__signs" }, kind.signs.join(" · ")) : null));
  }

  /** *What is this project for?* and **Read it**: an empty folder is asked one line (the host reads it with a cheap model; the line is kept by no one). */
  function ask() {
    const input = h("input", { class: "ork-field", type: "text", "aria-label": "What is this project for?", maxlength: String(ABOUT_CHARS) });
    input.value = line;
    const read = h("button", { class: "ork-btn primary", type: "button", "data-act": "read-it", disabled: reading || !line.trim() }, reading ? "Reading…" : "Read it");
    input.addEventListener("input", () => { line = input.value; read.disabled = reading || !line.trim(); });
    input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !read.disabled) { e.preventDefault(); read.click(); } });
    read.addEventListener("click", async () => {
      const text = line.trim();
      if (!text || reading) return;
      reading = true; read.disabled = true; read.textContent = "Reading…";
      const got = await core.call("ideas.proposals", { about: text.slice(0, ABOUT_CHARS) });
      reading = false;
      if (got && Array.isArray(got.proposals)) { data = got; note = got.read === false ? "It could not read your line: these are the proposals for code." : ""; scrolled = false; }
      draw();
    });
    return h("div", { class: "props__ask", "data-sec": "ask" }, field("What is this project for?", input, "a line is enough: a mobile app for…, our team's wiki, my design files"), read);
  }

  /** A proposal's card: name, line, why, the switch, and for the size picked its heads, its agents and its price a goal; **Make it**. */
  function card(p) {
    const detail = h("div", { class: "prop__detail", "aria-live": "polite" });
    const make = h("button", { class: "ork-btn primary big", type: "button", "data-act": "make-it", "aria-label": `Make it: ${p.name}` }, "Make it");
    const heads = h("span", { class: "prop__heads" });
    const switchEl = sizeSwitch({ label: `Its size: ${p.name}`, onPick: (id) => { size.set(p.id, id); paint(); } });
    switchEl.prices(Object.fromEntries(SIZES.map(([id]) => [id, ""])));
    const have = Boolean(p.have);
    const paint = () => {
      const id = size.get(p.id) || STANDARD, s = p.sizes?.[id];
      switchEl.set(id);
      make.disabled = !s;
      if (!s) { detail.replaceChildren(); heads.replaceChildren(); return; }
      heads.replaceChildren(...(s.heads || []).map((x) => head(x.race || "peon", x.tier || "warrior")));
      detail.replaceChildren(...[heads, h("span", { class: "prop__agents" }, agentsWords(s.agents ?? (1 + (s.team || []).length))),
        s.price ? h("span", { class: "prop__price" }, priceWords(s.price)) : null].filter(Boolean));
    };
    make.addEventListener("click", () => act.make(p, size.get(p.id) || STANDARD, art, make));
    const art = h("article", { class: `prop${have ? " is-have" : ""}${pickedId === p.id ? " is-picked" : ""}`, "data-proposal": p.id, "aria-label": p.name },
      h("div", { class: "prop__text" }, h("b", { class: "prop__name" }, p.name), p.line ? h("small", { class: "muted prop__line" }, p.line) : null,
        have ? h("small", { class: "prop__why" }, "You have one") : p.why ? h("small", { class: "prop__why" }, p.why) : null),
      switchEl.el, detail, make);
    paint();
    return art;
  }

  function draw() {
    if (!data) { el.replaceChildren(h("p", { class: "muted props__wait" }, "Reading…")); return; }
    const cards = (data.proposals || []).map(card);
    const library = h("button", { class: "ork-btn props__library", type: "button", "data-act": "more-library", onclick: () => act.library() }, "More: the library", h("i", { class: "ork-chev right", "aria-hidden": "true" }));
    el.replaceChildren(...[top(), data.ask || line.trim() ? ask() : null, note ? h("p", { class: "muted props__note", role: "status" }, note) : null,
      hold, h("div", { class: "props__cards" }, ...cards), library].filter(Boolean));
    const at = cards.find((c) => c.dataset.proposal === pickedId);
    if (at && !scrolled) { scrolled = true; requestAnimationFrame(() => at.scrollIntoView({ block: "start" })); }
  }

  return {
    el,
    /** The field *What it is for* the cards' **Make it** reads, drawn under the Orkmaster's head (the sheet owns it: it goes with the person to the library). */
    hold(node) { hold = node; if (data) draw(); },
    /** The line the person gave an empty folder lives on this page only. */
    forget() { line = ""; note = ""; },
    /** Asks the host, draws; `id`: a proposal to scroll to (the deal's press). False when the host cannot (the library is then New party). */
    async load(id = "") {
      data = null; pickedId = id; scrolled = false; size.clear(); note = "";
      draw();
      const got = await loadProposals(core);
      if (!got) return false;
      data = got;
      draw();
      return true;
    },
  };
}

/** The deal's tile for a proposal (shell-project.js): its Standard heads small, its name, its line, its Standard price a goal and its why. */
export function proposalTile(p, press) {
  const s = p.sizes?.[STANDARD] || Object.values(p.sizes || {})[0];
  const heads = (s?.heads || []).map((x) => head(x.race || "peon", x.tier || "warrior", { small: true }));
  const price = s?.price ? priceWords(s.price) : "";
  return h("button", { class: `pj-tile${p.have ? " is-have" : ""}`, type: "button", "data-proposal": p.id, "data-why": p.have ? "have" : "proposal", onclick: press },
    h("span", { class: "pj-tile__heads" }, ...heads), h("b", {}, p.name), p.line ? h("small", { class: "muted" }, p.line) : null,
    price ? h("small", { class: "pj-tile__price" }, price) : null,
    p.have ? h("small", { class: "pj-tile__why muted" }, "You have one") : p.why ? h("small", { class: "pj-tile__why" }, p.why) : null);
}
