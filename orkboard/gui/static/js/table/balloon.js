// The Orkmaster's balloon (docs/specs/168-the-window-played-as-a-card-games-table.md A6, decisions §283.9; before: the strip under the pane's title, decisions §177.2): at the wide width, where the Orkmaster's column is drawn, what the Orkmaster says unasked
// (the work moved to another AI tool, Orkboard mended or mending) rises from the column's crown over the start of the leaders' tabs. It starts at the column's right edge, so it never covers the project's name in the column's head; a tail points left
// to the crown. One at a time: the newest of the news (notice.js `useNotes`: the rules for when each shows and its dismissal are that module's, a day at most). A polite live region that never takes the focus; × puts it away. Its only act, *Show*, waits
// for news that is about a goal (none of today's is). Narrower, where the column is not drawn, the strip of notice.js stays.
import { html } from "../html.js";
import { Icon } from "../orkui.js";
import { inventory, over } from "../frame/state.js";
import { laidNow } from "./laying.js";
import { useNotes } from "./notice.js";

export function Balloon() {
  const notes = useNotes(), n = notes[notes.length - 1];
  if (!n || over.value || inventory.value !== null || !laidNow()) return null;      // as the strip: not while the table is bare or something lies over the pane (the inventory, a form, Play)
  return html`<div class="ork-frame table-balloon" role="status" aria-live="polite" key=${n.key} data-balloon=${n.kind} data-at=${n.at || undefined}>
    <p class="table-balloon__line">${n.text}</p>
    ${n.put && html`<button type="button" class="ork-btn quiet table-balloon__x" aria-label="Dismiss" title="Dismiss" onClick=${n.put}><${Icon} name="close" /></button>`}
  </div>`;
}
