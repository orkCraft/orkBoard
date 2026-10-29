// The phone (docs/specs/103-the-phones-app-a-native-frame.md §1, decisions §174.1, §180.1): a window under a touch pointer (`pointer: coarse`) is a phone, held upright (narrow) or on its side (a low window), and its one screen is
// the hand (hand/upright.js), with the top card's context above it. There is no Board on a phone for now (§180.1): upright or on its side the table is not drawn, only what is opened over the pane (a tool's story, a goal's way,
// the projects, Settings). A narrow window with a fine pointer (a desktop's, VS Code's side bar) is not this: it keeps spec 94 §3's table over the hand, and so does a wide window with a touch pointer that is not low (a tablet).
import { signal } from "@preact/signals";

export const UPRIGHT = "(pointer: coarse) and ((max-width: 759.98px) or (max-height: 499.98px))";

const media = typeof matchMedia === "function" ? matchMedia(UPRIGHT) : null;
/** Whether the window is a phone (a touch pointer, narrow or low): a signal, so a face that reads it redraws when the phone turns. */
export const uprightNow = signal(!!media?.matches);
media?.addEventListener?.("change", () => { uprightNow.value = media.matches; });
