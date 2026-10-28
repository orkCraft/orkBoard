// Remove party (docs/specs/80-a-party-removed.md §0, §3, §4; decisions §97): the question that follows *Remove party* in Edit the party (goaldialog.js), a place over the pane. Its goals move to General
// (the default, first, focused) or go with it (the danger colour), or nothing is done (Cancel, Esc). A party with no goal asks only Remove / Cancel. A refusal of the host
// (a goal at work, the party gone) is said in the question, which stays. On success: the toast, the tabs redrawn, and the Orkmaster's tab shown when the removed one was open.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { command, toast } from "../link.js";
import { board } from "../board/store.js";
import { Place, closePlace } from "../frame/place.js";
import { refreshShell } from "./store.js";

export const GENERAL = "general";
const goals = (n) => `${n} ${n === 1 ? "goal" : "goals"}`;

/** What the toast says after: *<party> removed*, with *k goals moved to General* or *k goals removed* when there were any. */
export const removedWords = (name, k, how) => `${name} removed${k ? `: ${goals(k)} ${how === "drop" ? "removed" : "moved to General"}` : ""}`;

export function RemovePartyPlace({ slug }) {
  const g = (board.value?.tracks || []).find((t) => t.slug === slug);
  const name = g?.title || slug, k = g?.count || 0;
  const [busy, setBusy] = useState(false);
  const [refused, setRefused] = useState("");
  const go = async (how) => {
    if (busy || slug === GENERAL) return;
    setBusy(true);
    setRefused("");
    let got = null;
    try { got = await command("ideas.track_drop", { slug, goals: how }, true); }
    catch (e) { setRefused(e.message || "That party is gone"); }
    if (!got) { setBusy(false); refreshShell(); return; }
    closePlace();                                                                    // the table shows the Orkmaster's tab when the party's own is gone
    const n = (got.moved || 0) + (got.dropped || 0);
    toast(removedWords(got.title || name, n, how));
    refreshShell();
  };
  const foot = k
    ? html`<button type="button" class="ork-btn primary" autofocus disabled=${busy} onClick=${() => go("move")}>Move its ${goals(k)} to General and remove</button>
        <button type="button" class="ork-btn danger" disabled=${busy} onClick=${() => go("drop")}>Remove the party and its ${goals(k)}</button>
        <button type="button" class="ork-btn" onClick=${closePlace}>Cancel</button>`
    : html`<button type="button" class="ork-btn danger" autofocus disabled=${busy} onClick=${() => go("move")}>Remove</button>
        <button type="button" class="ork-btn" onClick=${closePlace}>Cancel</button>`;
  return html`<${Place} title=${`Remove ${name}?`} foot=${foot}>
    <p class="place__text">${k ? `${name} has ${goals(k)}. They can move to General or be removed with it. A removed goal's spend is kept.` : "It has no goals"}</p>
    ${refused && html`<p class="place__text place__refused" role="alert">${refused}</p>`}
  <//>`;
}
