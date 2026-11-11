// The plate that says the page runs on mocks (goal 170, stage M): which project's recording, when, and that nothing is sent;
// pressed, what would have been sent. Drawn only with `?mock=1` (board.js).
import { html } from "../html.js";
import { useState } from "preact/hooks";
import { recorded, sent } from "./mocklink.js";

export function MockPlate() {
  const [open, setOpen] = useState(false), r = recorded.value, n = sent.value;
  if (!r) return null;
  return html`<div class="mock-plate" role="status">
    <button class="mock-plate__b" aria-expanded=${open} onClick=${() => setOpen(!open)}>
      Mock data: ${r.folder}, recorded ${r.at}. Nothing is sent.</button>
    ${open && html`<ul class="mock-plate__sent">${n.length ? n.slice(-12).reverse().map((x) => html`<li>${x.name} <code>${JSON.stringify(x.args)}</code></li>`)
      : html`<li>Nothing would have been sent yet.</li>`}</ul>`}
  </div>`;
}
