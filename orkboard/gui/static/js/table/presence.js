// The door as the person: **Here** or **Away** (docs/specs/139-the-die-the-door-and-the-bug.md C.2 and C.4, decisions §246.4–§246.5; the look: docs/mockups/die-and-door/index.html section 4; the host's side is spec 139 C.1,
// gui/board_host.py `presence` and `presence.set`, realm/hours.py). orkUI's `.ork-door` (design-system/orkui/door/README.md) stands at the top row's end, where *Stop all* stood (it moved to the die): **open** (`is-open`) with the word *Here*
// and, under it, its line (*until 23:00*, the hours' next edge), **shut** with *Away* (*until 19:00*, the word muted); *· held* is appended while the press of the door holds the other state till the edge. The word is in the pixel face
// as the tabs' words are, its line in the caption face. The door has no words inside (it is `aria-hidden`): the button carries them, `aria-pressed` is *here*, and `title` says what a press does. A press sends `presence.set {here: !here}`
// and the snapshot that follows turns the door (nothing is guessed here). With no `presence` in the snapshot (an older host) there is no door. Under 760 px (a narrow desktop window) the door is the small one with its word alone;
// the phone's top row (hand/uptop.js) has `PresenceDoor` with `small` too. The sheet is presence.css (orkUI's tokens only).
import { html, cls } from "../html.js";
import { town, command } from "../link.js";

/** The door's state as the snapshot has it (`{here, until, held}`), or null from a host that does not say. */
export function presenceNow() {
  const p = town.value?.presence;
  return p && typeof p.here === "boolean" ? p : null;
}

/** The hours' edge as a clock time: *23:00* from the host's local ISO time (a stamp with no time says nothing). */
export function untilWord(until) {
  const m = /T(\d\d:\d\d)/.exec(String(until || ""));
  return m ? m[1] : "";
}

/** What the press does (the title). */
export const HERE_TITLE = "You are here: questions come as they arise. Press to be away.";
export const AWAY_TITLE = "You are away: steps that ask wait for your hours. Press to be here.";

/** The line under the word: *until 23:00*, *until 19:00 · held*, *held* alone when the edge is not known. */
export function presenceLine(p) {
  const at = untilWord(p.until);
  return [at && `until ${at}`, p.held && "held"].filter(Boolean).join(" · ");
}

/** A press: the other state, said to the host. A refusal is the host's toast; the door keeps what the snapshot says. */
export async function pressDoor() {
  const p = presenceNow();
  if (!p) return;
  try { await command("presence.set", { here: !p.here }); } catch { /* the host's toast says why */ }
}

/** The door and its word. `small`: orkUI's small door and the word alone (the phone's top row; the line is in the title and the label). */
export function PresenceDoor({ small = false }) {
  const p = presenceNow();
  if (!p) return null;
  const line = presenceLine(p), word = p.here ? "Here" : "Away", title = `${p.here ? HERE_TITLE : AWAY_TITLE}${line ? ` (${line})` : ""}`;
  return html`<button type="button" class=${cls("presence-door", { "is-away": !p.here, "is-small": small })} aria-pressed=${String(p.here)} aria-label=${`${word}${line ? `, ${line}` : ""}`} title=${title} data-here=${String(p.here)} onClick=${pressDoor}>
    <span class=${cls("ork-door", { "is-open": p.here, small })} aria-hidden="true"></span>
    <span class="presence-door__words"><b class="presence-door__word">${word}</b>${!small && line && html`<span class="presence-door__line">${line}</span>`}</span>
  </button>`;
}
