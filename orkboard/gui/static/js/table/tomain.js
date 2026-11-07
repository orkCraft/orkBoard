// **To main**, the picked ready card's act (docs/specs/156-one-pick-and-the-release-column.md D.4, decisions §261.8): while the goal picked is ready for main (the gate holds it: hand/data.js `readyOf`), a line under the pane's title says where it goes and what stands in
// the way, and the button *To main* sends it alone with the goals it stands on through the portal's way (portal.js `toMain`: its plan, its checks, then `ideas.to_main`; a red check or a seal says its reason and nothing is sent). It is shown on every tab, since a
// ready goal's route is the tabs' that are not grey (part B); the ring and the rite play at the top of Release's lane (ring.js). Nothing here decides for the person: nothing reaches main without this press. Layout only: lane.css.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { picked } from "../frame/state.js";
import { readyOf } from "../hand/data.js";
import { CHECKING, checksOf, isRed, pending, sealedWords } from "./checks.js";
import { chosenSlug, echo, lineOf, plan, reasonOf, toMain } from "./portal.js";

export function ToMain() {
  const slug = picked.value, r = readyOf(), [busy, setBusy] = useState(false);
  if (!slug || !r || !r.goals.some((g) => g.slug === slug)) return null;
  const main = r.main || "main", mine = chosenSlug() === slug, p = mine ? plan.value : null;
  const list = p?.state === "ok" && (!p.sealed || p.conflict) ? checksOf(slug) : [], asking = mine && pending.value === slug && !list.length, red = isRed(list), checking = !red && (asking || list.some((c) => c.state !== "passed"));
  const sealed = p?.state === "fail" || (!!p?.sealed && !(p.conflict && (list.length > 0 || asking))), reason = sealed ? reasonOf(p) : red ? sealedWords(list) : "";
  const line = !p || p.state === "wait" ? "" : checking ? CHECKING : p.state === "ok" ? lineOf(p, slug, main) : `Into ${main}`;
  const go = async () => { setBusy(true); try { await toMain(slug); } finally { setBusy(false); } };
  return html`<div class=${cls("table-tomain", { "is-sealed": !!reason })} data-tomain=${slug} data-portal=${reason ? "sealed" : checking ? "check" : "open"}>
    <button type="button" class="ork-btn primary" data-to-main disabled=${busy} aria-disabled=${checking || !p || p.state === "wait" ? "true" : undefined}
      title=${`Sends the goal through the portal to ${main}: its checks run first, nothing reaches ${main} without you`} onClick=${go}>To ${main}</button>
    <span class="table-tomain__line" role="status" aria-live="polite">${reason ? html`<span key=${echo.value} class="table-tomain__sealed">Sealed: ${reason}</span>` : line}</span>
  </div>`;
}
