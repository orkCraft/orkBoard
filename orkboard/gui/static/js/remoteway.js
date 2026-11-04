// The phone's way through the project's remote, as the page asks for it (docs/specs/136 C.5–C.6, spec 137 C): when the link to the computer is down, the + card's goal and the
// hand's answers are written to the project's inbox on GitHub instead of being sent over the phone's socket. The frame holds the repository, the token and the writing
// (pwa/frame.js → `globalThis.orkboardPhone.remote`); this module only decides whether it is the way now and says what came of it. The page imports nothing of the frame;
// where there is no frame (the desktop) there is no way, and everything is as it was.
import { isPaired, online, toast } from "./link.js";

const remote = () => (isPaired() && !online.value ? globalThis.orkboardPhone?.remote || null : null);

/** The repository's way is open now: a paired phone whose computer cannot be reached and whose repository and token are set. */
export const through = () => {
  const r = remote();
  return r && r.ready() ? r : null;
};

/** A paired phone with no signal and no repository set: *Set your repository in Settings to send goals while your computer is away*, said once; "" otherwise. */
export function hintOnce() {
  const r = remote();
  return r && !r.ready() ? r.hint() : "";
}

/**
 * A goal through the repository: `{ok, kept?, error?}`; `error` is toasted here. `kept`: it waits for the network.
 * Returns null when the repository is not the way (the caller sends as it always did).
 */
export async function goalThrough(goal) {
  const r = through();
  if (!r) {
    const line = hintOnce();
    if (line) toast(line);
    return null;
  }
  const got = await r.sendGoal(goal);
  if (!got.ok) toast(got.error, "error");
  return got;
}

/** An answer to a card of the hand through the repository, or undefined when it is not the way (the page sends the command as it always did). A refusal is toasted and gives null. */
export async function answerThrough(name, args) {
  const r = through();
  if (!r || !r.answers(name)) return undefined;
  const got = await r.sendAnswer(name, args);
  if (!got.ok) { toast(got.error, "error"); return null; }
  toast(got.kept ? "Waits for the network" : "Sent through your repository: your computer or a cloud session will take it");
  return { sent: true, kept: Boolean(got.kept) };
}
