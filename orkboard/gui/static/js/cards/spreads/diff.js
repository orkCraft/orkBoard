// A post's words before and after (docs/mockups/spreads/, "diff"): two L-size cards side by side, the one before muted with the words taken
// out struck, the one after with the words put in marked. The host's post says only its words now (`p.text`); a post that carries the words
// before (`p.before`, the contract proposed) is compared word by word. Where there are none, the right card is the post as it stands and the
// left says *Before: not recorded*. ← and → light one card or the other.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { whoOf, when } from "../../table/post.js";
import { Index, Token } from "../card.js";
import { nodeOf, tokensOf } from "../feed.js";
import { Key, SpreadFrame } from "./shell.js";

/** Two texts compared word by word: {before: [{t, out}], after: [{t, in}]}; a text too long to compare is marked whole. */
export function wordsDiff(before, after) {
  const a = before.split(/(\s+)/).filter(Boolean), b = after.split(/(\s+)/).filter(Boolean);
  if (a.length * b.length > 250000) return { before: a.map((t) => ({ t, out: true })), after: b.map((t) => ({ t, in: true })) };
  const m = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i -= 1) for (let j = b.length - 1; j >= 0; j -= 1) m[i][j] = a[i] === b[j] ? m[i + 1][j + 1] + 1 : Math.max(m[i + 1][j], m[i][j + 1]);
  const x = [], y = [];
  let i = 0, j = 0;
  while (i < a.length || j < b.length) {
    if (i < a.length && j < b.length && a[i] === b[j]) { x.push({ t: a[i++] }); y.push({ t: b[j++] }); }
    else if (j >= b.length || (i < a.length && m[i + 1][j] >= m[i][j + 1])) x.push({ t: a[i++], out: true });
    else y.push({ t: b[j++], in: true });
  }
  return { before: x, after: y };
}

/** The words of a text with its runs of taken-out or put-in words marked as one. */
function Words({ parts }) {
  const runs = [];
  for (const w of parts) {
    const kind = w.out ? "out" : w.in ? "in" : "";
    if (runs.length && runs[runs.length - 1].kind === kind) runs[runs.length - 1].t += w.t; else runs.push({ kind, t: w.t });
  }
  return runs.map((r, i) => (r.kind === "out" ? html`<del key=${i}>${r.t.trim()}</del>${" "}` : r.kind === "in" ? html`<ins key=${i}>${r.t.trim()}</ins>${" "}` : r.t));
}

export function Diff({ p }) {
  const [side, setSide] = useState("after"), w = whoOf(p.leader), n = nodeOf(p.goal);
  useEffect(() => {
    const key = (e) => { if (e.key === "ArrowLeft") setSide("before"); else if (e.key === "ArrowRight") setSide("after"); };
    addEventListener("keydown", key);
    return () => removeEventListener("keydown", key);
  }, []);
  const known = typeof p.before === "string" && p.before.length > 0, d = known ? wordsDiff(p.before, p.text) : null;
  const goal = n?.short || n?.title || "", card = { element: n?.element, hue: n?.hue, sign: n?.type?.sign || "" }, tokens = p.goal ? tokensOf(p.goal) : [];
  const say = known ? "The words struck were taken out, the words marked were put in. The rest is as you read it." : "The host did not record the words before; here is the post as it stands.";
  return html`<${SpreadFrame} kind="diff" title=${p.kind === "change" ? `${w.name} changed ${goal || "its words"}` : `${w.name}: what changed`} line=${[goal, when(p.at)].filter(Boolean).join(" · ")} say=${say}
      note=${html`<${Key} k="←" /><${Key} k="→" /> turn between before and after.`}>
    <div class="sp-diff">
      <article class=${cls("ork-card sp-l is-before", { "is-lit": side === "before" })} data-race=${w.race || "orkmaster"} aria-current=${side === "before" ? "true" : undefined} aria-label="Before">
        <${Index} n=${card} /><span class="sp-tag was">Before${known && p.before_at ? ` · ${when(p.before_at)}` : ""}</span>
        <h2>${goal || w.name}</h2>
        <p>${known ? html`<${Words} parts=${d.before} />` : "Before: not recorded"}</p></article>
      <span class="sp-arrow" aria-hidden="true">→</span>
      <article class=${cls("ork-card sp-l", { "is-lit": side === "after" })} data-race=${w.race || "orkmaster"} aria-current=${side === "after" ? "true" : undefined} aria-label="After">
        <${Index} n=${card} /><span class="sp-tag now">After${p.at ? ` · ${when(p.at)}` : ""}</span>
        <h2>${goal || w.name}</h2>
        <p>${known ? html`<${Words} parts=${d.after} />` : p.text}</p>
        ${tokens.length > 0 && html`<div class="cards-toks">${tokens.map((t) => html`<${Token} ...${t} />`)}</div>`}</article>
    </div>
  </${SpreadFrame}>`;
}
