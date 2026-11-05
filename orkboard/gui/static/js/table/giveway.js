// How *At work · later* gives way to a short window (docs/specs/147-one-card-four-corners.md part B.5, decisions §251.4): the Orkmaster's column never scrolls, and only this pile gives way (the fan and the deck keep their height whatever they hold), in three steps:
// **1.** every card behind the front shows its **foot** (26 px: who, how much) while the pile fits; **2.** then the cards behind show a thin **edge** (3 px), the furthest first; **3.** then the **pile sinks** under the hand's rim, as the hand's cards go under the window's edge: the cards behind lie
// at the front card's right, 3 px more each, and the rim falls between two lines of the front card (its top 32 px, then a line of 20 px), never through one. Pure: the page measures (`column.js`), this decides.
export const FOOT = 26, EDGE = 3, TOP = 32, LINE = 20;

/** `room`: the height the pile may take (px); `front`: the front card's height (202); `behind`: how many cards lie behind it.
 *  Returns `{ steps, sunk, push }`: `steps[i]` is how far card i + 1 lies below card i (26 a foot, 3 an edge; ignored once `sunk`); `sunk` the px of the front card under the rim (0 while the pile fits), `push` how far of it is only to land the rim between two lines (the pile moves down by it). */
export function giveWay({ room, front, behind }) {
  const n = Math.max(0, Math.floor(behind) || 0), steps = Array.from({ length: n }, () => FOOT);
  const height = () => front + steps.reduce((a, b) => a + b, 0);
  for (let i = n - 1; i >= 0 && height() > room; i--) steps[i] = EDGE;               // the furthest card's foot gives way first
  if (height() <= room) return { steps, sunk: 0, push: 0 };
  steps.fill(EDGE);
  const shown = Math.max(0, Math.min(front, room)), kept = shown < TOP ? 0 : TOP + LINE * Math.floor((shown - TOP) / LINE), push = shown - kept;
  return { steps, sunk: front - shown + push, push };
}
