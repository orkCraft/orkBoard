// The Orkmaster's deal on the desktop (docs/specs/75-parties-fitted-to-the-project.md §5, docs/specs/91-the-owners-list.md §7): what a preset's card in New party says of its why. Pure functions.

/** What a deal card says of its why: *3 flags wait and no party releases them*, *No party judges small ideas yet*, *You have one* (muted). "" for none. */
export function whyWords(entry) {
  if (!entry) return "";
  if (entry.why === "flags_wait") return entry.n === 1 ? "1 flag waits and no party releases it" : `${entry.n} flags wait and no party releases them`;
  if (entry.why === "no_pitches") return "No party judges small ideas yet";
  if (entry.why === "have") return "You have one";
  return "";
}

/** A preset's entry in the deal, or null (an older host has no deal). */
export const dealEntry = (deal, id) => (deal || []).find((d) => d.id === id) || null;
