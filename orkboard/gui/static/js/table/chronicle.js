// The chronicle over the pane (docs/specs/134-release-keeps-the-chronicle.md part B, decisions §238.3–§238.4): Release's past, a chapter a version, newest first, the newest open, each older one a line (*v0.3 · 28 Oct*) opened by a press;
// a search at its top; its finds by chapter, the others folded away. A goal's row opens the goal as it was and a decision's row its entry (chroniclerows.js). ← or Esc go back to Release's lens (the pane's own back). It decides nothing
// and writes nothing: every command it asks reads (`ideas.chronicle*`, gui/ideas_chronicle.py). Answers are keys and data; the words are said here (chroniclewords.js). Not on the phone (§238.6).
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { drawn } from "../frame/kinds.js";
import { openOver, tab } from "../frame/state.js";
import { mapName, partiesAll } from "./data.js";
import { Decision, GoalAsItWas } from "./chroniclerows.js";
import { DecisionRow, GoalRow, ask } from "./chronicleparts.js";
import { chapterName, dayWord } from "./chroniclewords.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as mapkit.js links its own
  const href = new URL("./chronicle.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const FIND_WAIT = 250;

/** Opens the chronicle over the pane from where it is pressed (Release's lens); `props`: `{goal}` or `{decision}` to land on one. */
export function openChronicle(props = {}) {
  openOver("chronicle", props, { title: mapName(tab.value, partiesAll()), key: "" }, "Chronicle");
}

/** A chapter: its head (the version and its day) pressed to open or fold it, and, open, its goals and the decisions of no goal. */
function Chapter({ c, open, onToggle, onGoal, onDecision, hit = false }) {
  const rows = c.goals || [], more = c.decisions || [];
  return html`<section class=${cls("chr-chapter", { "is-open": open })} data-chapter=${c.id} data-kind=${c.kind}>
    <h3 class="chr-chapter__hd"><button type="button" class="ork-row chr-chapter__btn" aria-expanded=${String(open)} onClick=${onToggle}>
      <${Icon} name=${open ? "chevron-down" : "chevron-right"} /><span class="chr-chapter__nm">${chapterName(c)}</span><span class="chr-chapter__day">${c.kind === "week" ? "" : dayWord(c.day)}</span></button></h3>
    ${open && html`<ul class="chr-rows">
      ${rows.map((g) => html`<${GoalRow} key=${g.idea} g=${g} found=${hit} onGoal=${onGoal} onDecision=${onDecision} />`)}
      ${more.map((d) => html`<${DecisionRow} key=${d.number} d=${d} onDecision=${onDecision} />`)}
      ${!rows.length && !more.length && c.goals && html`<li class="table-over__muted">Nothing is kept for it.</li>`}</ul>`}
  </section>`;
}

/** The search's finds: the chapters that have some. */
function Finds({ f, onGoal, onDecision }) {
  if (!f.chapters.length && !f.unreleased) return html`<p class="table-over__muted" data-finds="none">Nothing in the chronicle matches.</p>`;
  const un = f.unreleased && (f.unreleased.goals?.length || f.unreleased.decisions?.length) ? [{ id: "unreleased", kind: "unreleased", name: "Unreleased", day: "", ...f.unreleased }] : [];
  return html`<div class="chr-finds" data-finds=${f.found}>${[...un, ...f.chapters].map((c) => html`<${Chapter} key=${c.id} c=${c} open=${true} hit=${true} onToggle=${() => {}} onGoal=${onGoal} onDecision=${onDecision} />`)}
    ${f.more > 0 && html`<p class="table-over__muted">${f.more} more match. Add a word to narrow it.</p>`}</div>`;
}

function List({ onGoal, onDecision }) {
  const [d, setD] = useState(null), [err, setErr] = useState(""), [shown, setShown] = useState({}), [loaded, setLoaded] = useState({}), [q, setQ] = useState(""), [f, setF] = useState(null);
  useEffect(() => { let live = true; ask("ideas.chronicle", {}).then(([r, e]) => { if (live) { setD(r); setErr(e); } }); return () => { live = false; }; }, []);
  useEffect(() => {
    const want = q.trim();
    if (!want) { setF(null); return undefined; }
    let live = true;
    const id = setTimeout(() => ask("ideas.chronicle_find", { query: want }).then(([r, e]) => { if (live) { setF(r); setErr(e); } }), FIND_WAIT);
    return () => { live = false; clearTimeout(id); };
  }, [q]);
  const isOpen = (c) => shown[c.id] ?? c.open;
  const toggle = async (c) => {
    const now = !isOpen(c);
    setShown((s) => ({ ...s, [c.id]: now }));
    if (now && !c.goals && !loaded[c.id]) {                              // an older chapter is a line until it is pressed
      const [r, e] = await ask("ideas.chronicle_chapter", { id: c.id });
      if (r) setLoaded((l) => ({ ...l, [c.id]: r })); else { setErr(e); setShown((s) => ({ ...s, [c.id]: false })); }
    }
  };
  const chapters = d?.chapters || [];
  return html`<div class="chr">
    <div class="chr-search"><${Icon} name="search" /><input type="search" class="ork-field" aria-label="Search the chronicle" placeholder="Search the chronicle" value=${q} onInput=${(e) => setQ(e.currentTarget.value)} /></div>
    ${err && html`<p class="chr-err" role="alert">${err}</p>`}
    ${f && q.trim() ? html`<${Finds} f=${f} onGoal=${onGoal} onDecision=${onDecision} />`
      : d && html`<div class="chr-chapters">${chapters.map((c) => html`<${Chapter} key=${c.id} c=${loaded[c.id] ? { ...c, ...loaded[c.id] } : c} open=${isOpen(c)} onToggle=${() => toggle(c)} onGoal=${onGoal} onDecision=${onDecision} />`)}
        ${!chapters.length && html`<p class="table-over__muted" data-chronicle="empty">Nothing has gone through the portal yet.</p>`}</div>`}
  </div>`;
}

/** The face of kind `chronicle`: the list, or a goal as it was, or a decision. A press inside walks on and the quiet button above walks back to the list; the pane's ← leaves for the lens. */
export function Chronicle({ props }) {
  const [view, setView] = useState(props?.goal ? { goal: props.goal } : props?.decision ? { decision: props.decision } : null);
  const goal = (idea) => setView({ goal: idea }), decision = (number) => setView({ decision: number });
  return html`<div class="table-over__chronicle" data-view=${!view ? "list" : view.goal ? "goal" : "decision"}>
    ${view && html`<p class="chr-back"><button type="button" class="ork-btn quiet" onClick=${() => setView(null)}><${Icon} name="arrow-left" /> Chronicle</button></p>`}
    ${!view ? html`<${List} onGoal=${goal} onDecision=${decision} />`
      : view.goal ? html`<${GoalAsItWas} key=${view.goal} idea=${view.goal} onDecision=${decision} />`
      : html`<${Decision} key=${view.decision} number=${view.decision} onDecision=${decision} onGoal=${goal} />`}
  </div>`;
}

drawn("chronicle", Chronicle);
