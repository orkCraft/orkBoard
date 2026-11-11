// A question answered in an L (goal 170, the talk of 11 November 2026; docs/mockups/table-cards/ ?face=desk&open=ask). On the table of
// cards (`cardsOn()`) a question's card of the hand, pressed, does not open the answer face over the pane: it opens an L over the table
// with the question, why it is asked, the leaders' tokens, its ways as buttons numbered 1–4 (the leader's pick marked, the last
// *Your own words…*) and the leaders' notes under *Why the tokens*. Every way sends what the hand's own face sends: a goal's question
// (`talk`, `project_q`) through questioncard.js `asking` (`ideas.talk_answer`, `ideas.project_answer`), a stop that asks (`asks`, `goal`)
// through answercards.js `stepWays`, `sendAnswers`, `decideStop` (`ideas.answer`). What the face has beyond the ways stays as buttons with
// its words: *Let <leader> decide*, *All the questions*, *Open…*, *Put it back*. Keys 1–4 play a way, Esc and *Close* put the L away
// and the focus goes back to the card it came from (back.js). Layout only: ask.css.
import { useEffect, useLayoutEffect, useRef, useState } from "preact/hooks";
import { signal } from "@preact/signals";
import { html, cls } from "../html.js";
import { Icon } from "../orkui.js";
import { board } from "../board/store.js";
import { mapData } from "../shell/store.js";
import { lower, tab } from "../frame/state.js";
import { mapName, partiesAll } from "../table/data.js";
import { HeadOf, when, whoOf } from "../table/post.js";
import { askedInfo, decideStop, sendAnswers } from "../hand/answers.js";
import { OWN_WORDS, answerSet, pickOf, stepWays } from "../hand/answercards.js";
import { stopByKey, stopsOfProject } from "../hand/data.js";
import { asking } from "../hand/questioncard.js";
import { named } from "../hand/todoform.js";
import { Index, Token } from "./card.js";
import { giveBack, keepTab } from "./back.js";
import { nodeOf, viewsOf } from "./feed.js";

/** The question asked in an L: `{key, scope, kind, from}` (the stop of the hand, the element the focus goes back to), null when none. */
export const asked = signal(null);
export const closeAsk = () => { const was = asked.peek(); asked.value = null; giveBack(was?.from); };

/** Whether a stop of the hand is a question this L answers. */
export const isQuestion = (s) => !!s && (((s.kind === "talk" || s.kind === "project_q") && !!s.card) || ((s.kind === "asks" || s.kind === "goal") && !!answerSet(s)));

/** The hand's card pressed (hand.js draws this in place of the lifted card in the cards' look): it opens the L and lowers the card. */
export function AskToL({ s, anchor }) {
  useLayoutEffect(() => { asked.value = { key: s.key, scope: s.scope, kind: s.kind, from: anchor || document.querySelector(`.frame-hand button.hand-card[data-key="${CSS.escape(s.key)}"]`) }; lower(); }, [s.key]);
  return null;
}

const WORDS = { pick: (lead) => `${lead}'s pick` };

