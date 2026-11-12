// What each card costs to play (docs/mockups/spreads/, "cost"): the AI tools' potions at the left (orkUI's `.ork-potion`, what is left today), then
// each goal still to start as a card with its cost in its corner (its tool's mark and its share, like a card game's mana) and its words under it
// (*about 12% of Claude*). A card the tools cannot pay is muted with why and the two ways out: wait for the reset (`ideas.route_later`, which
// exists) or play it on another tool (`ideas.tool_for`: the host keeps no such choice yet). The host answers no
// cost before a goal is played: the shares lie empty, saying who fills them (this mat's own goal), the tools' left today the host's
// own limits (`town.limits`) when it reads them. A cost is an estimate from the work's size; it can be more.
import { useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { command, toast, town } from "../../link.js";
import { Icon } from "../../orkui.js";
import { windowsOf } from "../../hand/windows.js";
import { markSrc } from "../../table/data.js";
import { nodes } from "../feed.js";
import { closeSpread } from "./open.js";
import { SpCard, SpreadFrame, faceOf } from "./shell.js";

const IN_TALK = new Set(["new", "talk", "spec", "idea"]);

/** The tools and what is left of each today: [{id, name, left (0–1)}], from the host's limits; none when it reads none. */
export function toolsLeft() {
  const own = (town.value?.limits || []).map((l) => ({ id: l.provider, name: l.name, w: windowsOf(l) })).filter((t) => t.w.read)
    .map((t) => ({ id: t.id, name: t.name, left: Math.max(0, Math.min(1, parseFloat(t.w.now.share) / 100 || 0)) }));
  return own;
}

/** The goals to price (the ones in talk or spec, the first four: a spread shows few cards) with their cost: [{n, tool, pct, alt}]; `tool` null when it is not known. */
export function pricedGoals() {
  return nodes().filter((n) => IN_TALK.has(n.state)).slice(0, 4).map((n) => ({ n, tool: null, pct: 0 }));
}

const pct = (x) => `${Math.round(x * 100)}%`;
const Mark = ({ id }) => html`<img class="ork-mark sp-mark" src=${markSrc(id, true, true)} width="14" height="14" alt="" />`;

/** A tool's potion with what is left under it; `over` frames the one a card cannot be paid from. */
function Pot({ t, over }) {
  const words = `${t.name}: ${pct(t.left)} left today`;
  return html`<span class=${cls("sp-pot", { "is-over": over })} role="img" aria-label=${words} title=${words}><span class="sp-pot__mark"><${Mark} id=${t.id} /></span>
    <span class=${cls("ork-potion", { "is-warn": t.left < 0.3 && t.left >= 0.1, "is-danger": t.left < 0.1 })} style=${`--ork-potion-left:${t.left}`}></span><b>${pct(t.left)}</b></span>`;
}

export function Cost() {
  const tools = toolsLeft(), goals = pricedGoals(), costs = {}, left = (id) => tools.find((t) => t.id === id)?.left ?? 0, nameOf = (id) => tools.find((t) => t.id === id)?.name || id;
  const unpaid = (g) => g.tool && g.pct / 100 > left(g.tool);
  const first = goals.find((g) => !unpaid(g)) || goals[0];
  const [at, setAt] = useState(first?.n.slug || ""), pick = goals.find((g) => g.n.slug === at) || first;
  const note = costs.mark || "", reset = costs.reset || "its reset";
  const bad = goals.find(unpaid), over = bad ? bad.tool : "";
  const say = tools.length ? `${tools.map((t) => `${t.name} has ${pct(t.left)}`).join(", ")} left today.${bad ? ` ${bad.n.short || bad.n.title} needs more ${nameOf(bad.tool)} than is left.` : ""}`
    : "The tools' limits are not read, so no card can say its cost yet.";
  const play = (g, tool = "") => {
    const sent = tool ? command("ideas.tool_for", { idea: g.n.slug, tool }) : command("ideas.start", { slug: g.n.slug, via: "spread" });
    Promise.resolve(sent).then(() => { toast(tool ? `Sent: ${g.n.short || g.n.title} on ${nameOf(tool)}` : `Sent: play ${g.n.short || g.n.title}`); closeSpread(); }).catch((e) => toast(e?.message || "Not sent", "error"));
  };
  const wait = (g) => Promise.resolve(command("ideas.route_later", { idea: g.n.slug })).then(() => { toast("In line: it plays by itself after the limits reset."); closeSpread(); }).catch((e) => toast(e?.message || "Not sent", "error"));
  const title = (g) => g.n.short || g.n.title;
  const acts = !pick ? null : unpaid(pick)
    ? html`${pick.alt && html`<button type="button" class="ork-btn primary" data-act="play_on" onClick=${() => play(pick, pick.alt.tool)}><span>${title(pick)} on ${nameOf(pick.alt.tool)}</span></button>`}
      <button type="button" class="ork-btn" data-act="wait" onClick=${() => wait(pick)}><${Icon} name="clock" /><span>Wait for ${reset}</span></button>`
    : html`<button type="button" class="ork-btn primary" data-act="play" onClick=${() => play(pick)}><${Icon} name="play" /><span>Play ${title(pick)}</span></button>`;
  return html`<${SpreadFrame} kind="cost" title="What each card costs to play" line="An estimate from the work's size; it can be more" say=${say}
      note="The cost is the AI tools' use, said before you play; a card you cannot pay says so and why." acts=${acts}>
    <div class="sp-costs">
      ${tools.length > 0 && html`<div class="sp-col"><div class="sp-pots" role="group" aria-label="What is left of your AI tools">${tools.map((t) => html`<${Pot} key=${t.id} t=${t} over=${t.id === over} />`)}</div>
        <p class="sp-cap">left today${costs.reset ? `, refilled at ${costs.reset}` : ""}${note}</p></div>`}
      ${goals.map((g) => html`<div class="sp-col" key=${g.n.slug}>
        <${SpCard} party=${g.n.goal} n=${faceOf(g.n)} name=${title(g)} line=${g.n.line || (g.n.state === "talk" ? "in talk" : g.n.state === "spec" ? "its spec" : "new")} size="xl" muted=${!!unpaid(g)}
            onPress=${() => setAt(g.n.slug)} picked=${pick?.n.slug === g.n.slug}
            label=${`${title(g)}: ${g.tool ? `about ${g.pct}% of ${nameOf(g.tool)}${unpaid(g) ? `, more than is left` : ""}` : "cost not known yet"}`}>
          ${g.tool && html`<span class=${cls("sp-cost", { "is-over": unpaid(g) })} aria-hidden="true"><${Mark} id=${g.tool} />${g.pct}%</span>`}</${SpCard}>
        <p class=${cls("sp-costw", { "is-over": unpaid(g) })}>${g.tool ? `about ${g.pct}% of ${nameOf(g.tool)}${unpaid(g) ? `: ${pct(left(g.tool))} left. Wait for ${reset}${g.alt ? `, or play it on ${nameOf(g.alt.tool)}` : ""}` : ""}${note}` : "Its cost is not known yet: the costs' mat lays it when its goal is done"}</p></div>`)}
      ${!goals.length && html`<p class="sp-cap">No goal waits to be played.</p>`}
    </div>
  </${SpreadFrame}>`;
}
