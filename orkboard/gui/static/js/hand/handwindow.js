// The window of a stop's card (docs/specs/148-a-window-on-every-card.md part B.1, B.5, decisions §252): what the work made (its task's `craft_made`), else the goal's first picture (`stop.node.picture`, the host's thumbnail), else nothing here — the card keeps its words where they
// were (the hand's under the cut, the opened card's body). A fork whose two sides both have a picture shows them side by side. The frame and the choice are table/cardwindow.js's.
import { html } from "../html.js";
import { CardWindow, windowOf } from "../table/cardwindow.js";

/** What a stop's window is made of: `{made, picture, name}` (`made`: the task's `craft_made`, `picture`: its goal's first picture, a URL or ""). */
export const windowOfStop = (s) => ({ made: s.task?.craft_made, picture: s.node?.picture || "", name: s.node?.short || s.node?.title || s.title || "" });

/** The two pictures of a fork's sides, when both have one; else []. */
export function sidePictures(s) {
  const sides = (s.row?.sides || []).slice(0, 2).map((x) => (typeof x?.picture === "string" ? x.picture.trim() : ""));
  return sides.length === 2 && sides.every(Boolean) ? sides : [];
}

/** Whether the stop has a window to draw (`made` or a picture, or a fork's two): its words are drawn where they were when it has not. */
export const hasWindow = (s) => sidePictures(s).length === 2 || windowOf(windowOfStop(s)).kind !== "none";

/** The window of a stop `s`; `h`: its height in px where the place gives one (else its sheet's). */
export function StopWindow({ s, h }) {
  const sides = sidePictures(s);
  if (sides.length === 2) return html`<span class="hand-win-pair" data-window="pair">${sides.map((url, i) => html`<${CardWindow} key=${i} of=${{ picture: url, name: s.row?.sides?.[i]?.party || "" }} h=${h} />`)}</span>`;
  return html`<${CardWindow} of=${windowOfStop(s)} h=${h} />`;
}
