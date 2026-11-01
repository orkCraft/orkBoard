// Work at night's words (docs/specs/121-the-day-the-morning-and-the-night.md §1, §4, §7.3; decisions §199.4): the setting's label and hint, the held plan's line and its two ways to start it by day. The host says them (`ideas.board`'s `night_words`,
// gui/ideas_board.py `night_words`, the night's hour said); a host that does not send them is answered in the same words from the Board's `night` (`01:00-07:00`). Pure: no template, no signal of its own.
import { board } from "../board/store.js";

const FALLBACK_NIGHT = "01:00-07:00";

/** The words with the night's hour said: `{label, hint, waits, now, now_sketch}`. `b`: the Board's snapshot (`ideas.board`). */
export function nightWordsOf(b = board.value) {
  const night = String(b?.night || FALLBACK_NIGHT), start = night.split("-")[0], own = b?.night_words && typeof b.night_words === "object" ? b.night_words : {};
  return {
    label: "Work at night",
    hint: `What you decide by day is built in the night's window (${night.replace("-", "–")}). Talk, hearings and sketches still run by day. A bug's short way, and anything you start with a press, starts at once.`,
    waits: `Waits for the night (${start})`,
    now: "Build it now",
    now_sketch: "Pick and build now",
    ...Object.fromEntries(Object.entries(own).filter(([, v]) => typeof v === "string" && v)),
  };
}

/** *Work at night* is on for the project (the Board's `work_at_night`). */
export const workAtNight = (b = board.value) => b?.work_at_night === true;
