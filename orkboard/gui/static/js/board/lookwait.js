// Give me time to look (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md B.1; decisions §225.1): the project's one wait for every spec made, before its plan is passed by itself.
// A switch of four choices, and under it the line that says what follows. The words are the host's (realm/look_wait.py `LINES`); the page says them the same.
import { html } from "../html.js";
import { Switch } from "../orkui.js";
import { board } from "./store.js";
import { act } from "../shell/store.js";

export const LOOK_LABEL = "Give me time to look";
export const LOOKS = [["30m", "30 min"], ["2h", "2 h"], ["tonight", "until tonight"], ["none", "do not wait"]];
export const LOOK_LINES = {
  "30m": "If you do not look, it starts: you give every spec 30 minutes",
  "2h": "If you do not look, it starts: you give every spec 2 hours",
  tonight: "If you do not look, it starts: you give every spec until tonight",
  none: "A spec starts as soon as it is made",
};

export const lookWaitOf = (b) => (LOOKS.some(([id]) => id === b?.look_wait) ? b.look_wait : "2h");

export function LookWaitSetting() {
  const now = lookWaitOf(board.value);
  const pick = (id) => { if (id !== now) act("ideas.board_set", { look_wait: id }); };
  return html`<div class="shell-field" role="group" aria-label=${LOOK_LABEL} data-settings="look-wait"><span class="ok-font-label">${LOOK_LABEL}</span>
    <${Switch} label=${LOOK_LABEL} options=${LOOKS} value=${now} onPick=${pick} />
    <span class="ok-font-status ok-tone-muted" data-settings="look-wait-line">${LOOK_LINES[now]}</span></div>`;
}
