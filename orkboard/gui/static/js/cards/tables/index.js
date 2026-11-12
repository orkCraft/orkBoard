// The leaders' tables (goal 170, the talk of 11 November 2026; docs/mockups/frameworks/), on the table of cards only (cards/on.js): a leader whose
// framework the host holds (`ideas.tables`) gets a switch in its lane's head, *Feed* and its framework's name; the framework is drawn in the
// pane in place of the lanes, as the mockup draws it (the whole table, its rules beside it, the person's tokens under it), because a framework
// is read as a spread across the pane, not as a column; the same switch, at its head, goes back to the lanes. Product's (knights') is Jobs to be done, Tech's (orks') Architecture.
import { html } from "../../html.js";
import { Switch } from "../../orkui.js";
import { nameOf } from "../../table/data.js";
import { raceOf } from "../../table/felt.js";
import { HeadOf, whoOf } from "../../table/post.js";
import { Architecture } from "./arch.js";
import { Jobs } from "./jtbd.js";
import { TokenStrip } from "./parts.js";
import { frameworkOf, laid, laidAt } from "./state.js";
import { useEffect, useRef } from "preact/hooks";
import { Said } from "../said.js";

/** The switch in a lane's head: *Feed* (the lane as it is) and the leader's framework; nothing for a party with none. */
export function FrameSwitch({ g }) {
  const fw = frameworkOf(g);
  if (!fw) return null;
  return html`<${Switch} label=${`${nameOf(g)}'s lane`} cls="tb-switch" options=${[["feed", "Feed"], [fw.id, fw.name]]} value=${laid.value === g.slug ? fw.id : "feed"} onPick=${(id) => { laidAt.value = null; laid.value = id === "feed" ? "" : g.slug; }} />`;
}

/** The framework of the party laid, in the pane in place of the lanes. */
export function TablesView({ parties }) {
  const g = parties.find((x) => x.slug === laid.value), fw = g && frameworkOf(g);
  if (!g || !fw) return null;
  const ctx = { party: g.slug, framework: fw.id, race: raceOf(g), leader: nameOf(g) }, Face = fw.id === "architecture" ? Architecture : Jobs;
  const at = laidAt.value?.party === g.slug && laidAt.value.framework === fw.id ? laidAt.value : null, root = useRef();
  useEffect(() => { if (at) root.current?.querySelector(`.tb-card[data-card="${CSS.escape(at.card)}"]`)?.scrollIntoView?.({ block: "nearest", inline: "nearest" }); }, [at]);
  return html`<section ref=${root} class="tb" data-at=${at?.card || undefined} data-race=${ctx.race} data-party=${g.slug} data-framework=${fw.id} aria-label=${`${nameOf(g)}'s table: ${fw.name}`}>
    <header class="tb-head"><span class="tb-av"><${HeadOf} w=${whoOf(g.slug)} size="big" /></span>
      <span class="tb-t"><b>${nameOf(g)}'s table</b><small>${fw.data.line}</small></span>
      <${FrameSwitch} g=${g} /></header>
    ${at?.p && html`<${Said} p=${at.p} />`}
    <div class="tb-body"><${Face} ctx=${ctx} data=${fw.data} /></div>
    <${TokenStrip} ctx=${ctx} leader=${nameOf(g)} />
  </section>`;
}
