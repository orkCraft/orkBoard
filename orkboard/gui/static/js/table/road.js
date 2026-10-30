// The road after the work (docs/specs/111-a-goals-rune-release-and-live-at-the-portal.md §4.1, §4.3, decisions §188.1–§188.4): at the wide width Release and Live are no tabs and have no lanes; they wait in the portal ring's corners
// (portal.js lays them), Release at the lower left (before main), Live at the upper right (past it). **Asleep** a corner is its leader's head alone, grey and still (orkUI's `.is-asleep`); **awake**, in colour and with up to two of the
// party's members' heads, its leader stepping while one of its tasks runs (`.is-working`, the tabs' `isWorking`), an alert sign on it when the party has one (`hasAlert`). Each corner is a button that opens that party's view in the
// pane as a tab does (`openTab`), with no tab lit in the row. Release wakes when a goal is ready for main, a task of its runs, it asks (a card of its in the hand) or has an alert, or while the checks of the goal chosen for main run;
// Live when a task of its runs, it asks or it has an alert. The skeletons that have passed their checks stand in Release's corner beside its leader, each with a tick, in place of its members; the ones still checking, and a red
// one, stand in the gate in front of the portal (`Gate`). A party the project does not have has no corner, and a project with no gate (table/data.js `noGate`) has no ring: `roadParties` says none, so Release and Live are tabs there (docs/specs/113-a-project-with-no-preview-or-no-gate.md §4).
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { closeOver, openTab } from "../frame/state.js";
import { partyOf } from "../arena/arenawords.js";
import { readyOf, stopsOfProject } from "../hand/data.js";
import { nodesFor, roadParties } from "./data.js";
import { hasAlert } from "./concerns.js";
import { isWorking } from "./tabs.js";

/** A party asks: a card of it lies in the hand (a question, a plan to look at, a failure, a result). */
const asks = (g) => !!g && stopsOfProject().some((s) => (s.g?.slug || s.row?.goal || "") === g.slug);

/** Up to two of a party's members' heads (its leader is the corner's first). */
const membersOf = (g) => partyOf(g, nodesFor(g)).members.filter((m) => m.head).slice(0, 2).map((m) => m.head);

const GuardHead = ({ head, tick = false, alert = false, title = "" }) => html`<span class="ork-portal-ring__guard" title=${title || undefined}>
  <${Head} race=${head.race} tier=${head.tier} />${tick && html`<span class="ork-portal-ring__tick" aria-hidden="true"></span>`}${alert && html`<span class="ork-portal-ring__alert" aria-hidden="true"></span>`}</span>`;

/** What each corner shows now: `{release, live}`, each null (no such party) or `{g, awake, working, alert, members}`. `checks`: the skeletons of the goal chosen for main, `{state}` each; `running`: its checks are not over. */
export function roadNow(skeletons = [], running = false) {
  const { release, live } = roadParties();
  const corner = (g, awake, working) => g && { g, awake, working, alert: hasAlert(g), members: awake ? membersOf(g) : [] };
  const r = release && (() => {
    const working = isWorking(release) || running, awake = (readyOf()?.goals || []).length > 0 || working || asks(release) || hasAlert(release) || skeletons.length > 0;
    return corner(release, awake, working);
  })();
  const l = live && (() => {
    const working = isWorking(live), awake = working || asks(live) || hasAlert(live);
    return corner(live, awake, working);
  })();
  return { release: r || null, live: l || null };
}

/** One corner of the ring: a button that opens the party's view. `passed`: while the goal chosen for main has checks, the skeletons that have passed beside Release's leader with their ticks (none yet: its leader alone), in place of its members; null otherwise. */
export function Corner({ side, words, c, passed = null }) {
  if (!c) return null;
  const head = c.g.leader?.head, ticks = side === "before" ? passed : null;
  return html`<button type="button" class=${cls(`ork-portal-ring__${side}`, { "is-asleep": !c.awake, "is-working": c.working })} title=${words} aria-label=${words} data-road=${side === "before" ? "release" : "live"}
      data-awake=${String(c.awake)} onClick=${() => { closeOver(); openTab(c.g.slug); }}>
    ${head && html`<${GuardHead} head=${head} alert=${c.alert} />`}
    ${ticks ? ticks.map((s) => html`<${GuardHead} key=${s.at} head=${{ race: "skeleton", tier: s.tier }} tick=${true} title=${s.label} />`)
      : c.members.map((h, i) => html`<${GuardHead} key=${i} head=${h} />`)}
  </button>`;
}

/** The gate: the skeletons whose checks have not passed, in front of the portal's lower part (orkUI `.ork-portal-ring__gate`, three at most), the one running stepping, a red one with its alert sign. It lies over the portal, so a press on it is a press on the portal (`onPress`: the sealed portal says its reason again; `drag`: a card dropped on it is dropped on the portal, which says it is checking). */
export function Gate({ skeletons, onPress, drag = {} }) {
  const standing = skeletons.filter((s) => s.state !== "passed");
  if (!standing.length) return null;
  const running = standing.find((s) => s.state === "running")?.at;
  return html`<span class="ork-portal-ring__gate" data-gate=${standing.map((s) => s.state).join(" ")} onClick=${onPress} ...${drag}>${standing.map((s) => html`<span key=${s.at} class=${cls("ork-portal-ring__guard", { "is-working": s.at === running, "is-red": s.state === "failed" })}
      role="img" aria-label=${s.label} title=${s.label} data-check=${s.state}><${Head} race="skeleton" tier=${s.tier} size="big" />${s.state === "failed" && html`<span class="ork-portal-ring__alert" aria-hidden="true"></span>`}</span>`)}</span>`;
}
