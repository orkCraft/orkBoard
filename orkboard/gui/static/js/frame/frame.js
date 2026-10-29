// The window as two parts (docs/specs/98-the-table-and-the-hand.md §7, decisions §145.1): the table (js/table/table.js `Table`) over the hand (js/hand/hand.js `Hand`), the page's only window. The top bar,
// the left column, the right column and the dialogs are gone: what was a dialog lies over the pane (frame/place.js), what was the drawer is the pane's one thing (frame/kinds.js). Nothing is drawn beside them.
import { html } from "../html.js";
import { Table } from "../table/table.js";
import { Hand } from "../hand/hand.js";
import { partiesNow } from "../table/data.js";

const sheets = ["./frame.css", "../table/table.css", "../table/discard.css", "../hand/hand.css", "../hand/mana.css"].map((p) => new URL(p, import.meta.url).href);
if (typeof document !== "undefined") {
  for (const href of sheets) {
    if (!document.querySelector(`link[href="${href}"]`)) {
      const link = document.createElement("link");
      link.rel = "stylesheet";
      link.href = href;
      document.head.appendChild(link);
    }
  }
}

// One grid for the tabs, the Board and the hand (decisions §167.7): `--lanes` columns of one width, the first the project's, then a party's each, then the tabs' end.
export function Frame() {
  return html`<div class="frame" data-frame="1" style=${`--lanes:${partiesNow().length + 1}`}>
    <div class="frame-table"><${Table} /></div>
    <div class="frame-hand"><${Hand} /></div>
  </div>`;
}
