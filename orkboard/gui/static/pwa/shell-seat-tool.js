// A seat's AI tool on the phone (docs/specs/91-the-owners-list.md §6, §7, decisions §107.4): a sheet that opens from a seat's button. Its first row is *The party's tool (<name>)*; then the group **Can do
// what <role> needs** (the ready tools whose `makes` covers the role's `needs`; all the ready ones for a role that needs nothing) and **Cannot make pictures** / **Cannot make sound** (or **Cannot run yet**),
// each tool with its mark, its name, what it makes and which model its tier runs, *experimental* in the alert colour, and the reason it cannot in words (*draws no pictures*, *not installed*, *not signed
// in*). A tool that cannot do the need may still be picked — the person decides; only a tool that is not installed is shown and not taken. No tool makes sound today: the first group then says so
// plainly, and every tool is listed under *Cannot make sound*, pickable. The phone opens nothing on the computer: a tool not signed in, picked, stays picked and says so on the seat. Rows are 44 px.
import { h, sheet } from "./util.js";
import { mark } from "./shell-who.js";
import { toolCaption, toolGroups } from "./shell-party-model.js";
import { toolRow } from "./shell-party-tool.js";

const MARKED = ["claude", "codex", "agy", "cursor", "hermes", "pi"];

/** A tool's mark (orkUI's marks/), null for a tool it draws none for. */
export const toolMark = (id) => (MARKED.includes(id) ? mark(`harness-${id}`) : null);

/** `core`: the board's frame. Returns {el, open({role, tier, value, partyTool, onPick(id)})}: `value` the seat's tool ("" the party's), `partyTool` the party's ("" the Main tool). */
export function makeSeatTool(core) {
  const body = h("div", { class: "seat-tools" });
  const sh = sheet("Its AI tool", body);
  function row(t, value, pick) {
    const off = !t.installed && value !== t.id;
    return h("button", { class: `tool-row${off ? " is-off" : ""}`, type: "button", "data-tool": t.id, "aria-pressed": String(value === t.id), disabled: off || null, onclick: () => pick(t.id) },
      toolMark(t.id), h("span", { class: "tool-row__text" }, h("b", {}, t.name, t.experimental ? h("span", { class: "tool-row__alert", "data-experimental": "" }, " experimental") : null),
        h("small", { class: "muted" }, t.caption, t.reason ? [" · ", h("span", { class: "tool-row__why", "data-why": "" }, t.reason)] : null)));
  }
  return {
    el: sh.el,
    open({ role, tier, value = "", partyTool = "", onPick }) {
      const tools = core.st.tools, party = toolRow(core, partyTool), groups = toolGroups(tools, role), said = (t) => ({ ...t, caption: toolCaption(t, tier) });
      const pick = (id) => { sh.close(); onPick(id); };
      sh.title(`Its AI tool for ${role?.name}`);
      body.replaceChildren(...[
        h("button", { class: "tool-row", type: "button", "data-tool": "", "aria-pressed": String(!value), onclick: () => pick("") }, toolMark(party?.id), h("span", { class: "tool-row__text" }, h("b", {}, `The party's tool (${party?.name || "Claude Code"})`))),
        h("section", { class: "tool-group", "aria-label": groups.canTitle, "data-group": "can" }, h("h4", {}, groups.canTitle),
          groups.none ? h("p", { class: "muted", "data-none": "" }, groups.none) : null, ...groups.can.map((t) => row(said(t), value, pick))),
        groups.cannot.length ? h("section", { class: "tool-group", "aria-label": groups.cannotTitle, "data-group": "cannot" }, h("h4", {}, groups.cannotTitle), ...groups.cannot.map((t) => row(said(t), value, pick))) : null,
        h("p", { class: "muted tool-foot" }, "The tier comes from the party's size. Each tool runs its own model for it.")].filter(Boolean));
      sh.open();
    },
  };
}
