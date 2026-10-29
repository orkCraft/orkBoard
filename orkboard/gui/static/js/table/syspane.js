// Tech's map: the System as read today (docs/specs/98-the-table-and-the-hand.md §3.4), `arena/systemarch.js`'s `Lens` as it is, inside the pane — its containers, their links, the parts in layers, the reveal of what
// changed. *Feature modules* is gone from the tabs: one map a tab. A press on a part or a link lifts that card where it lies and turns it over (arena/systemmap.js `openPart`, arena/systemarch.js; card.js `Lifted`); its back is today's part pane (`PartView`, `LinkView`) with **Open** on it.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { command } from "../link.js";
import { lift, openOver, pick, partKey } from "../frame/state.js";
import { Lens, LinkView } from "../arena/systemarch.js";
import { PartView, useSystem, shownSys } from "../arena/systemmap.js";

/** System's parts are pickable (spec 102 §6, picking.js): a part's id is its path, its group its container (the *Shared* column its own). The page draws the parts (arena/), so each is stamped with the
 *  attributes a card of any map carries; the stamp is renewed whenever the System is drawn again. */
export function stampParts(root) {
  const set = (el, k, v) => { if (el.getAttribute(k) !== v) el.setAttribute(k, v); };
  for (const b of root.querySelectorAll(".sys-part[data-part]")) {
    if (b.closest(".is-gone") || b.getAttribute("aria-hidden") === "true") { b.removeAttribute("data-pick-id"); continue; }
    const col = b.closest(".arch-col"), shared = !!col?.classList.contains("arch-shared");
    set(b, "data-pick-map", "system");
    set(b, "data-pick-id", b.dataset.part);
    set(b, "data-pick-name", b.dataset.part);
    set(b, "data-pick-group", shared ? "shared" : col?.dataset.container || "");
    set(b, "data-pick-group-name", shared ? "Shared" : col?.getAttribute("aria-label") || "");
  }
}

/** The System of a party the Architect leads. */
export function SystemPane({ g }) {
  const sys = useSystem(true, g.slug), root = useRef();
  useLayoutEffect(() => {
    const el = root.current;
    if (!el) return undefined;
    stampParts(el);
    const watch = new MutationObserver(() => stampParts(el));
    watch.observe(el, { subtree: true, childList: true });
    return () => watch.disconnect();
  }, [sys.none]);
  if (sys.none) return html`<div class="table-sys" data-state="none" ref=${root}></div>`;
  return html`<div class="table-sys" ref=${root}><${Lens} sys=${sys} party=${g.slug} tab="system" /></div>`;
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
