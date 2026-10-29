// The window as two parts (docs/specs/98-the-table-and-the-hand.md §7, decisions §145.1): the table (js/table/table.js `Table`) over the hand (js/hand/hand.js `Hand`), the page's only window. The top bar,
// the left column, the right column and the dialogs are gone: what was a dialog lies over the pane (frame/place.js), what was the drawer is the pane's one thing (frame/kinds.js). Nothing is drawn beside them.
import { html } from "../html.js";
import { Table } from "../table/table.js";
import { Hand } from "../hand/hand.js";
import { partiesNow } from "../table/data.js";
import { over } from "./state.js";
import { uprightNow } from "./upright.js";

const sheets = ["./frame.css", "../table/table.css", "../table/work.css", "../table/discard.css", "../table/portal.css", "../table/notice.css", "../table/ask.css", "../hand/hand.css", "../hand/mana.css", "../hand/upright.css"].map((p) => new URL(p, import.meta.url).href);
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

// A touch phone (frame/upright.js, upright or on its side) shows the hand as its one screen and the table only as a thing opened over the pane (a limit's story, a goal's way, the settings): `data-upright`, `data-over` (upright.css).
// One grid for the tabs, the Board and the hand (decisions §167.7): `--lanes` columns of one width, the first the project's, then a party's each, then the tabs' end.
export function Frame() {
  return html`<div class="frame" data-frame="1" data-upright=${uprightNow.value ? "1" : undefined} data-over=${uprightNow.value && over.value ? "1" : undefined} style=${`--lanes:${partiesNow().length + 1}`}>
    <div class="frame-table"><${Table} /></div>
    <div class="frame-hand"><${Hand} /></div>
  </div>`;
}
