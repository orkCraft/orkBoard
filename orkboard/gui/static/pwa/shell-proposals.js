// The Orkmaster's proposals on the phone (docs/specs/75-parties-fitted-to-the-project.md §4, §5; decisions §90; docs/specs/91-the-owners-list.md §7, §8): the words and the host's asking. The Orkmaster's *Parties* row
// (shell-project.js) shows the proposals first and New party (shell-party-new.js) opens on one (`core.newParty("proposal:<id>")`, a stage of the project, seats and all); a Lean · Standard · Full switch (`sizeSwitch`) is in
// that sheet and in a party's *Its size* (shell-party.js, shell-goal.js). A host without `ideas.proposals` (its Map's `project` says no `kind`) keeps today's phone: `proposes(core)` is false.
// Pure words here too: `priceWords`, `agentsWords`.
import { h } from "./util.js";
import { pctRange } from "./shell-spend.js";

export const SIZES = [["lean", "Lean"], ["standard", "Standard"], ["full", "Full"]];
export const STANDARD = "standard";
export const PROPOSAL = "proposal:";                        // `core.newParty("proposal:<id>")`: New party opens on that proposal

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
