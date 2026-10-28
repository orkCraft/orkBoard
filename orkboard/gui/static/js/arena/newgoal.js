// New goal at the Orkmaster (docs/specs/73-a-lighter-column.md §4, decisions §88): the **+** in the project line, between the Orkmaster's head and the project switcher. A press deals *Your own
// goal* and the goal types — the party shown's first, then the other parties' of the project — as the project's New goal does (spec 70 §4), and New goal opens with that party shown picked
// (*Its party*: the others are its chips, asked of `ideas.party_for` when a type is picked). On the project's level, or with no party shown, it is spec 70 §4: no party at first.
// A host from before spec 70 (`ideas.map` has no `project`) has no Orkmaster to suggest: the + deals the shown party's own types and New goal is that party's, as its pile was.
// A host with no types opens New goal at once.
// Spec 91 §8: with an Orkmaster this + is gone — New goal is a row of the Orkmaster's level (projectrows.js), the one way in; partylist.js draws this + only for a host with no Orkmaster.
import { useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { Icon } from "../orkui.js";
import { PROJECT } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { openDialog } from "../shell/modals.js";
import { TypesSpread } from "./types.js";
import { projectOn } from "./goaltabs.js";
import { typesFirst } from "./projectwords.js";

/** `want`: what the column shows (a party's slug or PROJECT). */
export function NewGoalPlus({ want }) {
  const [from, setFrom] = useState(null), button = useRef();
  const goals = (mapData.value?.goals || []).filter((g) => g.slug !== "general");
  const shown = goals.find((g) => g.slug === want), party = shown?.slug || "", name = shown ? shown.short || shown.title : "", level = projectOn();
  const types = level ? typesFirst(goals, party) : shown?.types || [], label = party ? `New goal: in ${name}, or another` : "New goal: your own, or pick its type";
  const at = { slug: level ? PROJECT : party, first: level ? party : "", title: name || "the project", short: name || "the project", types };
  const press = (e) => {
    if (from) return;
    if (!goals.length) { openDialog("goal", { then: "idea" }); return; }                                                 // a goal needs a party: this makes one first
    if (types.length) setFrom(e.currentTarget.getBoundingClientRect()); else openDialog("idea", { goal: at.slug, ...(at.first ? { party: at.first } : {}) });
  };
  return html`<button type="button" ref=${button} class="ork-btn arena-plus" aria-label="New goal" title=${label} aria-haspopup=${types.length ? "dialog" : undefined} onClick=${press}><${Icon} name="plus" /></button>
    ${from && html`<${TypesSpread} g=${at} from=${from} back=${button.current} done=${() => setFrom(null)} />`}`;
}
