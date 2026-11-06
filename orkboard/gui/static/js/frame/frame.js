// The window as two parts (docs/specs/98-the-table-and-the-hand.md §7, decisions §145.1): the table (js/table/table.js `Table`) over the hand (js/hand/hand.js `Hand`), the page's only window. The top bar,
// the left column, the right column and the dialogs are gone: what was a dialog lies over the pane (frame/place.js), what was the drawer is the pane's one thing (frame/kinds.js). Nothing is drawn beside them.
import { html } from "../html.js";
import { Table } from "../table/table.js";
import { Hand } from "../hand/hand.js";
import { Column } from "../table/column.js";
import { columnOn, partiesNow } from "../table/data.js";
import { ReportPanel } from "../hand/logsbtn.js";           // the bug's panel and a crash's card, once on the page (spec 139 A.5)
import { CrashNote } from "../crashes.js";
import { over } from "./state.js";
import { uprightNow } from "./upright.js";
import { SetupWatch } from "../hand/setupcards.js";     // what the Orkmaster asks now, on the first open (spec 130 B.4)
import { laidNow, laying, useLaying } from "../table/laying.js";   // the window not yet laid, and the laying at Start (spec 130 C.6)
import { Edge, edgeOn } from "./edge.js";                 // the table's edge at the wide width: the ring, the discard, the die, the potions (spec 150 D)
import { FirstGoal, Room, roomOn } from "./firstopen.js";   // the first open as four cards in the dark room (spec 150 G)

const sheets = ["./frame.css", "../table/table.css", "../table/work.css", "../table/corners.css", "../table/made.css", "../table/cardwindow.css","../table/discard.css", "../table/portal.css", "../table/notice.css", "../table/ask.css", "../table/back.css", "../table/column.css", "../table/goalview.css", "../table/steps.css", "../table/presence.css", "../table/dayline.css", "../hand/hand.css", "../hand/mana.css", "../hand/handcard.css", "../hand/openedcard.css", "../hand/upright.css", "../hand/upmenu.css", "../hand/uplook.css", "./edge.css", "./firstopen.css"].map((p) => new URL(p, import.meta.url).href);
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
// One grid for the tabs, the Board and the hand (decisions §167.7): `--lanes` columns of one width, a party's each, then the tabs' end; the project's lane is the Orkmaster's column pinned at the window's left (table/column.js, spec 128 B,
// decisions §206.2) at the wide width, and at the narrow one the Board's first lane (its tab the first), counted in `--lanes`.
export function Frame() {
  const column = columnOn(), edge = edgeOn();
  useLaying();
  if (roomOn()) {                                                                    // the first open at the wide width: the dark room, nothing of the table, the hand or the edge but what its cards have laid (frame/firstopen.js)
    return html`<div class="frame fo-room" data-frame="1" data-laid="0" data-room="1" data-laying=${laying.value ? "1" : undefined}>
      <${Room} /><${SetupWatch} /><${CrashNote} /><${ReportPanel} />
    </div>`;
  }
  return html`<div class="frame" data-frame="1" data-laid=${laidNow() ? "1" : "0"} data-laying=${laying.value ? "1" : undefined} data-column=${column ? "1" : undefined} data-edge=${edge ? "1" : undefined} data-upright=${uprightNow.value ? "1" : undefined} data-over=${uprightNow.value && over.value ? "1" : undefined} style=${`--lanes:${partiesNow().length + (column ? 0 : 1)}`}>
    ${column && html`<aside class="frame-column" aria-label="The Orkmaster's goals"><${Column} /></aside>`}
    <div class="frame-table"><${Table} column=${column} /></div>
    <div class="frame-hand"><${Hand} /></div>
    ${edge && html`<${Edge} />`}
    <${SetupWatch} /><${FirstGoal} /><${CrashNote} /><${ReportPanel} />
  </div>`;
}
