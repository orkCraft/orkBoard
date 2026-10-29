// Drop a goal from its card (docs/specs/107-what-the-owners-day-said.md §4, decisions §182.3): a **…** on a goal's cards (the Orkmaster's lane, the line, the route card lifted, the goal's face over the pane) with one item,
// **Drop this goal…** (orkUI's `trash`). It asks in place — *Drop this goal?*, what goes and what stays, **Keep it** · **Drop it** — and drops: `ideas.stop` first when the goal's tasks run, then `ideas.drop` (the host
// refuses while the Orkmaster is reading it: said in the card). `where`: "card" (over the lower right of a card, opening upward), "head" (a face's header, opening downward), "inline" (in the flow of a lifted card's or a back's body).
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command } from "../link.js";
import { mapData, refreshShell } from "../shell/store.js";
import { lower, picked, pick } from "../frame/state.js";
import { Menu } from "./menu.js";

/** What the host's refusal says in the person's words: the keeper busy with the goal is the Orkmaster reading it. */
export function refusalWords(text) {
  const said = String(text || "").trim();
  return /keeper is busy/i.test(said) ? "The Orkmaster is reading it: drop it when it is done" : said || "It could not be dropped";
}

/** Whether a goal has tasks running, so that dropping it stops its work first. */
export const worksNow = (slug) => ((mapData.value?.nodes || []).find((n) => n.slug === slug)?.tasks || []).some((t) => t.state === "running" || t.state === "testing");

export function GoalMenu({ slug, where = "inline" }) {
  const [asking, setAsking] = useState(false), [busy, setBusy] = useState(false), [said, setSaid] = useState(""), box = useRef(), keep = useRef();
  const works = worksNow(slug);
  useEffect(() => { if (asking) keep.current?.focus(); }, [asking]);
  const close = () => { setAsking(false); setSaid(""); box.current?.querySelector(".table-menu__btn")?.focus(); };
  const drop = async () => {
    setBusy(true);
    setSaid("");
    try {
      if (works) await command("ideas.stop", { slug }, true);
      await command("ideas.drop", { slug }, true);
    } catch (e) {
      setSaid(refusalWords(e?.message));
      setBusy(false);
      return;
    }
    if (picked.value === slug) pick(slug);                    // the goal is gone: what was picked is put down
    lower();
    await refreshShell();
  };
  const keys = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); } };
  return html`<span class=${cls("table-dropper", `is-${where}`)} ref=${box} data-dropper=${slug}>
    <${Menu} label="This goal's menu" items=${[["Drop this goal…", () => { setSaid(""); setAsking(true); }, false, "trash"]]} />
    ${asking && html`<div class="ork-frame table-drop" role="alertdialog" aria-label="Drop this goal?" aria-describedby=${`drop-${slug}`} onKeyDown=${keys}>
      <h3 class="table-drop__title">Drop this goal?</h3>
      <p class="table-drop__text" id=${`drop-${slug}`}>Its page and its plan go; what it spent stays counted.${works ? " Its work stops first." : ""}</p>
      ${said && html`<p class="table-drop__said is-danger" role="alert">${said}</p>`}
      <div class="table-drop__acts">
        <button type="button" class="ork-btn" ref=${keep} disabled=${busy} onClick=${close}>Keep it</button>
        <button type="button" class="ork-btn danger" disabled=${busy} onClick=${drop}>Drop it</button>
      </div>
    </div>`}
  </span>`;
}
