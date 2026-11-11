// Sort the new goals (docs/mockups/spreads/, "sort"): one new goal at a time in the middle, three piles to put it on: To work (1), Later (2),
// Drop (3); the pile at the left thins as the goals go. Drag the card onto a pile, press the pile, or press its key; *Back one* takes the last
// one back. The page keeps where each went; *Done: send this sorting* sends it (`ideas.sort {sort: {slug: "work" | "later" | "drop"}}`, the
// contract proposed: the host sorts no new goals this way yet, the mock logs it). A dropped goal stays in the history.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { command, toast } from "../../link.js";
import { Icon } from "../../orkui.js";
import { nodes } from "../feed.js";
import { closeSpread } from "./open.js";
import { Key, SpCard, SpreadFrame, Thick, faceOf } from "./shell.js";

const NEW = new Set(["new", "idea"]);
const PILES = [["work", "To work", "play", "1"], ["later", "Later", "clock", "2"], ["drop", "Drop", "trash", "3"]];

export function Sort() {
  const all = nodes().filter((n) => NEW.has(n.state)), [went, setWent] = useState([]);                // [[slug, pile]] in the order sorted
  const cur = all.find((n) => !went.some(([s]) => s === n.slug)), left = all.length - went.length;
  const put = (pile) => { if (cur) setWent((w) => [...w, [cur.slug, pile]]); };
  const back = () => setWent((w) => w.slice(0, -1));
  useEffect(() => {
    const key = (e) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const p = PILES.find(([, , , k]) => k === e.key);
      if (p) put(p[0]); else if (e.key === "Backspace") back();
    };
    addEventListener("keydown", key);
    return () => removeEventListener("keydown", key);
  });
  const last = (pile) => went.filter(([, p]) => p === pile).length > 0;
  const send = () => Promise.resolve(command("ideas.sort", { sort: Object.fromEntries(went) })).then(() => { toast("Sent: where each new goal goes"); closeSpread(); }).catch((e) => toast(e?.message || "The sorting was not sent", "error"));
  const say = all.length ? "New goals came in. Where does each go?" : "No new goal waits to be sorted.";
  return html`<${SpreadFrame} kind="sort" title="Sort the new goals" line="One at a time; the pile at the left thins as you go" say=${say}
      note="Drag the card onto a pile, or press its key. A dropped goal stays in the history."
      acts=${html`<button type="button" class="ork-btn" data-act="back" disabled=${!went.length} onClick=${back}><${Icon} name="arrow-left" /><span>Back one</span></button>
        <button type="button" class="ork-btn primary" data-act="send" disabled=${!went.length} onClick=${send}><${Icon} name="check" /><span>Done: send this sorting</span></button>`}>
    <${Thick} n=${left - (cur ? 1 : 0)} label="new, to sort" />
    ${cur ? html`<div class="sp-col sp-sortcard" draggable="true" onDragStart=${(e) => e.dataTransfer?.setData("text/plain", cur.slug)}>
        <${SpCard} party=${cur.goal} n=${faceOf(cur)} name=${cur.short || cur.title} line=${cur.origin || "a new goal"} size="xl" key=${cur.slug} /></div>`
      : html`<p class="sp-cap sp-field__say">${all.length ? "Every new goal is sorted. Send the sorting, or take one back." : ""}</p>`}
    <div class="sp-bins">${PILES.map(([id, word, icon, k]) => html`<div class="sp-col" key=${id}>
      <button type="button" class=${cls(`sp-bin is-${id}`, { "is-full": last(id) })} disabled=${!cur} onClick=${() => put(id)} onDragOver=${(e) => e.preventDefault()} onDrop=${(e) => { e.preventDefault(); put(id); }}
          aria-label=${`${word}: put the goal on this pile`}>${last(id) && html`<span class="sp-bin__in"></span>`}<${Icon} name=${icon} /></button>
      <span class="sp-cap"><${Key} k=${k} /> ${word}</span></div>`)}</div>
  </${SpreadFrame}>`;
}
