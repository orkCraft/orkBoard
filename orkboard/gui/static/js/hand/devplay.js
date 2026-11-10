// A goal's branch, in play (docs/specs/168 F2, decisions §283.27; D1's way of playing: hand/sayplay.js `PlayWays`): the card at the table's foot at its left, its ways the hand's row cut by the rim. Three things are played here.
// **A card of the discard's lower pile** (`playing.value = {dev: "card", slug}`): a goal done on its own branch, waiting for dev. Its way **To dev** (`ideas.goal_to_dev`: dev merged into the branch, the gate run on that, dev moved only when it is green) and, in its menu, **To dev without the tests**
// (`untested: true`, nothing else skips them). **A goal blocked before dev** (a stop of the hand, devcard.js `devStops`, kind `dev_blocked`): the card says why, its ways **Try again** (the same command) and, when no test ran, **To dev without the tests**.
// **A plate pressed** (`playing.value = {dev: "plate", which: "dev" | "main"}`): the branches are dealt to the hand (`ideas.branch_set {which}` says them: never `orkboard/*`, `goal/*`, `idea/*`), the lower plate's also **A new branch from dev**, written in a field of its own; a card warns first when goals are at work.
// A choice sets the project's setting (`ideas.branch_set {which, branch}`), never a view. A refusal is the host's toast and the card stays; done, the card goes back.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";
import { ORKMASTER, lower, playing } from "../frame/state.js";
import { mapData } from "../shell/store.js";
import { PlayWays } from "./sayplay.js";
import { TO_DEV, TO_DEV_UNTESTED, TRY_AGAIN, CANNOT, devName, devRow } from "./devcard.js";

const CROWN = { race: "peon", tier: "crown" };                    // the Orkmaster's head: it asks the plates' questions
export const WARN = "Goals are at work", WARN_LINE = "Changing the branch moves where the work still to come lands and is checked; what is done stays where it is.", WARN_GO = "Choose a branch anyway";
export const ASK_DEV = "Which branch do goals land in?", ASK_MAIN = "Which branch is main?", NEW_BRANCH = (dev) => `A new branch from ${dev}`, HERE = "Here now";

const WAY_LINE = {
  to_dev: (dev) => `Merges ${dev} into the goal's branch, runs the tests on that and puts the goal in ${dev} once they are green.`,
  untested: (dev) => `Puts the goal in ${dev} with no test run: nothing has shown it is safe.`,
  again: (dev) => `Asks the gate again: ${dev} merged into the branch, the tests run once more.`,
};

/** Sends the goal into dev (`untested` only from *To dev without the tests*); a refusal is the host's toast and the card stays, done the card goes back. */
const send = (idea, untested = false) => command("ideas.goal_to_dev", { idea, ...(untested ? { untested: true } : {}) }).then(() => lower()).catch(() => {});

const headOf = (n) => (mapData.value?.goals || []).find((g) => g.slug === n?.goal)?.leader?.head || null;

/** A card of the lower pile in play: `slug` the goal. Gone from the pile (it went into dev, or was sent back to work): the card goes back. */
export function LowerPlay({ slug }) {
  const n = (mapData.value?.nodes || []).find((x) => x.slug === slug), row = devRow(slug), dev = devName();
  const card = n && row?.waits_for_dev ? {
    title: n.short || n.title, foot: row.dev_why || `Waiting for ${dev}`, sign: "check", element: n.element || "", hue: n.hue || "", head: headOf(n), tab: n.goal,
    ways: [{ id: "to_dev", name: TO_DEV, line: WAY_LINE.to_dev(dev), pick: false, kind: "go_on", run: () => send(slug) }],
    acts: [{ id: "to_dev_untested", name: TO_DEV_UNTESTED, line: WAY_LINE.untested(dev), run: () => send(slug, true) }],
  } : null;
  return html`<${PlayWays} card=${card} id=${`dev:${slug}`} idea=${slug} kind="lower" />`;
}

/** A goal blocked before dev, as a stop of the hand: `s`. */
export function DevPlay({ s }) {
  const r = s.ref, n = s.node, row = devRow(r.idea), dev = r.dev;
  const ways = [{ id: "try_again", name: TRY_AGAIN, line: WAY_LINE.again(dev), pick: false, kind: "start_again", run: () => send(r.idea) }];
  if (r.dev_kind === "no_tests") ways.push({ id: "to_dev_untested", name: TO_DEV_UNTESTED, line: WAY_LINE.untested(dev), pick: false, kind: "accept_risk", run: () => send(r.idea, true) });
  const card = row?.dev_blocked ? { title: s.title, foot: row.dev_why || r.why, sign: "alert", element: n?.element || "", hue: n?.hue || "", head: s.head, tab: n?.goal || ORKMASTER, ways } : null;
  return html`<${PlayWays} card=${card} id=${s.key} idea=${r.idea} kind="dev_blocked" />`;
}

/** The plate's branches dealt to the hand: asked of the host once, a warning card first when goals are at work. */
export function PlateDeal({ which }) {
  const [got, setGot] = useState(null), [went, setWent] = useState(false);
  useEffect(() => {
    let live = true;
    setGot(null);
    setWent(false);
    command("ideas.branch_set", { which }, true).then((r) => { if (live) setGot(r); }).catch(() => { if (live) lower(); });
    return () => { live = false; };
  }, [which]);
  if (!got) return null;
  if (got.at_work > 0 && !went) {
    const warn = { title: WARN, foot: WARN_LINE, sign: "alert", element: "", hue: "", head: CROWN, tab: "", ways: [{ id: "warn_go", name: WARN_GO, line: WARN_LINE, pick: false, kind: "go_on", run: () => setWent(true) }] };
    return html`<${PlayWays} card=${warn} id=${`plate:${which}:warn`} idea="" kind="plate" />`;
  }
  const choose = (branch) => (branch === got.now ? lower() : command("ideas.branch_set", { which, branch }).then(() => lower()).catch(() => {}));
  const card = {
    title: which === "dev" ? ASK_DEV : ASK_MAIN, foot: `${HERE}: ${got.now}`, sign: "compass", element: "", hue: "", head: CROWN, tab: "",
    ways: got.branches.map((b) => ({ id: `branch:${b}`, name: b, line: b === got.now ? HERE : which === "dev" ? `Goals land in ${b}.` : `Goals are sent to ${b}.`, pick: false, kind: b === got.now ? "keep" : "take", run: () => choose(b) })),
    pen: which === "dev" ? {
      name: NEW_BRANCH(got.from), line: `Name it: it is made from ${got.from} and goals land in it.`, who: "the Orkmaster", ask: { label: "The new branch's name", hold: "A name for the new branch…", rows: 1, button: "Make the branch", note: `Enter makes it from ${got.from}` },
      send: (text) => command("ideas.branch_set", { which, new: text.trim() }).then(() => lower()).catch(() => {}),
    } : null,
  };
  return html`<${PlayWays} card=${card} id=${`plate:${which}:pick`} idea="" kind="plate" />`;
}

/** What `playing.value` names when it is a branch's play (`dev`), or null for the say's. */
export function DevLifted() {
  const p = playing.value;
  if (p?.dev === "card") return html`<${LowerPlay} slug=${p.slug} />`;
  if (p?.dev === "plate") return html`<${PlateDeal} which=${p.which} />`;
  return null;
}
export const isDevPlay = () => !!playing.value?.dev;
export { CANNOT };
