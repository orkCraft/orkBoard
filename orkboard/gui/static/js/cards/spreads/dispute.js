// Who says what on a goal (docs/mockups/spreads/, "dispute"): the goal in the middle with every leader's token, the leaders' views at its sides
// (an M card each, from the feed's posts about the goal, one a leader), the ways in the hand: each leader's way and *Your own words…*. Playing a
// way answers the goal's question when one is asked (`ideas.answer`, as the hand's way cards do); with none asked it is only said to the leaders
// (`ideas.way`, the contract proposed: the host keeps no such word yet, the mock logs it). 1, 2, 3 play the ways in the hand.
import { useEffect, useState } from "preact/hooks";
import { html, cls } from "../../html.js";
import { command, toast } from "../../link.js";
import { Icon } from "../../orkui.js";
import { HeadOf, PostHead, when, whoOf } from "../../table/post.js";
import { CardS, Token } from "../card.js";
import { nodeOf, viewsOf } from "../feed.js";
import { closeSpread } from "./open.js";
import { Key, SpCard, SpreadFrame, faceOf } from "./shell.js";

const WAYS = { risk: (who) => `Settle ${who}'s doubt first`, question: (who) => `Answer ${who}'s question first`, for: (who) => `Go with ${who}'s view` };

/** The ways of a goal: each leader's (the post's own `way` when the host says one, else its view in words), as the hand plays them. */
export function waysOf(views) {
  return views.map((v) => ({ leader: v.leader, view: v.view, ask: !!v.p.asks, name: v.p.way?.name || WAYS[v.view](whoOf(v.leader).name), line: `${whoOf(v.leader).name}'s way` }));
}

/** A leader's view as an M card, its head beside it in its party's colour. */
function Voice({ v, right }) {
  const w = whoOf(v.leader);
  return html`<div class=${cls("sp-voice", { "is-right": right })} data-race=${w.race || "orkmaster"}>
    <span class="sp-voice__av"><${HeadOf} w=${w} size="big" /></span>
    <article class="ork-card cards-m sp-voice__m" data-race=${w.race || "orkmaster"} data-kind=${v.p.kind} aria-label=${`${w.name}: ${v.p.text}`}>
      <${PostHead} leader=${v.leader} sub=${`its view · ${when(v.p.at)}`} asks=${!!v.p.asks} />
      <b class="sp-voice__title">${v.p.text}</b>
      <div class="cards-toks"><${Token} leader=${v.leader} view=${v.view} /></div></article></div>`;
}

export function Dispute({ slug }) {
  const n = nodeOf(slug), views = viewsOf(slug), ways = waysOf(views), [own, setOwn] = useState(null), title = n?.short || n?.title || slug;
  const asked = views.some((v) => v.p.asks);
  const send = (name, leader) => {
    const sent = asked ? command("ideas.answer", { slug, answers: [name], from: "spread", goal: true }) : command("ideas.way", { slug, leader, way: name });
    Promise.resolve(sent).then(() => { toast(`Sent: ${name}`); closeSpread(); }).catch((e) => toast(e?.message || "The way was not sent", "error"));
  };
  useEffect(() => {
    const key = (e) => {
      if (e.target.closest?.("input, textarea") || e.metaKey || e.ctrlKey || e.altKey) return;
      const i = "123456789".indexOf(e.key);
      if (i < 0) return;
      if (i < ways.length) send(ways[i].name, ways[i].leader); else if (i === ways.length) setOwn("");
    };
    addEventListener("keydown", key);
    return () => removeEventListener("keydown", key);
  });
  const names = views.map((v) => whoOf(v.leader).name), half = Math.ceil(views.length / 2);
  const say = views.length > 1 ? `They each put a token on it. Read ${views.length === 2 ? "both" : "them"}, then play a way from your hand.` : "One leader has said its view of it.";
  const mid = html`<${SpCard} party=${n?.goal} n=${faceOf(n)} name=${title} line=${n?.state === "talk" ? "being talked" : n?.state || ""} size="xl" label=${`${title}, with its tokens`}>
    <span class="cards-toks">${views.map((v) => html`<${Token} leader=${v.leader} view=${v.view} word=${v.view === "question" ? "?" : ""} />`)}</span></${SpCard}>`;
  return html`<${SpreadFrame} kind="dispute" title=${names.length > 1 ? `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]} disagree` : `${names[0] || "A leader"} on ${title}`}
      line=${`${title} · the Orkmaster brings it to you`} say=${say}
      note=${html`Play a way and ${names.length > 1 ? "every leader is" : "the leader is"} told. ${ways.map((_, i) => html`<${Key} k=${String(i + 1)} />`)}<${Key} k=${String(ways.length + 1)} />`}
      hand=${html`${ways.map((w, i) => html`<${CardS} key=${w.leader} n=${{ title: w.name, ...faceOf(n), leader: w.leader }} line=${w.line} asks=${w.view === "risk"} tilt=${i % 2 ? 2 : -2} onOpen=${() => send(w.name, w.leader)} />`)}
        <${CardS} n=${{ title: "Your own words…", element: "void", sign: "text", leader: "orkmaster" }} tilt=${-2} onOpen=${() => setOwn(own ?? "")} />`}
      acts=${own === null ? null : html`<textarea class="sp-own" aria-label="Your own words" placeholder="Say it in your own words" value=${own} onInput=${(e) => setOwn(e.currentTarget.value)} autofocus></textarea>
        <button type="button" class="ork-btn primary" disabled=${!own.trim()} onClick=${() => send(own.trim(), "")}><${Icon} name="check" /><span>Send these words</span></button>`}>
    <div class="sp-dispute">
      <div class="sp-voices">${views.slice(0, half).map((v) => html`<${Voice} key=${v.leader} v=${v} />`)}</div>
      ${mid}
      <div class="sp-voices">${views.slice(half).map((v) => html`<${Voice} key=${v.leader} v=${v} right=${true} />`)}</div>
    </div>
  </${SpreadFrame}>`;
}
