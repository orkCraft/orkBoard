// The gate (docs/specs/49-one-window.md §5.6, docs/specs/90-what-the-first-look-said.md §2.3, decisions §104.9): what dev holds that main lacks is **one card in the hand** for the batch,
// *n goals ready for main*, its answer *Merge into main* (arenawords.js `gateStop`, stops.js). A press on the card outside its button opens the gate's screen in the right column
// (`GateView`): the goals listed under *In dev, not in main* with their goals, the commits and files counts, and the one press that merges.
// The press that merges keeps its box for 10 s (flags.js): the flags it raises travel from there to the flag line (docs/specs/64-flags-raised.md).
import { html } from "../html.js";
import { Sign } from "../orkui.js";
import { toast } from "../link.js";
import { act, gateData, mapData } from "../shell/store.js";
import { gateOf, plural } from "./arenawords.js";
import { mergePressed, mergeRefused } from "./flags.js";

/** The gate's command (spec 49 §5.6, as the gate's screen has it): merge dev into main. `e`: the press, whose box the flags it raises travel from. */
export async function mergeGate(e) {
  mergePressed(e.currentTarget.getBoundingClientRect());                    // where the flags it raises travel from (spec 64), kept before the call is answered
  const got = await act("ideas.gate_merge", {});
  if (!got) mergeRefused();
  if (got?.note) toast(got.note, "warning");
  return got;
}

export function GateView() {
  const gate = gateData.value, shape = gateOf(gate);
  if (!gate || !shape) return html`<p class="ok-tone-muted">${gate ? "Results merge into main itself: there is no gate." : "Reading the gate…"}</p>`;
  const goals = Object.fromEntries((mapData.value?.goals || []).map((g) => [g.slug, g.title]));
  return html`<div class="arena-gateview">
    <div class="arena-gateview__head"><span class="shell-ptab__kind">The gate</span><h2>${gate.into} → ${gate.main}</h2>
      <span class="arena-cap">${shape.off ? `${gate.main} has every goal of ${gate.into}` : shape.words}</span></div>
    <section aria-label=${shape.off ? `In ${gate.main}` : `In ${gate.into}, not in ${gate.main}`}>
      <h3 class="board-sub">${shape.off ? `In ${gate.main}` : `In ${gate.into}, not in ${gate.main}`}</h3>
      ${gate.ideas.length ? html`<ul class="arena-done">${gate.ideas.map((i) => html`<li key=${i.slug}><span class="arena-ok"><${Sign} name="check" /></span> ${i.title} <span class="arena-cap">· ${goals[i.goal] || i.goal} · ${plural(i.tasks, "task", "tasks")}</span></li>`)}</ul>`
        : html`<p class="ok-tone-muted">${shape.off ? "Nothing is waiting." : "Nothing of a goal’s: only commits."}</p>`}
      <p class="arena-cap">${plural(gate.commits, "commit", "commits")} · ${plural(gate.files, "file", "files")}</p>
    </section>
    <div class="board-row"><button type="button" class="ork-btn primary" disabled=${shape.off} onClick=${mergeGate}>${shape.label}</button>
      <span class="arena-cap">Nothing reaches ${gate.main} without you.</span></div>
  </div>`;
}
