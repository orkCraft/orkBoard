// A goal at the gate, a battle nobody disputes (goal "The battle and the gate", stage L; decisions §300.8, §303; docs/mockups/mats/, the shots gate and gate-ok), laid upright in 171's mat frame on the host's answer
// `ideas.gate_guards {idea}` (gui/ideas_battle.py), asked when the mat opens: the zone *What its tests guard* above (each failing test's §N face up as a decision card with the gate's no, three at most and the rest a
// pile; a failing test naming none as a part card with its file; the agreeing §N a pile by its thickness, never a number, pressed it spreads), the line (one column, the gate's, *No total* beside it) and the zone *Yours*
// below with the goal's stack. The hand while it is open holds *Fix it* and *The test is out of date*; the seal is *Send to <branch>* on the way to dev, *Merge into main* on the way to main, dim with its why while a check
// disagrees. Where the goal is says what Fix it does (decisions §303.5): on its branch its stage runs again (`ideas.gate_fix_stage`, sealed, its cost said), done a new Fix goal is made (`ideas.gate_fix_goal`, one press with
// Undo). *The test is out of date* asks Tech (`ideas.ask_leader`, a paid pass on the seal with its cost said). Every move says where it was pressed (`from`: "mat", or "hand" when its hand card opened the mat).
import { useEffect, useState } from "preact/hooks";
import { html } from "../../html.js";
import { command } from "../../link.js";
import { phaseOf } from "../../table/data.js";
import { toMain } from "../../table/portal.js";            // the discard's own way to main: its checks, then the merge
import { gateData } from "../../shell/store.js";
import { costWords, useAskCost } from "../askcost.js";
import { devName } from "../../hand/devcard.js";
import { nodeOf } from "../feed.js";
import { TokenDot } from "../handtokens.js";
import { Seal, Zone } from "../matframe.js";
import { playMove } from "../played.js";
import { closeSpread } from "./open.js";
import { SpBack, SpCard, SpreadFrame, Thick, faceOf } from "./shell.js";

const FACE_UP = 3;           // failing decisions laid face up; the rest a pile
const TOKEN_MAX = 5;         // squares of a kind on the gate's token

/** What the host holds of the goal's last gate: `{way, failing, files, agreeing, cost}`; null while it is asked, false when it could not be read. */
function useGuards(slug) {
  const [got, set] = useState(null);
  useEffect(() => {
    let live = true;
    set(null);
    command("ideas.gate_guards", { idea: slug }, true).then((r) => live && set(r && typeof r === "object" ? r : false)).catch(() => live && set(false));
    return () => { live = false; };
  }, [slug]);
  return got;
}

/** The ids of the tests that fail, once each. */
export const failingIds = (g) => [...new Set([...(g?.failing || []), ...(g?.files || [])].flatMap((x) => x.ids || []))];
export const disagreeWords = (n) => (n === 1 ? "1 check disagrees" : `${n} checks disagree`);
const testsWords = (ids) => (ids.length === 1 ? "1 test fails" : `${ids.length} tests fail`);

/** A decision face up: its § for its picture, its number and title; `no` when a test guarding it fails, `ok` when it agrees. */
export function DecisionCard({ number, title, mark = "", note = "" }) {
  return html`<${SpCard} kind="decision" size="md" party="orkmaster" n=${{ sign: "balance" }} name=${`§${number}`} line=${title} mark=${mark} label=${`§${number} ${title}${note ? `: ${note}` : ""}`}>
    <span class="gt-sect" aria-hidden="true">§</span></${SpCard}>`;
}

/** A test naming no decision, as the part it lives in: its file in the code face. */
export const PartCard = ({ file, ids }) => html`<${SpCard} kind="part" size="md" party="orkmaster" n=${{ sign: "compass" }} name=${file.split("/").flatMap((w, i) => (i ? [html`/<wbr />`, w] : [w]))} line="fails" mark="no" label=${`${file}: ${testsWords(ids)}`} />`;

