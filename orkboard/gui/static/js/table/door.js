// Stop all, the halt behind the die's front face (docs/specs/139-the-die-the-door-and-the-bug.md A.2, decisions §246.1–§246.2; before it a door at the tabs' row's end, docs/specs/123-the-leaders-at-the-table.md §7.6, decisions §201.8, orkUI 0.27.0 `door/`:
// the door itself stays in orkUI and comes back as the person's presence, part C). The press is the die's (hand/playdie.js: the front face is a second `<button>`); what it does is kept here: it asks the host to stop everything
// (`command("halt")`: the host's toast says *Stopped n runs*); on the answer the orks are **stopped** (`stopped`: the front face's word says *Stopped*, muted, a second press does nothing), and it goes back when work starts: a party has a task
// running again (`isWorking`) or a goal is started from this page (`goalStarted`, told by board/store.js `ask` after `ideas.add` and `ideas.start`). The state is this page's (a second window keeps its own: the host's toast says what happened).
// A task that still shows as running just after the answer (the map is read a moment later) does not turn it back: work *starts again* only after the map has been seen with none at work. Not *Exit*: it halts, it closes nothing.
// `useOrks()` is the die's read of it: `{stopped, running}`, and the one place where *work starts again* is seen. Resume (part B) is not here yet.
import { useEffect } from "preact/hooks";
import { signal } from "@preact/signals";
import { command } from "../link.js";
import { partiesAll } from "./data.js";
import { isWorking } from "./moods.js";

/** Whether the orks are stopped: everything was stopped from this page and no work has started since. */
export const stopped = signal(false);
let seenIdle = false;                                                // the map has been seen with no party at work since they were stopped

/** A goal was started from this page: the orks are no longer stopped. */
export function goalStarted() { stopped.value = false; }

/** Stops everything; *stopped* is said on the host's answer (a refusal leaves it as it was). */
export async function halt() {
  if (stopped.peek()) return;
  try { await command("halt"); } catch { return; }
  seenIdle = !partiesAll().some(isWorking);
  stopped.value = true;
}

/** The die's read of the orks (a hook of the die's front face): `stopped` after a halt from this page and until work starts; `running` while a party has a task running (and not stopped). */
export function useOrks() {
  const open = stopped.value, working = partiesAll().some(isWorking);
  useEffect(() => {                                                  // work starts again: no longer stopped
    if (!open) return;
    if (!working) seenIdle = true;
    else if (seenIdle) { seenIdle = false; stopped.value = false; }
  }, [open, working]);
  return { stopped: open, running: working && !open };
}
