// The Orkmaster's *Assets and files* tab (docs/specs/91-the-owners-list.md §3): Assets (assets.js, spec 88) with, at the top right, a two-way switch *Assets* / *Files*. *Files* is the Files pane
// as it was (shell/files.js: the project's tree, a file opened in the right column). The switch is two buttons, the pressed one marked (aria-pressed); the choice is kept while the page is.
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { FilesPane } from "../shell/files.js";
import { Assets } from "./assets.js";

const SWITCH = [["assets", "Assets"], ["files", "Files"]];
const side = signal("assets");                 // "assets" | "files"

export function AssetsAndFiles() {
  const on = side.value;
  return html`<div class="assets-and-files" data-side=${on}>
    <div class="assets-switch ork-tabs" role="group" aria-label="Show">
      ${SWITCH.map(([id, word]) => html`<button type="button" key=${id} class=${cls("ork-tab", { "is-on": id === on })} data-side=${id} aria-pressed=${String(id === on)} onClick=${() => { side.value = id; }}>${word}</button>`)}
    </div>
    ${on === "files" ? html`<div class="assets-files"><${FilesPane} /></div>` : html`<${Assets} />`}
  </div>`;
}
