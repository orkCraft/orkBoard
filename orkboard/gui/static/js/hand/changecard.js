// A change asked of a leader (docs/specs/128-the-orkmasters-column-and-a-goal-at-every-leader.md E; decisions §206.5; mockup docs/mockups/goal-card/ `[data-dec]`): the person's words to a leader about a goal that is agreed or at work (the bubble's
// *Make it a change*, table/ask.js) come back as a decision in the hand. The row is `{kind: "leader_change", idea, id, goal/party (the leader's party: the card lies in its lane), part, said, shape: "plan" | "looks", status: "ready" | "failed",
// text, why, before, after: {tasks: [{id, title, short, op}], lines: [text]}, looks: [{key, name, why, lines}], usd_low, usd_high, error}` (realm/leader_change.py). Its face is the hand's card (stopcard.js): the page sign, the leader's head as its asker,
// the price as its gem (ways.js `price`), *<the words>* at its foot. Lifted:
//   - a plan: **Now** and **Proposed** side by side (the party's tasks not started, a changed task marked ~, an added + and a dropped −, then its lines of what the goal will change), the cost's words under them (stopcard.js `Spend`), and
//     **Accept** (`ideas.change_take`: the runner takes the plan change for its tasks not started, the party's lines are written into its section of the spec and the person's decision into the goal's Decisions), **Talk more** (the change is dropped
//     and the bubble opens again on the leader's tab with the part and the words kept) and **Keep the spec** (`ideas.change_keep`: nothing changes);
//   - Design's three looks: each a choice of its own (a name, its line, its lines of the change), **Let <Design> decide** (the leader's first) and **Keep the spec**;
//   - a change that did not come (`status: "failed"`): its error, **Talk more** and **Keep the spec**.
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { toast } from "../link.js";
import { act } from "../shell/store.js";
import { openTab, picked } from "../frame/state.js";
import { changeToast } from "../arena/arenawords.js";
import { openAsk } from "../table/ask.js";
import { way } from "./ways.js";
import { useState } from "preact/hooks";

if (typeof document !== "undefined") {                                  // the sheet, once, as frame.js links the others
  const href = new URL("./changecard.css", import.meta.url).href;
  if (!document.querySelector(`link[href="${href}"]`)) {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }
}

const MARK = { change: "~", add: "+", drop: "−" };
const LINE = /^(new|changed|gone)\s+/i;
const SIGN = { new: "+", changed: "~", gone: "−" };

/** A line of what the goal will change as the card says it: `changed Results — note` is `~ Results — note`, `new` `+`, `gone` `−`; any other line as it is. */
export const lineWords = (text) => { const m = LINE.exec(String(text || "")); return m ? `${SIGN[m[1].toLowerCase()]} ${String(text).slice(m[0].length)}` : String(text || ""); };

/** A task as a line: its name (the short one when it has one), marked when the change touches it. */
const taskName = (t) => t.short || t.title;

/** One side of Now · Proposed. */
export function Side({ label, side, now }) {
  const tasks = side?.tasks || [], lines = side?.lines || [];
  return html`<div class="hand-change__side" data-side=${now ? "now" : "proposed"}><span class="ork-label hand-change__lab">${label}</span>
    ${tasks.length > 0 && html`<ul class="hand-change__list" aria-label=${`${label}: its tasks`}>${tasks.map((t, i) => html`<li key=${`${t.id}${i}`} class=${cls("hand-change__task", { "is-gone": t.op === "drop" && now })} data-op=${t.op || undefined}>
        <span class="hand-change__mark" aria-hidden="true">${MARK[t.op] || ""}</span><span>${taskName(t)}</span></li>`)}</ul>`}
    ${lines.length > 0 && html`<ul class="hand-change__list hand-change__lines" aria-label=${`${label}: what the goal will change`}>${lines.map((l, i) => html`<li key=${i} class="cap">${lineWords(l)}</li>`)}</ul>`}
    ${!tasks.length && !lines.length && html`<p class="cap hand-change__none">Nothing yet</p>`}</div>`;
}

