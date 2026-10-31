// A party on the phone's middle (docs/specs/117-the-phone-a-menu-of-the-leaders.md §5.2, docs/mockups/phone/sidebar.html A3, decisions §195.2): the party picked in the menu — its leader's header (the head big, its name in the heading face and what it is for in one line, its size's
// word), its squad grouped *Leads* | *Does* | *Checks* (the heads only; one pressed opens its popover as a sheet at the foot, table/seatpop.js), the tools of its sword and shield in words (§192.4: *Does on the default (now Claude Code)*, *Checks on Codex, set for this party*, a Lean
// party's *no separate check*), its goals at work as the menu's rows (a press picks the goal), and its **Concerns**: what its leader says is wrong or at risk, the alert sign and the line, what it is on in the caption; none when it has none. A leader's map is not drawn on a phone
// (decisions §195.5). Layout only (uplook.css).
import { useEffect, useState } from "preact/hooks";
import { html } from "../html.js";
import { Head, Sign } from "../orkui.js";
import { mapData } from "../shell/store.js";
import { groupsOf, nameOf, sizeTip, sizeWord } from "../table/data.js";
import { Seat } from "../table/header.js";
import { SeatPop } from "../table/seatpop.js";
import { recordOf, readConcerns } from "../table/concerns.js";
import { Mark, marksOf, sideWords } from "../table/tabmarks.js";
import { pickGoal } from "./entries.js";
import { GoalRow, workOf } from "./upmenu.js";

/** The open concerns of a party's record (those not made into a goal yet), the alerts first: `[{id, level, what, on}]`. */
export function concernsOf(party) {
  const list = (recordOf(party)?.concerns || []).filter((c) => !(c.idea || c.goal) && c.what);
  return [...list.filter((c) => c.level === "alert"), ...list.filter((c) => c.level !== "alert")];
}

/** The tools of the sword and the shield in words, each with its sign and its tool's mark. */
function Tools({ m }) {
  return html`<ul class="up-tools" aria-label="Its tools">
    <li class="up-tool" data-side="does"><${Sign} name="sword" /><${Mark} id=${m.does} on=${false} mode=${m.doesMode} /><span>${sideWords("Does", m.does, m.doesMode, m.doesMixed)}</span></li>
    ${m.lean ? html`<li class="up-tool is-off" data-side="checks"><${Sign} name="shield" /><span>No separate check</span></li>`
      : html`<li class="up-tool" data-side="checks"><${Sign} name="shield" /><${Mark} id=${m.checks} on=${false} mode=${m.checksMode} /><span>${sideWords("Checks", m.checks, m.checksMode, m.checksMixed)}</span></li>`}
  </ul>`;
}

/** The party: its header, squad, tools, goals at work and concerns. `entries`: the hand's, so a goal with a card is picked as that card. */
export function Party({ g, entries }) {
  const [seat, setSeat] = useState(""), rev = mapData.value?.rev;
  useEffect(() => { readConcerns(g.slug); }, [g.slug, rev]);                             // the record now, and again when the Board changes
  useEffect(() => { setSeat(""); }, [g.slug]);
  const name = nameOf(g), size = sizeWord(g), marks = marksOf(g), work = workOf(g), concerns = concernsOf(g.slug), from = { title: "", key: "" };
  return html`<article class="up-party" data-party=${g.slug} aria-label=${name}>
    <header class="up-ph">${g.leader?.head && html`<${Head} race=${g.leader.head.race} tier=${g.leader.head.tier} size="big" />`}
      <div class="up-ph__txt"><h2 class="ork-head up-ph__name">${name}</h2>${g.brief && html`<p class="up-ph__brief">${g.brief}</p>`}</div>
      ${size && html`<span class="ork-chip up-ph__size" title=${sizeTip(g)}>${size}</span>`}</header>
    <div class="up-squad">${groupsOf(g).map((x) => html`<div key=${x.band} class="up-squad__col" role="group" aria-label=${x.word} data-band=${x.band}><span class="up-lab">${x.word}</span>
      <span class="up-squad__seats">${x.seats.map((m) => html`<${Seat} key=${m.slug} g=${g} m=${m} open=${seat === m.slug} onPress=${() => setSeat(seat === m.slug ? "" : m.slug)} />`)}</span></div>`)}</div>
    ${marks && html`<${Tools} m=${marks} />`}
    ${work.length > 0 && html`<section class="up-sec" aria-label="Goals at work"><p class="up-lab">At work</p>
      ${work.map((r) => html`<${GoalRow} key=${r.slug} r=${r} on=${false} onPress=${() => pickGoal(entries, r.slug)} />`)}</section>`}
    ${concerns.length > 0 && html`<section class="up-sec" aria-label="Concerns"><p class="up-lab">Concerns</p>
      <ul class="up-concerns">${concerns.map((c) => html`<li key=${c.id} class="up-concern" data-level=${c.level}>${c.level === "alert" ? html`<${Sign} name="alert" />` : html`<i class="cn-dot" aria-hidden="true"></i>`}
        <span><span class="up-concern__what">${c.what}</span>${c.on && html`<span class="up-concern__on">${c.on}</span>`}</span></li>`)}</ul></section>`}
    ${seat && html`<${SeatPop} g=${g} slug=${seat} from=${from} onClose=${() => setSeat("")} />`}
  </article>`;
}
