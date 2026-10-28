// The window as two parts (docs/specs/98-the-table-and-the-hand.md §7, decisions §145.1): the table (js/table/table.js `Table`)
// over the hand (js/hand/hand.js `Hand`). Until spec 98 E makes it the window, the shell draws it only when the page is opened
// with `?frame=1` (shell.js), so parts C and D are built and tested on the real page before the old window goes. Each part is
// loaded on its own: one not built yet is a quiet line in its place. Written by the lead.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";

const sheets = ["./frame.css", "../table/table.css", "../hand/hand.css"].map((p) => new URL(p, import.meta.url).href);
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

export const FRAME = typeof location !== "undefined" && new URLSearchParams(location.search).get("frame") === "1";

function usePart(path, name) {
  const [part, setPart] = useState(null);
  useEffect(() => {
    let live = true;
    import(path).then((m) => { if (live) setPart(() => m[name]); }).catch(() => { if (live) setPart(() => () => null); });
    return () => { live = false; };
  }, []);
  return part;
}

export function Frame() {
  const Table = usePart("../table/table.js", "Table"), Hand = usePart("../hand/hand.js", "Hand");
  return html`<div class="frame" data-frame="1">
    <div class="frame-table">${Table ? html`<${Table} />` : null}</div>
    <div class="frame-hand">${Hand ? html`<${Hand} />` : null}</div>
  </div>`;
}
