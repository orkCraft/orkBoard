// The road after the work (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4, decisions §188.2; docs/specs/156-one-pick-and-the-release-column.md D.2, decisions §261.7): Release and Live are the row's last two tabs at the wide
// width (Live, then Release last), and the corners' waking rules are on the tabs' faces. **Asleep**, a tab's head is its leader's, grey and still (mood asleep); **awake**, in colour, its leader stepping while one of its tasks runs (moods.js
// `isWorking`), an alert sign on it when the party has one (`hasAlert`). Release wakes when a goal is ready for main, a task of its runs, it asks (a card of its in the hand) or has an alert, or while the checks of the goal chosen for main run;
// Live when a task of its runs, it asks or it has an alert.
import { stopsOfProject, readyOf } from "../hand/data.js";
import { isRelease, isLive } from "./data.js";
import { hasAlert } from "./concerns.js";
import { isWorking } from "./moods.js";

/** A party asks: a card of it lies in the hand (a question, a plan to look at, a failure, a result). */
const asks = (g) => !!g && stopsOfProject().some((s) => (s.g?.slug || s.row?.goal || "") === g.slug);

/** Whether the party is one of the road's two (Release, Live): its tab's face wakes and sleeps by `roadAwake`. */
export const onRoad = (g) => isRelease(g) || isLive(g);

/** Whether a road party's tab is awake now. `checking`: the checks of the goal chosen for main are not over (checks.js); only Release's tab wakes for them. */
export function roadAwake(g, checking = false) {
  if (isRelease(g)) return (readyOf()?.goals || []).length > 0 || isWorking(g) || checking || asks(g) || hasAlert(g);
  return isWorking(g) || asks(g) || hasAlert(g);
}
