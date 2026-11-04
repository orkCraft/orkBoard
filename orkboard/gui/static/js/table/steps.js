// A task's steps on the page (docs/specs/129-a-tasks-steps.md part H2, decisions §207.1): the snapshot's task carries, while it is at work or checked, `steps` — `{items: [{text, state}], now, done, total, source, doing}`, `items` at most six, `state` `done`,
// `now` or `next`, `source` `file`, `todo` or `activity` — and the page says them three ways. **The label row** of a task's card: *Doing 2/5* (the stage's word and `done + 1` of `total`), the pips (6 x 6 squares, 2 px apart: done filled in the ink, the one
// now in the goal's colour and glowing with orkUI's own rhythm while the task is at work, the next faint) and, under them, the step now in one line (the body face: a person's words, never the pixel one; since spec 142 C they stand in the card's window, `StepsWindow`). With `source: "activity"` there are no pips, the
// `doing` line stands in the muted ink. **The lifted card** lists the steps (✓ done muted, the one now lit, the next faint) and says its source small. **A token** (under 760 px) shows the pips only. A task without `steps` has today's label.
// **A lane card's window by its state** (docs/specs/142-a-cards-window-where-it-has-something-to-show.md part C, decisions §249.3): the pips and the step now (two lines) stand in the window of a task at work (`StepsWindow`), with the worker's
// head, its word and the busy mark; a task waiting has the head of the seat that will take it, faint, and *an elf takes it next* (`WaitingWindow`, `seatWords`); a failed one the alert in the danger colour and its reason in one or two lines (`FailedWindow`).
// Pure functions first (`stepsOf`, `countWords`, `labelWords`, `sourceWords`), then the little components card.js and the lifted card draw.
import { html, cls } from "../html.js";
import { Sign, WhoHead } from "../orkui.js";
import { STAGES, stageOf } from "./data.js";

/** The stages that carry the steps on the label row: a task at work or being checked (a failed one stays *Doing*, with the step where it stopped). A task waiting to start has none to show. */
const SHOWN = ["doing", "checking"];

const STATES = ["done", "now", "next"];

/** A task's steps as the page reads them, or null when it has none to show: `{items, now, done, total, source, doing}`, the numbers whole and in range, the items at most six. */
export function stepsOf(t) {
  const s = t?.steps;
  if (!s || typeof s !== "object") return null;
  const source = s.source === "activity" || s.source === "todo" ? s.source : "file";
  const items = (Array.isArray(s.items) ? s.items : []).slice(0, 6).map((i) => ({ text: String(i?.text ?? ""), state: STATES.includes(i?.state) ? i.state : "next" }));
  const doing = String(s.doing ?? "").trim();
  if (source === "activity") return doing ? { items: [], now: -1, done: 0, total: 0, source, doing } : null;
  if (!items.length) return null;
  const total = Math.max(items.length, Number.isFinite(Number(s.total)) ? Math.floor(Number(s.total)) : 0);
  const at = Number.isInteger(s.now) && s.now >= 0 && s.now < items.length ? s.now : -1;
  const done = Math.max(0, Math.min(total, Number.isFinite(Number(s.done)) ? Math.floor(Number(s.done)) : items.filter((i) => i.state === "done").length));
  return { items, now: at, done, total, source, doing };
}

/** Whether the card's label row shows the steps: it has some and its stage is *Doing* or *Checking*. */
export const showsSteps = (t) => !!stepsOf(t) && SHOWN.includes(stageOf(t));

/** *2/5*: the step now of the whole (`done + 1`), or, with none now, how many are done (*5/5* when all are); "" with no count (what it is doing). */
export function countWords(st) {
  if (!st || st.source === "activity" || st.total <= 0) return "";
  return `${st.now >= 0 ? Math.min(st.done + 1, st.total) : st.done}/${st.total}`;
}

/** The step now in words: its text, or the `doing` line of an activity; "" when none is now. */
export const nowWords = (st) => (!st ? "" : st.source === "activity" ? st.doing : st.now >= 0 ? st.items[st.now].text : "");

/** The label row as one line, as a screen reader and the card's title say it: *Doing 2/5 · tests for join*. */
export function labelWords(t) {
  const st = stepsOf(t), head = [STAGES[stageOf(t)].word, countWords(st)].filter(Boolean).join(" "), now = nowWords(st);
  return now ? `${head} · ${now}` : head;
}

