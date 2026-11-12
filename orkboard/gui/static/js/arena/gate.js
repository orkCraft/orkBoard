// The gate's command (docs/specs/49-one-window.md §5.6, docs/specs/98-the-table-and-the-hand.md §4.3): what dev holds that main lacks is *n goals ready for main* on the hand's discard, and its one press merges dev into main.
// The host runs the tests first and the press waits for them (decisions §274.2): `testing` says so while they run, and a red is the host's error, said in words (*Sealed: Tests is red: …*).
import { signal } from "@preact/signals";
import { toast } from "../link.js";
import { act } from "../shell/store.js";

export const testing = signal(false);                             // the merge's tests are running
export const TESTING = "Running the tests…";

/** Merge dev into main (`ideas.gate_merge`); the host's note, when it has one, is said as a warning. */
export async function mergeGate() {
  testing.value = true;
  try {
    const got = await act("ideas.gate_merge", { sealed: true });
    if (got?.note) toast(got.note, "warning");
    return got;
  } finally { testing.value = false; }
}
