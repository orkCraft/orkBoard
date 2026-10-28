// Edit the party (docs/specs/91-the-owners-list.md §7; docs/specs/50-parties-and-goals.md §3.7): the place of New party (goalwizard.js, partyform.js) on a party that is there — its name is the person's to
// correct, its seats, its size, its AI tool and each seat's are as the party has them, and a preset pressed puts another team in the seats (nothing is changed until *Save party*). Saving sends only what
// changed, and the party to its leader at once; *Remove party* stays at the foot. A member with work open never leaves (its row says so). The code's goal is a party.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { say, toast } from "../link.js";
import { board } from "../board/store.js";
import { act } from "./store.js";
import { Place, closePlace, openPlace } from "../frame/place.js";
import { GoalWizard } from "./goalwizard.js";
import { PRIORITIES, PartyBody, footLine, usePartyForm } from "./partyform.js";
import { TASKMASTER } from "./party.js";

export { PRIORITIES };

export function PartyPlace({ slug = "", preset = "", proposal = "" }) {
  return slug ? html`<${GoalEdit} slug=${slug} />` : html`<${GoalWizard} preset=${preset} proposal=${proposal} />`;
}

function GoalEdit({ slug }) {
  const g = slug ? board.value?.tracks.find((t) => t.slug === slug) : null;
  const f = usePartyForm({ edit: g ? { ...g, slug } : { slug } });
  const { d, api } = f;
  const [saving, setSaving] = useState(false);
  const was = { leader: g?.leader?.slug || TASKMASTER, team: g?.team || [], every: g?.every || [], tools: g?.tools || {} };
  const moved = d.leader !== was.leader || JSON.stringify(d.team) !== JSON.stringify(was.team) || JSON.stringify(d.every) !== JSON.stringify(was.every);
  const save = async (e) => {
    e?.preventDefault();
    if (!f.about.trim() || saving) return;
    setSaving(true);
    const args = { slug, about: f.about.trim(), priority: f.priority };
    if (f.title.trim() && f.title.trim() !== g?.title) args.title = f.title.trim();     // a name typed is the person's
    if (moved || d.partyId) Object.assign(args, { leader: d.leader, team: d.team, every: d.every.filter((id) => d.team.includes(id)), ...(d.partyId ? { party: d.partyId } : {}) });   // the party, when changed
    if (d.size && d.size !== (f.shownSize || "")) args.size = d.size;
    if (d.tool !== (g?.tool || "")) args.tool = d.tool;
    const tools = f.seatTools(), before = f.seatTools(was.tools, g?.tool || "", [was.leader, ...was.team]);
    if (JSON.stringify(tools) !== JSON.stringify(before)) args.tools = tools;       // the seats' own AI tools, when they changed
    const from = f.rf.value();
    if (from) args.releases_from = from;
    const got = await act("ideas.goal_save", args);
    setSaving(false);
    if (!got?.slug) return;
    for (const note of got.notes || []) toast(note);
    closePlace();
  };
  return html`<${Place} title="Edit the party"
    foot=${html`${g && slug !== "general" && html`<button type="button" class="ork-btn danger place__left" title="Its goals move to General or go with it, after one question" onClick=${() => openPlace("party", { slug, remove: true }, "Remove party")}>Remove party</button>`}
      <span class="shell-p91__foot ok-font-status ok-tone-muted" data-foot="agents">${footLine(f)}</span>
      <button type="button" class="ork-btn" onClick=${closePlace}>Cancel</button>
      <button type="submit" form="goal-form" class="ork-btn primary" disabled=${!f.about.trim() || saving}>Save party</button>`}>
    <form id="goal-form" class="shell-form" onSubmit=${save}>
      <${PartyBody} f=${f} say=${say(`${g?.leader?.slug && g.leader.slug !== TASKMASTER ? g.leader.name : "The Taskmaster"} reads the repository and writes the summary.`)} />
    </form>
  <//>`;
}
