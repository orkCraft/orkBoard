// New party (docs/specs/91-the-owners-list.md §7, decisions §107.5; docs/specs/50-parties-and-goals.md §3.7): one place over the pane in two halves. **Left**, presets to start from — *By stage of the project* (Ideation,
// Concept, Build, Release, LiveOps, fitted to what the project is), *By craft* (Tech, Design, Data, Marketing, Product, Art and sound) and *Your own party* (the Taskmaster alone), and the person's saved parties.
// **Right**, the name and *What it is for*, the size (Lean · Standard · Full: the seats and their tiers change at once) with the party's AI tool, and the team by seats in the bands *Leads*, *Does*, *Checks*, each
// seat with its own AI tool and a dashed free seat that opens a short list of roles (partyform.js, partyseats.js, seattool.js); then what the party costs a goal, its checks and its priority. No metrics, no
// deadline, no links: a party has no end. *Save party* sends `ideas.goal_save` with `title`, `about`, `leader`, `team`, `every`, `size`, the party's `tool`, `tools` (the seats whose tool is not the party's), `priority`,
// `party` (a party of the person's that was picked), `proposal` and `preset` (the recipe or the library's party the seats still are). A task goes to the one of the party who does its kind of work; a checker's
// check adds its line to a goal's Done when and its task to the plan (realm/idea_checks.py). Once the party is saved, its tab opens. Edit the party (goaldialog.js) is the same dialog on a party that is there.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { say } from "../link.js";
import { act, roles } from "./store.js";
import { Place, closePlace } from "../frame/place.js";
import { savedParty } from "./proposals.js";
import { PartyBody, footLine, usePartyForm } from "./partyform.js";
import { agentOf } from "./party.js";

export { FOR_HINT } from "./partyform.js";

export function GoalWizard({ preset: first = "", proposal = "" }) {
  const f = usePartyForm({ first, proposal });
  const { d, api } = f;
  const [saving, setSaving] = useState(false);
  const ready = f.ready && !saving;
  const save = async (e) => {
    e?.preventDefault();
    if (!ready) return;
    setSaving(true);
    const tools = f.seatTools();
    const library = !d.partyId && d.lit && (roles.value?.presets || []).some((x) => x.id === d.lit);
    const got = await act("ideas.goal_save", { ...(f.title.trim() || (!f.about.trim() && f.suggest) ? { title: f.title.trim() || f.suggest } : {}), about: f.about.trim(), leader: d.leader, team: d.team, every: d.every.filter((id) => d.team.includes(id)), priority: f.priority,
      ...(d.partyId ? { party: d.partyId } : {}), ...(library ? { preset: d.lit } : {}), ...(f.routines.kept.length ? { routines: f.routines.kept } : {}), ...(f.sized && !d.partyId && d.lit && d.row?.recipe ? { proposal: d.row.recipe } : {}),
      ...(f.rf.value() ? { releases_from: f.rf.value() } : {}), ...(f.sized && d.size ? { size: d.size } : {}), ...(f.sized && d.tool ? { tool: d.tool } : {}), ...(f.sized && Object.keys(tools).length ? { tools } : {}) });
    setSaving(false);
    if (got?.slug) savedParty(got);
  };
  return html`<${Place} title="New party"
    foot=${html`<span class="shell-p91__foot ok-font-status ok-tone-muted" data-foot="agents">${footLine(f)}</span>
      <button type="button" class="ork-btn" onClick=${closePlace}>Cancel</button>
      <button type="submit" form="goal-form" class="ork-btn primary" disabled=${!ready}>Save party</button>`}>
    <form id="goal-form" class="shell-form" onSubmit=${save}>
      <${PartyBody} f=${f} say=${say(`${agentOf(d.leader)?.name || "The Taskmaster"} reads the repository and writes the summary.`)} />
    </form>
  <//>`;
}