/** What the L says of the question now, from the Board as it is: `{q, why, leader, goal, at, ways, own, decide, together, open, element, hue}`, null when the question is no more. */
function modelOf(a, step, kept, keep) {
  const stops = stopsOfProject(mapData.value, board.value?.needs_you || [], tab.value);
  if (a.kind === "talk" || a.kind === "project_q") {
    const mine = stops.filter((x) => x.scope === a.scope && x.card), top = mine[0];
    if (!top) return null;
    const k = asking(top, mine, { title: mapName(tab.value, partiesAll()), key: "" }), c = k.c, lead = top.party?.name || "The Orkmaster";
    return { s: top, q: c.q, why: c.why || "", leader: top.party?.slug || "orkmaster", lead, goal: top.row?.idea || "", at: top.row?.at || "", element: top.node?.element || "", hue: top.node?.hue || "",
      ways: k.choices.map((x, i) => ({ name: x.name, sub: [i === c.pick ? WORDS.pick(lead) : "", c.lines?.[i] || ""].filter(Boolean).join(" · "), pick: i === c.pick, run: () => k.answer({ pick: i }) })),
      own: (text) => k.answer({ text }), decide: { label: k.decide.label, run: k.decide.onDecide }, together: k.together ? { label: k.together.label, run: k.together.onTogether } : null, open: null };
  }
  const s = stopByKey(stops, a.key), set = s ? answerSet(s) : null;
  if (!s || !set || !set.asked.length) return null;
  const i = Math.min(step, set.asked.length - 1), q = set.asked[i], info = askedInfo(s), lead = s.party?.name || "The Orkmaster", many = set.asked.length > 1;
  const ways = stepWays(s, set.asked, i, kept, keep);
  return { s, q: q.ask, why: q.why || "", leader: s.party?.slug || "orkmaster", lead, goal: info.isGoal ? info.target : s.node?.slug || info.target, at: s.row?.at || "", element: s.node?.element || "", hue: s.node?.hue || "",
    ways: ways.map((w) => ({ name: w.name, sub: [w.pick ? WORDS.pick(lead) : "", w.own ? w.line : "", w.cost ? w.cost.gem : ""].filter(Boolean).join(" · "), pick: w.pick, run: w.run })),
    own: (text) => sendAnswers(s, [...kept.slice(0, i), text, ...set.asked.slice(i + 1).map(pickOf)]), decide: { label: `Let ${named(info.name)} decide`, run: () => decideStop(s) }, together: null,
    open: { label: "Open…", run: () => set.open() }, step: many ? `${i + 1}/${set.asked.length}` : "" };
}

/** The leaders' views of the goal, but the asker's own: [{leader, view, name, text}]. */
const notesOf = (m) => (m.goal ? viewsOf(m.goal).filter((v) => v.leader !== m.leader).map((v) => ({ leader: v.leader, view: v.view, name: whoOf(v.leader).name, text: v.p.text })) : []);

