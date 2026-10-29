// The phone upright (docs/specs/103-the-phones-app-a-native-frame.md §1, decisions §174.1, §178.7): a narrow window under a touch pointer (`pointer: coarse`) is a phone held upright, and its first screen is the hand (hand/upright.js),
// with the top card's context above it. There is no upright table on a touch phone: the Board is shown on its side only. A narrow window with a fine pointer (a desktop's, VS Code's side bar) is not this: it keeps spec 94 §3's table
// over the hand. A phone on its side is a low window of 760 px or more, so the narrow width alone tells the two apart.
//
// *The Board* (`showBoard`) is the one place where the page asks for the table. In the native app the frame turns the screen to its side (spec 103 §4.4): it registers what does that with `onTurn(fn)` (re-exported by frame.js), and a
// press on *The Board* then calls it. In a browser nothing turns a web page, so the page says so in a status line, *Turn the phone on its side to see the Board* (`turnLine`), until the next press away or a few seconds go by.
import { signal } from "@preact/signals";

export const UPRIGHT = "(max-width: 759.98px) and (pointer: coarse)";
export const TURN_WORDS = "Turn the phone on its side to see the Board";
const LINE_MS = 5000;                                         // how long the line stays when nothing is pressed

const media = typeof matchMedia === "function" ? matchMedia(UPRIGHT) : null;
/** Whether the window is a phone held upright (narrow and a touch pointer): a signal, so a face that reads it redraws when the phone turns. */
export const uprightNow = signal(!!media?.matches);
media?.addEventListener?.("change", () => { uprightNow.value = media.matches; });

/** The line that says the Board is on the phone's side: `""` while it is not shown. */
export const turnLine = signal("");

let turner = null, timer = 0, away = null;

/** The native frame says how it turns the screen to its side: `fn()` returns anything but `false` when it did. Returns the way to take it back. */
export function onTurn(fn) {
  turner = typeof fn === "function" ? fn : null;
  return () => { if (turner === fn) turner = null; };
}

/** Takes the line away (a press away, the timer, the phone turned). */
export function clearTurnLine() {
  turnLine.value = "";
  clearTimeout(timer);
  if (away) { removeEventListener("pointerdown", away, true); removeEventListener("keydown", away, true); away = null; }
}

/** *The Board* was pressed upright: the native frame turns the phone; in a browser the page says that the phone is to be turned by hand. */
export function showBoard() {
  clearTurnLine();
  if (turner) {
    let got;
    try { got = turner(); } catch { got = false; }
    if (got !== false) return true;
  }
  turnLine.value = TURN_WORDS;
  timer = setTimeout(clearTurnLine, LINE_MS);
  setTimeout(() => {                                          // after this press: the next one away takes the line off
    if (!turnLine.value) return;
    away = () => clearTurnLine();
    addEventListener("pointerdown", away, true);
    addEventListener("keydown", away, true);
  }, 0);
  return false;
}
