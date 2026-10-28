// Tech's map: the System as read today (docs/specs/98-the-table-and-the-hand.md §3.4), `arena/systemarch.js`'s `Lens` as it is, inside the pane — its containers, their links, the parts in layers, the reveal of what
// changed. *Feature modules* is gone from the tabs: one map a tab. What today's System does on a press (a part or a link opened in the old drawer) is the table's now: a press on a part or a link is
// caught here and lifts that card where it lies and turns it over (card.js `Lifted`); its back is today's part pane (`PartView`, `LinkView`) with **Open** on it. The old modules are imported, never changed.
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";
import { lift, lifted, openOver, pick } from "../frame/state.js";
import { Lens, LinkView } from "../arena/systemarch.js";
import { PartView, useSystem, shownSys } from "../arena/systemmap.js";
import { litKey, partKey, linkKey } from "./card.js";

/** The System of a party the Architect leads. A press on a part or on a link's name lifts its card (the old drawer is not drawn in the window as two parts). */
export function SystemPane({ g }) {
  const sys = useSystem(true, g.slug);
  const caught = (e) => {
    const part = e.target.closest?.(".sys-part[data-part]"), link = e.target.closest?.(".arch-link[data-link]");
    const to = part ? partKey(g.slug, part.dataset.part) : link ? linkKey(g.slug, link.dataset.link) : "";
    if (!to) return;
    e.stopPropagation();                                                     // the old modules would open it in the drawer
    e.preventDefault();
    litKey.value = "";
    lift(lifted.value === to ? "" : to);
  };
  if (sys.none) return html`<div class="table-sys" data-state="none"></div>`;
  return html`<div class="table-sys" onClickCapture=${caught}><${Lens} sys=${sys} party=${g.slug} tab="system" /></div>`;
}

/** The back of a part of the System: today's part pane (its files, *Uses*, *Used by*, its changes since the last look and their goals), **Open** on it. What is pressed inside it is the table's:
 *  a file opens over the pane, a part under *Uses* lifts in turn, a goal is picked. */
export function PartBack({ party, path, mapName }) {
  const [files, setFiles] = useState([]);
  const since = shownSys.value?.party === party ? shownSys.value?.doc?.since || "" : "";
  useEffect(() => {
    let live = true;
    setFiles([]);
    command("ideas.system_part", { path, party, ...(since ? { since } : {}) }, true).then((r) => { if (live && r && !r.error) setFiles(r.files || []); }).catch(() => {});
    return () => { live = false; };
  }, [path, party, since]);
  const from = { title: mapName, key: partKey(party, path) };
  const caught = (e) => {
    const file = e.target.closest?.(".sys-side__files li"), part = e.target.closest?.(".sys-side__part[data-part]"), goal = e.target.closest?.(".sys-change__goal[data-goal]");
    if (file) { e.stopPropagation(); openOver("file", { path: file.title || file.textContent.trim() }, from, file.title || file.textContent.trim()); }
    else if (part) { e.stopPropagation(); e.preventDefault(); lift(partKey(party, part.dataset.part)); }
    else if (goal) { e.stopPropagation(); e.preventDefault(); pick(goal.dataset.goal); }
  };
  return html`<div class="table-back__part" onClickCapture=${caught}>
    <${PartView} p=${{ kind: "part", path, slug: party }} />
    <div class="table-back__acts">${files.length > 0 && html`<button type="button" class="ork-btn table-back__open" title=${files[0]}
      onClick=${() => openOver("file", { path: files[0] }, from, files[0])}>Open</button>`}</div>
  </div>`;
}

/** The back of a link between two containers: its routes and events (today's link pane). */
export function LinkBack({ party, link }) {
  return html`<${LinkView} p=${{ kind: "link", slug: party, path: link }} />`;
}
