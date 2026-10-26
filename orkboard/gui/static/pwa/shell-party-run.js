// What New party adds on the phone for the project's running and for Team (docs/specs/92-running-and-the-team.md §2, §3, decisions §108); the desktop's twin is js/shell/partyrun.js. Under the team of a running
// party (LiveOps, Run, Upkeep) the **recurring goals** it proposes: each a 44 px tick box with how often it comes back (`routines` of the preset's row: `{id, title, every, words}`), all ticked, the person
// leaves out the ones they do not want. For the **Team** preset, which has no seats, a note in place of the team: what Team holds, and that it is one party, in one project. Save sends `routines`: the ids kept.
import { h } from "./util.js";

/** The recurring goals of the pressed preset. Returns {el, set(row), kept()}: `set` draws the row's (none: nothing), all ticked again each time another preset is pressed. */
export function makeRoutines() {
  const el = h("section", { class: "routines", "aria-label": "Recurring goals", hidden: true });
  let rowId = "", out = [], rows = [], last = "";
  const draw = () => {
    el.hidden = !rows.length;
    el.replaceChildren(...(rows.length ? [h("h4", {}, "Recurring goals it proposes"),
      h("p", { class: "muted cap" }, "Made with the party and drafted at once; each comes back when it is done and its time has passed. Leave out the ones you do not want."),
      ...rows.map((r) => {
        const box = h("input", { type: "checkbox", "data-routine": r.id, "aria-label": `${r.title}, ${r.words}`, ...(out.includes(r.id) ? {} : { checked: true }) });
        box.addEventListener("change", () => { out = box.checked ? out.filter((x) => x !== r.id) : [...out, r.id]; draw(); });
        return h("label", { class: `routine${out.includes(r.id) ? "" : " is-on"}` }, box, h("span", { class: "routine__text" }, h("b", {}, r.title), h("small", { class: "muted" }, r.words)));
      })] : []));
  };
  return {
    el,
    set(row) {
      const id = row?.id || "", next = row && !row.ops ? row.routines || [] : [], sig = `${id}|${next.map((r) => r.id).join(",")}`;
      if (sig === last) return;                              // the same preset: what the person ticked stays, and typing a name never redraws the boxes
      if (id !== rowId) { rowId = id; out = []; }
      last = sig;
      rows = next;
      draw();
    },
    kept: () => rows.map((r) => r.id).filter((id) => !out.includes(id)),
  };
}

/** What Team is, in place of a team to seat. */
export const teamNote = () => h("section", { class: "teamnote", "aria-label": "About Team", hidden: true },
  h("p", {}, "Team holds your Operations: the daily brief, 1:1s, the retro, mail and Jira."),
  h("p", { class: "muted" }, "They stay yours, in your own folder, the same in every project; Team only shows them here. There is one Team party, in one project: this one. Until it is made, Operations are in the parties' list."));
