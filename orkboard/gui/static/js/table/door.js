// Stop all as a door (docs/specs/123-the-leaders-at-the-table.md §7.6, decisions §201.8; orkUI 0.27.0 `door/`; it replaces the boards across a pole of decisions §190.1): at the dark row's end, shut at rest, whatever runs, its word *Stop all* in the danger
// colour while it can be pressed. Pressed, it asks the host to stop everything (`command("halt")`: the host's toast says *Stopped n runs*); on the answer the door is **open** (*All stopped*, muted, `aria-disabled`, a second press does nothing),
// and it shuts again when work starts: a party has a task running again (`isWorking`) or a goal is started from this page (`goalStarted`, told by board/store.js `ask` after `ideas.add` and `ideas.start`). The state is this page's (a second window keeps
// its own: the host's toast says what happened). A task that still shows as running just after the answer (the map is read a moment later) does not shut it again: work *starts again* only after the map has been seen with none at work. Not
// *Exit*: it halts, it closes nothing. Under 760 px the small door and **Stop**.
import { useEffect, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Door } from "../orkui.js";
import { command } from "../link.js";
import { partiesAll } from "./data.js";
import { isWorking } from "./moods.js";

/** Whether the door is open: everything was stopped from this page and no work has started since. */
export const stopped = signal(false);
let seenIdle = false;                                                // the map has been seen with no party at work since the door opened

/** A goal was started from this page: the door shuts. */
export function goalStarted() { stopped.value = false; }

/** Stops everything; the door opens on the host's answer (a refusal leaves it shut). */
export async function halt() {
  if (stopped.peek()) return;
  try { await command("halt"); } catch { return; }
  seenIdle = !partiesAll().some(isWorking);
  stopped.value = true;
}

/** The door's button: **Stop all**, shut; **All stopped**, open. */
export function StopDoor({ narrow }) {
  const open = stopped.value, working = partiesAll().some(isWorking), [lit, setLit] = useState(false);
  useEffect(() => {                                                  // work starts again: the door shuts
    if (!open) return;
    if (!working) seenIdle = true;
    else if (seenIdle) { seenIdle = false; stopped.value = false; }
  }, [open, working]);
  const word = open ? "All stopped" : narrow ? "Stop" : "Stop all", title = open ? "All stopped: the door shuts when work starts again" : "Stop every ork, script and browser at once";
  return html`<button type="button" class=${cls("table-door", { "is-open": open })} aria-label=${open ? "All stopped" : "Stop all"} aria-disabled=${open ? "true" : undefined} title=${title}
    onClick=${() => { if (!open) halt(); }} onPointerEnter=${() => setLit(true)} onPointerLeave=${() => setLit(false)}
    onFocus=${(e) => setLit(e.currentTarget.matches(":focus-visible"))} onBlur=${() => setLit(false)}>
    <${Door} open=${open} small=${narrow} lit=${lit && !open} /><span class="table-door__w">${word}</span>
  </button>`;
}
