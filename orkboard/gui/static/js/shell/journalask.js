// The one-time question under Settings' *Your phone* (docs/specs/136 A.2, decisions §243.8): when a phone is paired and the
// project's origin is on GitHub, whether to follow the project from the phone away from home. The host says whether to ask
// (gui/phone_journal.py `journal.phone_ask`) and what the line is; *Turn it on* writes `[journal]` with the inbox,
// *Not now* asks no more. Settings keep the switch.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";

export function JournalAsk() {
  const [ask, setAsk] = useState(null);
  useEffect(() => { command("journal.phone_ask").then(setAsk, () => {}); }, []);
  if (!ask || !ask.ask) return null;
  const answer = (name) => command(name).then(() => setAsk(null), () => {});
  return html`<div class="shell-field" data-settings="journal-ask" role="group" aria-label="Your phone, away from home">
    <span class="ok-font-status">${ask.line}</span>
    <span><button type="button" class="ork-btn primary" onClick=${() => answer("journal.turn_on")}>Turn it on</button>
      <button type="button" class="ork-btn" onClick=${() => answer("journal.not_now")}>Not now</button></span>
  </div>`;
}
