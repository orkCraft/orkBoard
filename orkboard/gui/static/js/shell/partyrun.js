// What New party adds for the project's running (docs/specs/92-running-and-the-team.md §2, decisions §108): under the team of a running party (LiveOps, Run, Upkeep) the **recurring
// goals** it proposes — each a tick box with how often it comes back (`routines` of the preset's row: `{id, title, every, words}`), all ticked, the person leaves out the ones they do not want. Save sends `routines`: the ids kept (ideas.goal_save).
import { useRef, useState } from "preact/hooks";
import { html } from "../html.js";

/** The recurring goals kept for the pressed preset: all of them to start with, again each time another preset is pressed (what is left out is remembered for the one preset only, in a ref that
 *  the render resets, so the ticks never flash unticked). Returns `{rows, kept, toggle}`; none for a party that is edited. */
export function useRoutines(row, edit) {
  const rows = !edit && row ? row.routines || [] : [], id = row?.id || "";
  const mine = useRef({ id: "", out: [] }), [, again] = useState(0);
  if (mine.current.id !== id) mine.current = { id, out: [] };
  const out = mine.current.out;
  const toggle = (rid) => { mine.current = { id, out: out.includes(rid) ? out.filter((x) => x !== rid) : [...out, rid] }; again((n) => n + 1); };
  return { rows, kept: rows.map((r) => r.id).filter((rid) => !out.includes(rid)), toggle };
}

/** The recurring goals a running party proposes, to keep or leave out. */
export function Routines({ r }) {
  if (!r.rows.length) return null;
  return html`<section class="shell-routines" aria-label="Recurring goals">
    <h3 class="ok-font-label">Recurring goals it proposes</h3>
    <small class="ok-tone-muted">Made with the party and drafted at once; each comes back when it is done and its time has passed. Leave out the ones you do not want.</small>
    <ul class="shell-routines__list">${r.rows.map((x) => html`<li key=${x.id}><label class=${`shell-routine${r.kept.includes(x.id) ? " is-on" : ""}`}>
      <input type="checkbox" data-routine=${x.id} checked=${r.kept.includes(x.id)} onChange=${() => r.toggle(x.id)} aria-label=${`${x.title}, ${x.words}`} />
      <span class="shell-routine__text"><b>${x.title}</b><small class="ok-tone-muted">${x.words}</small></span></label></li>`)}</ul></section>`;
}
