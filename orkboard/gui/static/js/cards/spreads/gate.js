// A goal at the gate of main as cards (docs/mockups/spreads/, "gate"): the goal in the middle in a dashed portal ring, its checks round it as
// small cards, each turned green with a check when it passed, face up and red with what failed, face down while it waits or runs. *To main* is
// disabled with its reason while a check is not green. The checks are the host's (`main_checks`, table/checks.js: {name, state, words}) when
// it holds them; the recording holds none (its `ideas.gate` reply says only what dev holds that main lacks, and a goal's `flag`/`route` that it
// is done), so then they are drawn from a fixed list: the critical tests, the tests of what the goal touched, each party's leader's acceptance
// (done when the stage is) and the reviewers that apply to it (`n.checks`), every one not run yet.
import { html, cls } from "../../html.js";
import { Icon } from "../../orkui.js";
import { gateData } from "../../shell/store.js";
import { checksOf } from "../../table/checks.js";
import { whoOf } from "../../table/post.js";
import { Token } from "../card.js";
import { nodeOf, tokensOf } from "../feed.js";
import { closeSpread } from "./open.js";
import { SpBack, SpCard, SpreadFrame } from "./shell.js";
import { stagesOf } from "./track.js";
import { toMain } from "../../table/portal.js";            // the discard's own way to main: its checks, then the merge
import { phaseOf } from "../../table/data.js";
import { Seal } from "../matframe.js";

const FIXED_TESTS = ["Critical tests", "Tests of what it touched"];
const STATE = { done: "passed", passed: "passed", green: "passed", failed: "failed", red: "failed", running: "running", testing: "running" };

/** The checks of a goal at the gate: [{name, state: passed | failed | running | waiting, words, party}]. */
export function checksFor(slug, n) {
  const party = n?.goal || "orkmaster", real = checksOf(slug);
  const tests = real.length ? real.map((c) => ({ name: c.name, state: STATE[c.state] || "waiting", words: c.words || "" })) : FIXED_TESTS.map((name) => ({ name, state: "waiting", words: "" }));
  const accepts = stagesOf(n).map((s) => ({ name: `${whoOf(s.party).name} accepts`, state: s.state === "done" ? "passed" : "waiting", words: "its section's Done when", party: s.party }));
  const reviewers = (n?.checks || []).filter((c) => c.applies).map((c) => ({ name: c.name, state: STATE[c.state] || "waiting", words: "" }));
  return [...tests, ...accepts, ...reviewers].map((c) => ({ party, ...c }));
}

const WORD = { passed: "passed", failed: "failed", running: "running", waiting: "waits to run" };

export function Gate({ slug, opened }) {
  const from = opened === "hand" ? "hand" : "mat";
  const n = nodeOf(slug), checks = checksFor(slug, n), g = gateData.value;
  const title = n?.short || n?.title || slug, tokens = tokensOf(slug);
  const green = checks.filter((c) => c.state === "passed").length, red = checks.find((c) => c.state === "failed"), open = checks.filter((c) => c.state !== "passed" && c.state !== "failed");
  const say = red ? `${red.name} is red${red.words ? `: ${red.words}` : ""}. To main stays shut until it is mended.`
    : `${green} of ${checks.length} checks green${open.length ? `; ${open.map((c) => c.name).slice(0, 2).join(" and ")} still to run` : ""}. To main opens when they turn.`;
  const reason = red ? `To main is sealed: ${red.name} is red` : open.length ? `To main opens after ${open.length === 1 ? open[0].name : `${open.length} checks`}` : "";
  const line = g?.commits ? `${g.commits} commits, ${g.files} files for ${g.main || "main"}` : "Every check turns green, then the portal opens";
  const at = (i) => { const a = (2 * Math.PI * i) / checks.length - Math.PI / 2; return `left:${(50 + 38 * Math.cos(a)).toFixed(1)}%;top:${(50 + 44 * Math.sin(a)).toFixed(1)}%`; };
  const card = { element: n?.element, hue: n?.hue, sign: n?.type?.sign || "" };
  return html`<${SpreadFrame} kind="gate" title=${`${title} at the gate`} line=${line} say=${say} note="A red check stays face up with what failed and who mends it."
      phase=${phaseOf(slug) || "work"}
      seal=${html`<${Seal} word="To main" why=${reason || "Merge into main: it cannot be undone"} lit=${!reason} kind="merge" onPress=${() => toMain(slug, from).then(closeSpread).catch(() => {})} />`}>
    <div class="sp-gate"><svg class="sp-ring" viewBox="0 0 420 420" aria-hidden="true"><circle cx="210" cy="210" r="208" /></svg>
      <div class="sp-gate__mid"><${SpCard} party=${n?.goal} n=${card} name=${title} line=${n?.state === "review" ? "to review" : "ready for main"} size="xl" portal=${true}>
        ${tokens.length > 0 && html`<span class="cards-toks">${tokens.map((t) => html`<${Token} ...${t} />`)}</span>`}</${SpCard}></div>
      ${checks.map((c, i) => html`<div class=${cls("sp-gk", `is-${c.state}`)} style=${at(i)} key=${i} role="group" aria-label=${`${c.name}: ${WORD[c.state]}`} data-check=${c.state}>
        ${c.state === "passed" || c.state === "failed"
          ? html`<${SpCard} party=${c.party} kind="decision" name=${c.name} size="sm" mark=${c.state === "passed" ? "ok" : "no"} />`
          : html`<${SpBack} size="sm" />`}
        <small>${c.state === "passed" || c.state === "failed" ? (c.words || WORD[c.state]) : html`<${Icon} name="clock" /> ${c.name}${c.state === "running" ? ", running" : ""}`}</small></div>`)}
    </div>
  </${SpreadFrame}>`;
}
