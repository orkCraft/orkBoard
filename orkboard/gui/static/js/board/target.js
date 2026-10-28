// The Target (docs/specs/35-goals-window.md §1, §11.1; docs/specs/75-parties-fitted-to-the-project.md §5.5): the Board's one setting, Thrift, Balance or Quality, picks every step's model and reasoning. It
// left the top bar with spec 75: a party's size is its Target now (Lean works as Thrift, Standard as Balance, Full as Quality), and the setting is what a party with no size of its own works as — the
// parties made before. It stays in Settings (shell/settings.js), as this three-way switch.
import { html } from "../html.js";
import { Switch } from "../orkui.js";
import { board } from "./store.js";
import { act } from "../shell/store.js";

export const TARGETS = [
  ["thrift", "Thrift", "lighter models, less reasoning"],
  ["balance", "Balance", "the default: each step on the tier it needs"],
  ["quality", "Quality", "heavier models, more reasoning"],
];

export const TARGET_LABEL = "A party with no size of its own works as";

export function TargetSetting() {
  const now = board.value?.target || "balance";
  const pick = (id) => { if (id !== now) act("ideas.board_set", { target: id }); };
  return html`<div class="shell-field" role="group" aria-label=${TARGET_LABEL} data-settings="target"><span class="ok-font-label">${TARGET_LABEL}</span>
    <${Switch} label="Target" options=${TARGETS.map(([id, word]) => [id, word])} value=${now} onPick=${pick} />
    <span class="ok-font-status ok-tone-muted">${(TARGETS.find(([id]) => id === now) || TARGETS[1])[2]}</span></div>`;
}
