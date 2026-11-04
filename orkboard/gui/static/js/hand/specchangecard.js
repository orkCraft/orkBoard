// A change to a spec asked of the Orkmaster (docs/specs/144-a-specs-wait-and-a-change-through-the-orkmaster.md D; decisions §224.4, §225.2–3; mockup docs/mockups/phone/goal-lens-v4.html): the person's words about a goal whose spec is made
// (the Orkmaster's bubble, table/ask.js *Change the spec*) go to the leaders whose sections they touch, and come back as **one card** for the goal. The row is `{kind: "spec_change", asker: "orkmaster", idea, id, said, status: "asking" | "ready" | "failed",
// text, agree: {ok, line}, parties: [{party, title, why, before, after: {tasks, lines}}], calls, usd_low, usd_high, low, reset, error}` (realm/spec_change.py). Its face is the hand's card (stopcard.js): the page sign, the Orkmaster's crowned head as its
// asker, the price as its gem, *<the join's line>* at its foot. Lifted:
//   - while `asking`: *Its leaders are rewriting*, and **Drop it** only;
//   - `ready`: the person's words, a tab a party (its head and name) with that leader's section *Now* and *Proposed*, the join's line (whether the sections agree), the cost's words (stopcard.js `Spend`), and **Accept and start** (the limits allow:
//     `ideas.spec_change_take`: every section and the person's decision written, each plan change taken) or *Accept · starts after the reset, Mon 09:00* (they run low), **Talk more** (the change is dropped and the Orkmaster's bubble opens on the
//     goal with the words kept) and **Drop it** (`ideas.spec_change_drop`: nothing changes);
//   - `failed`: its error, **Talk more** and **Drop it**.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Head } from "../orkui.js";
import { toast } from "../link.js";
import { act } from "../shell/store.js";
import { ORKMASTER, openTab, picked } from "../frame/state.js";
import { untilWords } from "../arena/arenawords.js";
import { openAsk } from "../table/ask.js";
import { Side } from "./changecard.js";
import { partyBy } from "./data.js";
import { way } from "./ways.js";

if (typeof document !== "undefined") {                                  // the sheet, once, as changecard.js links its own
  const href = new URL("./specchangecard.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const CROWN = { race: "peon", tier: "crown" };                          // the Orkmaster's head

/** The act that accepts, in the words that say what follows (decisions §225.3): *Accept and start* when the limits allow; *Accept · starts after the reset, Mon 09:00* when they run low (the reset as the potions say it). */
export function acceptWords(row) {
  if (!row?.low) return "Accept and start";
  const at = untilWords(row.reset);
  return at ? `Accept · starts after the reset, ${at}` : "Accept · starts after the reset";
}

/** The lifted card of a change to a spec asked of the Orkmaster. */
export function SpecChangeLifted({ s, close }) {
  const row = s.row || {}, parties = row.parties || [], [at, setAt] = useState(0), [busy, setBusy] = useState(false), by = partyBy();
  const asking = row.status === "asking", failed = row.status === "failed", mine = parties[Math.min(at, Math.max(0, parties.length - 1))] || null;
  const run = async (name, then) => {
    if (busy) return false;
    setBusy(true);
    try { const got = await act(name, { idea: row.idea, id: row.id, via: "hand" }); if (got) { then?.(got); close?.(); } return !!got; } finally { setBusy(false); }
  };
  const accept = () => run("ideas.spec_change_take", (got) => toast(got.starts === "reset" ? "Accepted: it starts after the reset." : got.starts === "now" ? "Accepted: it starts." : "Accepted: it starts by itself when you have had time to look."));
  const drop = () => run("ideas.spec_change_drop");
  const more = async () => {                                          // the Orkmaster's bubble again on the goal, the words kept
    const said = row.said;
    if (!(await run("ideas.spec_change_more"))) return;
    openTab(ORKMASTER);
    picked.value = row.idea;
    setTimeout(() => openAsk(ORKMASTER, null, said), 0);           // the tab's head is drawn first
  };
  return html`<div class="hand-way hand-change hand-spec" data-shape="spec" data-status=${row.status}>
    <p class="cap hand-change__said">You said: “${row.said}”</p>
    ${asking && html`<p class="body hand-way__words" role="status" data-spec="rewriting">Its leaders are rewriting</p>`}
    ${failed && html`<p class="body hand-way__words" role="alert">${row.error || row.text}</p>`}
    ${!asking && !failed && html`<div class="hand-spec__tabs" role="tablist" aria-label="The leaders' sections">${parties.map((p, i) => {
      const g = by[p.party] || null;
      return html`<button type="button" key=${p.party} role="tab" id=${`spec-tab-${p.party}`} class=${cls("ork-tab hand-spec__tab", { "is-open": i === at })} data-party=${p.party} aria-selected=${String(i === at)} aria-controls="spec-pane"
        onClick=${() => setAt(i)}>${g?.head && html`<${Head} race=${g.head.race} tier=${g.head.tier} />`}<span>${p.title || g?.name || p.party}</span></button>`;
    })}</div>
    ${mine && html`<div class="hand-spec__pane" role="tabpanel" id="spec-pane" aria-labelledby=${`spec-tab-${mine.party}`} data-party=${mine.party}>
      ${mine.why && html`<p class="body hand-way__words">${mine.why}</p>`}
      <div class="hand-change__ba"><${Side} label="Now" side=${mine.before} now=${true} /><${Side} label="Proposed" side=${mine.after} now=${false} /></div></div>`}
    ${row.agree?.line && html`<p class=${cls("cap hand-spec__agree", { "is-apart": row.agree.ok === false })} data-spec="agree">${row.agree.line}</p>`}`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      ${!asking && !failed && html`<button type="button" class="ork-btn primary" disabled=${busy} data-act="accept"
        title="Every leader's section and your decision are written, and the plan changes are taken" onClick=${accept}>${acceptWords(row)}</button>`}
      ${!asking && html`<button type="button" class="ork-btn" disabled=${busy} data-act="more" title="Asks the Orkmaster again, with your words kept" onClick=${more}>Talk more</button>`}
      <button type="button" class="ork-btn quiet" disabled=${busy} data-act="drop" title="Nothing changes" onClick=${drop}>Drop it</button>
    </div>
  </div>`;
}

// The face: the page sign, the price as its gem, the join's line as its foot; its asker is the Orkmaster's crowned head (decisions §225.2).
way("spec_change", {
  sign: "page",
  head: () => CROWN,
  foot: (s) => (s.row?.status === "asking" ? "Its leaders are rewriting" : s.row?.status === "failed" ? s.row.error || "No change came" : s.row?.agree?.line || s.row?.said || ""),
  price: (s) => {
    const r = s.row || {}, low = Number(r.usd_low), high = Number(r.usd_high);
    return r.status === "ready" && (low || high) ? { low, high, saves: false } : null;
  },
  Lifted: SpecChangeLifted,
});