/** The lifted card of a change asked of a leader. */
export function ChangeLifted({ s, close }) {
  const row = s.row || {}, party = row.party || s.g?.slug || "", who = s.party?.name || "The leader", [busy, setBusy] = useState(false);
  const done = (got) => { if (got) { toast(row.shape === "looks" ? `${who} took the look` : changeToast(got)); close?.(); } };
  const take = async (patch = {}) => {
    if (busy) return;
    setBusy(true);
    try { done(await act("ideas.change_take", { idea: row.idea, id: row.id, via: "hand", ...patch })); } finally { setBusy(false); }
  };
  const keep = async () => {
    if (busy) return false;
    setBusy(true);
    try { const got = await act("ideas.change_keep", { idea: row.idea, id: row.id, via: "hand" }); if (got) close?.(); return !!got; } finally { setBusy(false); }
  };
  const more = async () => {                                          // the bubble again on the leader's tab, the part and the words kept
    if (!(await keep())) return;
    openTab(party);
    picked.value = row.idea;
    setTimeout(() => openAsk(party, row.part ? { id: row.part, name: row.part } : null, row.said), 0);       // the tab's head is drawn first
  };
  const failed = row.status === "failed", looks = row.shape === "looks" && !failed;
  return html`<div class="hand-way hand-change" data-shape=${row.shape} data-status=${row.status}>
    <p class="cap hand-change__said">You said: “${row.said}”${row.part ? html` · <span class="hand-change__part"><${Icon} name="map" /> ${row.part}</span>` : null}</p>
    ${failed && html`<p class="body hand-way__words" role="alert">${row.error || row.text}</p>`}
    ${!failed && row.why && html`<p class="body hand-way__words">${row.why}</p>`}
    ${!failed && !looks && html`<div class="hand-change__ba"><${Side} label="Now" side=${row.before} now=${true} /><${Side} label="Proposed" side=${row.after} now=${false} /></div>`}
    ${looks && html`<div class="hand-change__looks" role="group" aria-label="The looks">${(row.looks || []).map((l) => html`<button type="button" key=${l.key} class="ork-btn hand-change__look" data-look=${l.key} disabled=${busy}
        title=${`Take the look ${l.name}`} onClick=${() => take({ look: l.key })}><span class="hand-change__lookname">${l.name}</span><span class="cap">${l.why}</span>
        ${(l.lines || []).map((x, i) => html`<span key=${i} class="cap hand-change__lookline">${lineWords(x)}</span>`)}</button>`)}</div>`}
    <div class="hand-answers hand-way__acts" role="group" aria-label="Answers">
      ${!failed && !looks && html`<button type="button" class="ork-btn primary" disabled=${busy}
        title="Its tasks not started take the plan, its lines go into the spec, and it is written down as your decision" onClick=${() => take()}>Accept</button>`}
      ${looks && html`<button type="button" class="ork-btn" disabled=${busy} title=${`${who} takes the look it would choose`} onClick=${() => take({ decide: true })}>Let ${who} decide</button>`}
      <button type="button" class="ork-btn" disabled=${busy} title="Asks the leader again, with your words and the part kept" onClick=${more}>Talk more</button>
      <button type="button" class="ork-btn quiet" disabled=${busy} title="Nothing changes" onClick=${keep}>Keep the spec</button>
    </div>
  </div>`;
}

// The face: the page sign, the price as its gem, the words the leader gave as its foot; its head is the leader's (stopcard.js).
way("leader_change", {
  sign: "page",
  foot: (s) => (s.row?.status === "failed" ? s.row.error || "No change came" : s.row?.text || s.row?.said || ""),
  price: (s) => {
    const r = s.row || {}, low = Number(r.usd_low), high = Number(r.usd_high);
    return r.shape !== "looks" && r.status === "ready" && (low || high) ? { low, high, saves: high < 0 } : null;
  },
  Lifted: ChangeLifted,
});
