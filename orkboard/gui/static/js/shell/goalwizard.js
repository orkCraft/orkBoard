// New party (docs/specs/91-the-owners-list.md §7, decisions §107.5; docs/specs/50-parties-and-goals.md §3.7): one dialog in two halves. **Left**, presets to start from — *By stage of the project* (Ideation,
// Concept, Build, Release, LiveOps, fitted to what the project is), *By craft* (Tech, Design, Data, Marketing, Product, Art and sound) and *Your own party* (the Taskmaster alone), and the person's saved parties.
// **Right**, the name and *What it is for*, the size (Lean · Standard · Full: the seats and their tiers change at once) with the party's AI tool, and the team by seats in the bands *Leads*, *Does*, *Checks*, each
// seat with its own AI tool and a dashed free seat that opens a short list of roles (partyform.js, partyseats.js, seattool.js); then what the party costs a goal, its checks and its priority. No metrics, no
// deadline, no links: a party has no end. *Save party* sends `ideas.goal_save` with `title`, `about`, `leader`, `team`, `every`, `size`, the party's `tool`, `tools` (the seats whose tool is not the party's), `priority`,
// `party` (a party of the person's that was picked), `proposal` and `preset` (the recipe or the library's party the seats still are). A task goes to the one of the party who does its kind of work; a checker's
// check adds its line to a goal's Done when and its task to the plan (realm/idea_checks.py). At the press the heads of the seats are kept: once the party is saved and shown, they gather into its deck
// (docs/specs/63-party-gathered.md §3, arena/goaltabs.js). Edit the party (goaldialog.js) is the same dialog on a party that is there.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { say } from "../link.js";
import { act, roles } from "./store.js";
import { Modal, closeDialog } from "./modals.js";
import { reducedMotion } from "../arena/motion.js";
import { savedParty } from "./proposals.js";
import { PartyBody, footLine, usePartyForm } from "./partyform.js";
import { agentOf, inBand, raceOfAgent } from "./party.js";

export { FOR_HINT } from "./partyform.js";

const boxOf = (r) => ({ left: r.left, top: r.top, width: r.width, height: r.height });
/** The heads of the seats as the dialog draws them now (spec 63 §3.1): [{race, tier, box}], the leader's first, then the builders', then the checkers' (six at most). A head whose seat is not on
 *  screen (scrolled out of the dialog) starts from *Save party*'s box: its own size, at that box's centre. */
function seatHeads(leader, team, tiers) {
  const heads = [leader, ...inBand("build", leader, team), ...inBand("check", leader, team)].map((id) => ({ id, a: agentOf(id) })).filter((x) => x.a).slice(0, 6);
  const seats = [...document.querySelectorAll("#goal-form .shell-team-seat .ork-race__head")].map((x) => x.getBoundingClientRect());
  const view = document.querySelector(".shell-modal__body")?.getBoundingClientRect(), save = document.querySelector(".shell-modal__foot button[type=submit]")?.getBoundingClientRect();
  const seen = (r) => !view || (r.bottom > Math.max(view.top, 0) && r.top < Math.min(view.bottom, innerHeight) && r.right > view.left && r.left < view.right);
  const atSave = (r) => (save ? { left: save.left + (save.width - r.width) / 2, top: save.top + (save.height - r.height) / 2, width: r.width, height: r.height } : r);
  return heads.map(({ id, a }, i) => seats[i] && { race: raceOfAgent(a), tier: tiers[id] || a.tier, box: boxOf(seen(seats[i]) ? seats[i] : atSave(seats[i])) }).filter(Boolean);
}

export function GoalWizard({ then = "", preset: first = "", proposal = "" }) {
  const f = usePartyForm({ first, proposal });
  const { d, api } = f;
  const [saving, setSaving] = useState(false);
  const ready = f.ready && !saving;
  const save = async (e) => {
    e?.preventDefault();
    if (!ready) return;
    const heads = then === "idea" || reducedMotion() || document.hidden ? [] : seatHeads(d.leader, d.team, api.tiers);       // the heads' boxes at the press: the dialog is gone when they travel
    setSaving(true);
    const tools = f.seatTools();
    const library = !d.partyId && d.lit && (roles.value?.presets || []).some((x) => x.id === d.lit);
    const got = await act("ideas.goal_save", { ...(f.title.trim() || (!f.about.trim() && f.suggest) ? { title: f.title.trim() || f.suggest } : {}), about: f.about.trim(), leader: d.leader, team: d.team, every: d.every.filter((id) => d.team.includes(id)), priority: f.priority,
      ...(d.partyId ? { party: d.partyId } : {}), ...(library ? { preset: d.lit } : {}), ...(f.routines.kept.length ? { routines: f.routines.kept } : {}), ...(f.sized && !d.partyId && d.lit && d.row?.recipe ? { proposal: d.row.recipe } : {}),
      ...(f.rf.value() ? { releases_from: f.rf.value() } : {}), ...(f.sized && d.size ? { size: d.size } : {}), ...(f.sized && d.tool ? { tool: d.tool } : {}), ...(f.sized && Object.keys(tools).length ? { tools } : {}) });
    setSaving(false);
    if (got?.slug) savedParty(got, heads, then);
  };
  return html`<${Modal} title="New party" onClose=${closeDialog} wide="xl"
    foot=${html`<span class="shell-p91__foot ok-font-status ok-tone-muted" data-foot="agents">${footLine(f)}</span>
      <button type="button" class="ork-btn" onClick=${closeDialog}>Cancel</button>
      <button type="submit" form="goal-form" class="ork-btn primary" disabled=${!ready}>Save party</button>`}>
    <form id="goal-form" class="shell-form" onSubmit=${save}>
      <${PartyBody} f=${f} say=${say(`${agentOf(d.leader)?.name || "The Taskmaster"} reads the repository and writes the summary.`)} />
    </form>
  <//>`;
}
