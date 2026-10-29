// The microphone on the blank card (docs/decisions.md §125, docs/specs/103 §1.1): pressed, it listens and writes what it hears into the field as it comes; a press again stops it. It never sends: the words stay to be read and corrected.
// There is no button where there is no way to recognise (§125.3): a browser with no speech recognition shows none, and the keyboard's own dictation still writes into the field. The voice goes where the phone's own dictation sends it;
// nothing is recorded or kept here (the button's tip says so). While it listens the signal `listening` is true (the button is pressed, its edge in the signal's colour).
import { signal } from "@preact/signals";
import { toast } from "../link.js";
import { fieldOpen, fieldText } from "./state.js";

const Speech = typeof window !== "undefined" ? window.SpeechRecognition || window.webkitSpeechRecognition : null;
export const canSpeak = !!Speech;
export const listening = signal(false);
/** What the microphone's tip says before the first use: where the voice goes, and that nothing is kept or sent as sound. */
export const VOICE_TIP = "Speak the goal: the phone’s own dictation writes it into the field. Nothing is recorded, and nothing is sent until you send it";

let rec = null;

/** Starts listening, or stops when it is. The words are added to what the field holds. */
export function toggleVoice() {
  if (!Speech) return;
  if (rec) { rec.stop(); return; }
  const base = fieldText.value ? `${fieldText.value.replace(/\s+$/, "")} ` : "";
  const r = new Speech();
  r.continuous = true;
  r.interimResults = true;
  r.lang = (typeof navigator !== "undefined" && navigator.language) || "en-US";
  r.onresult = (e) => { let said = ""; for (const x of e.results) said += x[0]?.transcript || ""; fieldText.value = `${base}${said}`.replace(/\s+$/, ""); };
  r.onerror = (e) => {
    if (e.error === "not-allowed" || e.error === "service-not-allowed") toast("Orkboard may not use the microphone: allow it in the phone’s settings for this browser.", "warning");
    else if (e.error !== "no-speech" && e.error !== "aborted") toast("Speech stopped: type it, or use the keyboard’s microphone.", "warning");
  };
  r.onend = () => { rec = null; listening.value = false; };
  try {
    rec = r;
    listening.value = true;
    r.start();
    fieldOpen.value = true;
  } catch {
    rec = null;
    listening.value = false;
    toast("Speech could not start: type it, or use the keyboard’s microphone.", "warning");
  }
}