export function Gate({ slug, opened }) {
  const from = opened === "hand" ? "hand" : "mat";
  const n = nodeOf(slug), g = useGuards(slug), ask = useAskCost(), [pick, setPick] = useState(""), [spread, setSpread] = useState(false);
  const title = n?.short || n?.title || slug, ready = !!g && !!g.way, dev = g?.way === "dev";
  const failing = g?.failing || [], files = g?.files || [], agreeing = g?.agreeing || [], bad = failingIds(g).length;
  const branch = dev ? devName() : gateData.value?.main || "main";
  const up = failing.slice(0, FACE_UP), more = failing.slice(FACE_UP);

  const hand = ready && bad > 0 ? [
    html`<button key="fix" type="button" class="ork-card gt-way" data-way="fix" aria-pressed=${dev ? String(pick === "fix") : undefined} aria-label=${`Fix it: ${dev ? "its stage again, through the seal" : "a new Fix goal, one press"}`}
      onClick=${() => (dev ? setPick(pick === "fix" ? "" : "fix") : playMove("ideas.gate_fix_goal", { idea: slug }, { from, goal: slug, said: "Made a Fix goal for what the gate found.", done: closeSpread }))}>
      <b>Fix it</b><small>${dev ? "back to work: its stage again, sealed with its cost" : "makes a new Fix goal; one press, you can undo it"}</small></button>`,
    html`<button key="stale" type="button" class="ork-card gt-way" data-way="stale" aria-pressed=${String(pick === "stale")} aria-label="The test is out of date: asks Tech, a new decision comes first"
      onClick=${() => setPick(pick === "stale" ? "" : "stale")}><b>The test is out of date</b><small>asks Tech; a new decision comes first, sealed with its cost</small></button>`,
  ] : null;

  let seal;
  if (!ready) seal = html`<${Seal} word=${`Send to ${branch}`} why=${g === false ? "The gate could not be read" : "reading the gate"} kind="dev" />`;
  else if (pick === "stale") {
    const text = `The gate is red on ${failingIds(g).slice(0, 3).join(", ")}. Is the test out of date? If it is, a new decision comes first. Say what the decision should be.`;
    seal = html`<${Seal} word="Ask Tech" why=${ask.words} lit=${ask.ready} kind="ask" onPress=${() => playMove("ideas.ask_leader", { slug, leader: "tech", text, sealed: true }, { from, goal: slug, sealed: true, said: "Tech is asked: a new decision comes first.", done: () => setPick("") })} />`;
  } else if (pick === "fix" && dev) {
    seal = html`<${Seal} word="Fix it" why=${costWords(g.cost)} lit=${true} kind="fix" onPress=${() => playMove("ideas.gate_fix_stage", { idea: slug, sealed: true }, { from, goal: slug, sealed: true, said: "Its stage runs again.", done: closeSpread })} />`;
  } else if (bad > 0) {
    seal = html`<${Seal} word=${dev ? `Send to ${branch}` : "Merge into main"} why=${disagreeWords(bad)} kind=${dev ? "dev" : "merge"} />`;
  } else if (dev) {
    seal = html`<${Seal} word=${`Send to ${branch}`} why="every check agrees" lit=${true} kind="dev" onPress=${() => playMove("ideas.goal_to_dev", { idea: slug, sealed: true }, { from, goal: slug, sealed: true, said: `Sent to ${branch}.`, done: closeSpread })} />`;
  } else {
    seal = html`<${Seal} word="Merge into main" why="it cannot be undone" lit=${true} kind="merge" onPress=${() => toMain(slug, from).then(closeSpread).catch(() => {})} />`;
  }

  const say = !ready ? (g === false ? "The gate could not be read" : "Reading what its tests guard")
    : bad ? `${disagreeWords(bad)}: ${failing.length ? `it guards ${failing.map((f) => `§${f.number}`).join(", ")}` : "it names no decision"}` : "Every check agrees";
  const token = { leader: "release", checks: [...Array.from({ length: Math.min(agreeing.length, TOKEN_MAX) }, () => ({ kind: "ok" })), ...Array.from({ length: Math.min(failing.length + files.length, TOKEN_MAX) }, () => ({ kind: "b" }))] };
  const nothing = ready && !agreeing.length && !failing.length && !files.length;

  return html`<${SpreadFrame} kind="gate" title=${`Gate: ${title} → ${branch}`} line="always, then the tests of what it touched" say=${say} note=${pick === "stale" ? "Tech is asked first; a new decision comes before the test changes." : bad ? "Above: what its tests guard. Below: your stack." : "Nobody disputes it: one move."}
      phase=${phaseOf(slug)} hand=${hand} seal=${seal}>
    <div class="gt" data-way=${g?.way || ""} data-red=${bad ? "1" : "0"}>
      <${Zone} label="What its tests guard" empty=${nothing ? "no test names a decision" : ""} class="gt-guards">
        ${agreeing.length > 0 && (spread
          ? html`<div class="gt-spread" role="group" aria-label="The checks that agree">${agreeing.map((a) => html`<${DecisionCard} key=${a.number} number=${a.number} title=${a.title} mark="ok" note="its tests agree" />`)}
            <button type="button" class="ork-btn gt-fold" data-act="fold" onClick=${() => setSpread(false)}>Gather them</button></div>`
          : html`<button type="button" class="gt-agree" data-act="agree" aria-expanded="false" aria-label="The checks that agree, a pile. Press to spread it." onClick=${() => setSpread(true)}>
              <${Thick} n=${agreeing.length} label=${bad ? "agree · press to spread" : "all agree · press to spread"} /></button>`)}
        ${up.map((f) => html`<${DecisionCard} key=${f.number} number=${f.number} title=${f.title} mark="no" note=${`${testsWords(f.ids)}, the gate says no`} />`)}
        ${more.length > 0 && html`<div class="gt-more" role="group" aria-label=${`${more.length} more decisions with a test that fails, face down`}>${more.map((f, i) => html`<${SpBack} key=${f.number} tilt=${i % 2 ? 3 : -3} size="sm" />`)}</div>`}
        ${files.map((f) => html`<${PartCard} key=${f.file} file=${f.file} ids=${f.ids} />`)}
      </${Zone}>
      ${ready && html`<div class="gt-line" role="group" aria-label="The gate's line">
        <span class="gt-ax ork-plate">The gate</span><${TokenDot} v=${token} /><span class="gt-nt ork-plate">No total</span></div>`}
      <${Zone} label="Yours" class="gt-yours">
        <div class="gt-stack"><${SpCard} party=${n?.goal} n=${faceOf(n)} name=${title} line="your stack" size="md" label=${`${title}, your stack`} /></div>
      </${Zone}>
    </div>
  </${SpreadFrame}>`;
}
