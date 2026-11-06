// Release's table shows the checks on the way into main (docs/specs/156-one-pick-and-the-release-column.md D.4, decisions §261.8; before it the skeletons stood in front of the portal, spec 111 §4.3, decisions §188.3–§188.4): for the goal chosen for main
// (the ready card picked), a skeleton a check — Release's members, the laborer, the warrior and the elder in that order — with its name and its state in words (*waiting*, *checking*, *passed*), and for a red one **why** (`words`, the check's own). Laid in the
// pane at Release's tab, not over a portal. The data is checks.js's; nothing here runs a check. Layout only: lane.css.
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { SKELETONS, checksOf, pending } from "./checks.js";
import { chosenSlug } from "./portal.js";

const STATE_WORD = { waiting: "waiting", running: "checking", passed: "passed", failed: "red" };

export function ChecksView() {
  const slug = chosenSlug(), list = slug ? checksOf(slug) : [];
  if (!slug || (!list.length && pending.value !== slug)) return null;
  return html`<section class="table-checks" aria-label="The checks on the way into main" data-checks=${slug}>
    <h2 class="ork-label table-checks__title">Checks before main</h2>
    ${!list.length ? html`<p class="table-over__muted">Asking the host to run them…</p>`
      : html`<ul class="table-checks__list">${list.map((c, i) => html`<li key=${c.name} class=${cls("table-check", { "is-red": c.state === "failed", "is-passed": c.state === "passed" })} data-check=${c.state}>
        <span class=${cls("table-check__head", { "is-working": c.state === "running" })}><${Head} race="skeleton" tier=${SKELETONS[Math.min(i, SKELETONS.length - 1)]} size="big" /></span>
        <span class="table-check__txt"><b class="table-check__name">${c.name}</b><span class="table-check__state">${STATE_WORD[c.state] || c.state}</span>
          ${c.state === "failed" && html`<span class="table-check__why">${c.words || "it failed"}</span>`}</span></li>`)}</ul>`}
  </section>`;
}
