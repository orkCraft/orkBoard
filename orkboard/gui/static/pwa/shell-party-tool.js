// A party's AI tool and who a size lets in and out, on the phone (docs/specs/81-a-party-its-tool-and-size.md §4, decisions §98).
// **Its AI tool**: the phone's own select (a native `<select>` as orkUI styles it), *Main tool (Claude Code)* picked first, then the tools in groups — **Ready**, **Not signed in**,
// **Not installed** (shown, never picked: disabled) — as `ideas.tools` gives them (the host reads what Settings' tool rows read and runs nothing). A tool with no tiers says it *runs its own model*.
// The phone opens nothing on the computer: a tool not signed in, picked, stays picked and says that its sign-in is the computer's to open and that the party's work waits for it.
// **Moves** (`sizeMoves`): under a party's size switch, before the press, the heads that join and leave for each other size (*Lean · Leaves: Grunt, Tester*; `ideas.party_sizes`).
// A host without `ideas.tools` has no list: `loadTools` gives null and the field stays hidden.
import { h, head } from "./util.js";
import { SIZES } from "./shell-proposals.js";

/** The three groups, as the host sorts them: [id, word, whether a tool is in it]. */
export const TOOL_GROUPS = [["ready", "Ready", (t) => t.ready], ["signed", "Not signed in", (t) => t.installed && !t.signed_in], ["missing", "Not installed", (t) => !t.installed]];

/** Asks `ideas.tools` and keeps the answer (`core.st.tools`); null (nothing said) when the host cannot. */
export async function loadTools(core) {
  const got = await core.call("ideas.tools", {}, () => {});
  if (!got || !Array.isArray(got.tools)) return null;
  core.st.tools = got;
  return got;
}

/** The row of a tool (the Main tool's for "" or none); undefined when the list is not known. */
export const toolRow = (core, id = "") => core.st.tools?.tools?.find((t) => t.id === (id || core.st.tools.main));

/** Whether the tool a party would run on has no tiers of its own: it runs its own model, and a size's price does not apply. */
export const runsOwn = (core, id = "") => toolRow(core, id)?.tiers === false;

const word = (t) => `${t.name}${t.tiers ? "" : " · runs its own model"}`;

/** **Its AI tool** as a field: `{el, set(id), get(), draw()}`. Hidden until the host's list is known; `draw()` after `loadTools`. `onPick(id)`: the pick. */
export function toolPick(core, { label = "Its AI tool", onPick = null } = {}) {
  let value = "";
  const select = h("select", { class: "ork-field", "aria-label": label, "data-act": "tool" });
  const hint = h("small", { class: "muted tool-hint", "aria-live": "polite" });
  const el = h("div", { class: "field tool-field", hidden: true, "data-sec": "tool" }, h("span", { class: "field-label" }, label), select, hint);
  function draw() {
    const tools = core.st.tools;
    el.hidden = !tools;
    if (!tools) return;
    const main = toolRow(core, "");
    select.replaceChildren(h("option", { value: "" }, `Main tool (${main?.name || "Claude Code"})${main && !main.tiers ? " · runs its own model" : ""}`),
      ...TOOL_GROUPS.map(([id, name, has]) => {
        const rows = tools.tools.filter(has);
        return rows.length ? h("optgroup", { label: name, "data-group": id },
          ...rows.map((t) => h("option", { value: t.id, ...(t.id === value ? { selected: true } : {}), ...(id === "missing" && t.id !== value ? { disabled: true } : {}) }, word(t)))) : null;
      }));
    select.value = value;
    const row = value ? tools.tools.find((t) => t.id === value) : null;
    hint.textContent = row && row.installed && !row.signed_in ? "Not signed in: sign in on the computer. The party's work waits for it." : "";
  }
  select.addEventListener("change", () => { value = select.value; draw(); onPick?.(value); });
  return { el, set(id) { value = id || ""; draw(); }, get: () => value, draw };
}

const names = (rows) => rows.map((a) => a.name).join(", ");

/** The heads that join or leave if a size is picked (`ideas.party_sizes`), for each size but the one the party has: `{el, load(slug, size)}`. Nothing for a size that changes no one;
 *  an older host (no such command) draws nothing. The answer is kept per party and size (`core.st.moves`). */
export function sizeMoves(core) {
  const el = h("ul", { class: "size-moves", "aria-label": "Who joins and leaves", hidden: true });
  function paint(rows, size) {
    const lines = SIZES.filter(([id]) => id !== size && (rows?.[id]?.joins?.length || rows?.[id]?.leaves?.length)).map(([id, name]) => h("li", { "data-size-move": id },
      h("b", {}, name),
      ...[["joins", "Joins"], ["leaves", "Leaves"]].filter(([k]) => rows[id][k].length).map(([k, label]) => h("span", { class: "size-move", "data-move": k },
        `${label}: `, h("span", { class: "size-move__heads" }, ...rows[id][k].map((a) => a.head && head(a.head.race, a.head.tier, { small: true, title: a.name }))), ` ${names(rows[id][k])}`))));
    el.replaceChildren(...lines);
    el.hidden = !lines.length;
  }
  return {
    el,
    async load(slug, size, sig = "") {
      core.st.moves = core.st.moves || {};
      const key = `${slug}|${size}|${sig}`;
      if (core.st.moves[key]) { paint(core.st.moves[key], size); return; }
      const got = await core.call("ideas.party_sizes", { slug }, () => {});
      if (!got?.sizes) return;
      core.st.moves[key] = got.sizes;
      paint(got.sizes, size);
    },
  };
}
