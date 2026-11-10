// The empty chair (docs/specs/123-the-leaders-at-the-table.md §7.5, decisions §201.6; orkUI 0.27.0 `chair/`; it replaces *+ Party* and its banner of decisions §190.1): the whole chair, faint, nobody on it, after the parties at the tabs' end, its word **New party**
// (two lines when it must); hovered or focused it is lit and, under no-preference motion, pulled out (orkUI's, by `is-lit`: the chair is inside a button, so the page says when). Pressed, at 760 px and over, it deals the crafts not seated to the hand (spec 161 I, hand/chairdeal.js); narrower, the one place of the parties opens over the pane (parties.js
// `openParties`, as *+ Party* did), and for a party's *Edit* too. It stands only while a craft is not at the table: the place's own list (`ideas.party_presets`, the parties' recipes for the project's kind, the stage's group, the locked Release left out) with every one of
// them made leaves nothing to offer and no chair (`useOffer`). A host that does not say (an older one, no list) gives no reliable signal: the chair is always there. Under 760 px a 36 px cell holds the chair small, the word in its label only.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { Chair } from "../orkui.js";
import { command } from "../link.js";
import { board } from "../board/store.js";
import { currentProject } from "../shell/projects.js";
import { lower, over } from "../frame/state.js";
import { dealCrafts, dealing } from "../hand/chairdeal.js";
import { useWide } from "../hand/answercards.js";
import { madeFrom, openParties } from "./parties.js";

/** Whether the parties' place would still offer a party: some craft of the project's kind is not made yet. Always true while the list is not there. */
export function useOffer() {
  const project = currentProject.value?.path || "", tracks = (board.value?.tracks || []).filter((t) => t.slug !== "general"), placeOpen = over.value?.kind === "parties";
  const [presets, set] = useState(null);
  useEffect(() => {                                                  // asked for the project, and again once the place of the parties is closed (a kind corrected there changes it)
    if (placeOpen) return undefined;
    let live = true;
    command("ideas.party_presets", {}, true).then((r) => { if (live) set(Array.isArray(r?.presets) ? r.presets.filter((p) => p && p.group === "stage" && !p.locked) : null); }).catch(() => { if (live) set(null); });
    return () => { live = false; };
  }, [project, placeOpen]);
  if (!presets || !presets.length) return true;
  return presets.some((p) => !p.waits && !madeFrom(p, tracks));            // Release and Live wait: their chairs are not offered (decisions §283.29)
}

/** The empty chair as a button at the tabs' end. `from`: where the pane was (the place says it came from there). */
export function EmptyChair({ from, narrow }) {
  const [lit, setLit] = useState(false), wide = useWide() && !narrow, deals = wide && dealing.value;      // 760 px and over: the chair deals its crafts to the hand (hand/chairdeal.js); narrower, the parties' place as before
  const press = () => { if (!wide) { openParties({}, from); return; } lower(); dealCrafts(); };
  return html`<button type="button" class="table-chair" aria-label="New party" title="New party" aria-pressed=${wide ? String(deals) : undefined} onClick=${press}
    onPointerEnter=${() => setLit(true)} onPointerLeave=${() => setLit(false)} onFocus=${(e) => setLit(e.currentTarget.matches(":focus-visible"))} onBlur=${() => setLit(false)}>
    <${Chair} empty=${true} small=${narrow} lit=${lit || deals} />${!narrow && html`<span class="table-chair__w">New party</span>`}
  </button>`;
}
