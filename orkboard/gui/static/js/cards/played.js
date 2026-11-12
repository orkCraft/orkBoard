// A move the person plays from a card of the hand or from a mat (goal 171 stage K; decisions §300.2, §302.4): one press sends the command with where it was pressed
// (`from`: "hand" or "mat", which the host logs as `move_played`, never a word), and the toast says what it did with **Undo**, which sends `ideas.undo {idea}` (the history's:
// the host refuses in plain words when the goal's page changed since, and the toast says it as the host does). A move that cannot be undone goes only on its seal (`sealed: true`,
// the mat's `Seal`) and offers no Undo. A refused move is toasted in the host's words and nothing is told as done. Nothing here imports a face.
import { command, toast } from "../link.js";

export const UNDO_S = 6;                      // the toast offers Undo this long; the history keeps it after (WCAG 2.2.1)
export const UNDO = "Undo";

/** Takes the last move of a goal back (`ideas.undo`); `back` runs once the page is as it was. Resolves whether it was put back. */
export async function undoMove(goal, back, party = false) {
  try { await command("ideas.undo", { idea: goal, ...(party ? { party: true } : {}) }); } catch { return false; }          // refused: the host's toast says why (it changed since)
  toast("Put back: the goal is as it was.");
  back?.();
  return true;
}

/** Plays a move: `name`/`args` the command, `from` where it was pressed (hand or mat), `goal` the goal it is about, `said` what the toast says, `done` runs once it went, `back` once it is undone.
 *  `sealed`: the seal (a move that cannot be undone): sent as such, no Undo offered. Resolves whether it went. */
export async function playMove(name, args, { from, goal, said, done, back, sealed = false, party = false }) {
  try { await command(name, { ...args, ...(sealed ? { sealed: true } : {}), from }, true); } catch (e) { if (e?.message !== "offline") toast(e?.message || "Refused", "error", name); return false; }
  done?.();
  if (sealed) toast(said);
  else toast(said, "information", "", UNDO_S, null, [{ label: UNDO, run: () => undoMove(goal, back, party) }]);
  return true;
}
