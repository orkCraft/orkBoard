// Low work may run at night? (docs/specs/83-one-field-and-the-night-asked.md §0, §3; decisions §100): the one standing permission, asked once, the first time a Low goal is added
// while the Board has not been asked (`board.night_low` is null). *Yes, at night* / *No, by day*; either answer is `ideas.night_allow`, and the question is never drawn again. Esc or ×
// answers nothing: it is asked the next time. `after(allow)` runs once it is answered (a pitch's *Tonight* goes on, or is kept). The Settings switch changes the answer at any time.
import { useState } from "preact/hooks";
import { html } from "../html.js";
import { board } from "../board/store.js";
import { act } from "./store.js";
import { Modal, closeDialog, openDialog } from "./modals.js";

/** Asked: the Board has never been told (null). A Board that does not say (older) is not asked. */
export const nightUnset = () => board.value?.night_low === null;
/** Answered *No*: *Tonight* is not drawn. */
export const nightOff = () => board.value?.night_low === false;
/** "01:00-07:00" → "between 01:00 and 07:00". */
export const nightSpan = (night) => (/^\d\d:\d\d-\d\d:\d\d$/.test(night || "") ? night : "01:00-07:00").split("-").join(" and ");

/** After a Low goal is added: the question, when the Board has not been asked. */
export function askAfterLow(priority) {
  if (priority === "low" && nightUnset()) openDialog("night-ask");
}

export function NightAskDialog({ after = null }) {
  const [busy, setBusy] = useState(false);
  const go = async (allow) => {
    if (busy) return;
    setBusy(true);
    await act("ideas.night_allow", { allow });
    closeDialog();
    if (after) after(allow);
  };
  return html`<${Modal} title="Low work may run at night?" onClose=${closeDialog}
    foot=${html`<button type="button" class="ork-btn primary" autofocus disabled=${busy} onClick=${() => go(true)}>Yes, at night</button>
      <button type="button" class="ork-btn" disabled=${busy} onClick=${() => go(false)}>No, by day</button>`}>
    <p class="shell-modal__text" data-night="line">Low goals then run between ${nightSpan(board.value?.night)}, on what is left of the window; you can change it in Settings</p>
  <//>`;
}
