// The stages of a goal as cards (docs/mockups/spreads/, "track"): the ones done a pile at the left with a check, the one now face up in the
// middle with a meeple in its party's colour, the ones to come face down at the right. The steps are the goal's route (`n.route`, the map's
// node: {step: "party", party, state, done, total, at}). A goal at work whose route the host has not drawn yet (the recording's are empty,
// a route of one step is left out) takes the steps of its plan (`n.steps`, one for each party), the first one now; else its own party's.
import { useState } from "preact/hooks";
import { html } from "../../html.js";
import { Icon } from "../../orkui.js";
import { whoOf, when } from "../../table/post.js";
import { nodeOf } from "../feed.js";
import { SpBack, SpCard, SpreadFrame } from "./shell.js";

/** A goal's stages, first to last: [{party, state: "done" | "now" | "next", done, total, at}]. */
export function stagesOf(n) {
  const legs = (n?.route || []).filter((r) => r.step === "party");
  if (legs.length) {
    let found = false;
    return legs.map((r) => {
      const now = !found && r.state !== "done";
      found ||= now;
      return { party: r.party, state: r.state === "done" ? "done" : now ? "now" : "next", done: r.done || 0, total: r.total || 0, at: r.at || "" };
    });
  }
  const parties = (n?.steps || []).map((s) => s.party).filter(Boolean);
  if (!parties.length && n?.goal) parties.push(n.goal);
  return parties.map((party, i) => ({ party, state: n?.state === "done" ? "done" : i === 0 ? "now" : "next", done: 0, total: 0, at: "" }));
}

const nameOfParty = (p) => whoOf(p).name;

export function Track({ slug }) {
  const n = nodeOf(slug), [turned, setTurned] = useState({}), [all, setAll] = useState(false);
  const stages = stagesOf(n), done = stages.filter((s) => s.state === "done"), now = stages.find((s) => s.state === "now"), next = stages.filter((s) => s.state === "next");
  const title = n?.short || n?.title || slug, card = { element: n?.element, hue: n?.hue, sign: n?.type?.sign || "" };
  const parties = [...new Set(stages.map((s) => nameOfParty(s.party)))];
  const say = !now ? "Every stage is done." : `${done.length} of ${stages.length} stages done, ${nameOfParty(now.party)} is at work. You need not look at the ones to come.`;
  const face = (i) => all || turned[i];
  return html`<${SpreadFrame} kind="track" title=${`${title}: where it is`} line=${parties.join(", then ")} say=${say}
      note="A stage to come turns face up when it starts. Pressed, a face-down card says only its name."
      acts=${next.length > 0 && html`<button type="button" class="ork-btn" aria-pressed=${String(all)} onClick=${() => setAll(!all)}><${Icon} name="eye" /><span>${all ? "Hide what comes" : "Show what comes"}</span></button>`}>
    <div class="sp-road">
      ${done.length > 0 && html`<div class="sp-col"><span class="sp-pile" aria-label="Stages done">${done.slice(-3).map((s, i, a) => html`<${SpCard} key=${i} party=${s.party} n=${card}
          name=${nameOfParty(s.party)} line="done" size="md" tilt=${(a.length - 1 - i) * 3 - 4} mark=${i === a.length - 1 ? "ok" : ""} />`)}</span><span class="sp-cap">done</span></div>`}
      ${now && html`<div class="sp-col sp-now"><span class="sp-meeple" data-race=${whoOf(now.party).race || "orkmaster"} aria-hidden="true"></span>
        <${SpCard} party=${now.party} n=${card} name=${nameOfParty(now.party)} line="now" size="xl" label=${`${nameOfParty(now.party)}, now`}>
          <p class="sp-card__text">${title}</p>
          ${now.total > 0 && html`<span class="cards-bar" aria-hidden="true"><i style=${`width:${Math.round(100 * now.done / now.total)}%`}></i></span>`}</${SpCard}>
        <span class="sp-cap">at work${now.at ? `, since ${when(now.at)}` : ""}</span></div>`}
      ${next.length > 0 && html`<div class="sp-col"><span class="sp-ahead">${next.map((s, i) => (face(i)
          ? html`<${SpCard} key=${i} party=${s.party} n=${card} name=${nameOfParty(s.party)} size="md" tilt=${i * 3} />`
          : html`<${SpBack} key=${i} tilt=${i * 3} name=${nameOfParty(s.party)} onPress=${() => setTurned({ ...turned, [i]: true })} />`))}</span>
        <span class="sp-cap">${all || Object.keys(turned).length ? "to come" : "to come, face down"}</span></div>`}
      ${!stages.length && html`<p class="sp-cap">This goal has no stages yet.</p>`}
    </div>
  </${SpreadFrame}>`;
}
