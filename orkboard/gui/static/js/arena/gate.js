// The gate's command (docs/specs/49-one-window.md §5.6, docs/specs/98-the-table-and-the-hand.md §4.3): what dev holds that main lacks is *n goals ready for main* on the hand's discard, and its one press merges dev into main.
import { toast } from "../link.js";
import { act } from "../shell/store.js";

/** Merge dev into main (`ideas.gate_merge`); the host's note, when it has one, is said as a warning. */
export async function mergeGate() {
  const got = await act("ideas.gate_merge", {});
  if (got?.note) toast(got.note, "warning");
  return got;
}
