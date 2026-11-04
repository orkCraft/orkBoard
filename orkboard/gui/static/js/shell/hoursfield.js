// **When I am at the computer** (docs/specs/138-the-day-read-from-the-resets.md B.1, decisions §245.5; the presence it gives is spec 139 C.1), a section of Settings: rows of days and a span (*Mon–Fri 19:00–23:00*, *Sat–Sun all day* is
// 00:00–00:00), empty by default and, empty, nothing changes. Kept as the Board's `hours` (`ideas.board_set {hours}`, gui/ideas_board.py): `[{days: [0..6], from: "HH:MM", to: "HH:MM"}]`, Monday 0, the machine's local time; a span whose
// end is not after its start runs over midnight. A row is saved when it is whole (a day and two times); **Add hours** adds a row, **Remove** takes one off. Words say plainly what happens: what asks the person waits for these hours.
import { useEffect, useRef, useState } from "preact/hooks";
import { html } from "../html.js";
import { act } from "./store.js";
import { board } from "../board/store.js";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const FIRST = { days: [0, 1, 2, 3, 4], from: "19:00", to: "23:00" };                 // what *Add hours* offers: weekday evenings
const whole = (r) => r.days.length > 0 && /^\d\d:\d\d$/.test(r.from) && /^\d\d:\d\d$/.test(r.to);

/** The rows said in a line, *Mon–Fri 19:00–23:00*: for a screen reader and the title of a row. */
export function hoursWords(r) {
  const run = r.days.length > 1 && r.days.every((d, i) => i === 0 || d === r.days[i - 1] + 1);
  const days = run ? `${DAYS[r.days[0]]}–${DAYS[r.days[r.days.length - 1]]}` : r.days.map((d) => DAYS[d]).join(", ");
  return `${days} ${r.from === r.to ? "all day" : `${r.from}–${r.to}`}`;
}

export function HoursField() {
  const saved = board.value?.hours || [];
  const [rows, setRows] = useState(saved);
  const key = JSON.stringify(saved), sent = useRef(key);                               // `sent`: the rows the host last had from here or from its own snapshot
  useEffect(() => { sent.current = key; setRows(saved); }, [key]);                     // what the host kept is what is shown
  if (!board.value) return null;
  const keep = (next) => { setRows(next); const done = next.filter(whole), now = JSON.stringify(done); if (now !== sent.current) { sent.current = now; act("ideas.board_set", { hours: done }); } };
  const edit = (i, part) => keep(rows.map((r, n) => (n === i ? { ...r, ...part } : r)));
  const flip = (i, d) => { const r = rows[i], days = r.days.includes(d) ? r.days.filter((x) => x !== d) : [...r.days, d].sort(); edit(i, { days }); };
  return html`<div class="shell-field" role="group" aria-label="When I am at the computer" data-settings="hours"><span class="ok-font-label">When I am at the computer</span>
    ${rows.map((r, i) => html`<div key=${i} class="shell-hours__row" data-hours=${i} title=${whole(r) ? hoursWords(r) : ""} style="display:flex;flex-wrap:wrap;gap:var(--ork-2);align-items:center">
      <div class="shell-seg" role="group" aria-label="Days">${DAYS.map((name, d) => html`<label key=${d} class=${`shell-seg__one${r.days.includes(d) ? " is-on" : ""}`}>
        <input type="checkbox" class="gui-onb__hide" checked=${r.days.includes(d)} onChange=${() => flip(i, d)} />${name}</label>`)}</div>
      <input type="time" class="ork-field" style="width:auto" aria-label="From" data-hours-from=${i} value=${r.from} onChange=${(e) => edit(i, { from: e.currentTarget.value })} />
      <span class="ok-font-status ok-tone-muted">to</span>
      <input type="time" class="ork-field" style="width:auto" aria-label="To" data-hours-to=${i} value=${r.to} onChange=${(e) => edit(i, { to: e.currentTarget.value })} />
      <button type="button" class="ork-btn quiet" data-hours-remove=${i} onClick=${() => keep(rows.filter((_, n) => n !== i))}>Remove</button>
    </div>`)}
    <span><button type="button" class="ork-btn" data-hours-add="1" onClick=${() => keep([...rows, { ...FIRST }])}>Add hours</button></span>
    <span class="ok-font-status ok-tone-muted" data-settings="hours-hint">${rows.length
      ? "While you are away, the orks go on with what asks you nothing; a Talk or a review waits for the first reset inside these hours. The same start and end is the whole day."
      : "Empty: nothing waits for you, and the orks start what they start at any hour. Add the days and hours you sit at the computer, and what will ask you waits for them while you are away."}</span></div>`;
}
