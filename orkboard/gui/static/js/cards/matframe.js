// The frame every mat lies in (goal 171 stage H; decisions §300.15; docs/mockups/mats/, the shots battle-2 and gate): a dialog over the pane on its owner's
// felt (orkUI's `.ork-table[data-party]` with its bronze frame), its head and every word on a plate (`.ork-plate`), its zones printed in bronze with their labels on
// the frame (`Zone`), the phases along its foot where it is about one goal (`Phases`), its seal at its foot's right for a move that cannot be undone (`Seal`).
// While it is open the table, the discard and the head are inert and dimmed; Tab goes through the mat only, Esc closes it and the focus goes back to what opened it.
// `spreads/shell.js` (a spread) and `tables/index.js` (a leader's table) draw their mats in it. The sheet is matframe.css. Layout only: every colour is orkUI's.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { HeadOf, whoOf } from "../table/post.js";
import { keepTab } from "./back.js";

const NARROW = "(max-width: 700px)";

/** Whether the window is a phone's width: the mat is the whole screen and its way out says *Back*. */
export function useNarrowMat() {
  const q = () => typeof matchMedia === "function" && matchMedia(NARROW).matches, [narrow, set] = useState(q);
  useEffect(() => {
    if (typeof matchMedia !== "function") return undefined;
    const m = matchMedia(NARROW), on = () => set(m.matches);
    m.addEventListener?.("change", on);
    return () => m.removeEventListener?.("change", on);
  }, []);
  return narrow;
}

/** The felt's party: its `data-party` (orkUI's list); one it does not know lies on the Orkmaster's. */
const PARTIES = new Set(["ork", "tech", "knight", "game", "product", "elf", "design", "art", "undead", "release", "goblin", "run", "liveops", "gnome", "market", "marketing", "orkmaster"]);
export const feltOf = (party) => (PARTIES.has(party) ? party : "orkmaster");

/** A goal's phases in order, along a mat's foot; `at` the one it is in. */
export const PHASES = [["new", "New"], ["talk", "Talk"], ["spec", "Spec"], ["work", "Work"], ["done", "Done"]];
export function Phases({ at }) {
  return html`<ol class="mf-phases" aria-label="Where the goal is">${PHASES.map(([id, word]) => html`<li key=${id} class=${cls("mf-phase", { "is-on": id === at })} aria-current=${id === at ? "step" : undefined}>${word}</li>`)}</ol>`;
}

/** A zone printed in bronze on the felt, its label on its frame; empty, its sign lies faint inside (`empty`: what it waits for). */
export function Zone({ label, empty = "", children, ...rest }) {
  return html`<section class=${cls("mf-zone", { "is-empty": !!empty })} aria-label=${label} ...${rest}><span class="mf-zl" aria-hidden="true">${label}</span>${empty ? html`<span class="mf-slot" aria-hidden="true"></span><span class="mf-zs ork-plate">${empty}</span>` : children}</section>`;
}

/** The seal at a mat's foot's right, for a move that cannot be undone (Merge into main, Send to a branch, Ship a release, a paid pass): dim with its why until it can be pressed
 *  (a way is picked, the checks are green), told by its rim and its why, never by opacity. Pressed lit, it sends the move with `sealed: true`; dim, it presses nothing. */
export function Seal({ word, why = "", lit = false, onPress, kind = "" }) {
  return html`<button type="button" class=${cls("mf-seal", { "is-dim": !lit })} data-seal=${kind || undefined} aria-disabled=${lit ? undefined : "true"} aria-label=${lit ? word : (why || word)}
    onClick=${() => { if (lit) onPress?.({ sealed: true }); }}><b>${word}</b>${why && html`<small>${why}</small>`}</button>`;
}

/** What goes inert while a mat is open: the frame's other children (the table, the discard, the head: the hand stays live); put back when it is put away. */
function useInertBehind(root) {
  const kin = useRef([]);
  const release = () => { kin.current.forEach((el) => el.removeAttribute("inert")); kin.current = []; };      // at once, so the focus can go back before the card is drawn again
  useLayoutEffect(() => {
    kin.current = [...(root.current?.closest(".frame")?.children || [])].filter((el) => el !== root.current && !el.hasAttribute("inert") && !el.classList.contains("frame-hand"));
    kin.current.forEach((el) => el.setAttribute("inert", ""));
    return release;
  }, []);
  return release;
}

/** The frame. `kind`: the mat (`data-spread`), `party`: whose felt, `title`, `line`, `say`: the head; `note`: the foot's words, `acts`: its buttons, `hand`: its cards, `seal`: a `Seal`, `phase`: the goal's, shown
 *  on the foot; `onClose`: puts it away; `head`: more in the head, `extra`: a row under it; `frame`, `fieldCls`, `footCls`: classes and data of the felt, the field and the foot; children: the field. */
export function MatFrame({ kind, party = "orkmaster", title, line = "", say = "", note = "", acts = null, hand = null, seal = null, phase = "", onClose, head = null, extra = null, frame = {}, fieldCls = "", footCls = "", children }) {
  const root = useRef(), narrow = useNarrowMat(), felt = feltOf(party);
  const release = useInertBehind(root), close = () => { release(); onClose(); };
  useLayoutEffect(() => {   // the keys at once, before the first paint: an Esc pressed as the mat opens closes it
    root.current?.querySelector(".sp-shut")?.focus();
    const key = (e) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); close(); } else keepTab(root.current, e); };
    addEventListener("keydown", key, true);
    return () => removeEventListener("keydown", key, true);
  }, []);
  return html`<div ref=${root} class="sp-veil mf-veil" role="dialog" aria-modal="true" aria-label=${title} data-spread=${kind}>
    <div ...${frame} class=${cls("sp mf ork-table", frame.class)} data-party=${felt}>
      <header class="sp-h mf-h"><span class="sp-av"><${HeadOf} w=${whoOf(felt === "orkmaster" ? "orkmaster" : party)} size="big" /></span>
        <span class="sp-t mf-t ork-plate"><b>${title}</b>${line && html`<small>${line}</small>`}</span>
        ${say && html`<span class="sp-say ork-plate">${say}</span>`}${head}
        <button type="button" class="ork-btn sp-shut" onClick=${close}><${Icon} name=${narrow ? "arrow-left" : "close"} /><span>${narrow ? "Back" : "Close"}</span></button></header>
      ${extra}
      <div class=${cls("sp-field mf-field", fieldCls)}>${children}</div>
      <footer class=${cls("sp-hand mf-foot", footCls)}>${hand && html`<div class="sp-cards" role="group" aria-label="Your hand">${hand}</div>`}${note && html`<p class="sp-note ork-plate">${note}</p>`}
        ${phase && html`<${Phases} at=${phase} />`}${(acts || seal) && html`<div class="sp-acts">${acts}${seal}</div>`}</footer>
    </div></div>`;
}