/** L: the question, its ways. */
export function AskL() {
  const a = asked.value, root = useRef(), live = useRef({}), [step, setStep] = useState(0), [kept, setKept] = useState([]), [pen, setPen] = useState(false), [words, setWords] = useState("");
  const m = a ? modelOf(a, step, kept, (all) => { setKept(all); setStep(step + 1); }) : null;
  live.current = { m, pen };
  useEffect(() => { setStep(0); setKept([]); setPen(false); setWords(""); }, [a?.key]);
  useEffect(() => { setPen(false); setWords(""); }, [m?.q]);                                 // the next question of the goal: its own field
  useEffect(() => { if (a && !m) closeAsk(); }, [a, !m]);                                    // answered, or gone from the Board: the L goes with it
  useEffect(() => {
    if (!a) return undefined;
    const key = (e) => {
      const { m: now, pen: writing } = live.current;
      if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); if (writing) { setPen(false); root.current?.querySelector("[data-way='own']")?.focus(); } else closeAsk(); return; }
      keepTab(root.current, e);
      if (!now || writing || e.ctrlKey || e.metaKey || e.altKey || /^(INPUT|TEXTAREA)$/.test(e.target?.tagName || "") || !/^[1-9]$/.test(e.key)) return;
      const n = Number(e.key) - 1;
      if (n < now.ways.length) { e.preventDefault(); e.stopPropagation(); now.ways[n].run(); }
      else if (n === now.ways.length) { e.preventDefault(); e.stopPropagation(); setPen(true); }
    };
    addEventListener("keydown", key, true);
    return () => removeEventListener("keydown", key, true);
  }, [a]);
  useEffect(() => { if (m) (root.current?.querySelector(".cards-way.is-pick") || root.current?.querySelector(".cards-way"))?.focus({ preventScroll: true }); }, [a?.key, m?.q]);
  useEffect(() => { if (pen) root.current?.querySelector(".cards-ask__field")?.focus({ preventScroll: true }); }, [pen]);
  if (!a || !m) return null;
  const notes = notesOf(m), others = viewsOf(m.goal).filter((v) => v.leader !== m.leader), goal = nodeOf(m.goal), w = whoOf(m.leader), face = { n: { element: m.element, hue: m.hue, sign: "question" } };
  const send = () => { const said = words.trim(); if (said) m.own(said); };
  return html`<div class="cards-veil" onClick=${(e) => { if (e.target === e.currentTarget) closeAsk(); }}>
    <article ref=${root} class="ork-card cards-l cards-ask" role="dialog" aria-modal="true" aria-label=${`${m.lead} asks you: ${m.q}`} data-race=${w.race || "orkmaster"} data-from="ask">
      <${Index} ...${face} />
      <button type="button" class="ork-btn quiet cards-l__shut" onClick=${closeAsk}><${Icon} name="close" /><span>Close</span></button>
      <header class="cards-ask__who"><span class="cards-ask__av"><${HeadOf} w=${w} /></span><span><b>${m.lead} asks you</b><small>${[goal?.short || goal?.title || "", when(m.at), m.step].filter(Boolean).join(" · ")}</small></span></header>
      <h2 class="cards-l__title cards-ask__q">${m.q}</h2>
      ${m.why && html`<p class="cards-l__body cards-ask__why">${m.why}</p>`}
      ${others.length > 0 && html`<div class="cards-toks is-big">${others.map((v) => html`<${Token} leader=${v.leader} view=${v.view} word=${whoOf(v.leader).name} />`)}</div>`}
      <div class="cards-ask__ways" role="group" aria-label="Ways">
        ${m.ways.map((x, i) => html`<button type="button" key=${`${m.q}:${i}`} class=${cls("cards-way", { "is-pick": x.pick })} data-way=${i} data-pick=${x.pick ? "1" : undefined} onClick=${x.run}>
          <kbd class="cards-way__k" aria-hidden="true">${i + 1}</kbd><span class="cards-way__t"><b>${x.name}</b>${x.sub && html`<small>${x.sub}</small>`}</span></button>`)}
        <button type="button" class="cards-way is-own" data-way="own" aria-expanded=${String(pen)} onClick=${() => setPen(!pen)}>
          <kbd class="cards-way__k" aria-hidden="true">${m.ways.length + 1}</kbd><span class="cards-way__t"><b>${OWN_WORDS}</b></span></button>
        ${pen && html`<div class="cards-ask__pen"><textarea class="ork-field cards-ask__field" rows="3" aria-label="Your own answer" placeholder=${`Your words to ${m.lead}…`} value=${words}
            onInput=${(e) => setWords(e.currentTarget.value)} onKeyDown=${(e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); } }}></textarea>
          <button type="button" class="ork-btn primary" data-act="send-words" disabled=${!words.trim()} onClick=${send}>Send to ${m.lead}</button></div>`}
      </div>
      <div class="cards-ask__acts" role="group" aria-label="More answers">
        <button type="button" class="ork-btn quiet" data-act="decide" onClick=${m.decide.run}>${m.decide.label}</button>
        ${m.together && html`<button type="button" class="ork-btn quiet" data-act="together" onClick=${() => { closeAsk(); m.together.run(); }}>${m.together.label}</button>`}
        ${m.open && html`<button type="button" class="ork-btn quiet" data-act="open" onClick=${() => { closeAsk(); m.open.run(); }}>${m.open.label}</button>`}
        <button type="button" class="ork-btn quiet" data-act="put" onClick=${closeAsk}>Put it back</button>
      </div>
      ${notes.length > 0 && html`<section class="cards-ask__notes" aria-label="Why the tokens"><p class="cards-lab">Why the tokens</p>
        ${notes.map((n) => html`<p class="cards-ask__note"><${Token} leader=${n.leader} view=${n.view} word=${n.name} /><span>${n.text}</span></p>`)}</section>`}
      <footer class="cards-ask__foot"><span>From the hand</span><span>${m.lead} waits for it</span></footer>
      <${Index} ...${face} turned=${true} />
    </article></div>`;
}
