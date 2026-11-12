// What lies round an opened goal card (decisions §298.4, §298.5; docs/mockups/card-path/ open): the craft tokens on their slips beside it (all open, each
// with its checks and **Reply to <leader>**), the card's faint marks where each token lay, and under it a row of heads, **Ask <leader>…**, the
// route's first and, after them, the other parties (*not on its route*). Both send the host's command (`ideas.reply`, `ideas.ask_leader`: a paid pass,
// its cost said beside *Send* before it runs, on its seal) and say *Sent to <leader>*.
import { useEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { command, toast } from "../link.js";
import { mapData } from "../shell/store.js";
import { HeadOf, whoOf } from "../table/post.js";
import { AskCost, useAskCost } from "./askcost.js";
import { Slip } from "./slip.js";
import { CraftToken, raceIn } from "./verdict.js";

/** Sends words to a leader: a field with the focus in it and *Send to <leader>*; the command is the caller's (`send(text)`). Esc closes it (`onClose`) and stops there:
 *  the opened card stays. */
function Field({ leader, label, send, onClose }) {
  const [text, setText] = useState(""), [busy, setBusy] = useState(false), name = whoOf(leader).name, area = useRef(), cost = useAskCost();
  useEffect(() => { area.current?.focus(); }, []);
  const go = async () => {
    if (!text.trim() || busy) return;
    setBusy(true);
    try { await send(text.trim()); toast(`Sent to ${name}`); setText(""); onClose(); } catch (e) { toast(e?.message || `It was not sent to ${name}`, "error"); } finally { setBusy(false); }
  };
  return html`<div class="cards-field" data-field=${leader}><label><span>${label}</span>
    <textarea ref=${area} class="ork-field" rows="2" value=${text} onInput=${(e) => setText(e.target.value)}
      onKeyDown=${(e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); onClose(); } else if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) { e.preventDefault(); go(); } }}></textarea></label>
    <${AskCost} words=${cost.words} />
    <button type="button" class="ork-btn" disabled=${!text.trim() || busy || !cost.ready} onClick=${go}>Send to ${name}</button></div>`;
}

/** A slip on an opened card: *Reply to <leader>* under its checks (a); pressed, its field opens in this slip only. */
export function ReplySlip({ slug, v }) {
  const name = whoOf(v.leader).name, [open, setOpen] = useState(false), btn = useRef();
  const close = () => { setOpen(false); setTimeout(() => btn.current?.focus(), 0); };
  return html`<${Slip} leader=${v.leader} checks=${v.checks} token=${html`<${CraftToken} leader=${v.leader} checks=${v.checks} on=${true} />`}>
    <button ref=${btn} type="button" class="cards-linkb" data-reply=${v.leader} aria-expanded=${open ? "true" : "false"} onClick=${() => (open ? close() : setOpen(true))}>Reply to ${name}</button>
    ${open && html`<${Field} leader=${v.leader} label="Your reply" onClose=${close} send=${(text) => command("ideas.reply", { slug, leader: v.leader, text, sealed: true }, true)} />`}<//>`;
}

/** The slips of an opened card in a column, the verdicts' own order, alternate ones on each side (`side` 0 or 1; all on one column on a phone: CSS). */
export const SlipsColumn = ({ slug, verdicts, side }) => html`<div class=${cls("cards-slips", side ? "is-right" : "is-left")}>${verdicts.map((v, i) => (i % 2 === side ? html`<${ReplySlip} key=${v.leader} slug=${slug} v=${v} />` : null))}</div>`;

/** The card's faint marks, where each token lay: a ring in its party's colour on the card's edge, on the side its slip lies. */
export const Marks = ({ verdicts }) => html`${verdicts.map((v, i) => html`<span key=${v.leader} class="cards-mark" data-race=${raceIn(v.leader) || "orkmaster"} data-side=${i % 2 ? "right" : "left"}
  style=${`top:${64 + Math.floor(i / 2) * 26}px`} aria-hidden="true"></span>`)}`;

/** Under the card: a head for each leader to ask, the route's first, then the other parties. */
export function AskRow({ slug, route }) {
  const [at, setAt] = useState(""), parties = (mapData.value?.goals || []).map((g) => g.slug).filter((s) => s !== "orkmaster");
  const heads = [...route.map((leader) => ({ leader, off: false })), ...parties.filter((s) => !route.includes(s)).map((leader) => ({ leader, off: true }))];
  const closeAsk = () => { const was = at; setAt(""); setTimeout(() => document.querySelector(`.cards-ask__b[data-ask="${CSS.escape(was)}"]`)?.focus(), 0); };
  if (!heads.length) return null;
  return html`<div class="cards-ask" role="group" aria-label="Ask a leader about this card">
    <div class="cards-ask__heads">${heads.map(({ leader, off }) => {
      const w = whoOf(leader);
      return html`<span key=${leader} class="cards-ask__one"><button type="button" class=${cls("cards-ask__b", { "is-on": at === leader })} data-ask=${leader} data-race=${raceIn(leader) || "orkmaster"} aria-expanded=${at === leader ? "true" : "false"}
          onClick=${() => (at === leader ? closeAsk() : setAt(leader))}><span class="cards-ask__ring"><${HeadOf} w=${w} /></span><span>Ask ${w.name}…</span></button>${off && html`<small>not on its route</small>`}</span>`;
    })}</div>
    ${at && html`<${Field} key=${at} leader=${at} label=${`Ask ${whoOf(at).name} about this card`} onClose=${closeAsk}
      send=${(text) => command("ideas.ask_leader", { slug, leader: at, text, sealed: true }, true)} />`}</div>`;
}
