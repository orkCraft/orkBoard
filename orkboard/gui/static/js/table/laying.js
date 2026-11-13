// The window not yet laid, and the laying (docs/specs/130-the-first-open-is-the-orkmasters.md C.6, decisions §232.1, §247.1): until the project's first Start the snapshot's `laid` is false and the window holds the Orkmaster alone: no tabs, no empty chair, no door, no die (tabs.js, hand.js), its column only its bubble (column.js),
// the table bare (pane.js), the hand only the Orkmaster's cards and the AI tools. A snapshot with no `tools` (a paired phone's) has no first open: its table is always laid. **At Start** (`laid` turns true while the page is open) the table is laid once, in order: the leaders sit down, the empty chair, the door and the die appear, the + card comes to the hand
// with its seal lit once, and the Orkmaster says so in its bubble (`layLine`); the ring and the discard's place come with their first content (§247.1). `frame[data-laying]` holds the motion (table.css); reduced motion: all at once. A project opened already laid is laid at once, with no motion.
import { useEffect, useRef } from "preact/hooks";
import { signal } from "@preact/signals";
import { town } from "../link.js";
import { currentProject } from "../shell/projects.js";

export const LAID_LINE = "The table is laid. What shall we make first? Play the + card.";
const LAYING_MS = 2400;
export const laying = signal(false);        // the laying plays now
export const layLine = signal("");          // what the Orkmaster says of it, until the first goal is written

/** The table is laid. */
export const laidNow = () => !town.value?.tools || town.value?.laid !== false;

const reduced = () => typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Plays the laying once when `laid` turns true for the project shown; another project is no laying. Mounted by the frame. */
export function useLaying() {
  const laid = laidNow(), project = currentProject.value?.path || "", was = useRef({ project, laid });
  useEffect(() => {
    const before = was.current;
    was.current = { project, laid };
    if (before.project !== project) { laying.value = false; layLine.value = ""; return undefined; }
    if (before.laid || !laid) return undefined;
    layLine.value = LAID_LINE;
    if (reduced()) return undefined;
    laying.value = true;
    const t = setTimeout(() => { laying.value = false; }, LAYING_MS);
    return () => clearTimeout(t);
  }, [laid, project]);
}
