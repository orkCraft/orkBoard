// The person's presence: **Here** or **Away**, the lamp's chain (`PresenceChain`, spec 161 G and K, decisions §271; before it the door of spec 139 C.2 and C.4, §246.4-§246.5): at the discard column's head on the desktop, small at the tabs' end
// under 760 px and small in the phone's top row (hand/uptop.js). A press sends `presence.set {here: !here}` and the snapshot that follows turns the chain (nothing is guessed here); the host's side is spec 139 C.1 (gui/board_host.py
// `presence` and `presence.set`, realm/hours.py). With no `presence` in the snapshot (an older host) there is no chain. The sheet is presence.css (orkUI's tokens only).
import { useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { town, command } from "../link.js";
import { HOURS_TITLE, HoursPanel, useLongPull } from "./presencehours.js";

/** The presence as the snapshot has it (`{here, until, held}`), or null from a host that does not say. */
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

/** A press: the other state, said to the host. A refusal is the host's toast; the chain keeps what the snapshot says. */
export async function pressDoor() {
  const p = presenceNow();
  if (!p) return;
  try { await command("presence.set", { here: !p.here }); } catch { /* the host's toast says why */ }
}

const reduced = () => !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** The lamp's chain (spec 161 G, decisions §271): orkUI's `.ork-chain` at the right of the discard column's head (lane.js; under 760 px, small, at the tabs' end), on one press: `presence.set {here: !here}`.
 *  Here it hangs at rest; Away it is `.is-pulled`. A press moves it once (`.is-tugging`, taken off at its animationend; at once under reduced motion: the class is never set). Its words stand beside it
 *  (*Here*, its line *until 23:00*, *· held*); `small` has no words and `aria-label` and `title` keep them (§271.5). With no `presence` in the snapshot there is no chain.
 *  `half` (the right column's head, spec 168 A4, decisions §285.2): orkUI's `.small` (6 × 29) with its words beside it; held down for a long pull (or pressed with Shift) it opens the person's hours (presencehours.js, spec 168 H2, decisions §283.31). */
export function PresenceChain({ small = false, half = false }) {
  const [tug, setTug] = useState(false), [hours, setHours] = useState(false), btn = useRef(null), p = presenceNow(), pull = useLongPull(half, () => setHours(true));
  if (!p) return null;
  const line = presenceLine(p), word = p.here ? "Here" : "Away", title = `${p.here ? HERE_TITLE : AWAY_TITLE}${line ? ` (${line})` : ""}${half ? `. ${HOURS_TITLE}.` : ""}`;
  const press = (e) => { if (pull.held(e)) return; if (!reduced()) setTug(true); pressDoor(); };
  return html`<button ref=${btn} type="button" ...${pull.props} class=${cls("presence-chain", { "is-away": !p.here, "is-small": small, "is-half": half })} aria-pressed=${String(p.here)} aria-label=${`${word}${line ? `, ${line}` : ""}`} title=${title} data-here=${String(p.here)} onClick=${press}>
    ${!small && html`<span class="presence-chain__words"><b class="presence-chain__word">${word}</b>${line && html`<span class="presence-chain__line">${line}</span>`}</span>`}
    <span class=${cls("ork-chain", { small: small || half, "is-pulled": !p.here, "is-tugging": tug })} aria-hidden="true" onAnimationEnd=${() => setTug(false)}></span>
  </button>${hours && html`<${HoursPanel} anchor=${btn.current} close=${() => setHours(false)} />`}`;
}