/** The source said small on a lifted card. */
export const SOURCE_WORDS = { file: "from its steps file", todo: "from its own list", activity: "what it is doing" };
export const sourceWords = (st) => SOURCE_WORDS[st?.source] || "";

const MARK = { done: "d", now: "n", next: "" };

/** The race of a head as a seat's word with its article, *an elf*, *a Grunt* (an ork of the code craft is a Grunt: CLAUDE.md, Orks by their orkish names; TERMS `race.*`, `orc.barracks`); a leader's higher form is its race's word. "" with no head. */
const SEAT = { peon: "a Grunt", elf: "an elf", goblin: "a goblin", gnome: "a gnome", knight: "a knight", skeleton: "a skeleton" };
/** The forms a party's leader wears, the higher forms of its race (decisions §154, §162): a leader's seat is *its leader*, never a member's word (spec 143 F.2). The host marks the head too (`leader: true`, `roles.task_head`). */
const LEADER_FORMS = new Set(["shaman", "dryad", "imp", "fairy", "unicorn", "lich"]);
export const isLeader = (head) => !!head && (head.leader === true || LEADER_FORMS.has(String(head.race || "").split("-")[0]));
export const seatWords = (head) => (isLeader(head) ? "its leader" : SEAT[String(head?.race || "").split("-")[0]] || "");

/** The window of a task waiting to start: the head of the seat that will take it, faint, and *an elf takes it next* under it. A task with no head has no such window (null). */
export function WaitingWindow({ head }) {
  const who = seatWords(head);
  if (!head || !who) return null;
  return html`<span class="table-win table-win--wait"><span class="table-win__faint"><${WhoHead} head=${head} size="mid" /></span><span class="table-win__line">${isLeader(head) ? "Its leader" : who} takes it next</span></span>`;
}

/** The window of a task at work: the pips, the step now in two lines, and who does it (its head, its word, the busy mark glowing with orkUI's rhythm while the task is at work). */
export function StepsWindow({ st, head, element = "", alive = false }) {
  const text = nowWords(st);
  return html`<span class="table-win table-win--steps">
    <${Pips} st=${st} element=${element} alive=${alive} />
    ${text && html`<span class=${cls("table-win__now", { "is-activity": st.source === "activity" })} title=${text}>${text}</span>`}
    ${head && html`<span class="table-win__by"><${WhoHead} head=${head} /><span class="table-win__who">${seatWords(head)}</span><i class=${cls("table-win__busy", { "is-glowing": alive })} aria-hidden="true"></i></span>`}
  </span>`;
}

/** The window of a failed task: orkUI's alert sign in the danger colour and the reason in one or two lines (the task's error, as the lifted card says it). */
export function FailedWindow({ reason = "" }) {
  const text = String(reason || "").trim().split("\n")[0] || "It failed";
  return html`<span class="table-win table-win--fail"><${Sign} name="alert" /><span class="table-win__reason" title=${text}>${text}</span></span>`;
}

/** The pips: one square a step (done filled, the one now in the goal's colour, glowing while the task is at work, the next faint). Shown, never named: the words say it. Nothing for an activity (it has no steps to count). `small`: the token's size. */
export function Pips({ st, element = "", alive = false, small = false }) {
  if (!st || !st.items.length) return null;
  return html`<span class=${cls("ork-pips table-pips", { "is-small": small })} aria-hidden="true" data-n=${st.items.length}>${st.items.map((it, k) =>
    html`<i key=${k} data-state=${it.state} class=${cls(MARK[it.state], { [`is-${element}`]: it.state === "now" && !!element, "is-glowing": it.state === "now" && alive })}></i>`)}</span>`;
}

/** A lifted task's steps: the list (✓ done, the one now lit, the next faint) and the source said small; an activity is its one line. */
export function StepsList({ st }) {
  if (!st) return null;
  return html`<div class="table-steps" data-source=${st.source}>
    ${st.source === "activity" ? html`<span class="table-steps__line is-now">${st.doing}</span>`
      : html`<ol class="table-steps__list">${st.items.map((it, k) => html`<li key=${k} class=${`table-steps__item is-${it.state}`} data-state=${it.state} aria-current=${it.state === "now" ? "step" : undefined}>
        <span class="table-steps__mark" aria-hidden="true">${it.state === "done" ? "✓" : ""}</span><span class="table-steps__text">${it.text}</span></li>`)}</ol>`}
    <span class="table-steps__src">${sourceWords(st)}</span>
  </div>`;
}
