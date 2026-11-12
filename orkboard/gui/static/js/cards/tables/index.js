// The leaders' tables (goal 170, the talk of 11 November 2026; docs/mockups/frameworks/), on the table of cards only (cards/on.js): a leader whose
// framework the host holds (`ideas.tables`) gets a switch in its lane's head, *Feed* and its framework's name; the framework is drawn in the
// pane in place of the lanes, as the mockup draws it (the whole table, its rules beside it, a line under it), because a framework
// is read as a spread across the pane, not as a column; the same switch, at its head, goes back to the lanes. Product's (knights') is Jobs to be done, Tech's (orks') Architecture.
import { html } from "../../html.js";
import { Switch } from "../../orkui.js";
import { nameOf } from "../../table/data.js";
import { raceOf } from "../../table/felt.js";
import { Architecture } from "./arch.js";
import { Jobs } from "./jtbd.js";
import { MatFrame } from "../matframe.js";
import { giveBack } from "../back.js";
import { frameworkOf, laid, laidAt, laidFrom } from "./state.js";
import { useEffect, useRef } from "preact/hooks";
import { Said } from "../said.js";

/** The switch in a lane's head: *Feed* (the lane as it is) and the leader's framework; nothing for a party with none. */
export function FrameSwitch({ g }) {
  const fw = frameworkOf(g);
  if (!fw) return null;
  return html`<${Switch} label=${`${nameOf(g)}'s lane`} cls="tb-switch" options=${[["feed", "Feed"], [fw.id, fw.name]]} value=${laid.value === g.slug ? fw.id : "feed"} onPick=${(id) => { const from = laidFrom.value || document.activeElement; laidAt.value = null; laid.value = id === "feed" ? "" : g.slug; laidFrom.value = id === "feed" ? null : from; if (id === "feed") giveBack(from); }} />`;
}

/** The framework of the party laid, as a mat over the pane (matframe.js): the leader's felt, its words at its head, the switch back to the lanes in its head. */
export function TablesView({ parties }) {
  const g = parties.find((x) => x.slug === laid.value), fw = g && frameworkOf(g);
  if (!g || !fw) return null;
  const ctx = { party: g.slug, framework: fw.id, race: raceOf(g), leader: nameOf(g) }, Face = fw.id === "architecture" ? Architecture : Jobs;
  const at = laidAt.value?.party === g.slug && laidAt.value.framework === fw.id ? laidAt.value : null, field = useRef();
  useEffect(() => { if (at) field.current?.querySelector(`.tb-card[data-card="${CSS.escape(at.card)}"]`)?.scrollIntoView?.({ block: "nearest", inline: "nearest" }); }, [at]);
  const close = () => { const from = at?.from || laidFrom.value; laidAt.value = null; laid.value = ""; laidFrom.value = null; giveBack(from); };
  return html`<${MatFrame} key=${g.slug + fw.id} kind="table" party=${ctx.race} title=${`${nameOf(g)}'s table`} line=${fw.data.line} onClose=${close}
      frame=${{ class: "tb", "data-at": at?.card || undefined, "data-race": ctx.race, "data-party": g.slug, "data-framework": fw.id, "aria-label": `${nameOf(g)}'s table: ${fw.name}` }}
      head=${html`<${FrameSwitch} g=${g} />`} extra=${at?.p && html`<${Said} p=${at.p} />`} fieldCls="tb-body" footCls="tb-hand"
      note="Press a card to turn it over; ask its leader about any part.">
    <div ref=${field} class="tb-face"><${Face} ctx=${ctx} data=${fw.data} /></div>
  </${MatFrame}>`;
}
