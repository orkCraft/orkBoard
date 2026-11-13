// A goal's wait on its back (docs/specs/120-a-goal-heard-and-thrown-to-a-side.md §6.3–§6.4, decisions §198.8): while the goal waits to start by itself the seal's ring of runes is the wait: it fills clockwise from the rune in eight steps, its share the page's
// `--ork-sigil-share` (orkUI's `.ork-sigil.is-waiting`, 0.28.0, lights the ring from it, rounded down to eighths; back.css only gives the lit runes the goal's colour). A leaf: the phone's piles (piles.js) read it.

export const STEPS = 8;                                    // the ring fills in eight steps over the wait (§187.4's rite, slowed)

/** The share of the wait gone, `1 - left/seconds`, in eighths (0 to 1): the ring stands where its step is. */
export function shareOf(ripe) {
  const total = Number(ripe?.seconds) || 0, left = Number(ripe?.left_s);
  if (!(total > 0) || !Number.isFinite(left)) return 0;
  return Math.min(STEPS, Math.max(0, Math.ceil((1 - left / total) * STEPS - 1e-9))) / STEPS;
}

/** *4 min*, *40 s*: the time left of a wait, rounded up (a minute is always shown whole). */
export function leftWords(left_s) {
  const s = Math.max(0, Math.ceil(Number(left_s) || 0));
  return s >= 60 ? `${Math.ceil(s / 60)} min` : `${Math.max(1, s)} s`;
}

