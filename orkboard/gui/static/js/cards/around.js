// What lies round an opened goal card (decisions §298.4, §298.5; docs/mockups/card-path/ open): the craft tokens on their slips beside it (all open, each
// with its checks and **Reply to <leader>**), the card's faint marks where each token lay, and under it a row of heads, **Ask <leader>…**, the
// route's first and, after them, the other parties (*not on its route*). Both send a proposed command (`ideas.reply`, `ideas.ask_leader`: the
// mock logs it, the host does not answer it yet) and say *Sent to <leader>*.
import { useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command, toast } from "../link.js";
import { mapData } from "../shell/store.js";
import { HeadOf, whoOf } from "../table/post.js";
import { Slip } from "./slip.js";
import { CraftToken } from "./verdict.js";

/** Sends words to a leader: a field and *Send to <leader>*; the command and the words are the caller's (`send(text)`). */
function Field({ leader, label, send, onDone = null, autofocus = false }) {
  const [text, setText] = useState(""), [busy, setBusy] = useState(false), name = whoOf(leader).name;
  const go = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    try { await send(text.trim()); toast(`Sent to ${name}`); setText(""); onDone?.(); } catch (e) { toast(e?.message || `It was not sent to ${name}`, "error"); } finally { setBusy(false); }
  };
  return html`<div class="cards-field" data-field=${leader}><label><span>${label}</span>
    <textarea class="ork-field" rows="2" value=${text} autofocus=${autofocus} onInput=${(e) => setText(e.target.value)} onKeyDown=${(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); go(); } }}></textarea></label>
    <button type="button" class="ork-btn" disabled=${!text.trim() || busy} onClick=${go}>Send to ${name}</button></div>`;
}

/** A slip on an opened card, a reply under its checks (a). */
export function ReplySlip({ slug, v }) {
  const name = whoOf(v.leader).name;
  return html`<${Slip} leader=${v.leader} checks=${v.checks} token=${html`<${CraftToken} leader=${v.leader} checks=${v.checks} on=${true} />`}>
    <${Field} leader=${v.leader} label=${`Reply to ${name}`} send=${(text) => command("ideas.reply", { slug, leader: v.leader, text }, true)} /><//>`;
}

/** The slips of an opened card in a column, the verdicts' own order, alternate ones on each side (`side` 0 or 1; all on one column on a phone: CSS). */
export const SlipsColumn = ({ slug, verdicts, side }) => html`<div class=${cls("cards-slips", side ? "is-right" : "is-left")}>${verdicts.map((v, i) => (i % 2 === side ? html`<${ReplySlip} key=${v.leader} slug=${slug} v=${v} />` : null))}</div>`;

/** The card's faint marks, where each token lay: a ring in its party's colour on the card's edge, on the side its slip lies. */
export const Marks = ({ verdicts }) => html`${verdicts.map((v, i) => html`<span key=${v.leader} class="cards-mark" data-race=${whoOf(v.leader).race || "orkmaster"} data-side=${i % 2 ? "right" : "left"}
  style=${`top:${64 + Math.floor(i / 2) * 26}px`} aria-hidden="true"></span>`)}`;

/** Under the card: a head for each leader to ask, the route's first, then the other parties. */
export function AskRow({ slug, route }) {
  const [at, setAt] = useState(""), parties = (mapData.value?.goals || []).map((g) => g.slug).filter((s) => s !== "orkmaster");
  const heads = [...route.map((leader) => ({ leader, off: false })), ...parties.filter((s) => !route.includes(s)).map((leader) => ({ leader, off: true }))];
  if (!heads.length) return null;
  return html`<div class="cards-ask" role="group" aria-label="Ask a leader about this card">
    <div class="cards-ask__heads">${heads.map(({ leader, off }) => {
      const w = whoOf(leader);
      return html`<span key=${leader} class="cards-ask__one"><button type="button" class=${cls("cards-ask__b", { "is-on": at === leader })} data-ask=${leader} data-race=${w.race || "orkmaster"} aria-expanded=${at === leader ? "true" : "false"}
          onClick=${() => setAt(at === leader ? "" : leader)}><span class="cards-ask__ring"><${HeadOf} w=${w} /></span><span>Ask ${w.name}…</span></button>${off && html`<small>not on its route</small>`}</span>`;
    })}</div>
    ${at && html`<${Field} key=${at} leader=${at} label=${`Ask ${whoOf(at).name} about this card`} autofocus=${true} onDone=${() => setAt("")}
      send=${(text) => command("ideas.ask_leader", { slug, leader: at, text }, true)} />`}</div>`;
}
